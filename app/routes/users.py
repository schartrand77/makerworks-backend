import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user, get_user_from_headers
from app.models import User
from app.schemas.token import TokenData
from app.schemas.user import (
    UpdateUserProfile,
    UserOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


# ─────────────────────────────────────────────────────────────
# Response Schemas
# ─────────────────────────────────────────────────────────────


class MeResponse(BaseModel):
    sub: str
    username: str
    email: str
    avatar: str
    groups: list[str]


class UsernameCheckResponse(BaseModel):
    available: bool
    note: str


class AdminUserListStub(BaseModel):
    note: str


# ─────────────────────────────────────────────────────────────
# GET /users/me
# ─────────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user (OIDC token from Authentik)",
)
async def get_me(token: TokenData = Depends(get_user_from_headers)):
    """Returns basic user info derived from the Authentik-issued token."""
    return {
        "sub": str(token.sub),
        "username": token.username,
        "email": token.email,
        "avatar": f"/static/avatars/user_{token.sub}.png",
        "groups": token.groups,
    }


# ─────────────────────────────────────────────────────────────
# PATCH /users/me
# ─────────────────────────────────────────────────────────────


@router.patch("/me", response_model=UserOut, summary="Update user profile (bio, etc.)")
async def update_profile(
    payload: UpdateUserProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allows a user to update their profile (currently only bio)."""
    current_user.bio = payload.bio
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


# ─────────────────────────────────────────────────────────────
# POST /users/avatar
# ─────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────
# GET /users/username/check
# ─────────────────────────────────────────────────────────────


@router.get(
    "/username/check",
    response_model=UsernameCheckResponse,
    summary="Stub: check username availability",
)
async def check_username():
    """Always returns false — username management is delegated to Authentik."""
    return {"available": False, "note": "Username is managed by Authentik"}


# ─────────────────────────────────────────────────────────────
# GET /users (admin-only stub)
# ─────────────────────────────────────────────────────────────


@router.get(
    "/", response_model=AdminUserListStub, summary="Admin-only: stub for full user list"
)
async def get_all_users(token: TokenData = Depends(get_user_from_headers)):
    """Stub for fetching all users — use Authentik API directly instead."""
    if "admin" not in token.groups:
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"note": "User listing handled by Authentik admin panel or API."}
