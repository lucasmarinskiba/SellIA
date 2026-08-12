"""Phase 30 Churn Prevention models."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.database import Base


class ChurnPrediction(Base):
    """Churn risk predictions."""

    __tablename__ = "churn_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    churn_probability = Column(Float, nullable=False)  # 0-1
    risk_level = Column(String(50))  # LOW, MEDIUM, HIGH
    churn_reasons = Column(JSONB)  # [{"reason": "...", "impact": 0.35}]
    predicted_churn_date = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_customer_risk", "customer_id", "risk_level"),
        Index("idx_probability", "churn_probability"),
        Index("idx_predicted_date", "predicted_churn_date"),
    )


class ExpansionOpportunity(Base):
    """Upsell + cross-sell opportunities."""

    __tablename__ = "expansion_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    opportunity_type = Column(String(50), nullable=False)  # upsell, cross_sell, seat_expansion
    base_feature = Column(String(255))  # what they're using
    adjacent_feature = Column(String(255))  # what they should buy
    revenue_potential = Column(Float, nullable=False)  # estimated annual value
    likelihood_score = Column(Float)  # 0-1
    recommended_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_customer_opp", "customer_id", "opportunity_type"),
        Index("idx_revenue_potential", "revenue_potential"),
    )


class ABMIntentScore(Base):
    """ABM intent scoring."""

    __tablename__ = "abm_intent_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    intent_score = Column(Integer)  # 0-100
    intent_level = Column(String(50))  # NOT_INTERESTED, AWARENESS, CONSIDERATION, BUY_SIGNAL
    top_signals = Column(JSONB)  # [{"signal": "page_views", "weight": 0.2, "value": "15"}]
    trending = Column(String(50))  # UP, DOWN, FLAT

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_account_intent", "account_id", "intent_score"),
        Index("idx_intent_level", "intent_level"),
    )


class RetentionCampaign(Base):
    """Win-back campaigns."""

    __tablename__ = "retention_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    churn_prediction_id = Column(UUID(as_uuid=True), ForeignKey("churn_predictions.id"), nullable=True)

    campaign_type = Column(String(50))  # win_back, value_add, competitive_offer
    playbook_message = Column(Text, nullable=False)
    offer_type = Column(String(50))  # discount_pct, free_month, feature_unlock
    offer_value = Column(String(255))  # "30%" or "3 months" or "premium_features"

    sent_at = Column(DateTime, nullable=False)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)

    converted = Column(Boolean, default=False)
    converted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_customer_campaign", "customer_id", "campaign_type"),
        Index("idx_converted", "converted"),
    )


class WinBackPlaybook(Base):
    """Win-back playbook templates."""

    __tablename__ = "win_back_playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    churn_reason = Column(String(50), nullable=False)  # payment_issue, feature_gap, competitor, price
    segment = Column(String(50), nullable=False)  # SMB, mid_market, enterprise, by_industry

    message_template = Column(Text, nullable=False)
    offer_template = Column(Text)
    executive_escalation_message = Column(Text)

    success_rate = Column(Float)  # historical conversion %
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_reason_segment", "churn_reason", "segment"),
        Index("idx_success_rate", "success_rate"),
    )


class CustomerEngagementMetrics(Base):
    """Customer engagement tracking."""

    __tablename__ = "customer_engagement_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    metric_date = Column(DateTime, nullable=False)

    login_count = Column(Integer)
    features_used_pct = Column(Float)  # 0-1
    support_tickets_count = Column(Integer)
    nps_score = Column(Integer)  # 0-10
    health_score = Column(Integer)  # 0-100: composite

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_customer_date", "customer_id", "metric_date"),
        Index("idx_health_score", "health_score"),
    )


class CustomerHealthScorecard(Base):
    """Daily customer health snapshot."""

    __tablename__ = "customer_health_scorecards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    health_score = Column(Integer)  # 0-100
    health_level = Column(String(50))  # HEALTHY, AT_RISK, CRITICAL
    churn_risk = Column(String(50))  # LOW, MEDIUM, HIGH
    churn_probability = Column(Float)  # 0-1
    expansion_potential = Column(Float)  # estimated annual value
    expansion_opportunities_count = Column(Integer)

    abm_intent_score = Column(Integer)  # 0-100
    abm_intent_level = Column(String(50))  # NOT_INTERESTED, AWARENESS, CONSIDERATION, BUY_SIGNAL

    trending = Column(String(50))  # UP, DOWN, FLAT
    recommended_action = Column(Text)

    snapshot_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_customer_health", "customer_id", "health_level"),
        Index("idx_snapshot_date", "snapshot_date"),
    )
