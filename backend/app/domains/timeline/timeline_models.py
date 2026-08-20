"""Customer timeline & activity models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventType(str, Enum):
    """Event types for customer timeline."""
    EMAIL_SENT = "email_sent"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    SMS_SENT = "sms_sent"
    SMS_DELIVERED = "sms_delivered"
    WHATSAPP_SENT = "whatsapp_sent"
    WHATSAPP_READ = "whatsapp_read"
    CALL_INCOMING = "call_incoming"
    CALL_OUTGOING = "call_outgoing"
    CALL_MISSED = "call_missed"
    MEETING_SCHEDULED = "meeting_scheduled"
    MEETING_COMPLETED = "meeting_completed"
    MEETING_NO_SHOW = "meeting_no_show"
    ORDER_CREATED = "order_created"
    ORDER_PAID = "order_paid"
    ORDER_FULFILLED = "order_fulfilled"
    DEAL_CREATED = "deal_created"
    DEAL_WON = "deal_won"
    DEAL_LOST = "deal_lost"
    SUPPORT_TICKET_OPENED = "support_ticket_opened"
    SUPPORT_TICKET_RESOLVED = "support_ticket_resolved"


class EventChannel(str, Enum):
    """Event channels."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    CALL = "call"
    MEETING = "meeting"
    ORDER = "order"
    DEAL = "deal"
    SUPPORT = "support"
    WEBSITE = "website"
    MANUAL = "manual"


class EventOutcome(str, Enum):
    """Event outcomes."""
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"


class CustomerEvent(Base):
    """Customer event record."""
    __tablename__ = "customer_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event metadata
    event_type = Column(String(50), nullable=False)  # EventType value
    channel = Column(String(50), nullable=False)     # EventChannel value
    outcome = Column(String(50), default=EventOutcome.SUCCESS.value)  # EventOutcome value

    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=False)  # e.g., {"email": "...", "subject": "...", "open_time": "..."}

    # Engagement metrics
    engagement_score = Column(Integer, default=0)  # 0-100
    is_important = Column(Boolean, default=False)  # Star/pin event
    revenue_impact = Column(String(50), nullable=True)  # "positive", "negative", "neutral"
    estimated_value = Column(Integer, nullable=True)  # In cents/units

    # Relationships
    related_deal_id = Column(UUID(as_uuid=True), nullable=True)
    related_order_id = Column(UUID(as_uuid=True), nullable=True)
    related_contact_id = Column(String(255), nullable=True)

    # Tracking
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_customer_date", "customer_id", "created_at"),
        Index("idx_business_type", "business_id", "event_type"),
        Index("idx_channel", "channel"),
    )


class EventTimeline(Base):
    """Customer timeline summary (materialized view)."""
    __tablename__ = "event_timelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Timeline stats
    total_events = Column(Integer, default=0)
    last_event_at = Column(DateTime(timezone.utc), nullable=True)
    first_event_at = Column(DateTime(timezone.utc), nullable=True)

    # Event type breakdown
    email_count = Column(Integer, default=0)
    sms_count = Column(Integer, default=0)
    whatsapp_count = Column(Integer, default=0)
    call_count = Column(Integer, default=0)
    meeting_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)
    deal_count = Column(Integer, default=0)

    # Engagement metrics
    avg_engagement_score = Column(Integer, default=0)
    important_events_count = Column(Integer, default=0)
    total_revenue_impact = Column(Integer, default=0)

    # Channel breakdown
    channel_breakdown = Column(JSONB, nullable=True)  # {"email": 45, "sms": 12, ...}
    event_type_breakdown = Column(JSONB, nullable=True)

    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_customer", "business_id", "customer_id"),
    )


class TimelineMetadata(Base):
    """Enriched metadata for timeline context."""
    __tablename__ = "timeline_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("customer_events.id", ondelete="CASCADE"), nullable=False, index=True)

    # Enrichment data
    geolocation = Column(String(255), nullable=True)  # "New York, NY"
    device_type = Column(String(50), nullable=True)   # "mobile", "desktop"
    browser = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Campaign tracking
    campaign_id = Column(UUID(as_uuid=True), nullable=True)
    campaign_name = Column(String(255), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # Sentiment (if applicable)
    sentiment = Column(String(50), nullable=True)  # "positive", "neutral", "negative"
    sentiment_score = Column(Integer, nullable=True)  # -100 to 100

    # Additional context
    context_json = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_event_id", "event_id"),
    )


class EventFilter(Base):
    """Saved timeline filter views."""
    __tablename__ = "event_filters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Filter definition
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)

    # Filter criteria
    event_types = Column(JSONB, default=list)  # ["email_sent", "order_created", ...]
    channels = Column(JSONB, default=list)     # ["email", "sms", ...]
    outcomes = Column(JSONB, default=list)     # ["success", "failed", ...]
    date_from = Column(DateTime(timezone.utc), nullable=True)
    date_to = Column(DateTime(timezone.utc), nullable=True)

    # Display options
    is_favorite = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_user_business", "user_id", "business_id"),
    )


class TimelineMetrics(Base):
    """Timeline aggregated metrics."""
    __tablename__ = "timeline_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Activity metrics
    total_events_7d = Column(Integer, default=0)
    total_events_30d = Column(Integer, default=0)
    active_customers = Column(Integer, default=0)

    # Event type distribution
    email_events_pct = Column(Integer, default=0)
    sms_events_pct = Column(Integer, default=0)
    whatsapp_events_pct = Column(Integer, default=0)
    call_events_pct = Column(Integer, default=0)
    meeting_events_pct = Column(Integer, default=0)

    # Engagement
    avg_events_per_customer = Column(Integer, default=0)
    avg_engagement_score = Column(Integer, default=0)
    important_events_pct = Column(Integer, default=0)

    # Business impact
    events_with_revenue_impact = Column(Integer, default=0)
    total_revenue_impact = Column(Integer, default=0)
    avg_days_to_purchase = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_date", "business_id", "created_at"),
    )
