"""Redis caching layer for SellIA.

Provides a @cached decorator for FastAPI endpoints and async functions.
"""

import json
import hashlib
import functools
from typing import Any, Callable
import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()


async def _get_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


def _make_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a deterministic cache key."""
    key_data = json.dumps({"f": func_name, "a": args, "k": kwargs}, sort_keys=True, default=str)
    return f"sellia:cache:{hashlib.sha256(key_data.encode()).hexdigest()[:32]}"


def cached(ttl_seconds: int = 60, key_prefix: str = ""):
    """Decorator that caches the result of an async function in Redis.

    Usage:
        @cached(ttl_seconds=300)
        async def get_expensive_data(business_id: UUID):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            redis_client = await _get_redis()
            try:
                key = _make_key(f"{key_prefix}:{func.__qualname__}", args, kwargs)
                cached_value = await redis_client.get(key)
                if cached_value is not None:
                    return json.loads(cached_value)

                result = await func(*args, **kwargs)
                await redis_client.setex(key, ttl_seconds, json.dumps(result, default=str))
                return result
            finally:
                await redis_client.close()
        return wrapper
    return decorator


async def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern."""
    redis_client = await _get_redis()
    try:
        keys = []
        async for key in redis_client.scan_iter(match=f"sellia:cache:{pattern}*"):
            keys.append(key)
        if keys:
            await redis_client.delete(*keys)
        return len(keys)
    finally:
        await redis_client.close()
