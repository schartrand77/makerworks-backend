# app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from passlib.context import CryptContext

from app.schemas.auth import SignupRequest, AuthResponse, UserOut
from app.models.models import User
from app.db.session import get_db
from app.services.token_service import create_access_token  # ✅ fixed import
from app.dependencies.auth import get_current_user
from app.utils.logging import logger

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/signup", response_model=AuthResponse)
async def signup(payload: SignupRequest, request: Request, db: AsyncSession = Depends(get_db)):
    logger.debug("[SignUp] Received payload: %s", payload.dict())

    result = await db.execute(
        select(User).where(
            or_(
                User.email == payload.email,
                User.username == payload.username
            )
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already exists")

    hashed = pwd_context.hash(payload.password)
    user = User(email=payload.email, username=payload.username, password=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("[SignUp] Success for: %s", user.email)

    return AuthResponse(**user.to_dict(), token=token)


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    logger.debug("[SignIn] Attempt for: %s", payload.email)

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(payload.password, user.password):
        logger.warning("[SignIn] Failed for %s", payload.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("[SignIn] Success for: %s", user.username)

    return AuthResponse(**user.to_dict(), token=token)


@router.get("/me", response_model=AuthResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.debug("[Me] Authenticated as: %s", current_user.email)
    return AuthResponse(**current_user.to_dict())


@router.get("/debug", response_model=AuthResponse)
async def debug_me(current_user: User = Depends(get_current_user)):
    logger.debug("[Debug] Testing serialization for user: %s", current_user.email)
    return AuthResponse(**current_user.to_dict(), token="debug-token")