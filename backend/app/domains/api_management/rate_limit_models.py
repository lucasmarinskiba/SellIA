"""API rate limiting & caching models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RateLimitTier(str, Enum):
    """API rate limit tier."""
    FREE = "free"  # 100 req/hour
    STARTER = "starter"  # 1000 req/hour
    PRO = "pro"  # 10000 req/hour
    ENTERPRISE = "enterprise"  # Unlimited or custom


class RateLimitWindow(str, Enum):
    """Rate limit time window."""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"


class ApiKey(Base):
    """API key for business."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Key
    key_name = Column(String(255), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA256 hash
    masked_key = Column(String(50), nullable=False)  # Last 8 chars visible

    # Tier
    rate_limit_tier = Column(String(20), default=RateLimitTier.STARTER)
    custom_rpm_limit = Column(Integer, nullable=True)  # Override default
    custom_rph_limit = Column(Integer, nullable=True)  # Override default

    # Permissions
    allowed_endpoints = Column(String(500), nullable=True)  # Comma-separated paths or "*"
    allowed_methods = Column(String(50), default="GET,POST,PUT,DELETE")  # Comma-separated

    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime(timezone.utc), nullable=True)  # Optional expiration

    notes = Column(String(255), nullable=True)

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_active", "business_id", "is_active"),
    )


class RateLimitLog(Base):
    """Track rate limit violations."""
    __tablename__ = "rate_limit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Request info
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)

    # Rate limit
    requests_in_window = Column(Integer, default=1)
    limit_threshold = Column(Integer, nullable=False)
    window_type = Column(String(20), nullable=False)  # per_minute, per_hour, per_day
    was_rate_limited = Column(Boolean, default=False)

    # Response
    response_status = Column(Integer, default=200)
    response_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    api_key = relationship("ApiKey", foreign_keys=[api_key_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "created_at"),
        Index("idx_rate_limited", "business_id", "was_rate_limited"),
    )


class CachePolicy(Base):
    """Cache policy for endpoints."""
    __tablename__ = "cache_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Endpoint
    endpoint_path = Column(String(255), nullable=False)  # e.g., "/api/v1/customers/{id}"
    method = Column(String(10), default="GET")

    # Cache config
    cache_enabled = Column(Boolean, default=True)
    ttl_seconds = Column(Integer, default=300)  # 5 min default
    cache_by = Column(String(100), nullable=True)  # e.g., "user_id", "business_id"

    # Invalidation
    invalidate_on_endpoints = Column(String(500), nullable=True)  # Comma-separated endpoints
    invalidate_on_methods = Column(String(50), default="POST,PUT,DELETE")

    # Stats
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_endpoint", "business_id", "endpoint_path", "method"),
    )


class ApiMetrics(Base):
    """Aggregate API performance metrics."""
    __tablename__ = "api_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Request volume
    total_requests = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    error_rate = Column(Integer, default=0)  # % of requests

    # Rate limiting
    rate_limited_requests = Column(Integer, default=0)
    rate_limit_violations = Column(Integer, default=0)
    most_limited_endpoint = Column(String(255), nullable=True)

    # Caching
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    cache_hit_rate = Column(Integer, default=0)  # %

    # Performance
    avg_response_time_ms = Column(Integer, default=0)
    p95_response_time_ms = Column(Integer, default=0)
    p99_response_time_ms = Column(Integer, default=0)

    # Endpoints
    unique_endpoints_called = Column(Integer, default=0)
    most_used_endpoint = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )
