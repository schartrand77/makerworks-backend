import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import User
from app.config import settings

# Use the correct database URL from your FastAPI settings
DATABASE_URL = settings.async_database_url

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# You can set this to a static sub value if known from Authentik, or leave as UUID for dev
ADMIN_DATA = {
    "id": "admin-dev-id",  # Replace with actual OIDC sub for real Authentik seed
    "email": "stephenchartrand77@gmail.com",
    "username": "techpunk",
    "name": "Stephen",
    "created_at": datetime.utcnow(),
    "is_verified": True,
    "role": "admin"
}

async def seed():
    async with AsyncSessionLocal() as session:
        existing = await session.get(User, ADMIN_DATA["id"])
        if existing:
            print("ℹ️ Admin user already exists.")
            return
        admin_user = User(**ADMIN_DATA)
        session.add(admin_user)
        await session.commit()
        print("✅ Admin user seeded.")

if __name__ == "__main__":
    asyncio.run(seed())