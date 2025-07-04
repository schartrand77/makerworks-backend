from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from redis.asyncio import Redis
import uuid

from app.db.database import get_db
from app.models import User, AuditLog
from app.config import settings
from app.services.redis_service import get_redis
from app.services.token_blacklist import is_token_blacklisted

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

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ────────────────────────────────────────────────────────────────────────────────
# JWT CREATION
# ────────────────────────────────────────────────────────────────────────────────

def create_access_token(
    user: User,
    expires_delta: Optional[timedelta] = timedelta(minutes=60)
) -> str:
    expire = datetime.utcnow() + expires_delta
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "jti": jti,
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token

# ────────────────────────────────────────────────────────────────────────────────
# JWT VERIFICATION
# ────────────────────────────────────────────────────────────────────────────────

async def verify_token(token: str, redis: Redis) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        jti = payload.get("jti")
        if jti and await is_token_blacklisted(redis, jti):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        return payload
    except JWTError:
        raise credentials_exception

decode_access_token = verify_token  # alias

# ────────────────────────────────────────────────────────────────────────────────
# GET CURRENT USER DEPENDENCY
# ────────────────────────────────────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    payload = await verify_token(token, redis)
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
