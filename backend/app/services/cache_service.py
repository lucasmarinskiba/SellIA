import redis
import json
import os
from typing import Any, Optional


class CacheService:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        self.default_ttl = 3600  # 1 hour

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.default_ttl
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0

    def get_or_set(self, key: str, fetch_fn, ttl: Optional[int] = None) -> Any:
        """Get from cache or fetch and cache."""
        cached = self.get(key)
        if cached is not None:
            return cached

        value = fetch_fn()
        self.set(key, value, ttl)
        return value

    def mget(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple keys."""
        try:
            values = self.redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            print(f"Cache mget error: {e}")
            return {}

    def mset(self, data: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple keys."""
        try:
            pipe = self.redis.pipeline()
            ttl = ttl or self.default_ttl

            for key, value in data.items():
                pipe.setex(key, ttl, json.dumps(value))

            pipe.execute()
            return True
        except Exception as e:
            print(f"Cache mset error: {e}")
            return False

    def incr(self, key: str) -> int:
        """Increment counter."""
        try:
            return self.redis.incr(key)
        except Exception as e:
            print(f"Cache incr error: {e}")
            return 0

    def decr(self, key: str) -> int:
        """Decrement counter."""
        try:
            return self.redis.decr(key)
        except Exception as e:
            print(f"Cache decr error: {e}")
            return 0

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration."""
        try:
            return bool(self.redis.expire(key, ttl))
        except Exception as e:
            print(f"Cache expire error: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live."""
        try:
            return self.redis.ttl(key)
        except Exception as e:
            print(f"Cache ttl error: {e}")
            return -1

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    def flush_all(self) -> bool:
        """Clear all cache (use with caution)."""
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            print(f"Cache flush error: {e}")
            return False


# Singleton instance
cache_service = CacheService()
