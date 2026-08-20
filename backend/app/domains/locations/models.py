"""Phase 5A: Local-First Funnel - Location Profiles & Configuration."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base


class LocationProfile(Base):
    __tablename__ = "location_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    hours_json = Column(JSONB, nullable=True)  # {mon: "9:00-18:00", tue: "9:00-18:00", ...}
    location_type = Column(String(50), nullable=False)  # showroom, factory, office, warehouse, retail
    capacity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    geofence_radius_km = Column(Float, default=5)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class BusinessModel(Base):
    __tablename__ = "business_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    model_class = Column(String(50), nullable=False)  # ONLINE_ONLY, HYBRID_LIGHT, HYBRID_HEAVY, OFFLINE_FIRST
    model_confidence = Column(Float, default=0)  # 0-1 confidence score
    locations_count = Column(Integer, default=0)
    has_online_presence = Column(Boolean, default=False)
    has_physical_location = Column(Boolean, default=False)
    detected_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ProximityEvent(Base):
    __tablename__ = "proximity_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    distance_km = Column(Float, nullable=False)
    triggered_automation_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String(50), default="proximity_detected")  # proximity_detected, entered_geofence, exited_geofence
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class OfflineConversion(Base):
    __tablename__ = "offline_conversions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True)
    visit_type = Column(String(50), nullable=False)  # visit, demo, in_store_pickup, service_appointment, tour
    entry_method = Column(String(50), nullable=True)  # qr_scan, staff_log, geo_detection, manual
    phone = Column(String(20), nullable=True)  # For fuzzy matching
    email = Column(String(255), nullable=True)
    entry_time = Column(DateTime(timezone.utc), nullable=True)
    exit_time = Column(DateTime(timezone.utc), nullable=True)
    dwell_minutes = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    matched_to_customer = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class LocationVisit(Base):
    __tablename__ = "location_visits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    entry_time = Column(DateTime(timezone.utc), nullable=False)
    exit_time = Column(DateTime(timezone.utc), nullable=True)
    dwell_minutes = Column(Integer, default=0)
    entry_channel = Column(String(50), nullable=True)  # qr, staff, geo
    categories_browsed = Column(ARRAY(String), nullable=True)
    items_viewed = Column(Integer, default=0)
    purchase_made = Column(Boolean, default=False)
    purchase_value = Column(Float, default=0)
    staff_interaction = Column(Boolean, default=False)
    recorded_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
