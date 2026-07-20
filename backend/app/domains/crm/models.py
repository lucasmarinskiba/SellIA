"""CRM Models — Pipeline, Deals, Lead Scoring

Sales pipeline management with lead scoring and deal tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class LeadStage(str, enum.Enum):
    NEW_LEAD = "new_lead"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NURTURE = "nurture"


class Pipeline(Base):
    """A sales pipeline for a business."""
    __tablename__ = "pipelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False, default="Pipeline Principal")
    description = Column(Text, nullable=True)
    stages = Column(JSONB, default=list, nullable=False)  # [{"id": "...", "name": "Contactado", "order": 1, "color": "#3B82F6"}]
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    deals = relationship("Deal", back_populates="pipeline", cascade="all, delete-orphan")


class Deal(Base):
    """A sales opportunity/deal."""
    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(100), nullable=True)

    # Deal value
    value = Column(Numeric(14, 2), nullable=True)
    currency = Column(String(3), default="ARS", nullable=False)

    # Pipeline stage
    stage = Column(Enum(LeadStage), default=LeadStage.NEW_LEAD, nullable=False, index=True)
    stage_order = Column(Integer, default=0, nullable=False)  # For custom ordering within stage

    # Deal health
    probability = Column(Integer, default=10, nullable=False)  # 0-100
    priority = Column(Integer, default=0, nullable=False)  # 0-5 (0=low, 5=urgent)

    # Expected close
    expected_close_date = Column(DateTime(timezone=True), nullable=True)
    actual_close_date = Column(DateTime(timezone=True), nullable=True)
    close_reason = Column(Text, nullable=True)  # Why won/lost

    # Source attribution
    source_channel = Column(String(50), nullable=True)
    source_campaign = Column(String(200), nullable=True)
    source_agent_id = Column(UUID(as_uuid=True), nullable=True)

    # Custom fields
    extra_data = Column(JSONB, default=dict, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    pipeline = relationship("Pipeline", back_populates="deals")


class LeadScore(Base):
    """Dynamic lead scoring for a conversation/lead."""
    __tablename__ = "lead_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    total_score = Column(Integer, default=0, nullable=False, index=True)  # 0-100
    # Component scores
    engagement_score = Column(Integer, default=0, nullable=False)  # +messages, +responses
    intent_score = Column(Integer, default=0, nullable=False)  # +price inquiry, +booking request
    demographic_score = Column(Integer, default=0, nullable=False)  # +has email, +has phone
    behavioral_score = Column(Integer, default=0, nullable=False)  # +revisited, +clicked link
    recency_score = Column(Integer, default=0, nullable=False)  # +recent activity

    # Score history
    score_history = Column(JSONB, default=list, nullable=False)  # [{"date": "...", "score": 45, "reason": "..."}]

    # Classification
    classification = Column(String(20), default="cold", nullable=False)  # cold, warm, hot

    # AI-generated expert commentary when classification changes
    commentary = Column(Text, nullable=True)

    last_calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LeadActivity(Base):
    """Activity log for leads (used by scoring engine)."""
    __tablename__ = "lead_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    activity_type = Column(String(50), nullable=False, index=True)  # message_received, message_sent, link_clicked, price_asked, appointment_set, etc.
    points = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)
    meta_data = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
