import logging
import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config.settings import settings

logger = logging.getLogger("makerworks.database")

database_url = os.getenv("ASYNC_DATABASE_URL", settings.database_url)

if not database_url:
    logger.critical("❌ DATABASE_URL is not set in the environment.")
    raise RuntimeError("❌ DATABASE_URL is not set. Please check your `.env`.")

logger.info(f"✅ Using DATABASE_URL: {database_url}")

engine = create_async_engine(
    database_url,
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

# Backwards compatible alias
get_db = get_async_db


async def init_db() -> None:
    """
    Initialize the database (create tables if necessary).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Tables created successfully.")
