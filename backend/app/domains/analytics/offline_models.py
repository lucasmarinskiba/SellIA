"""Offline conversion tracking models — visits, demos, pickups, service calls."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class VisitType(str, Enum):
    """Type of physical location visit."""
    WALK_IN = "walk_in"
    QR_SCAN = "qr_scan"
    SCHEDULED_DEMO = "scheduled_demo"
    SCHEDULED_TOUR = "scheduled_tour"
    SCHEDULED_APPOINTMENT = "scheduled_appointment"
    MANUAL_CHECKIN = "manual_checkin"
    GEOFENCE_ENTRY = "geofence_entry"


class DemographicSource(str, Enum):
    """How visitor was identified."""
    PHONE_MATCH = "phone_match"  # Fuzzy match on phone
    EMAIL_MATCH = "email_match"  # Exact email match
    GPS_MATCH = "gps_match"  # GPS + address match
    QR_DATA = "qr_data"  # QR code embedded data
    MANUAL_ENTRY = "manual_entry"  # Staff entered data
    GEOFENCE = "geofence"  # Geofence + IP match


class OfflineConversion(Base):
    """Track offline visits, demos, pickups, and in-store conversions."""
    __tablename__ = "offline_conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)

    # Visit details
    visit_type = Column(SQLEnum(VisitType), nullable=False, default=VisitType.WALK_IN)

    # Visitor identification (optional — may not have full data)
    visitor_phone = Column(String(20), nullable=True)
    visitor_email = Column(String(255), nullable=True)
    visitor_name = Column(String(255), nullable=True)

    # Location/device info at visit time
    visitor_latitude = Column(Float, nullable=True)
    visitor_longitude = Column(Float, nullable=True)
    visitor_ip_address = Column(String(50), nullable=True)

    # Match quality
    demographic_source = Column(SQLEnum(DemographicSource), nullable=True)
    confidence_score = Column(DECIMAL(3, 2), default=0, nullable=False)  # 0-1.0 confidence this is the right person

    # Visit timeline
    entry_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    exit_time = Column(DateTime(timezone=True), nullable=True)
    dwell_minutes = Column(Integer, nullable=True)

    # Outcome
    purchased = Column(Boolean, default=False, nullable=False)
    purchase_amount = Column(DECIMAL(14, 2), nullable=True)
    contact_collected = Column(Boolean, default=False, nullable=False)

    # Link to online lead/customer
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)

    # Notes + metadata
    staff_notes = Column(Text, nullable=True)
    visit_metadata = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    location = relationship("Location", foreign_keys=[location_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    order = relationship("Order", foreign_keys=[order_id])

    __table_args__ = (
        Index('idx_offline_conversions_business_date', 'business_id', 'created_at'),
        Index('idx_offline_conversions_location_date', 'location_id', 'created_at'),
        Index('idx_offline_conversions_phone', 'visitor_phone'),
        Index('idx_offline_conversions_email', 'visitor_email'),
        Index('idx_offline_conversions_conversation', 'conversation_id'),
    )


class GeoProximityEvent(Base):
    """Track when proximity automation is triggered for user."""
    __tablename__ = "geo_proximity_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)

    # User identification
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    visitor_phone = Column(String(20), nullable=True)
    visitor_email = Column(String(255), nullable=True)

    # Location data at event time
    user_latitude = Column(Float, nullable=False)
    user_longitude = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)

    # Trigger information
    trigger_name = Column(String(100), nullable=False)  # "proximity_check_nearby", "location_visit_detected", etc
    automation_id = Column(UUID(as_uuid=True), nullable=True)  # automation that will/was triggered

    # Outcome
    automation_triggered = Column(Boolean, default=False, nullable=False)
    automation_executed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    location = relationship("Location", foreign_keys=[location_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])

    __table_args__ = (
        Index('idx_proximity_events_business_date', 'business_id', 'created_at'),
        Index('idx_proximity_events_location_date', 'location_id', 'created_at'),
        Index('idx_proximity_events_trigger', 'trigger_name'),
    )


class LocationVisitMetric(Base):
    """Aggregated daily metrics per location for analytics."""
    __tablename__ = "location_visit_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)

    metric_date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Foot traffic
    total_visits = Column(Integer, default=0, nullable=False)
    walk_in_visits = Column(Integer, default=0, nullable=False)
    qr_scans = Column(Integer, default=0, nullable=False)
    scheduled_visits = Column(Integer, default=0, nullable=False)  # demos, tours, appointments

    # Conversions
    visitors_converted = Column(Integer, default=0, nullable=False)
    total_purchase_value = Column(DECIMAL(14, 2), default=0, nullable=False)
    avg_purchase_value = Column(DECIMAL(14, 2), default=0, nullable=False)

    # Engagement
    avg_dwell_minutes = Column(Integer, default=0, nullable=False)
    contact_collection_rate = Column(DECIMAL(5, 4), default=0, nullable=False)  # 0-1.0

    # Foot traffic by hour (heatmap data)
    hourly_visits_json = Column(JSONB, default=dict, nullable=False)  # {"09": 5, "10": 8, ...}

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index('idx_location_metrics_business_date', 'business_id', 'metric_date'),
        Index('idx_location_metrics_location_date', 'location_id', 'metric_date'),
    )
