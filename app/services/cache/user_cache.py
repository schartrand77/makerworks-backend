import json
from datetime import timedelta
from uuid import UUID
from typing import Optional

from redis.asyncio import Redis
from app.schemas.users import UserOut
import logging
import prometheus_client

logger = logging.getLogger("user_cache")

# Redis Key Prefixes
USER_CACHE_PREFIX = "user:cache:"
USER_ID_KEY = lambda user_id: f"{USER_CACHE_PREFIX}id:{user_id}"
USERNAME_KEY = lambda username: f"{USER_CACHE_PREFIX}username:{username}"

# Time-to-live (TTL) for user cache entries
DEFAULT_TTL = timedelta(hours=2)

# Prometheus Metrics
user_cache_hits = prometheus_client.Counter(
    "user_cache_hits", "Total Redis user cache hits", ["lookup_type"]
)
user_cache_misses = prometheus_client.Counter(
    "user_cache_misses", "Total Redis user cache misses", ["lookup_type"]
)
user_cache_sets = prometheus_client.Counter(
    "user_cache_sets", "Total Redis user cache set operations"
)
user_cache_deletes = prometheus_client.Counter(
    "user_cache_deletes", "Total Redis user cache delete operations"
)


def serialize_user(user: UserOut) -> str:
    return user.model_dump_json()


def deserialize_user(data: str) -> UserOut:
    return UserOut.model_validate_json(data)


async def cache_user_by_id(redis: Redis, user: UserOut, ttl: timedelta = DEFAULT_TTL):
    key = USER_ID_KEY(user.id)
    await redis.set(key, serialize_user(user), ex=ttl)
    user_cache_sets.inc()
    logger.info(f"[REDIS] Cached user by ID: {user.id}")


async def cache_user_by_username(redis: Redis, user: UserOut, ttl: timedelta = DEFAULT_TTL):
    key = USERNAME_KEY(user.username)
    await redis.set(key, serialize_user(user), ex=ttl)
    user_cache_sets.inc()
    logger.info(f"[REDIS] Cached user by username: {user.username}")


async def get_user_by_id(redis: Redis, user_id: UUID) -> Optional[UserOut]:
    key = USER_ID_KEY(user_id)
    data = await redis.get(key)
    if data:
        user_cache_hits.labels(lookup_type="id").inc()
        logger.debug(f"[REDIS] Cache hit for user ID: {user_id}")
        return deserialize_user(data)
    else:
        user_cache_misses.labels(lookup_type="id").inc()
        logger.debug(f"[REDIS] Cache miss for user ID: {user_id}")
        return None


async def get_user_by_username(redis: Redis, username: str) -> Optional[UserOut]:
    key = USERNAME_KEY(username)
    data = await redis.get(key)
    if data:
        user_cache_hits.labels(lookup_type="username").inc()
        logger.debug(f"[REDIS] Cache hit for username: {username}")
        return deserialize_user(data)
    else:
        user_cache_misses.labels(lookup_type="username").inc()
        logger.debug(f"[REDIS] Cache miss for username: {username}")
        return None


async def delete_user_cache(redis: Redis, user_id: UUID, username: str):
    deleted = await redis.delete(USER_ID_KEY(user_id), USERNAME_KEY(username))
    user_cache_deletes.inc(deleted)
    logger.info(f"[REDIS] Deleted {deleted} user cache entries for {user_id} / {username}")


async def auto_clear_expired_keys(redis: Redis):
    """
    Optional: clears all expired keys in the Redis user cache namespace.
    This only makes sense in Redis configurations that do not automatically evict expired keys.
    """
    try:
        keys = await redis.keys(f"{USER_CACHE_PREFIX}*")
        count = 0
        for key in keys:
            if await redis.ttl(key) == -2:  # TTL -2 means key does not exist (expired)
                await redis.delete(key)
                count += 1
        logger.info(f"[REDIS] Auto-cleared {count} expired user cache keys on boot.")
    except Exception as e:
        logger.warning(f"[REDIS] Error auto-clearing expired keys: {e}")
