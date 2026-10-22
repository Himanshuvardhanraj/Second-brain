from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from second_brain.auth import (
    create_guest_token,
    current_user,
    login as authenticate,
    refresh as refresh_session,
    revoke_token,
    signup as create_account,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=100)


class RefreshRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20)


def _complete_auth(response: Response, data: dict) -> dict:
    refresh_token = data.pop("refresh_token", None)
    if refresh_token:
        response.set_cookie(
            "second_brain_refresh",
            refresh_token,
            httponly=True,
            secure=os.getenv("FRONTEND_URL", "").startswith("https://"),
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/api/auth",
        )
    return data


@router.post("/signup")
def signup(credentials: Credentials, response: Response):
    return _complete_auth(response, create_account(credentials.email, credentials.password, credentials.name))


@router.post("/login")
def login(credentials: Credentials, response: Response):
    return _complete_auth(response, authenticate(credentials.email, credentials.password))


@router.post("/guest")
def guest_login():
    return create_guest_token()


@router.post("/refresh")
def refresh(request: RefreshRequest, response: Response):
    refresh_token = request.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh session is missing")
    return _complete_auth(response, refresh_session(refresh_token))


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if credentials:
        revoke_token(credentials.credentials)
    response = Response(content='{"ok":true}', media_type="application/json")
    response.delete_cookie("second_brain_refresh", path="/api/auth")
    return response


@router.get("/me")
def me(user=Depends(current_user)):
    return {"user": user}
