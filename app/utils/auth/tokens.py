# app/utils/auth/tokens.py

from jose import jwt, JWTError
from typing import Optional, Dict
import requests
from functools import lru_cache
from app.config import settings

JWKS_URL = f"{settings.authentik_url.rstrip('/')}/application/o/jwks/"

@lru_cache()
def fetch_jwks() -> Dict:
    try:
        res = requests.get(JWKS_URL)
        return res.json()
    except Exception:
        return {}

def verify_jwt(token: str) -> Optional[dict]:
    """
    Validates an Authentik JWT using public JWKS.
    """
    try:
        jwks = fetch_jwks()
        unverified_header = jwt.get_unverified_header(token)
        key = next((k for k in jwks.get("keys", []) if k["kid"] == unverified_header["kid"]), None)
        if not key:
            return None
        return jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            audience=settings.authentik_client_id,
        )
    except JWTError:
        return None
