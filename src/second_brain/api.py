import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from second_brain.rag import RAGPipeline
from second_brain.routes.documents import router as documents_router


app = FastAPI(
    title="Second Brain API",
    version="1.0.0"
)


frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url
    ],
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
def chat(request: QueryRequest):

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