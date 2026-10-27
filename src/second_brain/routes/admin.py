import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from second_brain.auth import require_role
from second_brain.supabase_client import supabase, supabase_auth

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)
RETENTION_DAYS = int(os.getenv("SEARCH_LOG_RETENTION_DAYS", "30"))


def audit(admin_id: str, action: str, target_user_id: str | None, metadata: dict[str, Any] | None = None):
    try:
        supabase.table("admin_audit_log").insert({
            "admin_id": admin_id,
            "action": action,
            "target_user_id": target_user_id,
            "metadata": metadata or {},
        }).execute()
    except Exception:
        logger.exception("Admin audit write failed for action %s", action)


def record_search(user_id: str | None, query: str, result_count: int | None, latency_ms: int | None):
    try:
        supabase.table("search_logs").insert({
            "user_id": user_id,
            "query_text": query,
            "result_count": result_count,
            "latency_ms": latency_ms,
        }).execute()
    except Exception:
        logger.exception("Search log write failed")


@router.get("/search-logs")
def search_logs(
    background_tasks: BackgroundTasks,
    user=Depends(require_role("admin")),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    contains: str | None = Query(default=None, min_length=1, max_length=200),
):
    audit(user["sub"], "view_search_logs", None, {"limit": limit, "offset": offset})
    try:
        query = supabase.table("search_logs").select("*", count="exact").order("created_at", desc=True)
        if user_id:
            query = query.eq("user_id", user_id)
        if start:
            query = query.gte("created_at", start.isoformat())
        if end:
            query = query.lte("created_at", end.isoformat())
        if contains:
            query = query.ilike("query_text", f"%{contains}%")
        response = query.range(offset, offset + limit - 1).execute()
        return {"logs": response.data or [], "offset": offset, "limit": limit, "retention_days": RETENTION_DAYS}
    except Exception as exc:
        audit(user["sub"], "view_search_logs_failed", None, {"reason": "database_error"})
        raise HTTPException(status_code=502, detail="Could not load search logs") from exc


@router.get("/audit-log")
def audit_log(
    user=Depends(require_role("admin")),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    audit(user["sub"], "view_audit_log", None, {"limit": limit, "offset": offset})
    try:
        response = (
            supabase.table("admin_audit_log").select("*")
            .order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        )
        return {"events": response.data or [], "offset": offset, "limit": limit}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not load audit log") from exc


@router.get("/users")
def users(user=Depends(require_role("admin"))):
    audit(user["sub"], "view_users", None)
    try:
        response = supabase_auth.auth.admin.list_users()
        return {"users": [
            {"id": item.id, "email": item.email, "role": (item.app_metadata or {}).get("role", "user")}
            for item in (response or [])
        ]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not load users") from exc


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    confirm_email: str = Query(..., min_length=3),
    confirm_admin: bool = Query(default=False),
    user=Depends(require_role("admin")),
):
    if user_id == user["sub"]:
        audit(user["sub"], "delete_user_rejected_self", user_id)
        raise HTTPException(status_code=400, detail="Administrators cannot delete themselves")
    try:
        target = supabase_auth.auth.admin.get_user_by_id(user_id)
        target_user = getattr(target, "user", target)
        target_email = getattr(target_user, "email", None)
        target_role = (getattr(target_user, "app_metadata", {}) or {}).get("role", "user")
        if target_email != confirm_email:
            raise HTTPException(status_code=400, detail="Confirmation email does not match")
        if target_role == "admin":
            if not confirm_admin:
                raise HTTPException(status_code=400, detail="Deleting an admin requires confirm_admin=true")
            admin_users = [
                item for item in (supabase_auth.auth.admin.list_users() or [])
                if (item.app_metadata or {}).get("role") == "admin"
            ]
            if len(admin_users) <= 1:
                raise HTTPException(status_code=400, detail="The last administrator cannot be deleted")

        documents = supabase.table("documents").select("id,file_path").eq("user_id", user_id).execute().data or []
        paths = [item["file_path"] for item in documents if item.get("file_path")]
        supabase.table("document_chunks").delete().eq("user_id", user_id).execute()
        supabase.table("documents").delete().eq("user_id", user_id).execute()
        supabase.table("notes").delete().eq("user_id", user_id).execute()
        supabase.table("answer_feedback").delete().eq("user_id", user_id).execute()
        supabase.table("search_logs").delete().eq("user_id", user_id).execute()
        supabase.table("users").delete().eq("id", user_id).execute()
        if paths:
            supabase.storage.from_("documents").remove(paths)
        supabase_auth.auth.admin.delete_user(user_id)
        audit(user["sub"], "delete_user", user_id, {"deleted_documents": len(documents)})
        return {"message": "User and associated data deleted", "user_id": user_id}
    except HTTPException as exc:
        audit(user["sub"], "delete_user_failed", user_id, {"status": exc.status_code})
        raise
    except Exception as exc:
        audit(user["sub"], "delete_user_failed", user_id, {"reason": "database_error"})
        raise HTTPException(status_code=502, detail="Could not delete user data completely") from exc
