# app/db/database.py

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

# ───────────────────────────────────────────────
# Config
# ───────────────────────────────────────────────
# Default to a local development database if none is provided
DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://user:pass@localhost:5432/makerworks",
)

logger = logging.getLogger("makerworks.database")
# Avoid logging full connection string to prevent credential leakage
logger.info("[DB] Loaded database configuration")

# ───────────────────────────────────────────────
# Engine & Session
# ───────────────────────────────────────────────
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    future=True,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

AsyncSessionLocal = async_session  # alias for consistency

# ───────────────────────────────────────────────
# Declarative Base
# ───────────────────────────────────────────────
Base = declarative_base()


# ───────────────────────────────────────────────
# FastAPI Dependency
# ───────────────────────────────────────────────
@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# ───────────────────────────────────────────────
# Init DB (used on startup or for Alembic bootstraps)
# ───────────────────────────────────────────────
async def init_db() -> None:

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Tables created successfully.")
