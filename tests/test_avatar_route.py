import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DOMAIN", "http://testserver")
os.environ.setdefault("BASE_URL", "http://testserver")
os.environ.setdefault("VITE_API_BASE_URL", "http://testserver")
os.environ.setdefault("UPLOAD_DIR", "/tmp")
os.environ.setdefault("MODEL_DIR", "/tmp")
os.environ.setdefault("AVATAR_DIR", "/tmp")
os.environ.setdefault("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "secret")

import importlib.util
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db

spec = importlib.util.spec_from_file_location(
    "app.routes.avatar",
    Path(__file__).resolve().parents[1] / "app" / "routes" / "avatar.py",
)
avatar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(avatar)


def create_test_app():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session() as session:
            yield session

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(avatar.router, prefix="/api/v1/users", tags=["users"])

    import asyncio

    asyncio.get_event_loop().run_until_complete(init_models())
    return app


@pytest.fixture()
def client():
    app = create_test_app()
    with TestClient(app) as c:
        yield c


def test_avatar_route_registered(client):
    paths = [route.path for route in client.app.routes]
    assert "/api/v1/users/avatar" in paths
