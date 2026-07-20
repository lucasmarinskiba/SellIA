"""Intelligence Models

MessageAnalysis — per-message AI analysis.
ConversationIntelligence — aggregated intelligence per conversation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Numeric, Integer, Boolean, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class MessageAnalysis(Base):
    """AI analysis of a single inbound message."""
    __tablename__ = "message_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Sentiment
    sentiment_score = Column(Numeric(4, 3), default=0, nullable=False)  # -1.0 to 1.0
    sentiment_label = Column(String(20), default="neutral", nullable=False)  # positive, negative, neutral, mixed

    # Intent
    intent_type = Column(String(50), default="neutral", nullable=False, index=True)
    intent_confidence = Column(Numeric(4, 3), default=0, nullable=False)  # 0.0 to 1.0

    # Detected signals
    objections_detected = Column(JSONB, default=list, nullable=False)
    pain_points_detected = Column(JSONB, default=list, nullable=False)
    buying_signals_detected = Column(JSONB, default=list, nullable=False)

    # Urgency & language
    urgency_level = Column(String(20), default="low", nullable=False)  # low, medium, high, critical
    language_detected = Column(String(10), default="es", nullable=False)

    # Entities and recommendations
    key_entities = Column(JSONB, default=dict, nullable=False)  # {products: [], prices: [], dates: []}
    recommended_action = Column(String(50), nullable=True)
    recommended_personality = Column(String(50), nullable=True)

    # Raw AI response for debugging
    raw_analysis = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_message_analyses_business_intent", "business_id", "intent_type"),
        Index("ix_message_analyses_conversation", "conversation_id", "created_at"),
    )


class ConversationIntelligence(Base):
    """Aggregated AI intelligence for a conversation."""
    __tablename__ = "conversation_intelligences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Aggregated sentiment
    overall_sentiment_trend = Column(String(20), default="stable", nullable=False)  # improving, stable, declining
    average_sentiment_score = Column(Numeric(4, 3), default=0, nullable=False)

    # Dominant intent and buying readiness
    dominant_intent = Column(String(50), default="neutral", nullable=False)
    buying_readiness_score = Column(Integer, default=0, nullable=False)  # 0-100

    # Objection and churn tracking
    objection_history = Column(JSONB, default=list, nullable=False)  # [{objection: "too_expensive", resolved: true, resolved_by: "discount_offer"}]
    churn_risk_signals_count = Column(Integer, default=0, nullable=False)

    # Next best action
    next_best_action = Column(String(50), nullable=True)
    next_best_action_reason = Column(Text, nullable=True)

    # Engagement quality
    total_messages_analyzed = Column(Integer, default=0, nullable=False)
    positive_messages_count = Column(Integer, default=0, nullable=False)
    negative_messages_count = Column(Integer, default=0, nullable=False)
    buying_signals_count = Column(Integer, default=0, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_conv_intel_business_readiness", "business_id", "buying_readiness_score"),
        Index("ix_conv_intel_business_intent", "business_id", "dominant_intent"),
    )
