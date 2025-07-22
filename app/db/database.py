import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config.settings import settings

logger = logging.getLogger("makerworks.database")

if not settings.async_database_url:
    logger.critical("❌ ASYNC_DATABASE_URL is not set in the environment. Did you load `.env.dev`?")
    raise RuntimeError("❌ ASYNC_DATABASE_URL is not set. Please ensure your .env.dev is loaded or set ENV_FILE when starting.")

logger.info(f"✅ Using ASYNC_DATABASE_URL: {settings.async_database_url}")

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    poolclass=NullPool,
    future=True,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Tables created successfully.")
