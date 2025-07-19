from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.models import User
from app.schemas.auth import SignupRequest, SigninRequest, AuthPayload, UserOut
from app.services.token_service import create_access_token, decode_token
from app.utils.security import hash_password, verify_password

router = APIRouter()


def get_guest_user() -> UserOut:
    """
    Return a fully populated guest user.
    """
    now = datetime.utcnow()
    return UserOut(
        id="00000000-0000-0000-0000-000000000000",
        username="guest",
        email="guest@example.com",
        name="Guest User",
        bio="Guest user - limited access.",
        role="guest",
        is_verified=False,
        created_at=now,
        last_login=None,
        avatar_url="/static/images/guest-avatar.png",
        thumbnail_url="/static/images/guest-thumbnail.png",
        avatar_updated_at=now,
        language="en",
    )


async def get_current_user(
    authorization: str = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """
    Tries to fetch the current authenticated user.
    If token is missing/invalid → returns guest user.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return get_guest_user()

    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
    except Exception:
        return get_guest_user()

    user_id = payload.get("sub")
    if not user_id:
        return get_guest_user()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return get_guest_user()

    return UserOut.model_validate(user, from_attributes=True)


@router.post("/signup", response_model=AuthPayload)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account.
    """
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

    token = create_access_token(user_id=str(user.id), email=user.email)
    return AuthPayload(user=UserOut.model_validate(user, from_attributes=True), token=token)


@router.post("/signin", response_model=AuthPayload)
async def signin(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate an existing user.
    """
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

    token = create_access_token(user_id=str(user.id), email=user.email)
    return AuthPayload(user=UserOut.model_validate(user, from_attributes=True), token=token)


@router.post("/signout")
async def signout(authorization: str = Header(default=None)):
    """
    Sign out user (currently no-op, but client should discard token).
    """
    if authorization and not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return {"status": "ok"}


@router.get("/me", response_model=AuthPayload)
async def me(user: UserOut = Depends(get_current_user)):
    """
    Get current authenticated user or guest if not authenticated.
    """
    # Return an empty string token for guest
    token = "" if user.role == "guest" else None
    return AuthPayload(user=user, token=token)


@router.get("/debug")
async def debug_route():
    """
    Debug route for development.
    """
    return {"token": "debug-token"}