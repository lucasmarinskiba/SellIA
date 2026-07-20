"""Outreach Cadence Models

ContactFatigueScore, OutreachCadenceRule, OutreachLog.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class FatigueLevel(str, enum.Enum):
    RELAXED = "relaxed"      # 0-1 contactos/semana
    NORMAL = "normal"        # 2-3 contactos/semana
    TIRED = "tired"          # 4-5 contactos/semana
    EXHAUSTED = "exhausted"  # 6+ contactos/semana


class OutreachLogStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"
    FAILED = "failed"


class ContactFatigueScore(Base):
    """Real-time fatigue score per conversation to prevent over-contacting."""
    __tablename__ = "contact_fatigue_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Contact counts
    total_contacts_last_7d = Column(Integer, default=0, nullable=False)
    total_contacts_last_30d = Column(Integer, default=0, nullable=False)
    contacts_by_channel = Column(JSONB, default=dict, nullable=False)  # {"whatsapp": 3, "email": 1}

    # Timing
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    last_response_at = Column(DateTime(timezone=True), nullable=True)
    consecutive_no_replies = Column(Integer, default=0, nullable=False)

    # Fatigue level
    fatigue_level = Column(Enum(FatigueLevel), default=FatigueLevel.RELAXED, nullable=False, index=True)
    recommended_cooldown_until = Column(DateTime(timezone=True), nullable=True)

    # AI-generated recommendation
    ai_recommendation = Column(Text, nullable=True)  # "Esperar 48h antes de contactar de nuevo"
    recommended_channel = Column(String(50), nullable=True)
    recommended_message_type = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_fatigue_business_level", "business_id", "fatigue_level"),
        Index("ix_fatigue_cooldown", "recommended_cooldown_until"),
    )


class OutreachCadenceRule(Base):
    """Configurable rules for how often a business can contact leads."""
    __tablename__ = "outreach_cadence_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Frequency limits
    max_messages_per_week = Column(Integer, default=3, nullable=False)
    max_messages_per_channel_per_week = Column(Integer, default=2, nullable=False)
    min_hours_between_contacts = Column(Integer, default=24, nullable=False)

    # Cooldown rules
    cooldown_after_no_reply_days = Column(Integer, default=3, nullable=False)
    cooldown_after_no_reply_count = Column(Integer, default=3, nullable=False)  # After N no-replies, enter long cooldown
    long_cooldown_days = Column(Integer, default=14, nullable=False)

    # Channel priority (ordered list)
    channel_priority = Column(JSONB, default=list, nullable=False)  # ["whatsapp", "email", "instagram"]

    # Business hours respect (optional)
    respect_local_hours = Column(Boolean, default=True, nullable=False)
    allowed_hours_start = Column(Integer, default=9, nullable=False)   # 9 AM
    allowed_hours_end = Column(Integer, default=20, nullable=False)    # 8 PM
    avoid_weekends = Column(Boolean, default=False, nullable=False)

    # Override for hot leads
    hot_lead_override = Column(Boolean, default=True, nullable=False)  # Can contact hot leads more frequently
    hot_lead_max_per_week = Column(Integer, default=5, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class OutreachLog(Base):
    """Log of every outreach attempt."""
    __tablename__ = "outreach_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    channel = Column(String(50), nullable=False, index=True)  # whatsapp, email, instagram, etc.
    message_type = Column(String(50), nullable=False)  # follow_up, proposal, nurture, recovery, etc.
    cadence_step = Column(Integer, default=1, nullable=False)  # Step in the sequence

    # Message content reference
    message_content = Column(Text, nullable=True)  # What was sent (truncated)
    workflow_execution_id = Column(UUID(as_uuid=True), nullable=True)
    sequence_step_id = Column(UUID(as_uuid=True), nullable=True)

    # Status tracking
    status = Column(Enum(OutreachLogStatus), default=OutreachLogStatus.SENT, nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Response quality
    response_type = Column(String(50), nullable=True)  # positive, negative, question, neutral
    response_content = Column(Text, nullable=True)

    # AI metadata
    ai_generated = Column(Boolean, default=False, nullable=False)
    ai_prompt_summary = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_outreach_logs_conv_sent", "conversation_id", "sent_at"),
        Index("ix_outreach_logs_business_channel", "business_id", "channel"),
    )
