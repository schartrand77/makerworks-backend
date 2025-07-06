# app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from passlib.context import CryptContext

from app.schemas.auth import SignupRequest, SigninRequest, UserOut
from app.models.models import User
from app.db.session import get_db
from app.services.token_service import create_access_token
from app.dependencies.auth import get_current_user
from app.utils.logging import logger

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/signup")
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

    return {
        "user": UserOut(**user.to_dict()),
        "token": token
    }


@router.post("/signin")
async def signin(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    logger.debug("[SignIn] Attempt for: %s", payload.email_or_username)

    result = await db.execute(
        select(User).where(
            or_(
                User.email == payload.email_or_username,
                User.username == payload.email_or_username
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        logger.warning("[SignIn] Failed for %s", payload.email_or_username)
        raise HTTPException(status_code=401, detail="Authentication failed")

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("[SignIn] Success for: %s", user.username)

    return {
        "user": UserOut(**user.to_dict()),
        "token": token
    }


@router.post("/login")
async def login(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    logger.debug("[Login] Delegating to /signin for: %s", payload.email_or_username)
    return await signin(payload, db)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    logger.debug("[Me] Authenticated as: %s", current_user.email)

    return {
        "user": UserOut(**current_user.to_dict()),
        "token": None
    }


@router.get("/debug")
async def debug_me(current_user: User = Depends(get_current_user)):
    logger.debug("[Debug] Testing serialization for user: %s", current_user.email)

    return {
        "user": UserOut(**current_user.to_dict()),
        "token": "debug-token"
    }