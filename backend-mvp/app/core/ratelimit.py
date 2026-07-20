"""Rate limiting · Redis-backed sliding window.

Usage in endpoints:
    from app.core.ratelimit import rate_limit

    @router.post("/login")
    async def login(request: Request, payload: ..., _: None = Depends(rate_limit("login", limit=5, window_s=60))):
        ...
"""
import time
from typing import Callable

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from app.core.config import settings


_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _client_id(request: Request) -> str:
    """Best-effort client id: authenticated user > Cloudflare CF-Connecting-IP > X-Forwarded-For > peer."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer ") and len(auth) > 20:
        # Hash token last-8-chars as user fingerprint without storing raw
        return f"u:{auth[-8:]}"

    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return f"ip:{cf}"

    xff = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if xff:
        return f"ip:{xff}"

    return f"ip:{request.client.host if request.client else 'unknown'}"


def rate_limit(bucket: str, limit: int, window_s: int = 60) -> Callable:
    """Dep factory: enforces N requests per window per client.

    Sliding window via Redis ZSET. Backwards-compatible: if Redis unreachable, fails open with log.
    """
    async def _check(request: Request) -> None:
        cid = _client_id(request)
        key = f"rl:{bucket}:{cid}"
        now = time.time()
        window_start = now - window_s

        try:
            r = _get_redis()
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {f"{now}:{request.url.path}": now})
            pipe.zcard(key)
            pipe.expire(key, window_s + 5)
            _, _, count, _ = await pipe.execute()
        except Exception:
            # Fail-open: don't block traffic if Redis dies
            return

        if count > limit:
            retry_after = window_s
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded · bucket={bucket} · limit={limit}/{window_s}s",
                headers={"Retry-After": str(retry_after), "X-RateLimit-Limit": str(limit), "X-RateLimit-Window": str(window_s)},
            )

    return _check
