from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import shutil
import os
import uuid
from datetime import datetime

from app.db.database import get_db
from app.config import settings
from app.schemas.auth import TokenPayload
from app.services.auth_service import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

AVATAR_DIR = os.path.join(settings.upload_dir, "avatars")

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
# GET /users/me (from Authentik token)
# ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=MeResponse, summary="Get current user (OIDC token from Authentik)")
async def get_me(token: TokenPayload = Depends(get_current_user)):
    """Returns basic user info derived from the Authentik-issued token."""
    return {
        "sub": token.sub,
        "username": token.username,
        "email": token.email,
        "avatar": f"/static/avatars/user_{token.sub}.png",
        "groups": token.groups,
    }

# ─────────────────────────────────────────────────────────────
# POST /users/avatar (store using Authentik UUID)
# ─────────────────────────────────────────────────────────────

@router.post("/avatar", response_model=AvatarUploadResponse, summary="Upload avatar image (stored by sub UUID)")
async def upload_avatar(
    file: UploadFile = File(...),
    token: TokenPayload = Depends(get_current_user)
):
    """Store a user avatar using their Authentik `sub` as file identifier."""
    os.makedirs(AVATAR_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    filename = f"user_{token.sub}{ext}"
    full_path = os.path.join(AVATAR_DIR, filename)

    with open(full_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "uploaded",
        "avatar_url": f"/static/avatars/{filename}",
        "uploaded_at": datetime.utcnow().isoformat()
    }

# ─────────────────────────────────────────────────────────────
# GET /users/username/check (placeholder — Authentik handles usernames)
# ─────────────────────────────────────────────────────────────

@router.get("/username/check", response_model=UsernameCheckResponse, summary="Stub: check username availability")
async def check_username():
    """Always returns false — username management is delegated to Authentik."""
    return {"available": False, "note": "Username is managed by Authentik"}

# ─────────────────────────────────────────────────────────────
# GET /users (admin-only stub — use Authentik API for user list)
# ─────────────────────────────────────────────────────────────

@router.get("/", response_model=AdminUserListStub, summary="Admin-only: stub for full user list")
async def get_all_users(token: TokenPayload = Depends(get_current_user)):
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
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        candidate = os.path.join(AVATAR_DIR, f"user_{user_sub}{ext}")
        if os.path.exists(candidate):
            return {"avatar_url": f"/static/avatars/user_{user_sub}{ext}"}
    raise HTTPException(status_code=404, detail="Avatar not found")