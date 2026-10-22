from __future__ import annotations

import os
import logging
import threading
import time
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from second_brain.supabase_client import supabase, supabase_auth

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "")
TOKEN_TTL_SECONDS = int(os.getenv("APP_TOKEN_TTL_SECONDS", "900"))
MAX_SESSIONS = int(os.getenv("MAX_IN_MEMORY_SESSIONS", "5000"))
bearer = HTTPBearer(auto_error=False)

# A bounded TTL session registry. It is deliberately process-local and dependency-free.
_sessions: OrderedDict[str, tuple[dict[str, Any], float]] = OrderedDict()
_sessions_lock = threading.RLock()


def _require_secret() -> str:
    if len(JWT_SECRET) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured securely")
    return JWT_SECRET


def _session_user(user: Any) -> dict[str, Any]:
    get_value = user.get if isinstance(user, dict) else lambda key, default=None: getattr(user, key, default)
    user_id = get_value("id")
    email = get_value("email")
    metadata = get_value("user_metadata", {}) or {}
    return {
        "sub": str(user_id),
        "email": email,
        "name": metadata.get("name") or email or "User",
        "is_guest": False,
    }


def _remember_session(user: dict[str, Any]) -> str:
    session_id = uuid.uuid4().hex
    with _sessions_lock:
        _sessions[session_id] = (user, time.monotonic() + TOKEN_TTL_SECONDS)
        _sessions.move_to_end(session_id)
        while len(_sessions) > MAX_SESSIONS:
            _sessions.popitem(last=False)
    return session_id


def _get_session(session_id: str) -> dict[str, Any] | None:
    with _sessions_lock:
        item = _sessions.get(session_id)
        if not item:
            return None
        user, expires_at = item
        if expires_at <= time.monotonic():
            _sessions.pop(session_id, None)
            return None
        _sessions.move_to_end(session_id)
        return user


def _forget_session(session_id: str) -> None:
    with _sessions_lock:
        _sessions.pop(session_id, None)


def _create_app_token(user: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    session_id = _remember_session(user)
    payload = {
        "sid": session_id,
        "sub": user["sub"],
        "iat": now,
        "exp": now + timedelta(seconds=TOKEN_TTL_SECONDS),
    }
    return jwt.encode(payload, _require_secret(), algorithm=JWT_ALGORITHM)


def _auth_response(user: dict[str, Any], session: Any) -> dict[str, Any]:
    get_value = session.get if isinstance(session, dict) else lambda key, default=None: getattr(session, key, default)
    access_token = get_value("access_token")
    refresh_token = get_value("refresh_token")
    if not access_token or not refresh_token:
        raise HTTPException(
            status_code=403,
            detail="Supabase did not create a session. Disable email confirmation or confirm the account first.",
        )
    return {
        # Supabase's signed access JWT is valid across all serverless instances.
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user["sub"],
            "name": user["name"],
            "email": user["email"],
            "is_guest": False,
        },
    }


def _profile(user: Any) -> dict[str, Any]:
    profile = _session_user(user)
    try:
        supabase.table("users").upsert(
            {
                "id": profile["sub"],
                "email": profile["email"],
                "name": profile["name"],
                "provider": "supabase",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="id",
        ).execute()
    except Exception as exc:
        # Supabase Auth remains authoritative; a profile-table outage must not
        # turn a successful authentication into a misleading login failure.
        logger.warning("Could not synchronize the Supabase profile: %s", exc)
    return profile


def signup(email: str, password: str, name: str | None) -> dict[str, Any]:
    try:
        result = supabase_auth.auth.sign_up(
            {"email": email, "password": password, "options": {"data": {"name": name or email}}}
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not create the Supabase account") from exc
    session = getattr(result, "session", None)
    user = getattr(result, "user", None)
    if not session or not user:
        raise HTTPException(status_code=403, detail="Check your email to confirm the account before logging in")
    return _auth_response(_profile(user), session)


def login(email: str, password: str) -> dict[str, Any]:
    try:
        result = supabase_auth.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc
    session = getattr(result, "session", None)
    user = getattr(result, "user", None)
    if not session or not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _auth_response(_profile(user), session)


def refresh(refresh_token: str) -> dict[str, Any]:
    try:
        result = supabase_auth.auth.refresh_session(refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Session expired; please log in again") from exc
    session = getattr(result, "session", None)
    user = getattr(result, "user", None)
    if not session or not user:
        raise HTTPException(status_code=401, detail="Session expired; please log in again")
    return _auth_response(_profile(user), session)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    # Guest tokens are application-issued and remain process-local.
    if claims.get("is_guest") is True:
        try:
            return _decode_app_token(token)
        except HTTPException:
            raise

    # Registered-user tokens are Supabase JWTs and can be validated from any
    # Vercel serverless instance through Supabase Auth.
    try:
        result = supabase_auth.auth.get_user(token)
        user = getattr(result, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return _session_user(user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def _decode_app_token(token: str) -> Dict[str, Any]:
    try:
        claims = jwt.decode(token, _require_secret(), algorithms=[JWT_ALGORITHM])
        user = _get_session(claims["sid"])
        if not user or user["sub"] != claims["sub"]:
            raise HTTPException(status_code=401, detail="Session revoked or expired")
        return user
    except HTTPException:
        raise
    except (jwt.PyJWTError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return decode_token(credentials.credentials)


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Dict[str, Any] | None:
    return decode_token(credentials.credentials) if credentials else None


def create_guest_token() -> Dict[str, Any]:
    guest = {"sub": f"guest_{uuid.uuid4()}", "email": None, "name": "Guest", "is_guest": True}
    return {"access_token": _create_app_token(guest), "user": {"id": guest["sub"], "name": "Guest", "email": None, "is_guest": True}}


def revoke_token(token: str) -> None:
    try:
        claims = jwt.decode(token, _require_secret(), algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        _forget_session(claims["sid"])
    except (jwt.PyJWTError, KeyError, TypeError):
        return
