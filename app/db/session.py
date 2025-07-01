from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from typing import AsyncGenerator

# Create the async engine
engine = create_async_engine(settings.async_database_url, echo=False)

# Legacy-style session maker (optional usage)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ✅ Modern async_sessionmaker export (required by scripts like seed_filaments.py)
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# Optional async session getter (used elsewhere in some apps)
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session