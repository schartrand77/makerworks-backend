import os
import redis
import logging

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

try:
    redis_client.ping()
except redis.exceptions.ConnectionError as e:
    raise RuntimeError(f"Redis connection failed: {e}")

logger = logging.getLogger("makerworks.redis")
logger.info(f"Connected to Redis at {REDIS_URL}")

def get_redis_client() -> redis.Redis:
    return redis_client