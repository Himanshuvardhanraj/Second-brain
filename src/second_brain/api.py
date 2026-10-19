import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from second_brain.rag import RAGPipeline
from second_brain.routes.documents import router as documents_router
from second_brain.routes.auth import router as auth_router
from second_brain.routes.notes import router as notes_router
from second_brain.auth import current_user


app = FastAPI(
    title="Second Brain API",
    version="1.0.0"
)


frontend_urls = [
    url.strip()
    for url in os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    ).split(",")
    if url.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


rag = RAGPipeline()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "second-brain-api"
    }


@app.post("/api/chat")
def chat(request: QueryRequest, user=Depends(current_user)):

    try:

        return rag.query(
            request.question,
            top_k=request.top_k
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


app.include_router(
    documents_router
)
app.include_router(auth_router)
app.include_router(notes_router)