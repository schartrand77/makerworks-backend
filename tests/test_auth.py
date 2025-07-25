import os
import sys
import uuid
from pathlib import Path

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
os.environ.setdefault("STRIPE_SECRET_KEY", "test")

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db.session import get_db
from app.models.models import User


@pytest.mark.asyncio
async def test_signup(client: AsyncClient, db: AsyncSession):
    email = f"user-{uuid.uuid4()}@example.com"
    username = f"user-{uuid.uuid4()}"
    password = "StrongPass123!"

    response = await client.post("/signup", json={
        "email": email,
        "username": username,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == email
    assert data["user"]["username"] == username

    # Validate user exists in DB
    user_in_db = await db.get(User, uuid.UUID(data["user"]["id"]))
    assert user_in_db is not None

    base = Path(os.environ.get("UPLOAD_DIR", "/tmp")) / "users" / data["user"]["id"]
    assert (base / "avatars").exists()
    assert (base / "models").exists()


@pytest.mark.asyncio
async def test_signin(client: AsyncClient):
    # You should have seeded a test user beforehand for this test.
    email_or_username = "admin@example.com"
    password = "adminpassword"

    response = await client.post("/signin", json={
        "email_or_username": email_or_username,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data


@pytest.mark.asyncio
async def test_me(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "user" in data


@pytest.mark.asyncio
async def test_debug(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/debug", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "debug-token"
