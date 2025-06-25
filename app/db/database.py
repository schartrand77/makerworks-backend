# app/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import os

DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "postgresql+asyncpg://authentik:authentik@192.168.1.170:5432/makerworks")

logger = logging.getLogger("makerworks.database")
logger.info(f"[DB] Loaded ASYNC_DATABASE_URL = {DATABASE_URL}")

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

AsyncSessionLocal = async_session  # alias

Base = declarative_base()

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# 🔥 FastAPI-compatible
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# ✅ Add init_db() for Alembic-style bootstrapping
async def init_db() -> None:
    import app.models  # ensure all models are registered with Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[DB] Tables created successfully.")