"""Multi-touch attribution models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class AttributionModel(str, Enum):
    """Attribution models."""
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"


class Touchpoint(Base):
    """Customer journey touchpoint."""
    __tablename__ = "touchpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Touchpoint details
    channel = Column(String(50), nullable=False)  # email, sms, web, social, ads, direct
    source = Column(String(100), nullable=True)  # google, facebook, newsletter, organic
    medium = Column(String(50), nullable=True)  # cpc, organic, email, social
    campaign = Column(String(255), nullable=True)  # campaign name/id

    # Interaction
    interaction_type = Column(String(50), nullable=False)  # click, view, form_submit, chat, call
    interaction_data = Column(JSONB, nullable=True)  # {utm_params, referrer, device}

    # Timing
    touched_at = Column(DateTime(timezone.utc), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=True)  # If converts to order

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_customer_touchpoint", "customer_id", "touched_at"),
        Index("idx_channel_source", "channel", "source"),
    )


class CustomerJourney(Base):
    """Complete customer journey from first to conversion."""
    __tablename__ = "customer_journeys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Journey timeline
    first_touch_at = Column(DateTime(timezone.utc), nullable=False)
    last_touch_at = Column(DateTime(timezone.utc), nullable=False)
    converted_at = Column(DateTime(timezone.utc), nullable=True)

    # Conversion
    order_id = Column(UUID(as_uuid=True), nullable=True)
    conversion_value = Column(Float, default=0)
    is_converted = Column(Boolean, default=False)

    # Journey composition
    touchpoint_count = Column(Integer, default=0)
    channels_involved = Column(JSONB, nullable=True)  # [email, web, social]
    journey_duration_days = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_journey_customer", "customer_id", "converted_at"),
        Index("idx_converted", "is_converted"),
    )


class AttributionCredit(Base):
    """Revenue attribution to touchpoint."""
    __tablename__ = "attribution_credits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Transaction & Touchpoint
    order_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    touchpoint_id = Column(UUID(as_uuid=True), ForeignKey("touchpoints.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Attribution
    attribution_model = Column(String(50), nullable=False)  # AttributionModel value
    credit_percentage = Column(Float, default=0)  # 0-100
    credited_amount = Column(Float, default=0)  # $ amount

    # Touchpoint context
    channel = Column(String(50), nullable=False)
    source = Column(String(100), nullable=True)
    position_in_journey = Column(Integer, nullable=True)  # 1, 2, 3...

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_order_touchpoint", "order_id", "touchpoint_id"),
        Index("idx_channel_credit", "channel", "credited_amount"),
    )


class ChannelPerformance(Base):
    """Channel-level attribution metrics."""
    __tablename__ = "channel_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Period
    period_start = Column(DateTime(timezone.utc), nullable=False)
    period_end = Column(DateTime(timezone.utc), nullable=False)

    # Channel
    channel = Column(String(50), nullable=False)
    source = Column(String(100), nullable=True)

    # Metrics
    touchpoint_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)
    total_revenue = Column(Float, default=0)
    avg_attributed_value = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)  # % of touchpoints leading to conversion

    # ROI (if cost data available)
    spend = Column(Float, nullable=True)  # Cost spent on channel
    roi = Column(Float, nullable=True)  # (revenue - spend) / spend

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_channel_period", "business_id", "channel", "period_start"),
    )


class AttributionMetrics(Base):
    """Aggregated attribution metrics."""
    __tablename__ = "attribution_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Overall metrics
    total_journeys = Column(Integer, default=0)
    conversion_journeys = Column(Integer, default=0)
    avg_journey_length = Column(Float, default=0)
    avg_touchpoint_count = Column(Float, default=0)

    # Revenue
    total_attributed_revenue = Column(Float, default=0)
    avg_order_value = Column(Float, default=0)

    # Channel breakdown
    top_first_touch_channel = Column(String(50), nullable=True)
    top_last_touch_channel = Column(String(50), nullable=True)
    top_linear_channel = Column(String(50), nullable=True)

    # Timeline
    last_calculated_at = Column(DateTime(timezone.utc), nullable=True)

    __table_args__ = (
        Index("idx_business_metrics", "business_id"),
    )
