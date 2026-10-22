import os
import json
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from second_brain.rag import RAGPipeline
from second_brain.routes.documents import router as documents_router
from second_brain.routes.auth import router as auth_router
from second_brain.routes.notes import router as notes_router
from second_brain.routes.feedback import router as feedback_router
from second_brain.auth import current_user
from second_brain.llm import GeminiQuotaError


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
    top_k: int = Field(default=8, ge=1, le=50)


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
            user["sub"],
            top_k=request.top_k
        )
    except GeminiQuotaError as exc:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "AI_QUOTA_EXHAUSTED",
                "message": "AI answer generation is temporarily unavailable because the Gemini quota is exhausted. Please try again after the quota resets.",
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CHAT_UNAVAILABLE",
                "message": "The answer could not be generated. Please try again later.",
            },
        ) from exc


@app.post("/api/chat/stream")
def chat_stream(request: QueryRequest, user=Depends(current_user)):
    def events() -> Iterator[str]:
        try:
            for event in rag.stream_query(request.question, user["sub"], request.top_k):
                yield f"data: {json.dumps(event)}\n\n"
        except GeminiQuotaError:
            yield f"data: {json.dumps({'type': 'error', 'code': 'AI_QUOTA_EXHAUSTED', 'message': 'AI answer generation is temporarily unavailable because the Gemini quota is exhausted.'})}\n\n"
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'code': 'CHAT_UNAVAILABLE', 'message': 'The answer could not be generated. Please try again later.'})}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


app.include_router(
    documents_router
)
app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(feedback_router)