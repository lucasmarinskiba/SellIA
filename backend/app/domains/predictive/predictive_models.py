"""Predictive modeling domain — ML scoring, segmentation, lookalike audiences."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ScoreType(str, Enum):
    """Predictive score types."""
    LEAD_SCORE = "lead_score"
    CHURN_RISK = "churn_risk"
    CLV_FORECAST = "clv_forecast"
    PROPENSITY_BUY = "propensity_buy"


class SegmentationType(str, Enum):
    """Segmentation types."""
    RULE_BASED = "rule_based"
    BEHAVIORAL = "behavioral"
    PREDICTIVE = "predictive"
    LOOKALIKE = "lookalike"


class CustomerScore(Base):
    """Predictive customer scores."""
    __tablename__ = "customer_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    lead_score = Column(Float, default=0)
    lead_score_reason = Column(String(255), nullable=True)
    lead_score_components = Column(JSONB, nullable=True)

    churn_risk = Column(Float, default=0)
    churn_risk_factors = Column(JSONB, nullable=True)
    days_until_churn = Column(Integer, nullable=True)

    clv_forecast = Column(Float, default=0)
    clv_confidence = Column(Float, default=0)
    clv_components = Column(JSONB, nullable=True)

    propensity_30d = Column(Float, default=0)
    propensity_next_action = Column(String(255), nullable=True)

    model_version = Column(String(50), default="v1")
    prediction_confidence = Column(Float, default=0)
    data_quality_score = Column(Float, default=0)

    last_calculated_at = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_scores", "business_id"),
        Index("idx_lead_score", "business_id", "lead_score"),
        Index("idx_churn_risk", "business_id", "churn_risk"),
    )


class DynamicSegment(Base):
    """Dynamic customer segments."""
    __tablename__ = "dynamic_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    segmentation_type = Column(String(50), nullable=False)

    rules = Column(JSONB, nullable=False)
    rule_logic = Column(String(10), default="AND")

    reference_segment_id = Column(UUID(as_uuid=True), nullable=True)
    similarity_threshold = Column(Float, default=0.7)

    is_active = Column(Boolean, default=True)
    member_count = Column(Integer, default=0)
    last_refreshed_at = Column(DateTime(timezone.utc), nullable=True)
    refresh_frequency_hours = Column(Integer, default=24)

    segment_metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_segment", "business_id", "is_active"),
        Index("idx_segment_type", "segmentation_type"),
    )


class SegmentMembership(Base):
    """Customer segment membership."""
    __tablename__ = "segment_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_segments.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    joined_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    left_at = Column(DateTime(timezone.utc), nullable=True)
    is_active = Column(Boolean, default=True)

    match_score = Column(Float, default=1.0)
    rank_in_segment = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_segment_customer", "segment_id", "customer_id"),
        Index("idx_active_members", "segment_id", "is_active"),
    )


class LookalikeAudience(Base):
    """Lookalike audiences from high-value customers."""
    __tablename__ = "lookalike_audiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    source_segment_id = Column(UUID(as_uuid=True), ForeignKey("dynamic_segments.id", ondelete="CASCADE"), nullable=True)
    source_customer_ids = Column(JSONB, nullable=True)

    similarity_threshold = Column(Float, default=0.75)
    target_size = Column(Integer, default=1000)
    features_to_match = Column(JSONB, nullable=True)

    audience_size = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0)
    last_generated_at = Column(DateTime(timezone.utc), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_lookalike", "business_id"),
        Index("idx_active_audiences", "is_active"),
    )


class PredictionLog(Base):
    """Audit log of predictions."""
    __tablename__ = "prediction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    prediction_type = Column(String(50), nullable=False)
    input_data = Column(JSONB, nullable=True)
    predicted_value = Column(Float, nullable=False)
    confidence = Column(Float, default=0)

    model_version = Column(String(50), default="v1")
    execution_time_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_prediction", "business_id", "prediction_type"),
    )


class PredictiveMetrics(Base):
    """Aggregated predictive metrics."""
    __tablename__ = "predictive_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    avg_lead_score = Column(Float, default=0)
    high_potential_count = Column(Integer, default=0)

    avg_churn_risk = Column(Float, default=0)
    at_risk_count = Column(Integer, default=0)

    avg_clv_forecast = Column(Float, default=0)
    total_clv_forecast = Column(Float, default=0)

    total_segments = Column(Integer, default=0)
    total_segment_members = Column(Integer, default=0)
    avg_segment_size = Column(Float, default=0)

    total_lookalike_audiences = Column(Integer, default=0)
    total_lookalike_candidates = Column(Integer, default=0)

    model_accuracy = Column(Float, default=0)
    last_model_training_at = Column(DateTime(timezone.utc), nullable=True)

    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_metrics", "business_id"),
    )
