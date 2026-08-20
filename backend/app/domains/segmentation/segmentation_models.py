"""Customer segmentation models — RFM + behavioral segmentation."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Decimal, Enum as SQLEnum, Index, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class RFMSegment(str, Enum):
    """RFM-based customer segment."""
    CHAMPIONS = "champions"  # High R, F, M
    LOYAL_CUSTOMERS = "loyal_customers"  # Medium-High R, F, M
    POTENTIAL_LOYALISTS = "potential_loyalists"  # Recent, Medium F
    AT_RISK = "at_risk"  # Low R, High F, M
    CANT_LOSE_THEM = "cant_lose_them"  # Low R, High M
    NEED_ACTIVATION = "need_activation"  # Low R, F, M


class BehavioralSegment(str, Enum):
    """Behavioral customer segment."""
    HIGH_VALUE_BUYER = "high_value_buyer"  # High LTV, frequent purchases
    BARGAIN_HUNTER = "bargain_hunter"  # High discount usage, lower AOV
    BROWSER = "browser"  # High engagement, low conversion
    IMPULSE_BUYER = "impulse_buyer"  # High AOV, low frequency
    CONTENT_CONSUMER = "content_consumer"  # High email/web engagement, low purchase
    MOBILE_FIRST = "mobile_first"  # 80%+ mobile traffic
    LOYAL_REPEAT = "loyal_repeat"  # Consistent repeat purchases


class ChurnRiskLevel(str, Enum):
    """Churn prediction risk level."""
    LOW = "low"  # 0-10% risk
    MEDIUM = "medium"  # 11-50% risk
    HIGH = "high"  # 51-80% risk
    CRITICAL = "critical"  # 81-100% risk


class CustomerSegment(Base):
    """Individual customer segment assignment."""
    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Segmentation
    rfm_segment = Column(SQLEnum(RFMSegment), nullable=True)
    behavioral_segment = Column(SQLEnum(BehavioralSegment), nullable=True)
    churn_risk_level = Column(SQLEnum(ChurnRiskLevel), default=ChurnRiskLevel.LOW)

    # RFM scores (0-5 scale)
    recency_score = Column(Integer, default=0)  # 0-5 (0=oldest, 5=newest)
    frequency_score = Column(Integer, default=0)  # 0-5 (0=rarest, 5=most frequent)
    monetary_score = Column(Integer, default=0)  # 0-5 (0=lowest value, 5=highest value)
    rfm_composite = Column(Integer, default=0)  # Average of R, F, M

    # Churn prediction
    churn_probability = Column(Decimal(5, 2), default=0)  # 0-100 %
    days_since_purchase = Column(Integer, nullable=True)
    purchase_consistency_score = Column(Decimal(3, 1), default=0)  # 0-10 (std dev of days between purchases)
    engagement_decay = Column(Decimal(3, 1), default=0)  # 0-10 (trend in activity)

    # CLV (Customer Lifetime Value)
    clv_score = Column(Decimal(10, 2), default=0)  # Predicted LTV
    clv_percentile = Column(Integer, nullable=True)  # Percentile rank vs peers

    # Engagement
    email_engagement_score = Column(Decimal(3, 1), default=0)  # 0-10
    web_engagement_score = Column(Decimal(3, 1), default=0)  # 0-10
    purchase_engagement_score = Column(Decimal(3, 1), default=0)  # 0-10
    overall_engagement_score = Column(Decimal(3, 1), default=0)  # 0-10 average

    # Tags for custom segmentation
    tags = Column(JSONB, default=list)  # ["vip", "seasonal", "price_sensitive"]

    # Metadata
    segment_created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    segment_updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), index=True)

    customer = relationship("Customer", foreign_keys=[customer_id])

    __table_args__ = (
        Index("idx_business_rfm", "business_id", "rfm_segment"),
        Index("idx_business_behavioral", "business_id", "behavioral_segment"),
        Index("idx_churn_risk", "business_id", "churn_risk_level"),
        Index("idx_clv_score", "business_id", "clv_score"),
    )


class SegmentationMetrics(Base):
    """Aggregate segmentation metrics."""
    __tablename__ = "segmentation_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # RFM distribution
    champions_count = Column(Integer, default=0)
    loyal_customers_count = Column(Integer, default=0)
    potential_loyalists_count = Column(Integer, default=0)
    at_risk_count = Column(Integer, default=0)
    cant_lose_them_count = Column(Integer, default=0)
    need_activation_count = Column(Integer, default=0)

    # Behavioral distribution
    high_value_buyers = Column(Integer, default=0)
    bargain_hunters = Column(Integer, default=0)
    browsers = Column(Integer, default=0)
    impulse_buyers = Column(Integer, default=0)
    content_consumers = Column(Integer, default=0)
    mobile_first = Column(Integer, default=0)
    loyal_repeats = Column(Integer, default=0)

    # Churn risk distribution
    low_risk = Column(Integer, default=0)
    medium_risk = Column(Integer, default=0)
    high_risk = Column(Integer, default=0)
    critical_risk = Column(Integer, default=0)

    # Aggregates
    avg_clv = Column(Decimal(10, 2), default=0)
    avg_engagement_score = Column(Decimal(3, 1), default=0)
    at_risk_revenue = Column(Decimal(12, 2), default=0)  # CLV of at-risk customers
    churn_risk_count = Column(Integer, default=0)  # High + critical

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )


class SegmentationStrategy(Base):
    """Retention/engagement strategy per segment."""
    __tablename__ = "segmentation_strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Segment target
    rfm_segment = Column(SQLEnum(RFMSegment), nullable=True)
    behavioral_segment = Column(SQLEnum(BehavioralSegment), nullable=True)
    churn_risk_level = Column(SQLEnum(ChurnRiskLevel), nullable=True)

    # Strategy
    strategy_name = Column(String(255), nullable=False)
    strategy_description = Column(String(500), nullable=True)

    # Tactics
    automation_trigger = Column(String(255), nullable=True)  # e.g., "email_sequence_champions"
    discount_offer = Column(Decimal(5, 2), nullable=True)  # % discount to offer
    frequency_per_month = Column(Integer, default=1)  # Contact frequency
    preferred_channel = Column(String(50), nullable=True)  # email, sms, push, in_app

    # Performance tracking
    is_active = Column(Boolean, default=True)
    target_outcome = Column(String(100), nullable=True)  # "increase_repeat_purchase", "reduce_churn"

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_rfm_strategy", "business_id", "rfm_segment"),
    )
