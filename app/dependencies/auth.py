import logging
from fastapi import Depends, HTTPException, status, Request
from app.db.database import get_async_db
from app.models.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Fetch user from Redis-backed session (via request.state).
    """
    user_id = request.session.get("user_id")
    if not user_id:
        logger.warning("No user_id in session.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def admin_required(
    user: User = Depends(get_current_user)
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
