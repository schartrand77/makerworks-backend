import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config.settings import settings

logger = logging.getLogger("makerworks.database")

if not settings.database_url:
    logger.critical("❌ DATABASE_URL is not set in the environment.")
    raise RuntimeError("❌ DATABASE_URL is not set. Please check your `.env`.")

logger.info(f"✅ Using DATABASE_URL: {settings.database_url}")

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,
    future=True,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    """
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """
    Initialize the database (create tables if necessary).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Tables created successfully.")
