# app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from passlib.context import CryptContext
import uuid

from app.schemas.auth import SignupRequest, SigninRequest, UserOut
from app.models.models import User
from app.db.session import get_db
from app.services.token_service import create_access_token
from app.dependencies.auth import get_current_user
from app.utils.logging import logger

router = APIRouter()

# Use bcrypt safely and log version
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger.info("[Auth] Using password hashing scheme(s): %s", pwd_context.schemes())


@router.post("/signup")
async def signup(
    payload: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    logger.debug("[SignUp] Received signup request for email: %s", payload.email)

    # check if user with email or username already exists
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
        logger.warning("[SignUp] Duplicate email or username: %s", payload.email)
        raise HTTPException(status_code=400, detail="Email or username already exists")

    # check if this is the very first user
    result = await db.execute(select(User))
    first_user = result.scalar_one_or_none()
    role = "admin" if first_user is None else "user"

    hashed_password = pwd_context.hash(payload.password)

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        username=payload.username,
        hashed_password=hashed_password,
        role=role
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("[SignUp] Success for: %s (role: %s)", user.email, user.role)

    return {
        "user": UserOut(**user.to_dict()),
        "token": token
    }


@router.post("/signin")
async def signin(
    payload: SigninRequest,
    db: AsyncSession = Depends(get_db)
):
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

    if not user:
        logger.warning("[SignIn] User not found: %s", payload.email_or_username)
        raise HTTPException(status_code=401, detail="Authentication failed")

    if not pwd_context.verify(payload.password, user.hashed_password):
        logger.warning("[SignIn] Invalid password for: %s", payload.email_or_username)
        raise HTTPException(status_code=401, detail="Authentication failed")

    token = create_access_token(user_id=user.id, email=user.email)
    logger.info("[SignIn] Success for: %s", user.username)

    return {
        "user": UserOut(**user.to_dict()),
        "token": token
    }


@router.post("/login")
async def login(
    payload: SigninRequest,
    db: AsyncSession = Depends(get_db)
):
    logger.debug("[Login] Delegating to /signin for: %s", payload.email_or_username)
    return await signin(payload, db)


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    logger.debug("[Me] Authenticated as: %s", current_user.email)

    return {
        "user": UserOut(**current_user.to_dict()),
        "token": None
    }


@router.get("/debug")
async def debug_me(
    current_user: User = Depends(get_current_user)
):
    logger.debug("[Debug] Testing serialization for user: %s", current_user.email)

    return {
        "user": UserOut(**current_user.to_dict()),
        "token": "debug-token"
    }


# 👑 Hidden God Mode Unlock Endpoint
@router.post("/admin/unlock")
async def admin_unlock(
    request: Request
):
    client_ip = request.client.host
    if client_ip not in {"127.0.0.1", "localhost"}:
        logger.warning("Unauthorized God Mode unlock attempt from: %s", client_ip)
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.warning("👑 God Mode unlocked from: %s", client_ip)
    # Optionally persist an audit record to DB here

    return {
        "status": "ok",
        "message": f"God Mode unlocked from {client_ip}"
    }