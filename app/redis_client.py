import os
import redis
import logging

# Load Redis URL from env or default to DB 1 on correct host
REDIS_URL = os.getenv("REDIS_URL", "redis://192.168.1.170:6379/1")

# Initialize Redis client with response decoding
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Set up logger
logger = logging.getLogger("makerworks.redis")

# Validate connection on import
try:
    redis_client.ping()
    logger.info(f"✅ Connected to Redis at {REDIS_URL}")
except redis.exceptions.ConnectionError as e:
    logger.error(f"❌ Redis connection failed: {e}")
    raise RuntimeError(f"Redis connection failed: {e}")

# Expose accessor for external use
def get_redis_client() -> redis.Redis:
    return redis_client