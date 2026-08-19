"""Location profile models for physical business locations.

Supports: showrooms, retail stores, factories, offices, service centers, pickup points.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LocationType(str, Enum):
    """Type of physical location."""
    SHOWROOM = "showroom"
    RETAIL_STORE = "retail_store"
    SERVICE_CENTER = "service_center"
    FACTORY = "factory"
    OFFICE = "office"
    WAREHOUSE = "warehouse"
    PICKUP_POINT = "pickup_point"
    HEADQUARTERS = "headquarters"


class LocalizationModel(str, Enum):
    """Business localization strategy."""
    ONLINE_ONLY = "online_only"
    HYBRID_LIGHT = "hybrid_light"        # ~20% foot traffic impact
    HYBRID_HEAVY = "hybrid_heavy"        # ~50% foot traffic impact
    OFFLINE_FIRST = "offline_first"      # >80% foot traffic impact


class Location(Base):
    """Physical location of a business."""
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Identification
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(LocationType), nullable=False, default=LocationType.RETAIL_STORE)

    # Address
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country_code = Column(String(2), nullable=False, default="AR")

    # Coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Operating info
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website_url = Column(String(500), nullable=True)
    google_maps_url = Column(String(1000), nullable=True)
    gmb_id = Column(String(255), nullable=True, index=True)  # Google Business Profile ID

    # Hours of operation (JSON: {"monday": {"open": "09:00", "close": "18:00"}, ...})
    hours_json = Column(JSON, default=dict, nullable=False)

    # Capacity & attributes
    capacity = Column(String(100), nullable=True)  # e.g., "50 pax", "10 workstations"
    wheelchair_accessible = Column(Boolean, default=False)
    parking_available = Column(Boolean, default=False)
    has_wifi = Column(Boolean, default=False)

    # Operational settings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    allows_walk_ins = Column(Boolean, default=True)
    allows_appointments = Column(Boolean, default=True)
    allows_pickups = Column(Boolean, default=False)
    allows_demos = Column(Boolean, default=False)

    # Service zones
    service_radius_km = Column(Float, nullable=True)  # delivery/service radius

    # Metadata
    metadata = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    business = relationship("Business", back_populates="locations")

    __table_args__ = (
        Index('idx_locations_business_active', 'business_id', 'is_active'),
        Index('idx_locations_city', 'city'),
        Index('idx_locations_gmb', 'gmb_id'),
    )


# ============================================================
# Pydantic schemas for API
# ============================================================

class LocationHours(BaseModel):
    """Operating hours for a single day."""
    open: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    close: str = Field(..., pattern=r"^\d{2}:\d{2}$")

    class Config:
        json_schema_extra = {
            "example": {
                "open": "09:00",
                "close": "18:00"
            }
        }


class LocationHoursWeekly(BaseModel):
    """Operating hours for a full week."""
    monday: Optional[LocationHours] = None
    tuesday: Optional[LocationHours] = None
    wednesday: Optional[LocationHours] = None
    thursday: Optional[LocationHours] = None
    friday: Optional[LocationHours] = None
    saturday: Optional[LocationHours] = None
    sunday: Optional[LocationHours] = None

    class Config:
        json_schema_extra = {
            "example": {
                "monday": {"open": "09:00", "close": "18:00"},
                "tuesday": {"open": "09:00", "close": "18:00"},
                "wednesday": {"open": "09:00", "close": "18:00"},
                "thursday": {"open": "09:00", "close": "18:00"},
                "friday": {"open": "09:00", "close": "18:00"},
                "saturday": {"open": "10:00", "close": "14:00"},
                "sunday": None
            }
        }


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: LocationType
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    state_province: str | None = None
    postal_code: str | None = None
    country_code: str = "AR"
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    phone: str | None = None
    email: str | None = None
    website_url: str | None = None
    gmb_id: str | None = None
    hours_json: LocationHoursWeekly
    capacity: str | None = None
    wheelchair_accessible: bool = False
    parking_available: bool = False
    has_wifi: bool = False
    allows_walk_ins: bool = True
    allows_appointments: bool = True
    allows_pickups: bool = False
    allows_demos: bool = False
    service_radius_km: float | None = None
    metadata: dict = Field(default_factory=dict)


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = None
    type: LocationType | None = None
    address: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    phone: str | None = None
    email: str | None = None
    website_url: str | None = None
    gmb_id: str | None = None
    hours_json: LocationHoursWeekly | None = None
    capacity: str | None = None
    wheelchair_accessible: bool | None = None
    parking_available: bool | None = None
    has_wifi: bool | None = None
    allows_walk_ins: bool | None = None
    allows_appointments: bool | None = None
    allows_pickups: bool | None = None
    allows_demos: bool | None = None
    service_radius_km: float | None = None
    is_active: bool | None = None
    metadata: dict | None = None


class LocationResponse(LocationBase):
    id: uuid.UUID
    business_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationProfileResponse(BaseModel):
    """Profile combining location info with foot-traffic metrics."""
    location: LocationResponse
    visitor_count_monthly: int = 0
    conversion_rate_offline: float = 0.0
    avg_dwell_time_minutes: int = 0
    peak_hours: list[str] = []
