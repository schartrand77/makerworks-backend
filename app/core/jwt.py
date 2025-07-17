from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from jose.exceptions import JWTError

from app.config.settings import settings

# JWT configuration
JWT_AUDIENCE = getattr(settings, "authentik_url", "http://localhost:9000")
JWT_ALGORITHM = getattr(settings, "algorithm", "RS256")
PRIVATE_KEY_PATH = getattr(settings, "private_key_path", "keys/private.pem")

print(f"[DEBUG] JWT_AUDIENCE: {JWT_AUDIENCE}")
print(f"[DEBUG] JWT_ALGORITHM: {JWT_ALGORITHM}")
print(f"[DEBUG] PRIVATE_KEY_PATH resolved to: {PRIVATE_KEY_PATH}")

PRIVATE_KEY = None

try:
    with open(PRIVATE_KEY_PATH, "rb") as f:
        PRIVATE_KEY = f.read()
        print(f"[DEBUG] Private key loaded successfully from {PRIVATE_KEY_PATH}")
except FileNotFoundError:
    print(f"[ERROR] Private key file not found: {PRIVATE_KEY_PATH}")
except Exception as e:
    print(f"[ERROR] Failed to load private key from {PRIVATE_KEY_PATH}: {e}")
    PRIVATE_KEY = None


def create_jwt_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT token.

    Args:
        data (dict): Payload data to include in the token.
        expires_delta (Optional[timedelta]): How long the token is valid for.

    Returns:
        str: Signed JWT token.

    Raises:
        RuntimeError: if the private key could not be loaded or JWT fails to encode.
    """
    if not PRIVATE_KEY:
        raise RuntimeError(
            f"Cannot create JWT: private key was not loaded. Check PRIVATE_KEY_PATH ({PRIVATE_KEY_PATH})."
        )

    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "aud": JWT_AUDIENCE})

    try:
        encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=JWT_ALGORITHM)
    except JWTError as e:
        raise RuntimeError(f"Failed to encode JWT: {e}")

    return encoded_jwt