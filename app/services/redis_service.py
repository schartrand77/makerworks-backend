import os
import logging
from redis.asyncio import Redis
from fastapi import Depends

# Load Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://192.168.1.170:6379/1")

# Initialize async Redis client
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

# Logger
logger = logging.getLogger("makerworks.redis")

# Connection test on startup
async def verify_redis_connection():
    try:
        await redis_client.ping()
        logger.info(f"✅ Connected to Redis at {REDIS_URL}")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise RuntimeError(f"Redis connection failed: {e}")

# Dependency-injectable Redis accessor
async def get_redis() -> Redis:
    return redis_client