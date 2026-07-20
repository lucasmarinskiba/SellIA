"""Deal Scoring Models

Predictive deal scoring and alert system for sales conversations.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class DealScore(Base):
    """Predictive deal score for a conversation."""

    __tablename__ = "deal_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    score = Column(Integer, nullable=False, default=0)  # 0-100
    category = Column(String(20), nullable=False, default="cold")  # cold, warm, hot, ready
    factors = Column(JSONB, default=dict, nullable=False)  # breakdown of factors
    recommendation = Column(Text, nullable=True)
    previous_score = Column(Integer, nullable=True)
    score_change = Column(Integer, nullable=True)
    calculated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class DealAlert(Base):
    """Alert generated when a deal score changes significantly."""

    __tablename__ = "deal_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_score_id = Column(
        UUID(as_uuid=True),
        ForeignKey("deal_scores.id", ondelete="CASCADE"),
        nullable=False,
    )
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    # 'score_drop', 'deal_cooling', 'ready_to_close', 'churn_risk'
    severity = Column(String(20), nullable=False, default="low")
    # 'low', 'medium', 'high', 'critical'
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
