"""Database models for security features.

These models are defined here for Alembic migration purposes.
Import in main ORM registry during app startup.
"""

from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Text, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class AuditLog(Base):
    """Audit log table for tracking all security-relevant events."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_seller_id", "seller_id"),
        Index("idx_event_type", "event_type"),
        Index("idx_created_at", "created_at"),
        Index("idx_seller_event_date", "seller_id", "event_type", "created_at"),
    )

    id = Column(String(50), primary_key=True)
    seller_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    status_code = Column(Integer, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(50), nullable=True, index=True)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    error_details = Column(JSON, nullable=True)
    data_accessed = Column(JSON, nullable=True)
    data_modified = Column(JSON, nullable=True)
    rows_affected = Column(Integer, nullable=True)
    is_risk = Column(Boolean, default=False, index=True)
    risk_score = Column(Integer, nullable=True)
    risk_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=True)


class TOTP2FA(Base):
    """Two-factor authentication via TOTP."""

    __tablename__ = "totp_2fa"
    __table_args__ = (
        Index("idx_seller_id", "seller_id"),
        Index("idx_user_id", "user_id"),
    )

    id = Column(String(50), primary_key=True)
    seller_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    secret = Column(String(32), nullable=False)
    provisioning_uri = Column(String(255), nullable=False)
    backup_codes = Column(JSON, nullable=True)
    backup_codes_used = Column(JSON, default=[])
    is_enabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class APIKey(Base):
    """API key for programmatic access."""

    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_seller_id", "seller_id"),
        Index("idx_user_id", "user_id"),
        Index("idx_key_hash", "key_hash"),
        Index("idx_is_active", "is_active"),
    )

    id = Column(String(50), primary_key=True)
    seller_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)
    key_encrypted = Column(String(500), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    scopes = Column(JSON, default=[])
    is_active = Column(Boolean, default=True, index=True)
    is_rotated = Column(Boolean, default=False)
    rate_limit_per_min = Column(Integer, default=60)
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    rotation_scheduled_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)
    created_by = Column(String(255), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(255), nullable=True)
    revoke_reason = Column(String(255), nullable=True)
