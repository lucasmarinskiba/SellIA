"""Rate limiting + request deduplication for API resilience."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging


logger = logging.getLogger(__name__)


class RateLimitTier(str, Enum):
    FREE = "free"  # 100 req/min, 10k/day
    PRO = "pro"  # 1000 req/min, 100k/day
    ENTERPRISE = "enterprise"  # 10k req/min, 1m/day
    UNLIMITED = "unlimited"  # No limits


@dataclass
class RateLimit:
    user_id: str
    tier: RateLimitTier
    requests_per_minute: int
    requests_per_day: int
    requests_this_minute: int = 0
    requests_today: int = 0
    minute_reset_at: datetime = None
    day_reset_at: datetime = None

    def __post_init__(self):
        if self.minute_reset_at is None:
            self.minute_reset_at = datetime.utcnow() + timedelta(minutes=1)
        if self.day_reset_at is None:
            self.day_reset_at = datetime.utcnow() + timedelta(days=1)


@dataclass
class RequestSignature:
    """Fingerprint for deduplication (idempotency)."""

    request_id: str
    user_id: str
    endpoint: str
    method: str
    payload_hash: str
    created_at: datetime
    response: Optional[dict] = None
    response_time_ms: int = 0


class RateLimiter:
    """
    Rate limiting per user + tier.

    Prevents:
    - API abuse (rate limit exceeded)
    - Brute force attacks
    - Resource exhaustion
    """

    TIER_LIMITS = {
        RateLimitTier.FREE: {"per_minute": 100, "per_day": 10_000},
        RateLimitTier.PRO: {"per_minute": 1000, "per_day": 100_000},
        RateLimitTier.ENTERPRISE: {"per_minute": 10_000, "per_day": 1_000_000},
        RateLimitTier.UNLIMITED: {"per_minute": 999_999, "per_day": 999_999_999},
    }

    def __init__(self):
        self.limits: dict[str, RateLimit] = {}

    def check_limit(self, user_id: str, tier: RateLimitTier) -> tuple[bool, dict]:
        """
        Check if user exceeded rate limit.

        Returns: (allowed: bool, info: dict with remaining/reset times)
        """

        limit = self.limits.get(user_id)
        if not limit:
            limit = self._create_limit(user_id, tier)
            self.limits[user_id] = limit

        # Reset counters if windows expired
        now = datetime.utcnow()
        if now > limit.minute_reset_at:
            limit.requests_this_minute = 0
            limit.minute_reset_at = now + timedelta(minutes=1)

        if now > limit.day_reset_at:
            limit.requests_today = 0
            limit.day_reset_at = now + timedelta(days=1)

        # Check limits
        tier_limit = self.TIER_LIMITS[tier]
        minute_ok = limit.requests_this_minute < tier_limit["per_minute"]
        day_ok = limit.requests_today < tier_limit["per_day"]
        allowed = minute_ok and day_ok

        # Increment if allowed
        if allowed:
            limit.requests_this_minute += 1
            limit.requests_today += 1

        info = {
            "allowed": allowed,
            "tier": tier.value,
            "requests_this_minute": limit.requests_this_minute,
            "requests_limit_minute": tier_limit["per_minute"],
            "requests_today": limit.requests_today,
            "requests_limit_day": tier_limit["per_day"],
            "minute_reset_at": limit.minute_reset_at.isoformat(),
            "day_reset_at": limit.day_reset_at.isoformat(),
            "retry_after_seconds": (limit.minute_reset_at - now).total_seconds() if not minute_ok else 0,
        }

        return allowed, info

    def _create_limit(self, user_id: str, tier: RateLimitTier) -> RateLimit:
        """Create new rate limit entry."""

        tier_limit = self.TIER_LIMITS[tier]
        return RateLimit(
            user_id=user_id,
            tier=tier,
            requests_per_minute=tier_limit["per_minute"],
            requests_per_day=tier_limit["per_day"],
        )


class RequestDeduplicator:
    """
    Detect + prevent duplicate requests (idempotency).

    Stores request signatures (hash of endpoint + method + payload).
    If duplicate detected within 10 minutes, return cached response.

    Use cases:
    - Form submission (double click)
    - Network retry (timeout then retry)
    - Webhook retries
    """

    def __init__(self, cache_ttl_minutes: int = 10):
        self.signatures: dict[str, RequestSignature] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)

    def get_signature(
        self,
        request_id: str,
        user_id: str,
        endpoint: str,
        method: str,
        payload: dict,
    ) -> str:
        """
        Generate request signature (SHA256 of payload).

        Signature = hash(endpoint + method + payload)
        """

        import json

        payload_json = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        signature = f"{user_id}:{endpoint}:{method}:{payload_hash}"
        return signature

    def is_duplicate(
        self,
        request_id: str,
        user_id: str,
        endpoint: str,
        method: str,
        payload: dict,
    ) -> tuple[bool, Optional[RequestSignature]]:
        """
        Check if request is duplicate.

        Returns: (is_duplicate: bool, cached_response: RequestSignature or None)
        """

        signature = self.get_signature(request_id, user_id, endpoint, method, payload)
        now = datetime.utcnow()

        # Clean up expired signatures
        self._cleanup_expired()

        # Check if signature exists and not expired
        if signature in self.signatures:
            cached = self.signatures[signature]
            if now - cached.created_at < self.cache_ttl:
                logger.info(f"Duplicate request detected: {signature}, returning cached response")
                return True, cached
            else:
                # Expired, remove it
                del self.signatures[signature]

        return False, None

    def record_request(
        self,
        request_id: str,
        user_id: str,
        endpoint: str,
        method: str,
        payload: dict,
        response: dict,
        response_time_ms: int,
    ) -> None:
        """Record request for future deduplication."""

        signature = self.get_signature(request_id, user_id, endpoint, method, payload)

        sig_obj = RequestSignature(
            request_id=request_id,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            payload_hash=hashlib.sha256(
                __import__("json").dumps(payload, sort_keys=True).encode()
            ).hexdigest(),
            created_at=datetime.utcnow(),
            response=response,
            response_time_ms=response_time_ms,
        )

        self.signatures[signature] = sig_obj

    def _cleanup_expired(self) -> None:
        """Remove expired signatures."""

        now = datetime.utcnow()
        expired = [
            sig
            for sig, sig_obj in self.signatures.items()
            if now - sig_obj.created_at > self.cache_ttl
        ]

        for sig in expired:
            del self.signatures[sig]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired request signatures")


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.

    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject requests
    - HALF_OPEN: Testing if service recovered

    Triggers:
    - 5 consecutive failures → OPEN
    - 30 second timeout in OPEN → HALF_OPEN
    - Success in HALF_OPEN → CLOSED
    """

    class State(str, Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 30,
    ):
        self.name = name
        self.state = self.State.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.last_failure_at: Optional[datetime] = None
        self.last_success_at: Optional[datetime] = None

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Raises: CircuitBreakerOpen if circuit is open
        """

        if self.state == self.State.OPEN:
            # Check if timeout expired
            if datetime.utcnow() - self.last_failure_at > timedelta(seconds=self.timeout_seconds):
                self.state = self.State.HALF_OPEN
                logger.info(f"CircuitBreaker {self.name}: OPEN → HALF_OPEN")
            else:
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""

        self.failure_count = 0
        self.last_success_at = datetime.utcnow()

        if self.state == self.State.HALF_OPEN:
            self.state = self.State.CLOSED
            logger.info(f"CircuitBreaker {self.name}: HALF_OPEN → CLOSED")

    def _on_failure(self):
        """Handle failed call."""

        self.failure_count += 1
        self.last_failure_at = datetime.utcnow()

        if self.failure_count >= self.failure_threshold and self.state != self.State.OPEN:
            self.state = self.State.OPEN
            logger.error(f"CircuitBreaker {self.name}: CLOSED → OPEN (failures: {self.failure_count})")

    def get_status(self) -> dict:
        """Get circuit breaker status."""

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
        }


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open."""

    pass


# Singleton instances
rate_limiter = RateLimiter()
deduplicator = RequestDeduplicator()

# Circuit breakers for external services
salesforce_breaker = CircuitBreaker("salesforce")
hubspot_breaker = CircuitBreaker("hubspot")
stripe_breaker = CircuitBreaker("stripe")
twilio_breaker = CircuitBreaker("twilio")
