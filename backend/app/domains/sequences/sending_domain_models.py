"""A business's own sending domain (Resend). One per business. Only a verified domain sends post-visit mail."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class BusinessSendingDomain(Base):
    __tablename__ = "business_sending_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    domain = Column(String(255), nullable=False)
    local_part = Column(String(64), nullable=False, default="ventas")
    resend_domain_id = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, verified, failed
    # DNS records the business adds at its own DNS provider (SPF, DKIM, DMARC), as Resend returns them.
    records = Column(JSON, nullable=False, default=list)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
