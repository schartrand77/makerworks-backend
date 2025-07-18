from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.models import User
from app.schemas.token import TokenData
from app.services.token_service import decode_token


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
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


async def get_user_from_headers(authorization: str = Header(...)) -> TokenData:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        return TokenData(**payload)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def get_user_from_token_query(token: str) -> TokenData:
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
    try:
        payload = decode_token(token)
        return TokenData(**payload)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


async def assert_user_is_admin(user: User = Depends(get_current_user)) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
