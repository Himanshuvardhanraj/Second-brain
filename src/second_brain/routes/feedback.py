from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from second_brain.auth import current_user
from second_brain.supabase_client import supabase

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class RatingRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=20000)
    rating: int = Field(ge=1, le=5)
    sources: list[dict] = Field(default_factory=list)


@router.post("")
def rate_answer(feedback: RatingRequest, user=Depends(current_user)):
    try:
        response = supabase.table("answer_feedback").insert({
            "user_id": user["sub"],
            **feedback.model_dump(),
        }).execute()
        return {"feedback": response.data[0] if response.data else None}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not save answer rating") from exc
