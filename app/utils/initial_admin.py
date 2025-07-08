import os
import logging
from sqlalchemy import select
from app.models.models import User
from app.db.session import async_session_maker
from app.utils.auth.crypto import hash_password

logger = logging.getLogger("makerworks.initial_admin")

async def ensure_initial_admin() -> None:
    """Create an admin user on first launch if none exist."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.role == "admin"))
        admin = result.scalars().first()
        if admin:
            logger.info("Admin user already exists: %s", admin.email)
            return

        email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
        username = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
        password = os.getenv("INITIAL_ADMIN_PASSWORD", "admin123")

        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            role="admin",
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        logger.info("Created initial admin user: %s", email)
