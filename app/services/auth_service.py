# app/services/auth_service.py

import logging
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_async_db
from app.models.models import AuditLog, User
from app.services.token_service import decode_token

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


def verify_token(token: str) -> dict:
    """Decode a JWT access token."""
    try:
        return decode_token(token)
    except Exception as e:
        raise credentials_exception from e


decode_access_token = verify_token  # alias

# ────────────────────────────────────────────────────────────────────────────────
# GET CURRENT USER DEPENDENCY
# ────────────────────────────────────────────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Returns the local User record corresponding to the Authentik-authenticated user.
    """
    payload = verify_token(token)
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


async def log_action(admin_id: str, action: str, target: str, db: AsyncSession):
    logger.info(
        "[log_action] Admin %s performed '%s' on user %s",
        admin_id,
        action,
        target,
    )
    entry = AuditLog(
        user_id=admin_id,
        action=action,
        target=target,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    await db.commit()

