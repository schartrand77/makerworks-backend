# app/routes/auth.py

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from passlib.context import CryptContext
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.models import User
from app.schemas.auth import SigninRequest, SignupRequest, UserOut
from app.services.token_service import create_access_token
from app.utils.logging import logger

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger.info("[Auth] Using password hashing scheme(s): %s", pwd_context.schemes())


@router.post("/signup")
async def signup(
    payload: SignupRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    logger.debug("[SignUp] Received signup request for email: %s", payload.email)

    result = await db.execute(
        select(User).where(
            or_(User.email == payload.email, User.username == payload.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        logger.warning("[SignUp] Duplicate email or username: %s", payload.email)
        raise HTTPException(status_code=400, detail="Email or username already exists")

    result = await db.execute(select(func.count()).select_from(User))
    count = result.scalar_one()
    role = "admin" if count == 0 else "user"

    hashed_password = pwd_context.hash(payload.password)

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        username=payload.username,
        hashed_password=hashed_password,
        role=role,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("[SignUp] Success for: %s (role: %s)", user.email, user.role)

    return {"user": UserOut(**user.to_dict()), "token": token}


@router.post("/signin")
async def signin(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    logger.debug("[SignIn] Attempt for: %s", payload.email_or_username)

    result = await db.execute(
        select(User).where(
            or_(
                User.email == payload.email_or_username,
                User.username == payload.email_or_username,
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("[SignIn] User not found: %s", payload.email_or_username)
        raise HTTPException(status_code=401, detail="Authentication failed")

    if not pwd_context.verify(payload.password, user.hashed_password):
        logger.warning("[SignIn] Invalid password for: %s", payload.email_or_username)
        raise HTTPException(status_code=401, detail="Authentication failed")

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("[SignIn] Success for: %s", user.username)

    return {"user": UserOut(**user.to_dict()), "token": token}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    logger.debug("[Me] Authenticated as: %s", current_user.email)

    return {"user": UserOut(**current_user.to_dict()), "token": None}


@router.get("/debug")
async def debug_me(current_user: User = Depends(get_current_user)):
    logger.debug("[Debug] Testing serialization for user: %s", current_user.email)

    return {"user": UserOut(**current_user.to_dict()), "token": "debug-token"}