"""Post-visit messages waiting to be sent, and the addresses that unsubscribed from a business."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class OfflineSequenceJob(Base):
    """One row per visit and template, so a repeated trigger cannot send twice."""

    __tablename__ = "offline_sequence_jobs"
    __table_args__ = (
        UniqueConstraint("conversion_id", "template_name", name="uq_offline_sequence_job_once"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversion_id = Column(
        UUID(as_uuid=True), ForeignKey("offline_conversions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_name = Column(String(64), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    # Frozen when the job is queued, so a later edit to the template does not change a message already promised.
    # The sender name and the unsubscribe footer are read at send time, so they follow the business as it is then.
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, sent, failed, skipped
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(String(500), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class OfflineMessageOptOut(Base):
    """An address that unsubscribed from one business's post-visit messages. Stored as SHA-256 of the address."""

    __tablename__ = "offline_message_opt_outs"
    __table_args__ = (
        UniqueConstraint("business_id", "email_hash", name="uq_offline_message_opt_out"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    email_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
