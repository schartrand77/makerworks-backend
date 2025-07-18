import os
import uuid
from datetime import datetime, timedelta

from jose import jwt, JWTError

from app.config.settings import settings

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm


def create_access_token(user_id: str, email: str, role: str = "user", expires_delta: timedelta = timedelta(hours=2)) -> str:
    now = datetime.utcnow()
    expire = now + expires_delta
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
