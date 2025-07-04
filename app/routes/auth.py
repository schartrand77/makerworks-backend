# app/routes/auth.py

from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_async_session
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


class AuthResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_verified: bool


async def get_user_from_headers(
    x_authentik_email: str = Header(..., alias="X-Authentik-Email"),
    x_authentik_username: str = Header(..., alias="X-Authentik-Username"),
    x_authentik_groups: Optional[str] = Header("", alias="X-Authentik-Groups"),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    # Try to find the user in our local DB
    result = await session.execute(
        select(User).where(User.email == x_authentik_email)
    )
    user = result.scalars().first()

    # If not found, auto-provision the user from Authentik
    if not user:
        user = User(
            email=x_authentik_email,
            username=x_authentik_username,
            is_verified=True,
            role="admin" if "admin" in x_authentik_groups.lower() else "user",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


@router.get("/me", response_model=AuthResponse)
async def get_current_user(user: User = Depends(get_user_from_headers)):
    return AuthResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_verified=user.is_verified,
    )
