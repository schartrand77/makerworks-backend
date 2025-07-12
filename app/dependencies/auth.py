from fastapi import Depends, Header, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.models.models import User
import os
import httpx
from jose import jwt, JWTError

AUTHENTIK_USERINFO_URL = os.getenv(
    "AUTHENTIK_USERINFO_URL",
    "http://localhost:9000/application/o/userinfo/",
)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")


def parse_groups(groups_raw: str) -> list[str]:
    return [g.strip() for g in groups_raw.split(",") if g.strip()]


async def get_current_user(
    request: Request,
    x_authentik_email: str = Header(None, alias="X-Authentik-Email"),
    x_authentik_username: str = Header(None, alias="X-Authentik-Username"),
    x_authentik_groups: str = Header("", alias="X-Authentik-Groups"),
    db: AsyncSession = Depends(get_db),
) -> User:
    email = x_authentik_email
    username = x_authentik_username
    groups_raw = x_authentik_groups

    if not email:
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing authentication headers or token.")
        token = token.split("Bearer ")[1]

        # Decode token with jose
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            email = payload.get("email")
            username = payload.get("username") or payload.get("preferred_username") or email
            groups_raw = ",".join(payload.get("groups", []))
        except JWTError:
            # If local decode fails, fallback to Authentik userinfo endpoint
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
                    groups_raw = ",".join(data.get("groups", []))
                except Exception:
                    raise HTTPException(status_code=401, detail="Invalid Authentik token.")

    groups = parse_groups(groups_raw)

    # Get or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        user = User(
            email=email,
            username=username,
            is_verified=True,
            role="admin" if "MakerWorks-Admin" in groups or email in ADMIN_EMAILS else "user",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Keep role in sync with Authentik groups
        if "MakerWorks-Admin" in groups or email in ADMIN_EMAILS:
            user.role = "admin"
        elif "MakerWorks-User" in groups:
            user.role = "user"
        else:
            user.role = "guest"

    return user


async def get_user_from_headers(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format.")

    token = authorization.split("Bearer ")[1]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                AUTHENTIK_USERINFO_URL,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")


async def get_user_from_token_query(token: str = Query(...)) -> dict:
    """Authenticate user from WebSocket query param: ?token=xxx"""
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                AUTHENTIK_USERINFO_URL,
                headers={"Authorization": token}
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or missing token in query")


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


def admin_required(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return user


async def assert_user_is_admin(user: User = Depends(get_current_user)) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")