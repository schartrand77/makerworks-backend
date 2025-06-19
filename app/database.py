import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with async_session() as session:
        yield session
        
        
from sqlalchemy.exc import SQLAlchemyError

async def check_db_connection(session_factory) -> bool:
    try:
        async with session_factory() as session:
            await session.execute("SELECT 1")
        return True
    except SQLAlchemyError:
        return False