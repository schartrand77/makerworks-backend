# app/routes/users.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.dependencies.auth import get_current_user
from app.models import User, Favorite, ModelMetadata
from app.schemas.user import UpdateUserProfile, UserOut
from app.schemas.models import ModelOut

logger = logging.getLogger(__name__)

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# PATCH /users/me
# ─────────────────────────────────────────────────────────────

@router.patch(
    "/me",
    response_model=UserOut,
    summary="Update user profile (bio, etc.)",
    status_code=status.HTTP_200_OK,
)
async def update_profile(
    payload: UpdateUserProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Allows a user to update their profile (currently only bio).
    """
    logger.info("🔷 Updating profile for user_id=%s", current_user.id)
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
    status_code=status.HTTP_200_OK,
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns current user info from the database.
    """
    logger.info("🔷 Fetching current user: %s", current_user.id)
    return UserOut.model_validate(current_user)


# ─────────────────────────────────────────────────────────────
# GET /users/username/check
# ─────────────────────────────────────────────────────────────

@router.get(
    "/username/check",
    summary="Check if username is available",
    status_code=status.HTTP_200_OK,
)
async def check_username(username: str, db: AsyncSession = Depends(get_async_db)):
    """
    Check if a username is already taken.
    """
    logger.debug("🔷 Checking username availability: %s", username)
    result = await db.execute(select(User).where(User.username == username))
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
    status_code=status.HTTP_200_OK,
)
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Fetch all users — admin only.
    """
    if current_user.role != "admin":
        logger.warning("⛔ User %s attempted to access admin-only user list.", current_user.id)
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info("🔷 Admin %s fetching all users.", current_user.id)
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserOut.model_validate(u) for u in users]


# ─────────────────────────────────────────────────────────────
# GET /users/{user_id}/favorites
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{user_id}/favorites",
    summary="Get user's favorite models",
    status_code=status.HTTP_200_OK,
)
async def get_user_favorites(
    user_id: str = Path(..., description="User ID to fetch favorites for"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Fetch a user's favorite models.
    """
    logger.info("🔷 Fetching favorites for user_id=%s", user_id)

    result = await db.execute(
        select(ModelMetadata)
        .join(Favorite, Favorite.model_id == ModelMetadata.id)
        .where(Favorite.user_id == user_id)
    )
    models = result.scalars().all()

    logger.info("✅ Found %d favorite models for user_id=%s", len(models), user_id)

    return [ModelOut.model_validate(m).model_dump() for m in models]
