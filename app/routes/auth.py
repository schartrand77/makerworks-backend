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


async def _get_current_user(authorization: str = Header(...), db: AsyncSession = Depends(get_db)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/signup", response_model=AuthPayload)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
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
    return AuthPayload(user=UserOut.model_validate(user), token=token)


@router.post("/signin", response_model=AuthPayload)
async def signin(payload: SigninRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where((User.email == payload.email_or_username) | (User.username == payload.email_or_username))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    user.last_login = datetime.utcnow()
    await db.commit()
    token = create_access_token(user_id=str(user.id), email=user.email)
    return AuthPayload(user=UserOut.model_validate(user), token=token)


@router.post("/signout")
async def signout(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return {"status": "ok"}


@router.get("/me", response_model=AuthPayload)
async def me(user: User = Depends(_get_current_user)):
    return AuthPayload(user=UserOut.model_validate(user))


@router.get("/debug")
async def debug_route():
    return {"token": "debug-token"}
