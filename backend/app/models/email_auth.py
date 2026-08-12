"""Email verification & account approval models."""

from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from backend.app.database import Base


class EmailVerificationToken(Base):
    """Email verification tokens for signup."""

    __tablename__ = "email_verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(255), unique=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24), nullable=False)
    verified_at = Column(DateTime)

    is_verified = Column(Boolean, default=False)
    verification_attempts = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_email_verification_token", "token"),
        Index("idx_email_verification_user", "user_id"),
        Index("idx_email_verification_email", "email"),
    )


class AccountApproval(Base):
    """Account approval workflow."""

    __tablename__ = "account_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    company = Column(String(255))
    role = Column(String(255))

    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    requested_by = Column(String(255))  # Usually the user themselves

    approval_status = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected
    approved_by = Column(String(255))  # Admin who approved
    approved_at = Column(DateTime)

    approval_notes = Column(Text)
    rejection_reason = Column(Text)

    auto_approved = Column(Boolean, default=False)
    auto_approval_rule = Column(String(50))  # company_whitelist, domain_whitelist, etc

    __table_args__ = (
        Index("idx_approvals_user", "user_id"),
        Index("idx_approvals_status", "approval_status"),
        Index("idx_approvals_requested_at", "requested_at"),
    )


class ApprovalAuditLog(Base):
    """Audit log for approval actions."""

    __tablename__ = "approval_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("account_approvals.id", ondelete="CASCADE"), nullable=False)

    action = Column(String(50), nullable=False)  # requested, approved, rejected, escalated
    actor_id = Column(String(255))  # Who took action
    notes = Column(Text)

    action_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_audit_approval", "approval_id"),
    )


class EmailTemplate(Base):
    """Email templates for notifications."""

    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    template_name = Column(String(255), unique=True, nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)  # HTML template with {{placeholders}}

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_email_templates_name", "template_name"),
    )
