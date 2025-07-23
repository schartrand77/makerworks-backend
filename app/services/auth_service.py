# app/services/auth_service.py

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import AuditLog, User

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────────
# ADMIN AUDIT LOGGING
# ────────────────────────────────────────────────────────────────────────────────


async def log_action(
    admin_id: str,
    action: str,
    target: str,
    db: AsyncSession,
):
    """
    Record an admin or user action in the audit log.
    """
    logger.info(
        "[log_action] Admin %s performed '%s' on %s",
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
