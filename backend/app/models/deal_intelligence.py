"""Deal Intelligence models for Phase 27."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, ForeignKey, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.database import Base


class DealStakeholder(Base):
    """Buying committee members."""

    __tablename__ = "deal_stakeholders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Person details
    person_id = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    title = Column(String(255))
    company = Column(String(255))

    # Role in buying process
    buyer_role = Column(String(50), default="influencer")  # economic_buyer, user_buyer, coach, blocker, influencer
    influence_level = Column(Integer, default=5)  # 1-10 scale
    engagement_score = Column(Float, default=0.0)  # 0-100

    # Engagement tracking
    last_email_open = Column(DateTime)
    last_call_date = Column(DateTime)
    email_open_count = Column(Integer, default=0)
    meeting_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="active")  # active, churned, dormant, prospect
    identified_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_deal_stakeholders_deal", "deal_id"),
        Index("idx_deal_stakeholders_role", "buyer_role"),
        Index("idx_deal_stakeholders_engagement", "engagement_score"),
    )


class DealProbabilityScore(Base):
    """Deal close probability predictions."""

    __tablename__ = "deal_probability_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Predicted probability
    close_probability = Column(Float, nullable=False)  # 0-100
    confidence_level = Column(Float)  # 0-100

    # Input features
    features = Column(JSONB)  # Model features used for prediction

    # Model metadata
    model_version = Column(String(50))
    prediction_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Confidence intervals
    probability_low = Column(Float)  # 90% CI lower bound
    probability_high = Column(Float)  # 90% CI upper bound

    __table_args__ = (
        Index("idx_prob_scores_deal", "deal_id"),
        Index("idx_prob_scores_probability", "close_probability"),
    )


class DealHealthSnapshot(Base):
    """Real-time deal health evaluation."""

    __tablename__ = "deal_health_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Overall health
    health_score = Column(Integer, nullable=False)  # 0-100
    health_status = Column(String(20), nullable=False)  # healthy, at_risk, critical, won, lost

    # Component scores
    engagement_health = Column(Integer)  # 0-100
    momentum_health = Column(Integer)  # 0-100
    buyer_health = Column(Integer)  # 0-100
    competition_health = Column(Integer)  # 0-100

    # Risk indicators
    days_since_last_activity = Column(Integer)
    stakeholder_churn_count = Column(Integer, default=0)
    buying_committee_complete = Column(Boolean, default=False)
    economic_buyer_engaged = Column(Boolean, default=False)

    # Recommendations
    recommended_actions = Column(JSONB)  # [{action: str, priority: str}]

    # Metadata
    snapshot_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_health_deal", "deal_id"),
        Index("idx_health_status", "health_status"),
        Index("idx_health_date", "snapshot_date"),
    )


class DealHealthAlert(Base):
    """Deal health change alerts."""

    __tablename__ = "deal_health_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"))

    # Alert details
    alert_type = Column(String(50), nullable=False)  # low_engagement, lost_momentum, buyer_churn, stalled
    severity = Column(String(20), nullable=False)  # info, warning, critical
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Recommended action
    recommended_action = Column(Text)
    action_type = Column(String(50))  # call, email, meeting, escalate

    # Alert lifecycle
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    action_taken = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_alerts_deal", "deal_id"),
        Index("idx_alerts_user", "user_id"),
        Index("idx_alerts_status", "resolved_at"),
    )


class StakeholderEngagementEvent(Base):
    """Time-series engagement events (for analytics)."""

    __tablename__ = "stakeholder_engagement_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(String(255), nullable=False)

    # Event type
    event_type = Column(String(50), nullable=False)  # email_open, email_click, call, meeting, message
    engagement_value = Column(Integer, nullable=False)  # Points assigned

    # Event details
    event_details = Column(JSONB)  # {email_subject: "...", call_duration: 15}

    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_engagement_deal_person", "deal_id", "person_id"),
        Index("idx_engagement_timestamp", "event_timestamp"),
    )


class ModelPredictionsCache(Base):
    """Cache for ML model predictions."""

    __tablename__ = "model_predictions_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Cached prediction
    prediction_json = Column(JSONB, nullable=False)  # Full prediction object

    cache_created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cache_expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_cache_expires", "cache_expires_at"),
    )
