# app/services/token_service.py

import json
import logging
import uuid
from datetime import datetime, timedelta

import httpx
from authlib.jose import JsonWebKey, jwt as authlib_jwt
from fastapi import HTTPException, status
from jose import jwt

from app.config.settings import settings
from app.services.redis_service import get_redis

logger = logging.getLogger(__name__)

JWKS_CACHE_KEY = "jwks:authentik"
JWKS_TTL_SECONDS = int(timedelta(hours=6).total_seconds())  # 6 hours


# ──────────────────────────────────────────────────────────────
# Load RS256 Private Key for Signing
# ──────────────────────────────────────────────────────────────


def load_private_key() -> str:
    try:
        with open(settings.private_key_path) as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(
            f"Could not load private key from {settings.private_key_path}: {e}"
        ) from e


# ──────────────────────────────────────────────────────────────
# Create RS256 Access Token
# ──────────────────────────────────────────────────────────────


def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: timedelta = timedelta(hours=2),
) -> str:
    now = datetime.utcnow()
    expire = now + expires_delta
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(user_id),  # ensure UUID is string
        "email": email,
        "role": role,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "aud": settings.auth_audience,
        "iss": settings.domain,
    }

    private_key = load_private_key()
    return jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": settings.private_key_kid},
    )


# ──────────────────────────────────────────────────────────────
# Get JWKS from Redis or Fetch from Authentik
# ──────────────────────────────────────────────────────────────


async def get_jwks() -> JsonWebKey:
    redis = await get_redis()

    try:
        cached = await redis.get(JWKS_CACHE_KEY)
        if cached:
            logger.debug("[JWKS] Loaded JWKS from Redis cache")
            return JsonWebKey.import_key_set(json.loads(cached))
    except Exception as e:
        logger.warning(f"[JWKS] Redis fetch failed: {e}")

    try:
        jwks_url = f"{settings.authentik_issuer.rstrip('/')}/.well-known/jwks.json"
        async with httpx.AsyncClient() as client:
            res = await client.get(jwks_url, timeout=10)
            res.raise_for_status()
            jwks_json = res.json()

        try:
            await redis.set(JWKS_CACHE_KEY, json.dumps(jwks_json), ex=JWKS_TTL_SECONDS)
            logger.debug("[JWKS] Cached JWKS in Redis")
        except Exception as e:
            logger.warning(f"[JWKS] Redis set failed: {e}")

        return JsonWebKey.import_key_set(jwks_json)

    except Exception as e:
        raise RuntimeError(f"Failed to fetch JWKS from Authentik: {e}") from e


# ──────────────────────────────────────────────────────────────
# Validate RS256 Token from Authentik
# ──────────────────────────────────────────────────────────────


async def verify_token_rs256(token: str) -> dict:
    try:
        jwks = await get_jwks()
        claims = authlib_jwt.decode(
            token,
            key=jwks,
            claims_options={
                "iss": {"value": settings.authentik_issuer},
                "aud": {"value": settings.auth_audience},
                "exp": {"essential": True},
                "sub": {"essential": True},
            },
        )
        claims.validate()
        return claims
    except Exception as e:
        logger.warning(f"[JWT] Verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT: {e}",
        ) from e
