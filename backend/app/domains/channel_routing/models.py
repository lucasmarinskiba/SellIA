"""Phase 3: Smart Channel Routing - Intelligent Message Delivery."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class ChannelAffinityModel(Base):
    __tablename__ = "channel_affinity_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Channel affinity scores (0-1, sum = 1)
    email_score = Column(Float, default=0.25)
    sms_score = Column(Float, default=0.15)
    whatsapp_score = Column(Float, default=0.20)
    phone_score = Column(Float, default=0.15)
    in_app_score = Column(Float, default=0.15)
    push_score = Column(Float, default=0.10)

    # Response metrics (learning)
    email_response_rate = Column(Float, default=0)
    sms_response_rate = Column(Float, default=0)
    whatsapp_response_rate = Column(Float, default=0)
    phone_response_rate = Column(Float, default=0)

    # Primary recommendation
    recommended_primary = Column(String(20), default="email")
    recommended_secondary = Column(String(20), default="sms")
    recommended_tertiary = Column(String(20), nullable=True)

    # Optimal send windows (hours, 0-23)
    email_best_hour = Column(Integer, default=10)  # 10 AM
    sms_best_hour = Column(Integer, default=14)    # 2 PM
    whatsapp_best_hour = Column(Integer, default=20)  # 8 PM
    phone_best_hour = Column(Integer, default=15)  # 3 PM

    # Opt-out channels (user preference)
    opted_out_channels = Column(JSONB, default=list)  # ["sms", "phone"]

    # Engagement trend
    email_trend = Column(String(20), default="stable")  # increasing, stable, declining
    sms_trend = Column(String(20), default="stable")
    engagement_trend_days = Column(Integer, default=30)  # window for trend calculation

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class MessageRouting(Base):
    __tablename__ = "message_routings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    message_template_id = Column(UUID(as_uuid=True), nullable=True)

    # Routing decision
    routed_to_channel = Column(String(20), nullable=False)  # email, sms, whatsapp, phone, in_app
    routed_reason = Column(String(100), nullable=True)  # "highest_affinity", "optimal_time", "preferred_channel"
    confidence_score = Column(Float, default=0)  # 0-1

    # Fallback channels if primary fails
    fallback_channel_1 = Column(String(20), nullable=True)
    fallback_channel_2 = Column(String(20), nullable=True)

    # Send window
    optimal_send_time = Column(DateTime(timezone=True), nullable=True)
    actual_send_time = Column(DateTime(timezone=True), nullable=True)

    # Response tracking
    was_delivered = Column(Boolean, default=False)
    was_opened = Column(Boolean, default=False)
    was_clicked = Column(Boolean, default=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)

    # Learning feedback
    response_time_seconds = Column(Integer, nullable=True)
    feedback_positive = Column(Boolean, nullable=True)  # True = good, False = bad, None = neutral

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class ChannelPerformanceMetrics(Base):
    __tablename__ = "channel_performance_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(20), nullable=False, index=True)  # email, sms, whatsapp, phone, in_app

    # Aggregate metrics
    total_messages_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_responses = Column(Integer, default=0)

    # Rates
    delivery_rate = Column(Float, default=0)
    open_rate = Column(Float, default=0)
    click_rate = Column(Float, default=0)
    response_rate = Column(Float, default=0)

    # Average metrics
    avg_response_time_seconds = Column(Integer, default=0)
    avg_engagement_score = Column(Float, default=0)

    # Cost metrics
    cost_per_message = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    cost_per_response = Column(Float, default=0)

    # Trend
    week_over_week_growth = Column(Float, default=0)
    quality_score = Column(Float, default=0)  # 0-100

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
