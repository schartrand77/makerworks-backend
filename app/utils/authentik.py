from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import User
from datetime import datetime
from uuid import uuid4


async def upsert_user_from_authentik(
    db: AsyncSession,
    *,
    authentik_sub: str,
    email: str,
    username: str,
    avatar: str | None = None,
    role: str = "user",
) -> User:
    """
    Ensure a user exists in the MakerWorks DB for the given Authentik sub.
    If the user already exists (by `authentik_sub`), updates relevant fields.
    If not, creates a new user.
    """
    result = await db.execute(
        select(User).where(User.authentik_sub == authentik_sub)
    )
    user = result.scalar_one_or_none()

    if user:
        # update fields
        user.email = email
        user.username = username
        user.avatar = avatar
        user.last_login = datetime.utcnow()
    else:
        user = User(
            id=uuid4(),
            authentik_sub=authentik_sub,
            email=email,
            username=username,
            avatar=avatar,
            role=role,
            is_verified=True,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user
