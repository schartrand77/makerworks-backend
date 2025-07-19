from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.models import User
from app.services.token_service import decode_token


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extracts and returns the current authenticated User from DB
    based on the JWT in the Authorization header.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_user_from_headers(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Compatibility shim: behaves like get_current_user, but takes Request explicitly.
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Ensures the current user is an admin.
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
