import os

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from second_brain.auth import (
    create_guest_token,
    create_token,
    current_user,
    google_authorization_url,
    exchange_google_code,
    upsert_google_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/google")
def google_login():
    return {"url": google_authorization_url()}


@router.get("/google/callback")
def google_callback(code: str = Query(...)):
    profile = exchange_google_code(code)
    user = upsert_google_user(profile)
    token = create_token(str(user["id"]), user.get("email"), user["name"])
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(
        f"{frontend_url}/login/callback?token={token}"
    )


@router.post("/guest")
def guest_login():
    return create_guest_token()


@router.get("/me")
def me(user=Depends(current_user)):
    return {"user": user}
