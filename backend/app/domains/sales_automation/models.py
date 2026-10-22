"""Phase 36: Sales Automation."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class EmailSequence(Base):
    __tablename__ = "email_sequences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_name = Column(String(255), nullable=False)
    emails = Column(
        JSONB, nullable=False
    )  # [{"day": 0, "subject": "...", "body": "..."}]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(UTC), default=lambda: datetime.now(UTC))


class CallFollowUp(Base):
    __tablename__ = "call_followups"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    lead_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    call_recording_url = Column(String(500), nullable=True)
    transcript = Column(String(5000), nullable=True)
    followup_action = Column(String(255), nullable=True)
    created_at = Column(DateTime(UTC), default=lambda: datetime.now(UTC))


class SMSSequence(Base):
    __tablename__ = "sms_sequences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    messages = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(UTC), default=lambda: datetime.now(UTC))
