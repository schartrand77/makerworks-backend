import asyncio
from sqlalchemy import select
from app.models.user import User
from app.core.security import get_password_hash
from app.db.session import get_async_session
from datetime import datetime


ADMIN_EMAIL = "admin@makerworks.io"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_ROLE = "admin"


async def seed_admin():
    print("[⚙️] Running seed_admin...")

    try:
        async with get_async_session() as session:
            print("[🔍] Checking for existing admin...")
            result = await session.execute(
                select(User).where(User.email == ADMIN_EMAIL)
            )
            user = result.scalar_one_or_none()

            if user:
                print(f"[✅] Admin already exists: {user.email}")
                return

            print("[➕] Creating admin user...")

            new_user = User(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_verified=True,
                role=ADMIN_ROLE,
                created_at=datetime.utcnow()
            )

            session.add(new_user)
            await session.commit()

            print(f"[🎉] Admin seeded: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

    except Exception as e:
        print(f"[❌] Error seeding admin: {e}")


if __name__ == "__main__":
    asyncio.run(seed_admin())