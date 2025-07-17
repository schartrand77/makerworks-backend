# app/services/auth_service.py

import logging
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.models import AuditLog, User
from app.services.redis_service import get_redis
from app.services.token_blacklist import is_token_blacklisted
from app.services.token_service import (
    verify_token_rs256,
)

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────────
# AUTH CONSTANTS
# ────────────────────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/signin")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# ────────────────────────────────────────────────────────────────────────────────
# JWT VERIFICATION (RS256 + Redis JTI Blacklist)
# ────────────────────────────────────────────────────────────────────────────────


async def verify_token(token: str, redis: Redis) -> dict:
    """
    Verifies an RS256-signed JWT from Authentik and checks Redis blacklist.
    """
    try:
        payload = await verify_token_rs256(token)
        jti = payload.get("jti")
        if jti and await is_token_blacklisted(redis, jti):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        return payload
    except Exception as e:
        raise credentials_exception from e


decode_access_token = verify_token  # alias

# ────────────────────────────────────────────────────────────────────────────────
# GET CURRENT USER DEPENDENCY
# ────────────────────────────────────────────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    """
    Returns the local User record corresponding to the Authentik-authenticated user.
    """
    payload = await verify_token(token, redis)
    user_id: str | None = payload.get("sub")

    if not user_id:
        raise credentials_exception

    # NOTE: Authentik `sub` is usually a UUID → don’t cast to int.
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


# ────────────────────────────────────────────────────────────────────────────────
# ADMIN AUDIT LOGGING
# ────────────────────────────────────────────────────────────────────────────────


async def log_action(admin_id: str, action: str, target_user_id: str, db: AsyncSession):
    logger.info(
        "[log_action] Admin %s performed '%s' on user %s",
        admin_id,
        action,
        target_user_id,
    )
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        target_user_id=target_user_id,
        timestamp=datetime.utcnow(),
    )
    db.add(entry)
    await db.commit()