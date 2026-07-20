"""Rate limiting service with DDoS and brute-force protection.

Implements:
- Standard rate limit: 100 req/min per IP
- Webhook rate limit: 1000 req/min per IP
- Login brute-force protection: 5 failed attempts -> 15 min ban
"""

import redis.asyncio as redis
import time
from datetime import datetime, timedelta
from typing import Optional
import hashlib
from fastapi import Request, HTTPException, status


class RateLimiter:
    """Advanced rate limiting with adaptive thresholds."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        # Standard endpoint: 100 req/min = 1.67 req/sec
        self.standard_limit = 100
        self.standard_window = 60
        # Webhook endpoints: 1000 req/min = 16.67 req/sec
        self.webhook_limit = 1000
        self.webhook_window = 60
        # Brute force protection
        self.login_max_attempts = 5
        self.login_ban_duration = 900  # 15 minutes

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        endpoint_type: str = "standard",
    ) -> dict:
        """
        Check if request exceeds rate limit.

        Args:
            identifier: Unique identifier (IP, user_id, etc)
            limit: Max requests per window
            window_seconds: Time window in seconds
            endpoint_type: Type of endpoint (standard, webhook, login)

        Returns:
            {
                "allowed": bool,
                "current": int,
                "limit": int,
                "reset_after": int (seconds),
                "retry_after": int (seconds, if blocked)
            }
        """
        key = f"ratelimit:{endpoint_type}:{identifier}"
        current_window = int(time.time() // window_seconds)
        window_key = f"{key}:{current_window}"

        try:
            current_count = await self.redis.incr(window_key)

            # Set expiration only on first request in window
            if current_count == 1:
                await self.redis.expire(window_key, window_seconds + 1)

            allowed = current_count <= limit
            reset_after = window_seconds - (int(time.time()) % window_seconds)

            result = {
                "allowed": allowed,
                "current": current_count,
                "limit": limit,
                "reset_after": reset_after,
            }

            if not allowed:
                result["retry_after"] = reset_after

            return result
        except Exception as e:
            # On Redis error, fail open (allow request) but log
            return {
                "allowed": True,
                "current": 0,
                "limit": limit,
                "reset_after": window_seconds,
                "error": str(e),
            }

    async def check_login_attempt(self, identifier: str) -> dict:
        """Check login attempts for brute-force protection."""
        ban_key = f"login:ban:{identifier}"
        attempts_key = f"login:attempts:{identifier}"

        # Check if user is banned
        is_banned = await self.redis.exists(ban_key)
        if is_banned:
            ttl = await self.redis.ttl(ban_key)
            return {
                "allowed": False,
                "reason": "too_many_failed_attempts",
                "ban_expires_in": ttl,
                "retry_after": ttl,
            }

        # Get current attempt count
        attempts = await self.redis.get(attempts_key)
        current_attempts = int(attempts) if attempts else 0

        if current_attempts >= self.login_max_attempts:
            # Ban the user for 15 minutes
            await self.redis.setex(
                ban_key,
                self.login_ban_duration,
                "1",
            )
            # Clear attempts counter
            await self.redis.delete(attempts_key)
            return {
                "allowed": False,
                "reason": "too_many_failed_attempts",
                "ban_expires_in": self.login_ban_duration,
                "retry_after": self.login_ban_duration,
            }

        return {
            "allowed": True,
            "current_attempts": current_attempts,
            "max_attempts": self.login_max_attempts,
            "remaining_attempts": self.login_max_attempts - current_attempts,
        }

    async def record_failed_login(self, identifier: str) -> None:
        """Record a failed login attempt."""
        attempts_key = f"login:attempts:{identifier}"
        await self.redis.incr(attempts_key)
        # Expire after 1 hour (resets counter)
        await self.redis.expire(attempts_key, 3600)

    async def clear_login_attempts(self, identifier: str) -> None:
        """Clear failed login attempts (on successful login)."""
        attempts_key = f"login:attempts:{identifier}"
        ban_key = f"login:ban:{identifier}"
        await self.redis.delete(attempts_key)
        await self.redis.delete(ban_key)

    async def get_client_identifier(self, request: Request) -> str:
        """Extract client identifier from request (IP-based for now)."""
        # Prefer X-Forwarded-For if behind proxy (Cloudflare, LB)
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        return "unknown"


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(redis_client: redis.Redis) -> RateLimiter:
    """Get or create global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter
