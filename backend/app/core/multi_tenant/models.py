"""Multi-tenant models: Tenant, API Keys, Billing, Audit records."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Float, ForeignKey,
    Text, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.encrypted_types import EncryptedString, EncryptedJSONB


class Tenant(Base):
    """
    Multi-tenant organization container.
    Each tenant has isolated schema, data, API keys, and billing.
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)  # Organization name
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-safe identifier
    description = Column(Text, nullable=True)

    # Ownership
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_tenants")

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_paused = Column(Boolean, default=False, nullable=False)  # Pause for billing/compliance
    suspended_reason = Column(String(500), nullable=True)  # Why suspended
    suspended_at = Column(DateTime(timezone=True), nullable=True)

    # Database isolation
    schema_name = Column(String(63), unique=True, nullable=False)  # PostgreSQL schema (max 63 chars)
    database_url = Column(EncryptedString, nullable=True)  # Custom DB if multi-db setup

    # Tier and limits
    tier = Column(String(50), default="starter", nullable=False)  # starter, pro, enterprise
    max_users = Column(Integer, default=5, nullable=False)
    max_api_keys = Column(Integer, default=3, nullable=False)
    max_monthly_api_calls = Column(Integer, default=10000, nullable=False)

    # Configuration
    settings = Column(EncryptedJSONB, default=dict, nullable=False)  # Tenant-specific config
    features = Column(JSONB, default=dict, nullable=False)  # Feature flags for tenant

    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    api_keys = relationship("TenantAPIKey", back_populates="tenant", cascade="all, delete-orphan")
    members = relationship("TenantMember", back_populates="tenant", cascade="all, delete-orphan")
    billing = relationship("TenantBilling", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tenant_owner_active", "owner_id", "is_active"),
        Index("ix_tenant_slug_active", "slug", "is_active"),
    )


class TenantMember(Base):
    """Tenant membership: which users belong to which tenants."""
    __tablename__ = "tenant_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Role-based access (RBAC)
    role = Column(String(50), default="member", nullable=False)  # owner, admin, member, viewer
    permissions = Column(JSONB, default=dict, nullable=False)  # Custom permissions

    # Audit
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="members", foreign_keys=[tenant_id])
    user = relationship("User", foreign_keys=[user_id], backref="tenant_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
        Index("ix_tenant_member_user", "user_id", "is_active"),
    )


class TenantAPIKey(Base):
    """
    API key management: one key per service integration.
    Rotatable, revocable, rate-limited per key.
    """
    __tablename__ = "tenant_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Key identity
    key_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hash (never store plaintext)
    key_prefix = Column(String(16), nullable=False)  # Visible prefix for debugging
    name = Column(String(255), nullable=False)  # User-friendly name
    description = Column(Text, nullable=True)

    # Scope & permissions
    scopes = Column(JSONB, default=list, nullable=False)  # ["read", "write", "admin"]
    ip_whitelist = Column(JSONB, default=list, nullable=False)  # Optional IP restrictions
    rate_limit_per_minute = Column(Integer, default=100, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(String(500), nullable=True)

    # Rotation
    last_rotated_at = Column(DateTime(timezone=True), nullable=True)
    rotation_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    must_rotate_by = Column(DateTime(timezone=True), nullable=True)  # Enforce rotation after 90 days

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Statistics
    total_requests = Column(Integer, default=0, nullable=False)
    total_errors = Column(Integer, default=0, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys", foreign_keys=[tenant_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("ix_api_key_tenant_active", "tenant_id", "is_active", "is_revoked"),
        Index("ix_api_key_last_used", "last_used_at"),
    )


class TenantBilling(Base):
    """
    Billing & usage tracking per tenant.
    Tracks API calls, compute, storage, and generates invoices.
    """
    __tablename__ = "tenant_billing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Billing period
    billing_period_start = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    billing_period_end = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(days=30), nullable=False)

    # Usage metrics
    api_calls_used = Column(Integer, default=0, nullable=False)
    storage_gb_used = Column(Float, default=0.0, nullable=False)
    compute_hours_used = Column(Float, default=0.0, nullable=False)

    # Costs
    base_tier_cost = Column(Float, default=0.0, nullable=False)
    overage_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)

    # Payment status
    status = Column(String(50), default="pending", nullable=False)  # pending, paid, failed, refunded
    invoice_number = Column(String(50), unique=True, nullable=True, index=True)
    last_payment_attempt = Column(DateTime(timezone=True), nullable=True)
    payment_failed_reason = Column(String(500), nullable=True)

    # Stripe/payment gateway integration
    stripe_invoice_id = Column(String(255), nullable=True)
    payment_method_id = Column(EncryptedString, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="billing", foreign_keys=[tenant_id])

    __table_args__ = (
        Index("ix_billing_status_period", "status", "billing_period_start"),
    )


class AuditLog(Base):
    """
    Immutable audit trail: all tenant actions logged.
    Required for compliance (SOC2, GDPR, HIPAA).
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Action identity
    action = Column(String(100), nullable=False)  # "user.login", "api_key.created", "data.exported"
    resource_type = Column(String(50), nullable=False)  # "user", "api_key", "billing", "data"
    resource_id = Column(String(255), nullable=True)  # UUID or identifier of affected resource
    change_type = Column(String(20), nullable=False)  # "create", "update", "delete", "read"

    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)  # Denormalized for deleted users
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(500), nullable=True)

    # Context
    status = Column(String(20), default="success", nullable=False)  # success, failed, warning
    reason = Column(String(500), nullable=True)  # Why failed/warning
    details = Column(EncryptedJSONB, default=dict, nullable=False)  # Full payload (encrypted)

    # Data change tracking
    old_values = Column(EncryptedJSONB, nullable=True)  # Before snapshot
    new_values = Column(EncryptedJSONB, nullable=True)  # After snapshot

    # Compliance
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs", foreign_keys=[tenant_id])
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_audit_tenant_action_time", "tenant_id", "action", "created_at"),
        Index("ix_audit_tenant_user_time", "tenant_id", "user_id", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id", "created_at"),
    )
