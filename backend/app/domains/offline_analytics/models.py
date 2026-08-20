"""Phase 5D: Offline Analytics & Re-engagement."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base


class OfflineToOnlineAttribution(Base):
    __tablename__ = "offline_to_online_attribution"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    first_online_channel = Column(String(50), nullable=True)
    first_online_date = Column(DateTime(timezone.utc), nullable=True)
    location_visited_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=True)
    location_visit_date = Column(DateTime(timezone.utc), nullable=True)
    post_visit_order_date = Column(DateTime(timezone.utc), nullable=True)
    post_visit_order_value = Column(Float, default=0)
    time_to_conversion_days = Column(Integer, default=0)
    conversion_type = Column(String(50), nullable=False)  # online_to_offline, offline_to_online, full_loop
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class OfflineAnalyticsMetrics(Base):
    __tablename__ = "offline_analytics_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_foot_traffic = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    total_conversions_offline = Column(Integer, default=0)
    conversion_rate_offline = Column(Float, default=0)
    avg_dwell_time_minutes = Column(Float, default=0)
    total_revenue_from_visits = Column(Float, default=0)
    online_to_offline_conversions = Column(Integer, default=0)
    offline_to_online_conversions = Column(Integer, default=0)
    full_loop_conversions = Column(Integer, default=0)
    peak_traffic_hour = Column(Integer, default=0)
    repeat_visitor_rate = Column(Float, default=0)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LocationFootTrafficHourly(Base):
    __tablename__ = "location_foot_traffic_hourly"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    hour_of_day = Column(Integer, nullable=False)  # 0-23
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    avg_visitors = Column(Integer, default=0)
    peak_visitors = Column(Integer, default=0)
    total_visits_recorded = Column(Integer, default=0)
    avg_dwell_minutes = Column(Float, default=0)
    recorded_month = Column(String(50), nullable=False)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PostVisitSequence(Base):
    __tablename__ = "post_visit_sequences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_name = Column(String(255), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=True)
    trigger_type = Column(String(50), nullable=False)  # post_visit, no_purchase_visit, high_dwell
    is_active = Column(Boolean, default=True)
    email_count = Column(Integer, default=0)
    sms_count = Column(Integer, default=0)
    whatsapp_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class PostVisitSequenceExecution(Base):
    __tablename__ = "post_visit_sequence_executions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("post_visit_sequences.id", ondelete="CASCADE"), nullable=False)
    offline_conversion_id = Column(UUID(as_uuid=True), ForeignKey("offline_conversions.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="active")  # active, paused, completed, failed
    email_sent_count = Column(Integer, default=0)
    sms_sent_count = Column(Integer, default=0)
    whatsapp_sent_count = Column(Integer, default=0)
    engagement_count = Column(Integer, default=0)
    conversion_happened = Column(Boolean, default=False)
    conversion_value = Column(Float, default=0)
    started_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone.utc), nullable=True)
