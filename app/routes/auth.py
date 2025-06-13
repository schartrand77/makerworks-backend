# app/routes/auth.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import User
from app.schemas import (
    UserLogin,
    UserCreate,
    PasswordUpdate,
    EmailUpdate,
    RoleUpdate,)
from app.utils.auth import (
    verify_password,
    hash_password,
    create_access_token,
    decode_token,)
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")


# ----------- Auth Dependency -----------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ----------- Authenticated Routes -----------

@router.get("/me", summary="Get current user info", status_code=status.HTTP_200_OK)
async def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email}


@router.patch("/password", summary="Update user password", status_code=status.HTTP_200_OK)
async def update_password(
    data: PasswordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect current password")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    await db.refresh(user)

    return {"detail": "Password updated successfully"}


@router.patch("/email", summary="Update user email", status_code=status.HTTP_200_OK)
async def update_email(
    data: EmailUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.email = data.new_email
    await db.commit()
    await db.refresh(user)

    return {"detail": "Email updated successfully"}


@router.delete("/delete", summary="Delete user account", status_code=status.HTTP_200_OK)
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(user)
    await db.commit()
    return {"detail": "Account deleted successfully"}


@router.patch("/role", summary="Update a user's role (admin only)", status_code=status.HTTP_200_OK)
async def update_user_role(
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")

    stmt = select(User).where(User.id == data.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = data.role
    await db.commit()
    await db.refresh(user)

    return {"detail": f"Updated user {user.id} to role '{user.role}'"}


# ----------- Public Auth Routes -----------


@router.post("/signin", summary="Authenticate user and return JWT", status_code=status.HTTP_200_OK)
async def signin(data: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # ✅ Track login time
    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/signin", summary="Authenticate user and return JWT", status_code=status.HTTP_200_OK)
async def signin(data: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}