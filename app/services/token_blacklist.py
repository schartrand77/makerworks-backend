import time

from redis.asyncio import Redis

BLACKLIST_PREFIX = "blacklist:token:"


async def blacklist_token(redis: Redis, jti: str, exp: int):
    ttl = exp - int(time.time())
    if ttl > 0:
        await redis.setex(f"{BLACKLIST_PREFIX}{jti}", ttl, "revoked")


async def is_token_blacklisted(redis: Redis, jti: str) -> bool:
    return await redis.exists(f"{BLACKLIST_PREFIX}{jti}") == 1
