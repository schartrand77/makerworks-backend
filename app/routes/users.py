from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

import shutil
import logging

from app.db.database import get_db
from app.config.settings import settings
from app.schemas.token import TokenData
from app.dependencies.auth import get_user_from_headers, get_current_user
from app.models import User
from app.schemas.user import UpdateUserProfile, UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

AVATAR_DIR = Path(settings.upload_dir) / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]


# ─────────────────────────────────────────────────────────────
# Response Schemas
# ─────────────────────────────────────────────────────────────

class MeResponse(BaseModel):
    sub: str
    username: str
    email: str
    avatar: str
    groups: list[str]


class AvatarUploadResponse(BaseModel):
    status: str
    avatar_url: str
    uploaded_at: str


class AvatarLookupResponse(BaseModel):
    avatar_url: str


class UsernameCheckResponse(BaseModel):
    available: bool
    note: str


class AdminUserListStub(BaseModel):
    note: str


# ─────────────────────────────────────────────────────────────
# GET /users/me
# ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=MeResponse, summary="Get current user (OIDC token from Authentik)")
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

@router.post("/avatar", response_model=AvatarUploadResponse, summary="Upload avatar image (stored by sub UUID)")
async def upload_avatar(
    file: UploadFile = File(...),
    token: TokenData = Depends(get_user_from_headers)
):
    """Store a user avatar using their Authentik `sub` as file identifier."""
    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported image format: {ext}")

    contents = await file.read()

    if len(contents) > MAX_AVATAR_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Avatar file too large (max 5 MB)")

    avatar_filename = f"user_{token.sub}{ext}"
    avatar_path = AVATAR_DIR / avatar_filename

    try:
        with avatar_path.open("wb") as buffer:
            buffer.write(contents)
        logger.info(f"Avatar uploaded for user {token.sub}: {avatar_path}")
    except Exception as e:
        logger.error(f"Failed to save avatar for user {token.sub}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save avatar")

    return AvatarUploadResponse(
        status="uploaded",
        avatar_url=f"/static/avatars/{avatar_filename}",
        uploaded_at=datetime.utcnow().isoformat()
    )


# ─────────────────────────────────────────────────────────────
# GET /users/username/check
# ─────────────────────────────────────────────────────────────

@router.get("/username/check", response_model=UsernameCheckResponse, summary="Stub: check username availability")
async def check_username():
    """Always returns false — username management is delegated to Authentik."""
    return {"available": False, "note": "Username is managed by Authentik"}


# ─────────────────────────────────────────────────────────────
# GET /users (admin-only stub)
# ─────────────────────────────────────────────────────────────

@router.get("/", response_model=AdminUserListStub, summary="Admin-only: stub for full user list")
async def get_all_users(token: TokenData = Depends(get_user_from_headers)):
    """Stub for fetching all users — use Authentik API directly instead."""
    if "admin" not in token.groups:
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"note": "User listing handled by Authentik admin panel or API."}


# ─────────────────────────────────────────────────────────────
# GET /users/avatar/{user_sub}
# ─────────────────────────────────────────────────────────────

@router.get("/avatar/{user_sub}", response_model=AvatarLookupResponse, summary="Lookup avatar by Authentik UUID")
async def get_avatar_url(user_sub: str):
    """Returns the URL of a locally stored avatar for a given user UUID (`sub`)."""
    for ext in ALLOWED_EXTENSIONS:
        candidate = AVATAR_DIR / f"user_{user_sub}{ext}"
        if candidate.exists():
            return {"avatar_url": f"/static/avatars/{candidate.name}"}
    raise HTTPException(status_code=404, detail="Avatar not found")