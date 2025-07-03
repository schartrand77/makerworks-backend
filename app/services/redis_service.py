import logging
from redis.asyncio import Redis
from fastapi import Depends

from app.config.settings import settings

# Use REDIS_URL from settings
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

# Logger
logger = logging.getLogger("makerworks.redis")

# ──────────────────────────────────────────────────────────────
# Verify Redis connection on startup
# ──────────────────────────────────────────────────────────────
async def verify_redis_connection():
    try:
        await redis_client.ping()
        logger.info(f"✅ Connected to Redis at {settings.redis_url}")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise RuntimeError(f"Redis connection failed: {e}")

# ──────────────────────────────────────────────────────────────
# Dependency-injectable accessor
# ──────────────────────────────────────────────────────────────
async def get_redis() -> Redis:
    return redis_client