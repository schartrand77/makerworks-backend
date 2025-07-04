# app/dependencies/auth.py

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.user import User
import os
import httpx

AUTHENTIK_USERINFO_URL = os.getenv("AUTHENTIK_USERINFO_URL", "http://192.168.1.170:9000/application/o/userinfo/")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")


async def get_current_user(
    request: Request,
    x_authentik_email: str = Header(None, alias="X-Authentik-Email"),
    x_authentik_username: str = Header(None, alias="X-Authentik-Username"),
    x_authentik_groups: str = Header("", alias="X-Authentik-Groups"),
    db: AsyncSession = Depends(get_db),
) -> User:
    email = x_authentik_email
    username = x_authentik_username
    groups = x_authentik_groups

    # Fallback: if headers are not present, use bearer token and fetch /userinfo
    if not email:
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing authentication headers or token.")
        token = token.split("Bearer ")[1]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    AUTHENTIK_USERINFO_URL,
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                data = response.json()
                email = data.get("email")
                username = data.get("username")
                groups = ",".join(data.get("groups", []))
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid Authentik token.")

    # Fetch user from DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    # Auto-create user if not found
    if not user:
        user = User(
            email=email,
            username=username,
            is_verified=True,
            role="admin" if "admin" in groups.lower() or email in ADMIN_EMAILS else "user",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return user
