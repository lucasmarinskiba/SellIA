"""Alerts & Recommendations Models

Tracks intelligent alerts and actionable recommendations for businesses.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AlertRuleType(str, enum.Enum):
    LEAD_SCORE_THRESHOLD = "lead_score_threshold"
    DEAL_STALLED = "deal_stalled"
    NO_REPLY = "no_reply"
    REVENUE_TARGET = "revenue_target"
    HOT_LEAD_NO_DEAL = "hot_lead_no_deal"
    CART_ABANDONED = "cart_abandoned"
    WORKFLOW_FAILED = "workflow_failed"
    COMPETITOR_MENTIONED = "competitor_mentioned"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"


class RecommendationType(str, enum.Enum):
    SCORE_INCREASE = "score_increase"
    DEAL_MOVE = "deal_move"
    FOLLOW_UP = "follow_up"
    ASSIGN_AGENT = "assign_agent"
    CREATE_ORDER = "create_order"
    CUSTOM = "custom"


class RecommendationActionType(str, enum.Enum):
    SEND_MESSAGE = "send_message"
    MOVE_STAGE = "move_stage"
    ASSIGN_AGENT = "assign_agent"
    CREATE_DEAL = "create_deal"
    WAIT = "wait"
    DISMISS = "dismiss"


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class AlertRule(Base):
    """Configurable rule that generates alerts when conditions are met."""
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    rule_type = Column(Enum(AlertRuleType), nullable=False, index=True)
    config = Column(JSONB, default=dict, nullable=False)  # {threshold: 80, days: 3, hours: 24, target_amount: 100000}

    severity = Column(Enum(AlertSeverity), default=AlertSeverity.INFO, nullable=False)
    channels = Column(JSONB, default=list, nullable=False)  # ["in_app", "email", "webhook"]
    cooldown_minutes = Column(Integer, default=60, nullable=False)
    max_alerts_per_day = Column(Integer, default=10, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Alert(Base):
    """A generated alert instance."""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True, index=True)

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.UNREAD, nullable=False, index=True)

    entity_type = Column(String(50), nullable=True)  # "deal", "conversation", "order"
    entity_id = Column(UUID(as_uuid=True), nullable=True)

    recommended_action = Column(Text, nullable=True)
    alert_metadata = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)


class Recommendation(Base):
    """An actionable recommendation generated from alerts or heuristics."""
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    type = Column(Enum(RecommendationType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=1, nullable=False)  # 1-5

    context_data = Column(JSONB, default=dict, nullable=False)
    action_type = Column(Enum(RecommendationActionType), nullable=False)
    action_payload = Column(JSONB, default=dict, nullable=False)

    status = Column(Enum(RecommendationStatus), default=RecommendationStatus.PENDING, nullable=False, index=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    applied_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
