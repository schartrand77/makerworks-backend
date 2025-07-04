import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

app.db.database import async_session
from app.models import User
from app.services.auth_service import hash_password
from app.config import settings


async def create_admin():
    async with async_session() as session:  # type: AsyncSession
        result = await session.execute(select(User))
        existing_users = result.scalars().first()

        if existing_users:
            print("✅ Admin seed skipped: Users already exist.")
            return

        # Use env or fallback
        admin_email = getattr(settings, "admin_email", "admin@makerworks.io")
        admin_username = getattr(settings, "admin_username", "admin")
        admin_password = getattr(settings, "admin_password", "changeme")

        print(f"🔧 No users found — seeding default admin: {admin_email}")

        new_admin = User(
            email=admin_email,
            username=admin_username,
            hashed_password=hash_password(admin_password),
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            is_verified=True,
            role="admin"
        )

        session.add(new_admin)
        await session.commit()
        print("✅ Admin user created.")


if __name__ == "__main__":
    asyncio.run(create_admin())
