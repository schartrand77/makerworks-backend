import sys
import os
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ensure required env vars for settings so importing routes doesn't fail
defaults = {
    "ENV": "test",
    "DOMAIN": "http://localhost",
    "BASE_URL": "http://localhost",
    "VITE_API_BASE_URL": "http://localhost",
    "UPLOAD_DIR": "/tmp",
    "MODEL_DIR": "/tmp",
    "AVATAR_DIR": "/tmp",
    "DATABASE_URL": "sqlite:///./test.db",
    "ASYNC_DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "REDIS_URL": "redis://localhost:6379/1",
    "AUTHENTIK_URL": "http://authentik",
    "AUTHENTIK_CLIENT_ID": "id",
    "AUTHENTIK_CLIENT_SECRET": "secret",
    "STRIPE_SECRET_KEY": "sk",
    "STRIPE_WEBHOOK_SECRET": "wh",
    "METRICS_API_KEY": "metrics",
}

for k, v in defaults.items():
    os.environ.setdefault(k, v)

from app.db import Base
from app.models import User, Model3D, ModelMetadata
from app.routes.admin import view_user_uploads

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_view_user_uploads_filters_by_uploader(db_session: AsyncSession):
    user_uuid = uuid.uuid4()
    other_uuid = uuid.uuid4()

    user_id = str(user_uuid)
    other_user_id = str(other_uuid)

    db_session.add_all([
        User(id=user_id, email="a@example.com", username="usera"),
        User(id=other_user_id, email="b@example.com", username="userb"),
    ])
    await db_session.commit()

    model_1 = Model3D(id=uuid.uuid4(), name="m1", uploader_id=user_uuid)
    model_2 = Model3D(id=uuid.uuid4(), name="m2", uploader_id=other_uuid)
    db_session.add_all([model_1, model_2])
    await db_session.commit()

    meta_1 = ModelMetadata(model_id=model_1.id, volume_mm3=1.0, dimensions_mm={"x":1,"y":1,"z":1}, face_count=10)
    meta_2 = ModelMetadata(model_id=model_2.id, volume_mm3=2.0, dimensions_mm={"x":2,"y":2,"z":2}, face_count=20)
    db_session.add_all([meta_1, meta_2])
    await db_session.commit()

    results = await view_user_uploads(user_id=user_uuid, db=db_session, admin=None)
    assert len(results) == 1
    assert results[0].model_id == model_1.id
