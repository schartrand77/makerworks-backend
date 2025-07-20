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
from uuid import uuid4
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from tempfile import gettempdir

from app.models.models import Base
from app.db.database import get_db
from app.models.models import User

spec = importlib.util.spec_from_file_location(
    "app.routes.users",
    Path(__file__).resolve().parents[1] / "app" / "routes" / "users.py",
)
users = importlib.util.module_from_spec(spec)
spec.loader.exec_module(users)


def create_test_app():
    db_file = Path(gettempdir()) / "test_profile.db"
    if db_file.exists():
        db_file.unlink()
    engine = create_engine(
        f"sqlite:///{db_file}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    session_local = sessionmaker(bind=engine, class_=Session)

    def override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    def init_models():
        User.__table__.create(engine)

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

    init_models()
    app.state._sessionmaker = session_local
    return app


def add_test_user(app, user_id):
    session_local = app.state._sessionmaker
    with session_local() as session:
        uid_str = str(user_id).replace("-", "")
        user = User(
            id=user_id,
            email=f"{uid_str}@example.com",
            username=uid_str,
            hashed_password="password123",
        )
        session.add(user)
        session.commit()


@pytest.fixture()
def client():
    app = create_test_app()
    with TestClient(app) as c:
        yield c


def test_update_profile_requires_auth(client):
    resp = client.patch("/api/v1/users/me", json={"bio": "hi"})
    assert resp.status_code == 401


