"""Customer journey mapping — track online → offline → online conversion path."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Decimal, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class JourneyChannel(str, Enum):
    """Initial discovery channel."""
    ORGANIC_SEARCH = "organic_search"
    PAID_SEARCH = "paid_search"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    DIRECT = "direct"
    REFERRAL = "referral"
    PROXIMITY_INVITE = "proximity_invite"
    OFFLINE_WALK_IN = "offline_walk_in"


class JourneyStage(str, Enum):
    """Customer journey stage."""
    AWARENESS = "awareness"  # First touchpoint
    CONSIDERATION = "consideration"  # Engagement (email open, click, etc)
    INTENT = "intent"  # Proximity invite opened, add-to-cart, etc
    VISIT = "visit"  # Physical location check-in
    PURCHASE = "purchase"  # Online order after visit
    RETENTION = "retention"  # Repeat purchase


class CustomerJourney(Base):
    """Track complete customer journey from discovery to repeat."""
    __tablename__ = "customer_journeys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Customer identity
    customer_email = Column(String(255), nullable=True, index=True)
    customer_phone = Column(String(20), nullable=True, index=True)
    customer_id = Column(String(255), nullable=True)  # CRM user ID if available

    # Stage tracking
    current_stage = Column(SQLEnum(JourneyStage), default=JourneyStage.AWARENESS)
    initial_channel = Column(SQLEnum(JourneyChannel), nullable=False)
    initial_campaign = Column(String(255), nullable=True)  # utm_campaign value
    initial_source = Column(String(255), nullable=True)  # utm_source value

    # Timestamps per stage
    awareness_date = Column(DateTime(timezone=True), nullable=False)  # First touchpoint
    consideration_date = Column(DateTime(timezone=True), nullable=True)  # First engagement
    intent_date = Column(DateTime(timezone=True), nullable=True)  # Intent signal
    visit_date = Column(DateTime(timezone=True), nullable=True)  # Location check-in
    purchase_date = Column(DateTime(timezone=True), nullable=True)  # First order after visit
    retention_date = Column(DateTime(timezone=True), nullable=True)  # Repeat purchase

    # Location context
    location_visited_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    checkin_id = Column(UUID(as_uuid=True), nullable=True)  # location_checkin.id

    # Purchase context
    first_order_id = Column(String(255), nullable=True)
    first_order_value = Column(Decimal(10, 2), nullable=True)
    first_order_date = Column(DateTime(timezone=True), nullable=True)

    # Repeat purchase
    repeat_purchase_count = Column(Integer, default=0)
    total_lifetime_value = Column(Decimal(12, 2), default=0)
    last_purchase_date = Column(DateTime(timezone=True), nullable=True)

    # Engagement metrics
    email_opens = Column(Integer, default=0)
    email_clicks = Column(Integer, default=0)
    web_sessions = Column(Integer, default=0)
    location_visits = Column(Integer, default=0)

    # Feedback
    nps_score = Column(Integer, nullable=True)
    sentiment_at_visit = Column(String(20), nullable=True)  # positive, neutral, negative

    # Metadata
    tags = Column(JSONB, default=list)  # ["vip", "churned", "high_value", "new"]
    metadata = Column(JSONB, default=dict)
    is_converted = Column(Boolean, default=False)  # Has purchased online after visit
    is_repeat_customer = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_visited_id])

    __table_args__ = (
        Index("idx_business_stage", "business_id", "current_stage"),
        Index("idx_email_business", "customer_email", "business_id"),
    )


class JourneyTouchpoint(Base):
    """Individual touchpoint in journey (email send, web visit, proximity check, etc)."""
    __tablename__ = "journey_touchpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey("customer_journeys.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Touchpoint details
    touchpoint_type = Column(String(50), nullable=False)  # email_sent, email_opened, web_visit, proximity_check, location_visit, order_placed
    channel = Column(SQLEnum(JourneyChannel), nullable=False)
    campaign = Column(String(255), nullable=True)

    # Metadata
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    order_id = Column(String(255), nullable=True)
    checkin_id = Column(UUID(as_uuid=True), nullable=True)

    # Engagement signal
    converted_this_touch = Column(Boolean, default=False)  # Did this touchpoint lead to conversion

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    journey = relationship("CustomerJourney", foreign_keys=[journey_id])

    __table_args__ = (
        Index("idx_journey_type", "journey_id", "touchpoint_type"),
        Index("idx_business_date", "business_id", "created_at"),
    )


class JourneyMetrics(Base):
    """Aggregated journey metrics per business."""
    __tablename__ = "journey_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Date
    date = Column(String(10), nullable=False)

    # Funnel stage counts
    awareness_count = Column(Integer, default=0)  # Leads
    consideration_count = Column(Integer, default=0)  # Engaged
    intent_count = Column(Integer, default=0)  # High intent
    visit_count = Column(Integer, default=0)  # Visited
    purchase_count = Column(Integer, default=0)  # Converted
    retention_count = Column(Integer, default=0)  # Repeat

    # Conversion rates
    awareness_to_visit = Column(Decimal(5, 2), default=0)  # % leads that visit
    visit_to_purchase = Column(Decimal(5, 2), default=0)  # % visitors that buy
    overall_conversion = Column(Decimal(5, 2), default=0)  # % leads that purchase

    # Channel breakdown
    top_channel_visits = Column(String(50), nullable=True)  # best performing channel
    top_channel_count = Column(Integer, default=0)

    # Customer value
    avg_ltv = Column(Decimal(10, 2), default=0)
    avg_time_to_visit_days = Column(Integer, nullable=True)
    avg_time_visit_to_purchase_days = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])
