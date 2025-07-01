# app/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging
import uuid

from app.models import User
from app.schemas.auth import SignupRequest, UserOut, AuthResponse
from app.db.session import get_async_db
from app.utils.security import hash_password, create_access_token
from app.dependencies.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=UserOut)
async def signup(
    payload: SignupRequest,
    db: AsyncSession = Depends(get_async_db),
    request: Request = None,
):
    try:
        logger.debug("[SignUp] Received payload: %s", payload.dict())

        # Check for existing email
        result = await db.execute(select(User).where(User.email == payload.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already in use.")

        # Check for existing username
        result = await db.execute(select(User).where(User.username == payload.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already taken.")

        new_user = User(
            id=str(uuid.uuid4()),
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
            is_active=True,
            is_verified=False,
            role="user",
            created_at=datetime.utcnow(),
            theme="system",
            language="en",
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info("[SignUp] User created successfully: %s", new_user.email)

        return UserOut(**UserOut.model_validate(new_user).model_dump(mode="json"))

    except HTTPException as he:
        raise he
    except Exception:
        logger.exception("[SignUp] Internal server error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal signup error. Please check backend logs."
        )


@router.post("/token", response_model=AuthResponse)
async def login_with_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        query = select(User).where(User.email == form_data.username)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            query = select(User).where(User.username == form_data.username)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

        if not user or not user.verify_password(form_data.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")

        token = create_access_token(data={"sub": str(user.id)})

        logger.info("[TokenLogin] Authenticated user: %s", user.email)

        return AuthResponse(
            **UserOut.model_validate(user).model_dump(),
            token=token
        )

    except Exception:
        logger.exception("[TokenLogin] Internal server error")
        raise HTTPException(status_code=500, detail="Token login failed")


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.debug("[GetMe] Current user: %s", current_user.email)
    return UserOut.model_validate(current_user)


@router.get("/test", response_model=AuthResponse)
async def test_auth(current_user: User = Depends(get_current_user)):
    logger.debug("[AuthTest] Current user: %s", current_user.email)
    token = create_access_token(data={"sub": str(current_user.id)})

    return AuthResponse(
        **UserOut.model_validate(current_user).model_dump(),
        token=token
    )
    
@router.get("/debug/user-out", response_model=UserOut)
def debug_user_response():
    user = db.query(User).first()
    return UserOut(**UserOut.model_validate(user).model_dump(mode="json"))


@router.get("/debug/validate-userout", response_model=UserOut)
async def debug_validate_userout(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database.")
    return UserOut.model_validate(user)