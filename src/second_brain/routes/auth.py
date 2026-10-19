from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from second_brain.auth import (
    create_guest_token,
    create_local_user,
    authenticate_local_user,
    create_token,
    current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    user_id: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=100)


@router.post("/signup")
def signup(credentials: Credentials):
    user = create_local_user(
        credentials.user_id,
        credentials.name or credentials.user_id,
        credentials.password,
    )
    return {
        "access_token": create_token(user["id"], None, user["name"]),
        "user": {"id": user["id"], "name": user["name"], "email": None, "is_guest": False},
    }


@router.post("/login")
def login(credentials: Credentials):
    user = authenticate_local_user(credentials.user_id, credentials.password)
    return {
        "access_token": create_token(user["id"], None, user["name"]),
        "user": {"id": user["id"], "name": user["name"], "email": None, "is_guest": False},
    }


@router.post("/guest")
def guest_login():
    return create_guest_token()


@router.get("/me")
def me(user=Depends(current_user)):
    return {"user": user}
