# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.models import User
from app.schemas.auth import UserOut, UserCreate, UserSignIn
from app.services.auth_service import authenticate_user, create_user
from app.services.session_backend import create_session, destroy_session
from app.services.cache.user_cache import cache_user_profile
from app.dependencies.auth import get_current_user

router = APIRouter()


def serialize_user(user: User, request: Request) -> UserOut:
    """
    Converts SQLAlchemy User to Pydantic UserOut and ensures avatar_url is absolute.
    """
    user_out = UserOut.from_orm(user)
    if user_out.avatar_url and not user_out.avatar_url.startswith("http"):
        user_out.avatar_url = str(request.base_url).rstrip("/") + user_out.avatar_url
    return user_out


@router.post("/signup")
async def signup(payload: UserCreate, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # ✅ Check if email exists
    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # ✅ Create user
    user = await create_user(db=db, user_in=payload)

    # ✅ Use UTC naive datetime for created_at and last_login
    now_utc = datetime.utcnow().replace(tzinfo=None)
    user.created_at = now_utc
    user.last_login = None  # No login yet for new account

    await db.commit()
    await db.refresh(user)

    user_out = serialize_user(user, request)

    # ✅ Cache user profile in Redis
    await cache_user_profile(user_out)

    # ✅ Create session token and set cookie
    session_token = await create_session(user.id)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="none",  # allow cross-origin localhost:5173
        secure=False,     # disable secure for local dev
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/"
    )

    return {
        "token": session_token,
        "user": user_out.model_dump()
    }


@router.post("/signin")
async def signin(payload: UserSignIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.email_or_username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # ✅ Use UTC naive datetime to match TIMESTAMP WITHOUT TIME ZONE
    now_utc = datetime.utcnow().replace(tzinfo=None)
    user.last_login = now_utc
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_out = serialize_user(user, request)

    # ✅ Cache user profile in Redis
    await cache_user_profile(user_out)

    # ✅ Create session token and set cookie
    session_token = await create_session(user.id)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="none",  # allow cross-origin localhost:5173
        secure=False,     # disable secure for local dev
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/"
    )

    return {
        "token": session_token,
        "user": user_out.model_dump()
    }


@router.get("/me", response_model=UserOut)
async def me(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_out = serialize_user(current_user, request)
    return user_out


@router.post("/signout")
async def signout(response: Response, current_user: User = Depends(get_current_user)):
    await destroy_session(current_user.id)
    # ✅ Clear the session cookie on sign out
    response.delete_cookie(key="session", path="/")
    return {"status": "ok", "message": "Signed out"}
