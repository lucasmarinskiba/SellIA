"""Auto-Responder Pilot Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class AutoResponderRule(Base):
    """Rule that triggers an automatic response."""
    __tablename__ = "auto_responder_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_name = Column(String(255), nullable=False)
    trigger_type = Column(String(30), nullable=False)  # time_of_day | day_of_week | keyword | inactivity
    trigger_config = Column(JSONB, nullable=False, default=dict)
    # Examples:
    # time_of_day: {"start": "18:00", "end": "08:00", "timezone": "America/Argentina/Buenos_Aires"}
    # day_of_week: {"days": ["saturday", "sunday"]}
    # keyword: {"keywords": ["urgente", "ayuda", "soporte"]}
    # inactivity: {"hours": 2}
    response_template = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AutoResponseLog(Base):
    """Log of auto-responses sent by the system."""
    __tablename__ = "auto_response_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("auto_responder_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    trigger_fired = Column(String(100), nullable=False)
    response_sent = Column(Text, nullable=False)
    customer_replied = Column(Boolean, nullable=False, default=False)
    outcome = Column(String(50), nullable=True)  # resolved | escalated | no_reply | converted
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_auto_response_logs_created", "created_at"),
    )
