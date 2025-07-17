from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import User
from app.schemas.users import UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_local_user(db: AsyncSession, user_data: dict) -> User:
    """Create a local DB mirror for an Authentik user (manual)."""
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_profile(
    db: AsyncSession, user_id: UUID, data: UserUpdate
) -> User | None:
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(**data.dict(exclude_unset=True))
    )
    await db.execute(stmt)
    await db.commit()
    return await get_user_by_id(db, user_id)


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    stmt = delete(User).where(User.id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def update_last_login(db: AsyncSession, user_id: UUID) -> None:
    await db.execute(
        update(User).where(User.id == user_id).values(last_login=datetime.utcnow())
    )
    await db.commit()


async def upsert_user_from_authentik(db: AsyncSession, userinfo: dict) -> User:
    """
    Upsert a user in the local DB based on Authentik /userinfo payload.
    """
    email = userinfo.get("email")
    username = (
        userinfo.get("preferred_username")
        or userinfo.get("username")
        or email.split("@")[0]
    )

    if not email:
        raise ValueError("Authentik userinfo must include an email")

    existing_user = await get_user_by_email(db, email)

    if existing_user:
        existing_user.username = username
        existing_user.is_active = True
        existing_user.is_verified = userinfo.get("email_verified", True)
        existing_user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_user)
        return existing_user

    # Create new user
    new_user = User(
        id=uuid4(),
        email=email,
        username=username,
        is_active=True,
        is_verified=userinfo.get("email_verified", True),
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow(),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user