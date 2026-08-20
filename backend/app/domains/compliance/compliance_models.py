"""GDPR/CCPA compliance models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    consent_type = Column(String(50), nullable=False)  # marketing, analytics, tracking, profiling
    consented = Column(Boolean, default=False)
    
    consent_version = Column(String(50), default="v1")
    consent_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    consent_metadata = Column(JSONB, nullable=True)  # ip, user_agent, etc
    
    revoked_at = Column(DateTime(timezone.utc), nullable=True)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class DataDeletionRequest(Base):
    __tablename__ = "data_deletion_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    request_status = Column(String(50), default="pending")  # pending, approved, processing, completed, rejected
    deletion_type = Column(String(50), nullable=False)  # full, anonymize
    
    requested_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone.utc), nullable=True)
    completed_at = Column(DateTime(timezone.utc), nullable=True)
    
    deletion_metadata = Column(JSONB, nullable=True)  # what was deleted


class DataExportRequest(Base):
    __tablename__ = "data_export_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    request_status = Column(String(50), default="pending")  # pending, processing, ready, expired
    export_format = Column(String(20), default="json")  # json, csv
    
    requested_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    generated_at = Column(DateTime(timezone.utc), nullable=True)
    expires_at = Column(DateTime(timezone.utc), nullable=True)
    
    export_url = Column(String(500), nullable=True)
    file_size_bytes = Column(String(50), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(100), nullable=False)  # user_login, data_accessed, data_exported, data_deleted
    resource_type = Column(String(50), nullable=True)  # customer, order, payment
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    actor_type = Column(String(50), default="system")  # user, admin, system
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    
    details = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class PrivacyPolicy(Base):
    __tablename__ = "privacy_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    policy_version = Column(String(50), default="v1")
    policy_text = Column(Text, nullable=False)
    
    effective_date = Column(DateTime(timezone.utc), nullable=False)
    
    contains_gdpr = Column(Boolean, default=True)
    contains_ccpa = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
