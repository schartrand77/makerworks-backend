from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

import logging

logger = logging.getLogger(__name__)

# ─── Database Engine ────────────────────────────────
DATABASE_URL = settings.async_database_url

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.env == "development",
    future=True,
)

# ─── Session Factory ────────────────────────────────
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

logger.info(f"✅ Async SQLAlchemy engine initialized: {DATABASE_URL}")


# ─── Dependency for FastAPI ─────────────────────────
async def get_async_db() -> AsyncSession:
    """
    Yield an async database session to the request.
    """
    async with AsyncSessionLocal() as session:
        yield session


# Alias for backwards compatibility
get_async_db = get_async_db
