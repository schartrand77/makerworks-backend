# app/services/auth_service.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status

from app.models import User
from app.config import settings
from app.schemas.auth import TokenResponse, UserOut  # ✅ added schema imports

# Raise 401 when token is invalid or missing
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid token or credentials",
)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT token with optional expiry.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })

    print("[auth_service] Creating access token with payload:")
    for k, v in to_encode.items():
        print(f"  - {k}: {v}")

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        print("[auth_service] JWT successfully encoded. Length:", len(encoded_jwt))
        return encoded_jwt
    except Exception as e:
        print("[auth_service] Error during token encoding:", str(e))
        raise


def verify_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    """
    print("[auth_service] Verifying access token...")
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        print("[auth_service] Token payload:", payload)
        return payload
    except JWTError as e:
        print("[auth_service] JWTError during verification:", str(e))
        raise credentials_exception


def verify_token(token: str) -> str:
    """
    Verify token and extract user ID.
    """
    print("[auth_service] Verifying token for user_id...")
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id or not isinstance(user_id, str):
            print("[auth_service] Invalid or missing user_id in token")
            raise credentials_exception
        print("[auth_service] Extracted user_id:", user_id)
        return user_id
    except JWTError as e:
        print("[auth_service] JWTError during user_id extraction:", str(e))
        raise credentials_exception


def create_token_for_user(user: User) -> str:
    """
    Generate a raw JWT string for a user instance.
    """
    print("[auth_service] Creating token for user:", user.id, user.email)
    return create_access_token({"sub": str(user.id)})


def generate_auth_response(user: User) -> TokenResponse:
    """
    Generate a full auth response including JWT and user info.
    """
    print("[auth_service] Generating auth response for user:")
    print("  - ID:", user.id)
    print("  - Email:", user.email)
    print("  - Role:", user.role)

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })

    print("[auth_service] Access token generated, sending response.")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.from_orm(user)
    )