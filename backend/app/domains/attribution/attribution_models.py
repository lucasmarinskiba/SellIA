"""Marketing attribution models — channel ROI + attribution tracking."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AttributionModel(str, Enum):
    """Attribution model."""
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"


class ChannelAttributionMetric(Base):
    """Track channel performance for attribution."""
    __tablename__ = "channel_attribution_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Channel
    channel = Column(String(50), nullable=False)  # organic_search, paid_search, etc
    campaign = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Touchpoint metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Decimal(5, 2), default=0)  # Click-through rate %
    cost = Column(Decimal(10, 2), default=0)  # Ad spend
    cpc = Column(Decimal(8, 2), default=0)  # Cost per click

    # Journey metrics
    journeys_initiated = Column(Integer, default=0)
    journeys_with_visit = Column(Integer, default=0)
    visit_rate = Column(Decimal(5, 2), default=0)  # % of journeys that visit

    # Revenue attribution
    revenue_attributed = Column(Decimal(12, 2), default=0)  # Total revenue from channel
    orders_attributed = Column(Integer, default=0)  # Orders from channel
    aov = Column(Decimal(10, 2), default=0)  # Average order value
    roas = Column(Decimal(8, 2), default=0)  # Return on ad spend

    # Efficiency
    cost_per_visit = Column(Decimal(8, 2), default=0)
    cost_per_order = Column(Decimal(8, 2), default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_channel_date", "business_id", "channel", "date"),
    )


class LocationChannelAttribution(Base):
    """Attribute visits + revenue per location-channel combination."""
    __tablename__ = "location_channel_attribution"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Attribution
    channel = Column(String(50), nullable=False)
    attribution_model = Column(SQLEnum(AttributionModel), default=AttributionModel.FIRST_TOUCH)

    # Date range
    date_start = Column(String(10), nullable=False)
    date_end = Column(String(10), nullable=False)

    # Metrics
    visits_attributed = Column(Integer, default=0)
    revenue_attributed = Column(Decimal(12, 2), default=0)
    orders_from_visits = Column(Integer, default=0)
    conversion_rate = Column(Decimal(5, 2), default=0)  # visits -> orders

    # Efficiency
    cost_per_visit = Column(Decimal(8, 2), nullable=True)
    revenue_per_visit = Column(Decimal(8, 2), default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_channel", "location_id", "channel"),
    )


class ChannelROIReport(Base):
    """Aggregated ROI per channel (daily snapshot)."""
    __tablename__ = "channel_roi_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Period
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Rankings
    channel_rank_by_visits = Column(String(50), nullable=True)  # Best channel by visits
    channel_rank_by_revenue = Column(String(50), nullable=True)  # Best channel by revenue
    channel_rank_by_roas = Column(String(50), nullable=True)  # Best channel by ROAS

    # Totals
    total_cost = Column(Decimal(12, 2), default=0)
    total_revenue = Column(Decimal(12, 2), default=0)
    total_visits = Column(Integer, default=0)
    blended_roas = Column(Decimal(8, 2), default=0)
    blended_cpv = Column(Decimal(8, 2), default=0)

    # Attribution model used
    attribution_model = Column(SQLEnum(AttributionModel), default=AttributionModel.FIRST_TOUCH)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )
