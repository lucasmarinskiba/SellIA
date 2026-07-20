"""Business Intelligence & Analytics Models

Funnel tracking, cohort metrics, churn predictions, LTV estimates.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class FunnelStage(str, enum.Enum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    DEAL = "deal"
    ORDER = "order"
    REPEAT = "repeat"


class ChurnRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FunnelMetric(Base):
    """Snapshot of funnel conversion rates per period."""
    __tablename__ = "funnel_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    period = Column(String(20), nullable=False)  # 2024-01, 2024-W05
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly

    leads_count = Column(Integer, default=0, nullable=False)
    qualified_count = Column(Integer, default=0, nullable=False)
    deals_count = Column(Integer, default=0, nullable=False)
    orders_count = Column(Integer, default=0, nullable=False)
    repeat_orders_count = Column(Integer, default=0, nullable=False)

    conversion_lead_to_qualified = Column(Numeric(5, 2), default=0, nullable=False)
    conversion_qualified_to_deal = Column(Numeric(5, 2), default=0, nullable=False)
    conversion_deal_to_order = Column(Numeric(5, 2), default=0, nullable=False)
    conversion_order_to_repeat = Column(Numeric(5, 2), default=0, nullable=False)

    revenue_total = Column(Numeric(14, 2), default=0, nullable=False)
    avg_order_value = Column(Numeric(14, 2), default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_funnel_metrics_business_period', 'business_id', 'period'),
    )


class CohortMetric(Base):
    """Cohort retention and revenue metrics."""
    __tablename__ = "cohort_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    cohort_month = Column(String(7), nullable=False)  # 2024-01
    cohort_size = Column(Integer, default=0, nullable=False)
    period_months = Column(Integer, default=0, nullable=False)  # 0 = first month, 1 = month 1, etc.

    active_customers = Column(Integer, default=0, nullable=False)
    revenue = Column(Numeric(14, 2), default=0, nullable=False)
    retention_rate = Column(Numeric(5, 2), default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_cohort_metrics_business_cohort', 'business_id', 'cohort_month', 'period_months'),
    )


class ChurnPrediction(Base):
    """AI-generated churn prediction for a conversation/customer."""
    __tablename__ = "churn_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    risk_level = Column(Enum(ChurnRiskLevel), nullable=False, index=True)
    churn_probability = Column(Numeric(5, 2), nullable=False)  # 0.00 - 1.00
    predicted_churn_date = Column(DateTime(timezone=True), nullable=True)

    factors = Column(JSONB, default=list, nullable=False)  # ["inactive_30_days", "no_reply_to_last_3", "competitor_mentioned"]
    recommended_action = Column(String(255), nullable=True)

    model_version = Column(String(20), default="v1", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_churn_predictions_business_risk', 'business_id', 'risk_level'),
    )


class LtvPrediction(Base):
    """Predicted lifetime value for a customer."""
    __tablename__ = "ltv_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    predicted_ltv = Column(Numeric(14, 2), nullable=False)
    predicted_orders = Column(Integer, default=1, nullable=False)
    prediction_horizon_months = Column(Integer, default=12, nullable=False)

    confidence_score = Column(Numeric(5, 2), default=0.5, nullable=False)  # 0.0 - 1.0
    factors = Column(JSONB, default=list, nullable=False)  # ["high_engagement", "repeat_buyer_pattern"]

    model_version = Column(String(20), default="v1", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_ltv_predictions_business_ltv', 'business_id', 'predicted_ltv'),
    )


class InsightAlert(Base):
    """AI-generated business insight or anomaly alert."""
    __tablename__ = "insight_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    insight_type = Column(String(50), nullable=False, index=True)  # funnel_drop, anomaly, opportunity, threat
    severity = Column(String(20), default="info", nullable=False)  # info, warning, critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metric_name = Column(String(100), nullable=True)
    metric_change_percent = Column(Numeric(7, 2), nullable=True)

    recommended_action = Column(Text, nullable=True)
    action_taken = Column(Boolean, default=False, nullable=False)
    action_result = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_insight_alerts_business_type', 'business_id', 'insight_type'),
    )
