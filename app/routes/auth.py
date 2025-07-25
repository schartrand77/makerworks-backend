from datetime import datetime, timedelta
from uuid import uuid4
import json

from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.db.session import get_async_db
from app.models.models import User
from app.schemas.auth import SignupRequest, SigninRequest, AuthPayload, UserOut
from app.utils.security import hash_password, verify_password
from app.utils.users import create_user_dirs
from app.services.cache.redis_service import get_redis
from app.config.settings import settings

SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

router = APIRouter()


def with_avatar_fields(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        username=user.username,
        name=user.name,
        bio=user.bio,
        role=user.role,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login,
        avatar_url=f"/avatars/{user.id}.png",
        thumbnail_url=f"/avatars/thumbnails/{user.id}.jpg",
        avatar_updated_at=user.avatar_updated_at,
        language=user.language,
    )


async def get_current_user(
    request: Request,
    authorization: str = Header(default=None),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_async_db)
) -> UserOut:
    """
    Dual-mode authentication:
    1️⃣ Bearer token in Authorization header → Redis lookup
    2️⃣ SessionMiddleware cookie → DB lookup
    """

    # --- Mode 1: Bearer token ---
    if authorization and authorization.startswith("Bearer "):
        session_token = authorization.split(" ")[1]
        session_data = await redis.get(session_token)
        if session_data:
            try:
                return UserOut(**json.loads(session_data))
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid session data")

    # --- Mode 2: SessionMiddleware cookie ---
    if "session" in request.scope:
        user_id = request.session.get("user_id")
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                return with_avatar_fields(user)

    raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/signup", response_model=AuthPayload)
async def signup(
    payload: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    redis: Redis = Depends(get_redis),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        id=uuid4(),
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    create_user_dirs(str(user.id))

    session_token = str(uuid4())
    user_out = with_avatar_fields(user)

    try:
        await redis.set(
            session_token,
            user_out.model_dump_json(),
            ex=SESSION_TTL_SECONDS
        )
    except Exception as e:
        print(f"[AUTH] Redis unavailable during signup: {e}")
        session_token = None

    # Also set session cookie for browser mode
    if "session" in request.scope:
        request.session["user_id"] = str(user.id)

    return AuthPayload(user=user_out, token=session_token)


@router.post("/signin", response_model=AuthPayload)
async def signin(
    payload: SigninRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    redis: Redis = Depends(get_redis),
):
    stmt = select(User).where(
        (User.email == payload.email_or_username)
        | (User.username == payload.email_or_username)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if (
        not user
        or not user.hashed_password
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    user.last_login = datetime.utcnow()
    await db.commit()

    session_token = str(uuid4())
    user_out = with_avatar_fields(user)

    try:
        await redis.set(
            session_token,
            user_out.model_dump_json(),
            ex=SESSION_TTL_SECONDS
        )
    except Exception as e:
        print(f"[AUTH] Redis unavailable during signin: {e}")
        session_token = None

    # Also set session cookie for browser mode
    if "session" in request.scope:
        request.session["user_id"] = str(user.id)

    return AuthPayload(user=user_out, token=session_token)


@router.post("/signout")
async def signout(
    request: Request,
    authorization: str = Header(default=None),
    redis: Redis = Depends(get_redis),
):
    # Clear bearer token
    if authorization and authorization.startswith("Bearer "):
        session_token = authorization.split(" ")[1]
        try:
            await redis.delete(session_token)
        except Exception as e:
            print(f"[AUTH] Redis unavailable during signout: {e}")

    # Clear session cookie
    if "session" in request.scope:
        request.session.clear()

    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(user: UserOut = Depends(get_current_user)):
    return user


@router.get("/debug")
async def debug_route():
    return {"token": "debug-token"}
