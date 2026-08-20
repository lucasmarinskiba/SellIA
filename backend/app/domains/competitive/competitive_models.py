"""Competitive intelligence models — competitor tracking + market analysis."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Decimal, Enum as SQLEnum, Index, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class CompetitorType(str, Enum):
    """Competitor classification."""
    DIRECT = "direct"  # Same product/service + location
    INDIRECT = "indirect"  # Similar product, different approach
    SUBSTITUTE = "substitute"  # Alternative solution
    ADJACENT = "adjacent"  # Complementary services


class CompetitorStatus(str, Enum):
    """Tracking status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MONITORING = "monitoring"


class Competitor(Base):
    """Tracked competitor business."""
    __tablename__ = "competitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Identity
    name = Column(String(255), nullable=False)
    website = Column(String(255), nullable=True)
    competitor_type = Column(SQLEnum(CompetitorType), default=CompetitorType.DIRECT)

    # Location
    primary_address = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    service_radius_km = Column(Integer, nullable=True)  # If franchise/multi-location

    # Business info
    founded_year = Column(Integer, nullable=True)
    employee_count = Column(Integer, nullable=True)
    primary_channel = Column(String(50), nullable=True)  # online, offline, hybrid
    product_categories = Column(JSONB, default=list)  # ["electronics", "home_goods"]

    # Market metrics
    estimated_monthly_revenue = Column(Decimal(12, 2), nullable=True)
    market_share_pct = Column(Decimal(5, 2), nullable=True)  # % of addressable market
    customer_base_size = Column(Integer, nullable=True)  # Estimated

    # Online presence
    social_media_followers = Column(Integer, default=0)  # Total across platforms
    google_rating = Column(Decimal(2, 1), nullable=True)  # 1-5 stars
    google_review_count = Column(Integer, default=0)
    domain_authority = Column(Integer, nullable=True)  # Moz/Ahrefs DA score

    # Tracking
    status = Column(SQLEnum(CompetitorStatus), default=CompetitorStatus.MONITORING)
    notes = Column(String(1000), nullable=True)
    threat_level = Column(String(20), nullable=True)  # low, medium, high, critical

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_competitor", "business_id", "competitor_type"),
    )


class CompetitorPricing(Base):
    """Track competitor pricing snapshots."""
    __tablename__ = "competitor_pricing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Product/service
    product_name = Column(String(255), nullable=False)
    product_category = Column(String(100), nullable=True)

    # Pricing
    base_price = Column(Decimal(10, 2), nullable=False)
    discount_active = Column(Boolean, default=False)
    discounted_price = Column(Decimal(10, 2), nullable=True)
    discount_pct = Column(Decimal(5, 2), nullable=True)

    # Availability
    in_stock = Column(Boolean, default=True)
    estimated_delivery = Column(String(50), nullable=True)  # "2-3 days", "1 week"

    # Date
    date_observed = Column(String(10), nullable=False)  # YYYY-MM-DD
    source = Column(String(100), nullable=True)  # website, store_visit, aggregator

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    competitor = relationship("Competitor", foreign_keys=[competitor_id])

    __table_args__ = (
        Index("idx_competitor_date", "competitor_id", "date_observed"),
        Index("idx_business_date", "business_id", "date_observed"),
    )


class CompetitorOffering(Base):
    """Track competitor product/service offerings."""
    __tablename__ = "competitor_offerings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Offering
    offering_type = Column(String(50), nullable=False)  # product, service, feature
    offering_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)

    # Details
    description = Column(String(500), nullable=True)
    features = Column(JSONB, default=list)  # ["premium_support", "api_access", "white_label"]
    launch_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    status = Column(String(20), default="active")  # active, beta, discontinued

    # Our gap analysis
    our_has_equivalent = Column(Boolean, default=False)
    competitive_advantage = Column(String(500), nullable=True)  # What they do better

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    competitor = relationship("Competitor", foreign_keys=[competitor_id])

    __table_args__ = (
        Index("idx_competitor_category", "competitor_id", "category"),
    )


class CompetitivePosition(Base):
    """Aggregate competitive position snapshot."""
    __tablename__ = "competitive_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Competitor counts
    total_competitors_tracked = Column(Integer, default=0)
    direct_competitors = Column(Integer, default=0)
    high_threat_count = Column(Integer, default=0)

    # Market position
    price_position = Column(String(20), nullable=True)  # premium, market_rate, discount
    feature_parity_score = Column(Decimal(3, 1), nullable=True)  # 0-10 (vs top 3 competitors)
    market_differentiation = Column(String(500), nullable=True)  # Our competitive advantage

    # Price intelligence
    avg_competitor_price = Column(Decimal(10, 2), nullable=True)
    price_gap_vs_avg = Column(Decimal(8, 2), nullable=True)  # Positive = more expensive
    most_common_discount_pct = Column(Decimal(5, 2), nullable=True)

    # Customer perception
    avg_competitor_rating = Column(Decimal(2, 1), nullable=True)  # 1-5
    avg_review_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )
