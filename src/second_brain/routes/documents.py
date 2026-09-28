import io
import uuid
from typing import List, Dict

from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader

from second_brain.supabase_client import supabase
from second_brain.rag import RAGPipeline


router = APIRouter(
    prefix="/api/documents",
    tags=["documents"]
)


rag = RAGPipeline()


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150
) -> List[str]:

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def extract_pdf_chunks(
    file_bytes: bytes
) -> List[Dict]:

    reader = PdfReader(
        io.BytesIO(file_bytes)
    )

    chunks = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        page_chunks = chunk_text(text)

        for chunk in page_chunks:
            chunks.append({
                "content": chunk,
                "page_number": page_number,
                "metadata": {
                    "page": page_number
                }
            })

    return chunks


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty"
        )

    document_id = str(uuid.uuid4())

    storage_path = (
        f"{document_id}/{file.filename}"
    )

    # 1. Upload original PDF
    supabase.storage \
        .from_("documents") \
        .upload(
            storage_path,
            file_bytes,
            {
                "content-type": "application/pdf"
            }
        )

    # 2. Insert document metadata
    supabase.table("documents").insert({
        "id": document_id,
        "filename": file.filename,
        "file_path": storage_path,
        "file_type": file.content_type,
        "file_size": len(file_bytes)
    }).execute()

    # 3. Extract + chunk
    chunks = extract_pdf_chunks(
        file_bytes
    )

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in PDF"
        )

    # 4. Embed + store chunks
    rag.add_chunks(
        document_id,
        chunks
    )

    return {
        "message": "PDF uploaded and indexed successfully",
        "document_id": document_id,
        "filename": file.filename,
        "chunks_created": len(chunks)
    }