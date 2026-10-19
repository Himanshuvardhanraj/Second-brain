import io
import uuid
from typing import List, Dict

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pypdf import PdfReader

from second_brain.supabase_client import supabase
from second_brain.rag import RAGPipeline
from second_brain.auth import current_user


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
    file: UploadFile = File(...),
    user=Depends(current_user),
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

    safe_filename = file.filename.replace("/", "_").replace("\\", "_")
    storage_path = f"{user['sub']}/{document_id}/{safe_filename}"

    # 1. Upload original PDF
    try:
        bucket = supabase.storage.from_("documents")
        try:
            bucket.upload(
                storage_path,
                file_bytes,
                {"content-type": "application/pdf", "upsert": "true"},
            )
        except Exception as upload_error:
            if "not found" not in str(upload_error).lower() and "bucket" not in str(upload_error).lower():
                raise
            supabase.storage.create_bucket("documents", options={"public": False})
            bucket.upload(
                storage_path,
                file_bytes,
                {"content-type": "application/pdf", "upsert": "true"},
            )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not store the PDF. Create a private Supabase Storage bucket named 'documents'.",
        ) from exc

    # 2. Insert document metadata
    try:
        supabase.table("documents").insert({
            "id": document_id,
            "filename": safe_filename,
            "file_path": storage_path,
            "file_type": file.content_type,
            "file_size": len(file_bytes),
        }).execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not save PDF metadata") from exc

    # 3. Extract + chunk
    try:
        chunks = extract_pdf_chunks(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable PDF") from exc

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in PDF"
        )

    # 4. Embed + store chunks
    try:
        rag.add_chunks(document_id, chunks)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not index the PDF for retrieval") from exc

    return {
        "message": "PDF uploaded and indexed successfully",
        "document_id": document_id,
        "filename": safe_filename,
        "chunks_created": len(chunks)
    }