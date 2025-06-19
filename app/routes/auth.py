# app/routes/auth.py

from fastapi import (
    APIRouter, HTTPException, Depends, status,
    UploadFile, File, Form, Request, Query
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from datetime import datetime

from app.dependencies import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    UserLogin,
    PasswordUpdate,
    EmailUpdate,
    RoleUpdate,
    TokenResponse,
    UserOut,
)
from app.utils.auth.tokens import decode_token, create_access_token
from app.utils.auth.crypto import hash_password, verify_password
from app.services.auth_service import generate_auth_response

router = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")


# ----------- Auth Dependency -----------

async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        async with get_db() as db:
            stmt = select(User).where(User.id == int(user_id))
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ----------- Public Auth Routes -----------

@router.get("/email-available", summary="Check if an email is available")
async def check_email_available(
    email: str = Query(..., description="Email address to check"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    return {"available": user is None}


@router.get("/username-available", summary="Check if a username is available")
async def check_username_available(
    username: str = Query(..., description="Username to check"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    return {"available": user is None}


@router.post("/signup", response_model=TokenResponse)
async def signup(
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        print("[auth] Signup attempt — Email:", email, "| Username:", username)

        result = await db.execute(
            select(User).where(or_(User.email == email, User.username == username))
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            print("[auth] Email or username already in use")
            raise HTTPException(status_code=400, detail="Email or username already in use")

        # ✅ Check if this is the first user
        count_result = await db.execute(select(User))
        all_users = count_result.scalars().all()
        is_first_user = len(all_users) == 0
        role = "admin" if is_first_user else "user"

        hashed_pw = hash_password(password)
        user = User(email=email, username=username, hashed_password=hashed_pw, role=role)

        if image:
            try:
                contents = await image.read()
                user.profile_image = contents
                print(f"[auth] Uploaded profile image: {len(contents)} bytes")
            except Exception as e:
                print(f"[auth] Failed to read image: {e}")

        db.add(user)
        await db.commit()
        await db.refresh(user)

        print(f"[auth] Signup successful — Role: {user.role} — Email: {user.email}")
        return generate_auth_response(user)

    except HTTPException:
        raise
    except Exception as e:
        print("[auth] Exception during signup:", repr(e))
        raise HTTPException(status_code=400, detail="Signup failed")


@router.post("/signin", response_model=TokenResponse)
async def signin(data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        print("[auth] Signin attempt — Email:", data.email)

        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user:
            print("[auth] No user found for email:", data.email)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(data.password, user.hashed_password):
            print("[auth] Password verification failed for:", data.email)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        print("[auth] Login successful — ID:", user.id, "| Email:", user.email)

        token_response = generate_auth_response(user)
        print("[auth] Token generated (truncated):", token_response.access_token[:30], "...")
        return token_response

    except Exception as e:
        print("[auth] Exception during signin:", repr(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ----------- Authenticated User Routes -----------

@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.from_orm(user)


@router.patch("/password", summary="Update user password")
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


@router.patch("/email", summary="Update user email")
async def update_email(
    data: EmailUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.email = data.new_email
    await db.commit()
    await db.refresh(user)
    return {"detail": "Email updated successfully"}


@router.delete("/delete", summary="Delete user account")
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(user)
    await db.commit()
    return {"detail": "Account deleted successfully"}


# ----------- Admin-Only Routes -----------

@router.patch("/role", summary="Update a user's role (admin only)")
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