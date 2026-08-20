"""Customer 360 & unified data platform models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class LifecycleStage(str, Enum):
    """Customer lifecycle stages."""
    PROSPECT = "prospect"
    LEAD = "lead"
    CUSTOMER = "customer"
    LOYAL = "loyal"
    ADVOCATE = "advocate"
    INACTIVE = "inactive"
    LOST = "lost"


class CustomerProfile(Base):
    """Unified customer profile."""
    __tablename__ = "customer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Identity
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Contact
    company = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # Lifecycle
    lifecycle_stage = Column(String(50), default=LifecycleStage.PROSPECT.value)
    lifecycle_stage_updated_at = Column(DateTime(timezone.utc), nullable=True)

    # Preferences
    preferences = Column(JSONB, nullable=True)  # Language, timezone, notification prefs, etc.
    tags = Column(JSONB, default=list)  # Custom tags/labels
    source = Column(String(100), nullable=True)  # How customer was acquired

    # Privacy & Consent
    gdpr_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    data_export_requested = Column(Boolean, default=False)

    # Timestamps
    first_seen_at = Column(DateTime(timezone.utc), nullable=True)
    last_seen_at = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_customer", "business_id", "customer_id"),
        Index("idx_lifecycle", "lifecycle_stage"),
    )


class CustomerScores(Base):
    """Customer scoring & predictions."""
    __tablename__ = "customer_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # RFM Scores (0-100)
    recency_score = Column(Integer, default=0)
    frequency_score = Column(Integer, default=0)
    monetary_score = Column(Integer, default=0)
    rfm_total_score = Column(Integer, default=0)  # Combined 0-100

    # Business Scores
    customer_lifetime_value = Column(Integer, default=0)  # In cents/units
    lifetime_purchases = Column(Integer, default=0)
    avg_order_value = Column(Integer, default=0)

    # Predictive Scores (0-100)
    churn_risk_score = Column(Integer, default=0)  # 0 = low, 100 = high
    lifetime_value_score = Column(Integer, default=0)  # Predicted CLV tier
    propensity_to_buy_score = Column(Integer, default=0)  # Likelihood to purchase
    engagement_score = Column(Integer, default=0)  # Overall engagement

    # Health
    health_score = Column(Integer, default=0)  # 0-100 overall health

    # Next Best Action
    next_best_action = Column(String(255), nullable=True)  # Recommended action
    next_best_channel = Column(String(50), nullable=True)  # Recommended channel

    # Score Metadata
    scores_calculated_at = Column(DateTime(timezone.utc), nullable=True)
    scores_confidence = Column(Integer, default=0)  # Confidence % based on data volume

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_customer_score", "business_id", "customer_id"),
        Index("idx_churn_risk", "churn_risk_score"),
        Index("idx_clv", "customer_lifetime_value"),
    )


class CustomerSegmentMembership(Base):
    """Customer segment membership."""
    __tablename__ = "customer_segment_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Segment
    segment_name = Column(String(100), nullable=False)  # "VIP", "At-Risk", "High-Growth", etc.
    segment_type = Column(String(50), nullable=False)  # "rfm", "behavioral", "predictive", "manual"

    # Membership
    joined_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    left_at = Column(DateTime(timezone.utc), nullable=True)

    # Scoring
    segment_score = Column(Integer, nullable=True)  # Score within segment

    __table_args__ = (
        Index("idx_customer_segment", "customer_id", "segment_name"),
        Index("idx_business_segment", "business_id", "segment_name"),
    )


class CustomerInsights(Base):
    """AI-generated customer insights & recommendations."""
    __tablename__ = "customer_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Insight
    insight_type = Column(String(50), nullable=False)  # "opportunity", "risk", "recommendation", "anomaly"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Integer, default=0)  # 0-100

    # Recommendation
    recommended_action = Column(String(255), nullable=True)
    recommended_channel = Column(String(50), nullable=True)
    estimated_impact = Column(Integer, nullable=True)  # Expected revenue/outcome
    impact_metric = Column(String(50), nullable=True)  # "revenue", "engagement", "retention"

    # Status
    is_actioned = Column(Boolean, default=False)
    actioned_at = Column(DateTime(timezone.utc), nullable=True)
    is_dismissed = Column(Boolean, default=False)

    # Metadata
    ai_model = Column(String(100), nullable=True)  # Model that generated insight
    generated_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_customer_insight", "customer_id", "generated_at"),
        Index("idx_insight_type", "insight_type"),
    )


class Customer360Metadata(Base):
    """Metadata for 360 profile assembly."""
    __tablename__ = "customer_360_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Data Completeness
    profile_completeness_pct = Column(Integer, default=0)  # % of fields filled
    data_sources_count = Column(Integer, default=0)  # How many sources contribute

    # Activity
    total_interactions = Column(Integer, default=0)
    total_transactions = Column(Integer, default=0)
    total_engagements = Column(Integer, default=0)

    # Enrichment
    is_enriched = Column(Boolean, default=False)  # Has enrichment data
    enrichment_sources = Column(JSONB, default=list)  # ["clearbit", "apollo", ...]

    # Computation
    last_360_computed_at = Column(DateTime(timezone.utc), nullable=True)
    compute_time_ms = Column(Integer, nullable=True)  # How long computation took

    # Data Quality
    data_quality_score = Column(Integer, default=0)  # 0-100
    duplicate_risk = Column(Boolean, default=False)  # Likely duplicate

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_customer_360", "business_id", "customer_id"),
    )
