from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

from app.config import settings

# ✅ Base class for all ORM models
Base = declarative_base()

# ✅ Load async DB URL from config
ASYNC_DATABASE_URL = settings.async_database_url
if not ASYNC_DATABASE_URL:
    raise RuntimeError("❌ 'async_database_url' is not set. Check your .env or environment variables.")
print(f"[✅] Loaded ASYNC_DATABASE_URL = {ASYNC_DATABASE_URL}")

# ✅ Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.env == "development",
    future=True,
)

# ✅ Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ✅ FastAPI-compatible dependency
@asynccontextmanager
async def get_db():
    """
    Yields an async DB session. Use with `Depends(get_db)` in your routes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ✅ Optional: check connection at runtime (e.g. from /status route)
async def check_db_connection(session_factory=AsyncSessionLocal) -> bool:
    try:
        async with session_factory() as session:
            await session.execute("SELECT 1")
        return True
    except SQLAlchemyError as e:
        print(f"[❌] Database connection failed: {e}")
        return False