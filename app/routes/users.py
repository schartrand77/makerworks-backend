import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.models import User
from app.schemas.user import (
    UpdateUserProfile,
    UserOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


# ─────────────────────────────────────────────────────────────
# PATCH /users/me
# ─────────────────────────────────────────────────────────────


@router.patch("/me", response_model=UserOut, summary="Update user profile (bio, etc.)")
async def update_profile(
    payload: UpdateUserProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Allows a user to update their profile (currently only bio).
    """
    current_user.bio = payload.bio
    await db.commit()
    await db.refresh(current_user)
    return UserOut.model_validate(current_user)


# ─────────────────────────────────────────────────────────────
# GET /users/me
# ─────────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current authenticated user",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns current user info from the database.
    """
    return UserOut.model_validate(current_user)


# ─────────────────────────────────────────────────────────────
# GET /users/username/check
# ─────────────────────────────────────────────────────────────


@router.get(
    "/username/check",
    summary="Check if username is available",
)
async def check_username(username: str, db: AsyncSession = Depends(get_db)):
    """
    Check if a username is already taken.
    """
    result = await db.execute(
        db.query(User).filter(User.username == username)
    )
    user = result.scalar_one_or_none()
    return {
        "available": user is None,
        "note": "Username is available" if user is None else "Username is already taken",
    }


# ─────────────────────────────────────────────────────────────
# GET /users (admin-only)
# ─────────────────────────────────────────────────────────────


@router.get(
    "/",
    summary="Admin-only: list all users",
)
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch all users — admin only.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(db.query(User))
    users = result.scalars().all()

    return [UserOut.model_validate(u) for u in users]