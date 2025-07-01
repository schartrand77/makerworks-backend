# app/db/database.py

import os
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

# ───────────────────────────────────────────────
# Config
# ───────────────────────────────────────────────
DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "postgresql+asyncpg://authentik:authentik@192.168.1.170:5432/makerworks")

logger = logging.getLogger("makerworks.database")
logger.info(f"[DB] Loaded ASYNC_DATABASE_URL = {DATABASE_URL}")

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
    import app.db.models  # ensure all models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Tables created successfully.")