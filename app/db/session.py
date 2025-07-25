import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

logger = logging.getLogger(__name__)

# ─── Database Engine ────────────────────────────────
DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", settings.database_url)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.env == "development",
    future=True,
)

# ─── Async Session Factory ──────────────────────────
# Primary async_session export for direct usage
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Optional legacy sessionmaker for compatibility
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

logger.info(f"✅ Async SQLAlchemy engine initialized: {DATABASE_URL}")

# ─── Dependency for FastAPI ─────────────────────────
async def get_async_session() -> AsyncSession:
    """
    Yield an async database session to the request.
    """
    async with async_session() as session:
        yield session

# Optional aliases
get_async_db = get_async_session
get_db = get_async_session
