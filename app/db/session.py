from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import logging

logger = logging.getLogger(__name__)

# Lazy-loaded engine and session_maker
engine = None
async_session_maker = None


def init_engine():
    """
    Initializes the async SQLAlchemy engine & sessionmaker.
    Called lazily on first DB access.
    """
    global engine, async_session_maker

    from app.config.settings import settings  # avoid circular import

    db_url = settings.async_database_url

    if not db_url.startswith("postgresql+asyncpg://"):
        raise ValueError(
            f"Invalid ASYNC_DATABASE_URL: {db_url} — must start with postgresql+asyncpg://"
        )

    logger.info(f"✅ Using ASYNC_DATABASE_URL: {db_url}")

    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )

    async_session_maker = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession. Lazily initializes the engine if needed.
    """
    global async_session_maker

    if async_session_maker is None:
        init_engine()

    async with async_session_maker() as session:
        yield session


# ✅ Legacy alias for backward compatibility
get_db = get_async_db
