import io
import logging
import re
import unicodedata
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


logger = logging.getLogger(__name__)
rag = RAGPipeline()


def ensure_documents_bucket():
    try:
        buckets = supabase.storage.list_buckets()
        if any(getattr(bucket, "name", None) == "documents" for bucket in buckets):
            return
        if any(isinstance(bucket, dict) and bucket.get("name") == "documents" for bucket in buckets):
            return
        supabase.storage.create_bucket(
            "documents",
            options={"public": False, "file_size_limit": 52428800},
        )
    except Exception:
        logger.exception("Could not verify the documents storage bucket")
        raise


def chunk_text(
    text: str,
    chunk_size: int = 1400,
    overlap: int = 220
) -> List[str]:
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= chunk_size:
            current = f"{current}\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        tail = current[-overlap:] if current else ""
        current = f"{tail}\n{paragraph}".strip()
    if current:
        chunks.append(current)
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

    original_filename = file.filename
    safe_filename = unicodedata.normalize("NFKD", original_filename).encode(
        "ascii", "ignore"
    ).decode("ascii")
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "_", safe_filename).strip("._")
    if not safe_filename:
        safe_filename = f"document-{document_id}.pdf"
    storage_path = f"{user['sub']}/{document_id}/{safe_filename}"

    # 1. Upload original PDF
    try:
        ensure_documents_bucket()
        bucket = supabase.storage.from_("documents")
        bucket.upload(
            storage_path,
            file_bytes,
            {
                "content-type": "application/pdf",
                "cache-control": "3600",
                "upsert": "true",
            },
        )
    except Exception as exc:
        logger.exception("PDF storage failed for document %s", document_id)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PDF_STORAGE_UNAVAILABLE",
                "message": "PDF storage is temporarily unavailable. Please try again later.",
            },
        ) from exc

    # 2. Insert document metadata
    try:
        supabase.table("documents").insert({
            "id": document_id,
            "filename": original_filename,
            "file_path": storage_path,
            "file_type": file.content_type,
            "file_size": len(file_bytes),
            "user_id": user["sub"],
        }).execute()
    except Exception as exc:
        logger.exception("PDF metadata insert failed for document %s", document_id)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PDF_METADATA_UNAVAILABLE",
                "message": "The PDF could not be registered. Please try again later.",
            },
        ) from exc

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
        rag.add_chunks(document_id, user["sub"], chunks)
    except Exception as exc:
        logger.exception("PDF indexing failed for document %s", document_id)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PDF_INDEXING_UNAVAILABLE",
                "message": "The PDF was uploaded, but indexing is temporarily unavailable.",
            },
        ) from exc

    return {
        "message": "PDF uploaded and indexed successfully",
        "document_id": document_id,
        "filename": original_filename,
        "chunks_created": len(chunks)
    }