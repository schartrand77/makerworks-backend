import logging
from datetime import datetime

from fastapi import Depends, Header, HTTPException, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_async_db, async_session
from app.models.models import User
from app.schemas.user import UserOut
from app.services.token_service import decode_token
from app.services.redis_service import get_redis
from app.services.token_blacklist import is_token_blacklisted

logger = logging.getLogger(__name__)


def get_guest_user() -> UserOut:
    """
    Returns a fully populated guest user.
    """
    return UserOut(
        id="00000000-0000-0000-0000-000000000000",
        username="guest",
        email="guest@example.com",
        name="Guest User",
        bio="Guest user - limited access.",
        role="guest",
        is_verified=False,
        created_at=datetime.utcnow(),
        last_login=None,
        avatar_url="/static/images/guest-avatar.png",
        thumbnail_url="/static/images/guest-thumbnail.png",
        avatar_updated_at=datetime.utcnow(),
        language="en",
    )


async def resolve_user(user_id: str, db: AsyncSession) -> User | None:
    """
    Looks up a user by user_id. Returns None if not found.
    Raises HTTP 500 if database errors occur.
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user
    except SQLAlchemyError as e:
        logger.error(f"[AUTH] DB error while resolving user_id={user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_async_db),
) -> User | UserOut:
    """
    Extracts and returns the current authenticated User from DB
    based on the JWT in the Authorization header.
    If no token or invalid → returns guest.
    If DB fails → raises HTTP 500.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return get_guest_user()

    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
    except Exception:
        logger.warning("[AUTH] Invalid token, returning guest")
        return get_guest_user()

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("[AUTH] Token missing 'sub', returning guest")
        return get_guest_user()

    logger.debug(f"[AUTH] Resolving user_id={user_id}")
    user = await resolve_user(user_id, db)

    if not user:
        logger.warning(f"[AUTH] No user found for id={user_id}, returning guest")
        return get_guest_user()

    return user


async def get_user_from_headers(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Similar to get_current_user but raises if no valid user is found.
    If DB fails → raises HTTP 500.
    If user not found → raises HTTP 404.
    """
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
    except Exception:
        logger.warning("[AUTH] Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("[AUTH] Token missing 'sub'")
        raise HTTPException(status_code=401, detail="Invalid token payload")

    logger.debug(f"[AUTH] Resolving user_id={user_id}")
    user = await resolve_user(user_id, db)

    if not user:
        logger.warning(f"[AUTH] No user found for id={user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Ensures the current user is an admin.
    Raises if not.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    """
    Sync dependency (can be used in non-async contexts) to ensure admin.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


async def assert_user_is_admin(user: User = Depends(get_current_user)) -> None:
    """
    Async version: raises if current user is not admin.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
async def get_user_from_token_query(websocket: WebSocket) -> User | None:
    """Return User from JWT passed as 'token' query param."""
    token = websocket.query_params.get("token")
    if not token:
        return None

    try:
        payload = decode_token(token)
    except Exception:
        logger.warning("[AUTH] Invalid token in websocket query")
        return None

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id:
        logger.warning("[AUTH] Token missing 'sub'")
        return None

    redis = await get_redis()
    if jti and await is_token_blacklisted(redis, jti):
        logger.warning("[AUTH] Token is blacklisted")
        return None

    async with async_session() as db:
        user = await resolve_user(user_id, db)
    return user
