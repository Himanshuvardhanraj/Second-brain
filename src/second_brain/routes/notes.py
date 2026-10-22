from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from second_brain.auth import current_user
from second_brain.supabase_client import supabase

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=20000)
    sources: list[Dict[str, Any]] = Field(default_factory=list)


@router.get("")
def list_notes(user=Depends(current_user)):
    try:
        response = (
            supabase.table("notes").select("*")
            .eq("user_id", user["sub"]).order("created_at", desc=True).execute()
        )
        notes = []
        seen = set()
        for note in response.data or []:
            key = (note.get("question", "").strip(), note.get("answer", "").strip())
            if key in seen:
                continue
            seen.add(key)
            notes.append(note)
        return {"notes": notes}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not load notes") from exc


@router.post("")
def save_note(note: NoteRequest, user=Depends(current_user)):
    try:
        existing = (
            supabase.table("notes").select("*")
            .eq("user_id", user["sub"])
            .eq("question", note.question)
            .eq("answer", note.answer)
            .limit(1)
            .execute()
        )
        if existing.data:
            return {"note": existing.data[0], "already_saved": True}

        response = supabase.table("notes").insert({
            "user_id": user["sub"],
            "question": note.question,
            "answer": note.answer,
            "sources": note.sources,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return {"note": response.data[0] if response.data else None, "already_saved": False}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not save this chat") from exc


@router.delete("/{note_id}")
def delete_note(note_id: str, user=Depends(current_user)):
    try:
        response = (
            supabase.table("notes").delete()
            .eq("id", note_id).eq("user_id", user["sub"]).execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"message": "Note deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not delete note") from exc
