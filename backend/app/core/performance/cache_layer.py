"""Cache Layer — Redis caching for KPIs, market data, agent status."""

import json
import logging
import time
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheKeyBuilder:
    """Build consistent cache keys."""

    @staticmethod
    def build(namespace: str, *parts: Any) -> str:
        """Build cache key from parts."""
        key_parts = [namespace] + [str(p) for p in parts]
        return ":".join(key_parts)

    @staticmethod
    def hash_query(query: str) -> str:
        """Hash a query for cache key."""
        return hashlib.md5(query.encode()).hexdigest()


@dataclass
class CacheEntry:
    """Cache entry metadata."""
    key: str
    value: Any
    ttl_seconds: int
    created_at: datetime
    accessed_at: datetime
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "ttl_seconds": self.ttl_seconds,
            "age_seconds": int((datetime.utcnow() - self.created_at).total_seconds()),
            "hit_count": self.hit_count,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
        }


class LocalCache:
    """In-memory cache (fallback when Redis unavailable)."""

    def __init__(self, max_size: int = 10000):
        """Initialize local cache."""
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        entry = self.cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None

        entry.hit_count += 1
        entry.accessed_at = datetime.utcnow()
        self.hits += 1
        return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set value in cache."""
        # Evict oldest entry if at max size
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].accessed_at
            )
            del self.cache[oldest_key]

        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
        )

    async def delete(self, key: str) -> None:
        """Delete entry from cache."""
        self.cache.pop(key, None)

    async def clear(self) -> int:
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "entries": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3),
            "total_requests": total_requests,
        }


class RedisCache:
    """Redis-based distributed cache."""

    def __init__(self, redis_client: Any):
        """Initialize Redis cache."""
        self.redis = redis_client
        self.local_stats = {"hits": 0, "misses": 0}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            value = await self.redis.get(key)

            if value is None:
                self.local_stats["misses"] += 1
                return None

            self.local_stats["hits"] += 1

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set value in Redis cache."""
        try:
            # Try to serialize as JSON
            try:
                serialized = json.dumps(value)
            except TypeError:
                serialized = str(value)

            await self.redis.setex(key, ttl_seconds, serialized)

        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete entry from Redis cache."""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")

    async def clear(self) -> int:
        """Clear Redis cache (all keys with app prefix)."""
        try:
            # In production, use pattern matching to avoid clearing unrelated keys
            keys = await self.redis.keys("app:*")
            if keys:
                await self.redis.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.local_stats["hits"] + self.local_stats["misses"]
        hit_rate = (
            self.local_stats["hits"] / total if total > 0 else 0
        )

        return {
            "hits": self.local_stats["hits"],
            "misses": self.local_stats["misses"],
            "hit_rate": round(hit_rate, 3),
            "total_requests": total,
        }


class CacheLayer:
    """Multi-tier cache layer with Redis and local fallback."""

    # Cache TTL presets
    TTL_SHORT = 300  # 5 minutes
    TTL_MEDIUM = 1800  # 30 minutes
    TTL_LONG = 3600  # 1 hour
    TTL_VERY_LONG = 86400  # 24 hours

    # Cache namespaces
    NAMESPACE_KPI = "kpi"
    NAMESPACE_MARKET = "market"
    NAMESPACE_AGENT = "agent"
    NAMESPACE_USER = "user"
    NAMESPACE_QUERY = "query"

    def __init__(self, redis_client: Optional[Any] = None):
        """Initialize cache layer."""
        self.redis = RedisCache(redis_client) if redis_client else None
        self.local = LocalCache(max_size=10000)
        self.stats = {"redis_available": redis_client is not None}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Try Redis first if available
        if self.redis:
            value = await self.redis.get(key)
            if value is not None:
                return value

        # Fall back to local cache
        return await self.local.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        local_only: bool = False,
    ) -> None:
        """Set value in cache."""
        # Set in local cache
        await self.local.set(key, value, ttl_seconds)

        # Set in Redis if available and not local_only
        if self.redis and not local_only:
            await self.redis.set(key, value, ttl_seconds)

    async def delete(self, key: str) -> None:
        """Delete entry from cache."""
        await self.local.delete(key)
        if self.redis:
            await self.redis.delete(key)

    async def clear(self) -> Dict[str, int]:
        """Clear all caches."""
        local_count = await self.local.clear()
        redis_count = 0

        if self.redis:
            redis_count = await self.redis.clear()

        return {"local": local_count, "redis": redis_count}

    def cache_decorator(
        self,
        ttl_seconds: int = 3600,
        namespace: str = "default",
    ):
        """Decorator for caching function results."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Build cache key from function name and arguments
                cache_key = CacheKeyBuilder.build(
                    namespace,
                    func.__name__,
                    str(args),
                    str(sorted(kwargs.items())),
                )

                # Try to get from cache
                cached = await self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached

                # Execute function
                result = await func(*args, **kwargs)

                # Store in cache
                await self.set(cache_key, result, ttl_seconds)

                return result

            return wrapper

        return decorator

    # Pre-configured cache methods for specific use cases

    async def cache_kpi(
        self,
        agent_id: str,
        metric_name: str,
        value: Any,
        ttl_seconds: int = TTL_MEDIUM,
    ) -> None:
        """Cache KPI metric."""
        key = CacheKeyBuilder.build(self.NAMESPACE_KPI, agent_id, metric_name)
        await self.set(key, value, ttl_seconds)

    async def get_kpi(self, agent_id: str, metric_name: str) -> Optional[Any]:
        """Get cached KPI metric."""
        key = CacheKeyBuilder.build(self.NAMESPACE_KPI, agent_id, metric_name)
        return await self.get(key)

    async def cache_market_data(
        self,
        market_id: str,
        data: Dict[str, Any],
        ttl_seconds: int = TTL_LONG,
    ) -> None:
        """Cache market data."""
        key = CacheKeyBuilder.build(self.NAMESPACE_MARKET, market_id)
        await self.set(key, data, ttl_seconds)

    async def get_market_data(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get cached market data."""
        key = CacheKeyBuilder.build(self.NAMESPACE_MARKET, market_id)
        value = await self.get(key)
        return value if isinstance(value, dict) else None

    async def cache_agent_status(
        self,
        agent_id: str,
        status: Dict[str, Any],
        ttl_seconds: int = TTL_SHORT,
    ) -> None:
        """Cache agent status."""
        key = CacheKeyBuilder.build(self.NAMESPACE_AGENT, agent_id, "status")
        await self.set(key, status, ttl_seconds)

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get cached agent status."""
        key = CacheKeyBuilder.build(self.NAMESPACE_AGENT, agent_id, "status")
        value = await self.get(key)
        return value if isinstance(value, dict) else None

    async def cache_query_result(
        self,
        query_hash: str,
        result: Any,
        ttl_seconds: int = TTL_MEDIUM,
    ) -> None:
        """Cache query result."""
        key = CacheKeyBuilder.build(self.NAMESPACE_QUERY, query_hash)
        await self.set(key, result, ttl_seconds)

    async def get_query_result(self, query_hash: str) -> Optional[Any]:
        """Get cached query result."""
        key = CacheKeyBuilder.build(self.NAMESPACE_QUERY, query_hash)
        return await self.get(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "local_cache": self.local.get_stats(),
            "redis_cache": self.redis.get_stats() if self.redis else None,
            "redis_available": self.redis is not None,
        }
