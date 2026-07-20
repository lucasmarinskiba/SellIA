"""Lead Qualifier Auto-Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Numeric, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class LeadQualification(Base):
    """BANT qualification result for a lead."""
    __tablename__ = "lead_qualifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    bant_score = Column(JSONB, nullable=False, default=dict)  # {"budget": 75, "authority": 60, "need": 90, "timeline": 50}
    qualification_score = Column(Numeric(5, 2), nullable=False, default=0.0)  # 0-100
    status = Column(String(20), nullable=False, default="nurture")  # qualified | disqualified | nurture
    routing_destination = Column(String(100), nullable=True)  # e.g. "sales_team", "drip_sequence"
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_lead_qualifications_score", "qualification_score"),
        Index("ix_lead_qualifications_status", "status"),
    )
