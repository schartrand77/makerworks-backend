from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from datetime import datetime
from app.schemas.auth import SignInRequest, TokenResponse
from app.schemas.users import UserOut
from app.services.auth_service import create_access_token, verify_password, get_current_user
from app.database import get_db
from app import models

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ────────────────────────────────────────────────────────────────────────────────
# Sign In Endpoint
# POST /api/v1/auth/signin
# ────────────────────────────────────────────────────────────────────────────────
@router.post("/signin", response_model=TokenResponse)
async def signin(credentials: SignInRequest, db: AsyncSession = Depends(get_db)):
    print("📦 Raw signin request received")

    try:
        async with db as session:
            query = select(models.User).where(models.User.email == credentials.email)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                print("❌ No user found")
                raise HTTPException(status_code=401, detail="Invalid credentials")

            if not pwd_context.verify(credentials.password, user.hashed_password):
                print("❌ Invalid password")
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Update last_login timestamp
            user.last_login = datetime.utcnow()
            await session.commit()

            # Create and return token
            token = create_access_token({
                "sub": str(user.id),
                "email": user.email,
                "role": user.role
            })

            return TokenResponse(access_token=token, token_type="bearer")

    except Exception as e:
        print(f"🔥 Signin route crashed:\n{e}")
        raise HTTPException(status_code=500, detail="Signin failed")

# ────────────────────────────────────────────────────────────────────────────────
# Get Authenticated User Info
# GET /api/v1/auth/me
# ────────────────────────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserOut)
async def get_me(current_user: models.User = Depends(get_current_user)):
    print(f"✅ Returning user profile: {current_user.email}")
    return current_user