from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from app.database import get_db
from app.models import User, AuditLog
from app.config import settings

# ────────────────────────────────────────────────────────────────────────────────
# AUTH CONSTANTS
# ────────────────────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/signin")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# ────────────────────────────────────────────────────────────────────────────────
# PASSWORD HASHING
# ────────────────────────────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ────────────────────────────────────────────────────────────────────────────────
# JWT CREATION
# ────────────────────────────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = timedelta(minutes=60)
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return token

# ────────────────────────────────────────────────────────────────────────────────
# JWT VERIFICATION
# ────────────────────────────────────────────────────────────────────────────────

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise credentials_exception

# Optional alias for compatibility
decode_access_token = verify_token

# ────────────────────────────────────────────────────────────────────────────────
# GET CURRENT USER DEPENDENCY
# ────────────────────────────────────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = verify_token(token)
    user_id: str = payload.get("sub")

    if not user_id:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

# ────────────────────────────────────────────────────────────────────────────────
# ADMIN AUDIT LOGGING
# ────────────────────────────────────────────────────────────────────────────────

async def log_action(
    admin_id: int,
    action: str,
    target_user_id: int,
    db: AsyncSession
):
    print(f"[log_action] Admin {admin_id} performed '{action}' on user {target_user_id}")
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        target_user_id=target_user_id,
        timestamp=datetime.utcnow()
    )
    db.add(entry)
    await db.commit()