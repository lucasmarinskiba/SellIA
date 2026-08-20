"""API rate limiting & caching service."""

import logging
import hashlib
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, Dict, Tuple
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.api_management.rate_limit_models import (
    ApiKey, RateLimitLog, CachePolicy, ApiMetrics, RateLimitTier, RateLimitWindow
)

logger = logging.getLogger(__name__)


class RateLimitService:
    """Manage API rate limiting and caching."""

    # Rate limit defaults (requests per hour)
    RATE_LIMITS = {
        RateLimitTier.FREE: 100,
        RateLimitTier.STARTER: 1000,
        RateLimitTier.PRO: 10000,
        RateLimitTier.ENTERPRISE: 999999
    }

    @staticmethod
    def create_api_key(
        business_id: UUID,
        key_name: str,
        tier: str = RateLimitTier.STARTER,
        custom_limit: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        db: Session = None
    ) -> dict:
        """Create new API key."""
        if not db:
            raise ValueError("Database session required")

        # Generate key
        import secrets
        raw_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        masked_key = raw_key[-8:]

        api_key = ApiKey(
            business_id=business_id,
            key_name=key_name,
            key_hash=key_hash,
            masked_key=masked_key,
            rate_limit_tier=tier,
            custom_rph_limit=custom_limit,
            expires_at=expires_at
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        logger.info(f"API key created: {key_name} for {business_id}")

        return {
            "api_key_id": str(api_key.id),
            "api_key": raw_key,  # Only return once
            "masked_key": masked_key,
            "tier": tier,
            "rate_limit": custom_limit or RateLimitService.RATE_LIMITS.get(tier)
        }

    @staticmethod
    def check_rate_limit(
        api_key_hash: str,
        endpoint: str,
        method: str,
        business_id: UUID,
        ip_address: str = None,
        user_agent: str = None,
        db: Session = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if request is rate limited."""
        if not db:
            raise ValueError("Database session required")

        # Find API key
        api_key = db.query(ApiKey).filter(
            ApiKey.key_hash == api_key_hash,
            ApiKey.is_active == True
        ).first()

        if not api_key:
            return False, "Invalid API key"

        # Check expiration
        if api_key.expires_at and datetime.now(timezone.utc) > api_key.expires_at:
            return False, "API key expired"

        # Get rate limit
        limit = api_key.custom_rph_limit or RateLimitService.RATE_LIMITS.get(
            api_key.rate_limit_tier, 1000
        )

        # Count requests in past hour
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        requests_in_hour = db.query(RateLimitLog).filter(
            RateLimitLog.api_key_id == api_key.id,
            RateLimitLog.created_at >= cutoff
        ).count()

        is_rate_limited = requests_in_hour >= limit

        # Log request
        log_entry = RateLimitLog(
            api_key_id=api_key.id,
            business_id=business_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            requests_in_window=requests_in_hour + 1,
            limit_threshold=limit,
            window_type=RateLimitWindow.PER_HOUR,
            was_rate_limited=is_rate_limited
        )

        db.add(log_entry)

        # Update last used
        api_key.last_used_at = datetime.now(timezone.utc)
        db.commit()

        if is_rate_limited:
            logger.warning(f"Rate limit exceeded: {api_key.key_name} - {requests_in_hour}/{limit}")
            return False, f"Rate limit exceeded: {requests_in_hour}/{limit} requests per hour"

        return True, None

    @staticmethod
    def get_rate_limit_status(
        api_key_id: UUID,
        db: Session = None
    ) -> dict:
        """Get current rate limit status for key."""
        if not db:
            raise ValueError("Database session required")

        api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
        if not api_key:
            raise ValueError(f"API key {api_key_id} not found")

        limit = api_key.custom_rph_limit or RateLimitService.RATE_LIMITS.get(
            api_key.rate_limit_tier, 1000
        )

        # Requests in past hour
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        requests_in_hour = db.query(RateLimitLog).filter(
            RateLimitLog.api_key_id == api_key_id,
            RateLimitLog.created_at >= cutoff
        ).count()

        remaining = max(0, limit - requests_in_hour)

        return {
            "api_key_name": api_key.key_name,
            "tier": api_key.rate_limit_tier,
            "limit_per_hour": limit,
            "requests_used": requests_in_hour,
            "requests_remaining": remaining,
            "reset_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }

    @staticmethod
    def set_cache_policy(
        business_id: UUID,
        endpoint_path: str,
        ttl_seconds: int = 300,
        cache_by: str = None,
        db: Session = None
    ) -> dict:
        """Set cache policy for endpoint."""
        if not db:
            raise ValueError("Database session required")

        policy = db.query(CachePolicy).filter(
            CachePolicy.business_id == business_id,
            CachePolicy.endpoint_path == endpoint_path
        ).first()

        if policy:
            policy.ttl_seconds = ttl_seconds
            policy.cache_by = cache_by
        else:
            policy = CachePolicy(
                business_id=business_id,
                endpoint_path=endpoint_path,
                ttl_seconds=ttl_seconds,
                cache_by=cache_by
            )
            db.add(policy)

        db.commit()

        logger.info(f"Cache policy set: {endpoint_path} - {ttl_seconds}s TTL")

        return {
            "endpoint": endpoint_path,
            "cache_enabled": policy.cache_enabled,
            "ttl_seconds": ttl_seconds,
            "cache_by": cache_by
        }

    @staticmethod
    def log_request_metrics(
        business_id: UUID,
        endpoint: str,
        response_time_ms: int,
        response_status: int,
        was_cached: bool = False,
        db: Session = None
    ) -> None:
        """Log API request metrics."""
        if not db:
            return

        # Update cache policy stats
        policies = db.query(CachePolicy).filter(
            CachePolicy.business_id == business_id,
            CachePolicy.endpoint_path == endpoint
        ).all()

        for policy in policies:
            if was_cached:
                policy.cache_hits += 1
            else:
                policy.cache_misses += 1
            db.commit()

    @staticmethod
    def get_api_metrics(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Get API performance metrics."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        date_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
        date_end = date_start + timedelta(days=1)

        # Request logs for day
        logs = db.query(RateLimitLog).filter(
            RateLimitLog.business_id == business_id,
            RateLimitLog.created_at >= date_start,
            RateLimitLog.created_at < date_end
        ).all()

        if not logs:
            return {"metrics_available": False}

        total_requests = len(logs)
        rate_limited = len([l for l in logs if l.was_rate_limited])
        error_responses = len([l for l in logs if l.response_status >= 400])

        # Response times
        response_times = [l.response_time_ms for l in logs if l.response_time_ms]
        avg_response_time = int(sum(response_times) / len(response_times)) if response_times else 0

        # Percentiles
        response_times_sorted = sorted(response_times)
        p95_idx = int(len(response_times_sorted) * 0.95)
        p99_idx = int(len(response_times_sorted) * 0.99)
        p95 = response_times_sorted[p95_idx] if p95_idx < len(response_times_sorted) else 0
        p99 = response_times_sorted[p99_idx] if p99_idx < len(response_times_sorted) else 0

        # Endpoints
        endpoints = {}
        for log in logs:
            endpoints[log.endpoint] = endpoints.get(log.endpoint, 0) + 1

        most_used = max(endpoints.items(), key=lambda x: x[1])[0] if endpoints else None

        # Cache stats
        cache_policies = db.query(CachePolicy).filter(
            CachePolicy.business_id == business_id
        ).all()

        total_hits = sum(p.cache_hits for p in cache_policies)
        total_misses = sum(p.cache_misses for p in cache_policies)
        hit_rate = (total_hits / max(total_hits + total_misses, 1)) * 100 if (total_hits + total_misses) > 0 else 0

        metrics = ApiMetrics(
            business_id=business_id,
            date=date,
            total_requests=total_requests,
            total_errors=error_responses,
            error_rate=int((error_responses / max(total_requests, 1)) * 100),
            rate_limited_requests=rate_limited,
            cache_hits=total_hits,
            cache_misses=total_misses,
            cache_hit_rate=int(hit_rate),
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            unique_endpoints_called=len(endpoints),
            most_used_endpoint=most_used
        )

        db.add(metrics)
        db.commit()

        logger.info(f"API metrics recorded: {business_id} - {total_requests} requests")

        return {
            "metrics_recorded": True,
            "date": date,
            "requests": {
                "total": total_requests,
                "errors": error_responses,
                "rate_limited": rate_limited
            },
            "performance": {
                "avg_ms": avg_response_time,
                "p95_ms": p95,
                "p99_ms": p99
            },
            "cache": {
                "hits": total_hits,
                "misses": total_misses,
                "hit_rate_pct": int(hit_rate)
            }
        }
