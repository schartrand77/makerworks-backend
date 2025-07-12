import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# set required environment variables before importing application modules
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
os.environ.setdefault("STRIPE_SECRET_KEY", "sk")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "wh")
os.environ.setdefault("DISCORD_CHANNEL_ID", "1")
os.environ.setdefault("DISCORD_BOT_TOKEN", "token")
os.environ.setdefault("DISCORD_WEBHOOK_URL", "http://testserver")
os.environ.setdefault("METRICS_API_KEY", "key")
os.environ.setdefault("AUTHENTIK_URL", "http://auth")
os.environ.setdefault("AUTHENTIK_ISSUER", "http://auth")
os.environ.setdefault("AUTHENTIK_CLIENT_ID", "client")
os.environ.setdefault("AUTHENTIK_CLIENT_SECRET", "secret")

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
    "app.routes.auth",
    Path(__file__).resolve().parents[1] / "app" / "routes" / "auth.py",
)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


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
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

    # patch token generation to avoid needing RSA keys
    auth.create_access_token = lambda *args, **kwargs: "testtoken"

    # initialize tables before returning app
    import asyncio

    asyncio.get_event_loop().run_until_complete(init_models())

    return app


@pytest.fixture()
def client():
    app = create_test_app()
    with TestClient(app) as c:
        yield c


def test_signup_and_signin_success(client):
    signup_payload = {
        "email": "test@example.com",
        "username": "tester",
        "password": "password123",
    }
    resp = client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 200
    token = resp.json()["token"]
    assert token == "testtoken"

    signin_payload = {
        "email_or_username": "test@example.com",
        "password": "password123",
    }
    resp = client.post("/api/v1/auth/signin", json=signin_payload)
    assert resp.status_code == 200
    assert resp.json()["token"] == "testtoken"


def test_signin_invalid_credentials(client):
    signup_payload = {
        "email": "foo@example.com",
        "username": "foo",
        "password": "goodpassword",
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    resp = client.post(
        "/api/v1/auth/signin",
        json={"email_or_username": "foo@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401
