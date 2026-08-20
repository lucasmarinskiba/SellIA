"""Multi-tenant isolation models — data boundaries, audit, compliance."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditActionType(str, Enum):
    """Audit log action types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    SETTINGS_CHANGED = "settings_changed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"


class DataClassification(str, Enum):
    """Data sensitivity classification."""
    PUBLIC = "public"  # Can be shared
    INTERNAL = "internal"  # Business use only
    CONFIDENTIAL = "confidential"  # Restricted access
    RESTRICTED = "restricted"  # Highest sensitivity


class TenantIsolationPolicy(Base):
    """Configure isolation level per business."""
    __tablename__ = "tenant_isolation_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Isolation
    isolation_level = Column(String(20), default="row_level")  # row_level, schema_level, database_level
    enforce_row_level_security = Column(Boolean, default=True)  # Filter rows by business_id
    cross_tenant_data_access_blocked = Column(Boolean, default=True)

    # Audit
    audit_enabled = Column(Boolean, default=True)
    audit_retention_days = Column(Integer, default=365)  # How long to keep logs
    log_all_reads = Column(Boolean, default=False)  # Privacy-intensive
    log_data_changes = Column(Boolean, default=True)

    # Compliance
    gdpr_compliance_mode = Column(Boolean, default=False)  # Extra data handling controls
    ccpa_compliance_mode = Column(Boolean, default=False)
    pii_encryption_enabled = Column(Boolean, default=False)  # Encrypt sensitive fields
    right_to_be_forgotten_supported = Column(Boolean, default=True)

    # Data residency
    allowed_regions = Column(JSONB, default=["us", "eu"])  # Where data can be stored
    data_residency_enforced = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])


class AuditLog(Base):
    """Track all user actions per tenant."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # User
    user_id = Column(String(255), nullable=True)  # User email or ID
    user_ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser info

    # Action
    action = Column(String(50), nullable=False)  # create, read, update, delete, export, login
    resource_type = Column(String(50), nullable=False)  # customers, orders, segments, etc
    resource_id = Column(String(255), nullable=True)  # UUID of affected resource

    # Change tracking
    change_details = Column(JSONB, nullable=True)  # {"field": "status", "old": "active", "new": "inactive"}
    data_classification = Column(String(20), default=DataClassification.INTERNAL)

    # Result
    action_status = Column(String(20), default="success")  # success, error, denied
    error_message = Column(Text, nullable=True)

    # Metadata
    api_key_id = Column(String(255), nullable=True)  # Which API key was used
    endpoint = Column(String(255), nullable=True)  # Which endpoint was called
    request_id = Column(String(100), nullable=True)  # Correlation ID

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_business_date", "business_id", "created_at"),
        Index("idx_resource", "business_id", "resource_type", "resource_id"),
        Index("idx_user", "business_id", "user_id"),
    )


class TenantUser(Base):
    """User access control per business."""
    __tablename__ = "tenant_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Identity
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)

    # Role-based access
    role = Column(String(50), default="member")  # owner, admin, analyst, member
    permissions = Column(JSONB, default=list)  # ["read_customers", "export_data", "manage_users"]

    # Resource access
    can_access_all_locations = Column(Boolean, default=False)
    allowed_location_ids = Column(JSONB, default=list)  # If not all, specific locations

    # Status
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone.utc), nullable=True)
    invited_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    joined_at = Column(DateTime(timezone.utc), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_email", "business_id", "email", unique=True),
        Index("idx_active", "business_id", "is_active"),
    )


class DataAccessLog(Base):
    """Track data exports/downloads per tenant."""
    __tablename__ = "data_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Access
    access_type = Column(String(50), nullable=False)  # export, download, api_access, report_view
    data_type = Column(String(50), nullable=False)  # customers, orders, segments, etc
    rows_accessed = Column(Integer, nullable=True)

    # User
    user_email = Column(String(255), nullable=False)
    user_ip = Column(String(45), nullable=True)

    # Details
    reason = Column(String(255), nullable=True)  # Why was data accessed?
    access_approval_id = Column(String(255), nullable=True)  # Approval request ID if needed
    was_approved = Column(Boolean, default=False)

    # Data security
    pii_fields_included = Column(Boolean, default=False)  # Contains personally identifiable info
    encrypted_in_transit = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_business_user_date", "business_id", "user_email", "created_at"),
        Index("idx_access_type", "business_id", "access_type"),
    )


class ComplianceReport(Base):
    """Generate compliance reports."""
    __tablename__ = "compliance_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Report
    report_type = Column(String(50), nullable=False)  # audit_trail, data_access, gdpr_dsar, ccpa_dsar
    report_period_start = Column(String(10), nullable=False)  # YYYY-MM-DD
    report_period_end = Column(String(10), nullable=False)

    # Content
    total_actions = Column(Integer, default=0)  # Total audit actions in period
    data_accesses = Column(Integer, default=0)  # Export/download events
    failed_access_attempts = Column(Integer, default=0)
    users_active = Column(Integer, default=0)

    # Findings
    policy_violations = Column(Integer, default=0)  # Unauthorized access attempts
    pii_exposure_incidents = Column(Integer, default=0)
    recommendations = Column(JSONB, default=list)

    # Report file
    report_file_url = Column(String(500), nullable=True)  # S3 URL to full report
    generated_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_type_date", "business_id", "report_type", "report_period_start"),
    )
