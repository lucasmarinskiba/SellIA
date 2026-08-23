"""Real-time feedback alerts — NPS monitoring + escalation."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Numeric, Enum as SQLEnum, Index, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class FeedbackSentiment(str, Enum):
    """Feedback sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class AlertStatus(str, Enum):
    """Alert lifecycle."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class NPSAlert(Base):
    """Alert triggered on low NPS (< 6) feedback."""
    __tablename__ = "nps_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("location_feedback.id", ondelete="CASCADE"), nullable=False)

    # Visitor context
    visitor_email = Column(String(255), nullable=True)
    visitor_phone = Column(String(20), nullable=True)
    visitor_name = Column(String(255), nullable=True)

    # Alert details
    nps_score = Column(Integer, nullable=False)  # 0-5 (detectors < 6)
    sentiment = Column(SQLEnum(FeedbackSentiment), nullable=False)
    comment = Column(String(1000), nullable=True)
    topics = Column(JSONB, default=list)  # Pain points: ["staff_rudeness", "wait_time", "product_quality"]

    # Status
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)  # Manager
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    # Resolution
    assigned_to_staff_id = Column(UUID(as_uuid=True), nullable=True)  # Staff assigned follow-up
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(String(1000), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Re-survey
    resurvey_scheduled_for = Column(DateTime(timezone=True), nullable=True)  # 7 days after resolution
    resurvey_completed = Column(Boolean, default=False)
    resurvey_nps_score = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_status", "location_id", "status"),
        Index("idx_business_created", "business_id", "created_at"),
    )


class NPSTrendMetric(Base):
    """Running NPS metrics per location (hourly snapshot)."""
    __tablename__ = "nps_trend_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Period
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    hour = Column(Integer, nullable=True)  # 0-23 for hourly, NULL for daily

    # Metrics
    nps_avg = Column(Numeric(5, 2), nullable=False)  # Average NPS 0-10
    promoters_count = Column(Integer, default=0)  # 9-10
    passives_count = Column(Integer, default=0)  # 7-8
    detractors_count = Column(Integer, default=0)  # 0-6
    total_responses = Column(Integer, default=0)

    # Sentiment breakdown
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)

    # Top topics (if negative)
    top_issues = Column(JSONB, default=list)  # [{"topic": "wait_time", "count": 3}, ...]

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_date", "location_id", "date"),
    )


class SentimentTrend(Base):
    """Track sentiment changes over time (daily)."""
    __tablename__ = "sentiment_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Period
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    # Sentiment % breakdown
    positive_pct = Column(Numeric(5, 2), default=0)  # 0-100
    neutral_pct = Column(Numeric(5, 2), default=0)
    negative_pct = Column(Numeric(5, 2), default=0)

    # Trend direction
    direction = Column(String(20), default="stable")  # improving, stable, declining
    day_over_day_change = Column(Numeric(5, 2), nullable=True)  # % change from previous day

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_location_trend_date", "location_id", "date"),
    )


class FeedbackFollowUp(Base):
    """Follow-up task + re-survey schedule for negative feedback."""
    __tablename__ = "feedback_follow_ups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nps_alert_id = Column(UUID(as_uuid=True), ForeignKey("nps_alerts.id", ondelete="CASCADE"), nullable=False)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("location_feedback.id", ondelete="CASCADE"), nullable=False)

    # Contact info
    visitor_email = Column(String(255), nullable=True)
    visitor_phone = Column(String(20), nullable=True)

    # Follow-up task
    assigned_to_staff_id = Column(UUID(as_uuid=True), nullable=True)
    task_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to staff_tasks.id

    # Communication
    outreach_method = Column(String(50), default="email")  # email, sms, phone, in_app
    outreach_sent_at = Column(DateTime(timezone=True), nullable=True)
    response_received_at = Column(DateTime(timezone=True), nullable=True)
    response_content = Column(String(1000), nullable=True)

    # Re-survey schedule
    initial_nps = Column(Integer, nullable=False)
    resurvey_scheduled_for = Column(DateTime(timezone=True), nullable=False)  # 7 days post-resolution
    resurvey_sent = Column(Boolean, default=False)
    resurvey_response_at = Column(DateTime(timezone=True), nullable=True)
    resurvey_nps = Column(Integer, nullable=True)
    nps_improvement = Column(Integer, nullable=True)  # resurvey_nps - initial_nps

    # Resolution
    resolved = Column(Boolean, default=False)
    resolution_details = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_alert_follow_up", "nps_alert_id"),
    )
