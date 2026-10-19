import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from second_brain.supabase_client import supabase


JWT_ALGORITHM = "HS256"
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
TOKEN_TTL_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
bearer = HTTPBearer(auto_error=False)


def create_token(user_id: str, email: str | None, name: str, is_guest: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "is_guest": is_guest,
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
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
    guest_id = f"guest_{uuid.uuid4()}"
    return {
        "access_token": create_token(guest_id, None, "Guest", is_guest=True),
        "user": {"id": guest_id, "name": "Guest", "email": None, "is_guest": True},
    }


def google_authorization_url() -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def exchange_google_code(code: str) -> Dict[str, Any]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not all((client_id, client_secret, redirect_uri)):
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    body = urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    try:
        request = Request(
            "https://oauth2.googleapis.com/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=10) as response:
            tokens = json.loads(response.read().decode())
        with urlopen(
            Request("https://openidconnect.googleapis.com/v1/userinfo",
                    headers={"Authorization": f"Bearer {tokens['access_token']}"}),
            timeout=10,
        ) as response:
            return json.loads(response.read().decode())
    except (KeyError, OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="Google authentication failed") from exc


def upsert_google_user(profile: Dict[str, Any]) -> Dict[str, Any]:
    user = {
        "id": profile["sub"],
        "email": profile.get("email"),
        "name": profile.get("name") or profile.get("email", "User"),
        "avatar_url": profile.get("picture"),
        "provider": "google",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        response = supabase.table("users").upsert(user, on_conflict="id").execute()
        return response.data[0] if response.data else user
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not save user profile") from exc
