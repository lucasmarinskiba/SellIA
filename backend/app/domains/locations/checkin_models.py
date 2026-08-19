"""Location check-in models — staff + customer app integrations."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class CheckinType(str, Enum):
    """Type of check-in."""
    QR_SCAN = "qr_scan"
    MANUAL_ENTRY = "manual_entry"
    GEOFENCE = "geofence"
    APPOINTMENT = "appointment"
    STAFF_CHECKIN = "staff_checkin"


class CheckinStatus(str, Enum):
    """Check-in status lifecycle."""
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    ABANDONED = "abandoned"  # Checked in but never checked out (timeout)


class LocationCheckin(Base):
    """Track visitor/staff check-ins at locations."""
    __tablename__ = "location_checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Who checked in
    checkin_type = Column(SQLEnum(CheckinType), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Registered customer
    visitor_phone = Column(String(20), nullable=True)
    visitor_email = Column(String(255), nullable=True)
    visitor_name = Column(String(255), nullable=True)

    # QR / device info
    qr_code = Column(String(255), nullable=True)
    device_id = Column(String(255), nullable=True)
    app_version = Column(String(50), nullable=True)

    # Timeline
    checkin_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    checkout_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(CheckinStatus), default=CheckinStatus.CHECKED_IN, nullable=False)

    # Engagement
    dwell_seconds = Column(Integer, nullable=True)  # Will be calculated at checkout
    visited_sections = Column(JSONB, default=list, nullable=False)  # e.g., ["showroom", "demo_area", "checkout"]

    # Metadata
    entry_source = Column(String(100), nullable=True)  # "door", "mobility_app", "web", etc
    metadata = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    location = relationship("Location", foreign_keys=[location_id])


class StaffCheckin(Base):
    """Track staff shifts at locations."""
    __tablename__ = "staff_checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    staff_id = Column(UUID(as_uuid=True), nullable=False)  # User ID
    staff_name = Column(String(255), nullable=False)
    staff_email = Column(String(255), nullable=True)
    staff_role = Column(String(100), nullable=False)  # "sales", "manager", "demo_specialist", etc

    checkin_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    checkout_time = Column(DateTime(timezone=True), nullable=True)

    # Performance
    visitors_engaged = Column(Integer, default=0)  # How many visitors did staff help
    demos_conducted = Column(Integer, default=0)
    sales_assisted = Column(Integer, default=0)
    nps_feedback = Column(Integer, nullable=True)  # avg NPS this shift

    notes = Column(String(1000), nullable=True)
    metadata = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    location = relationship("Location", foreign_keys=[location_id])


class LocationFeedback(Base):
    """Real-time feedback from visitors at location."""
    __tablename__ = "location_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    checkin_id = Column(UUID(as_uuid=True), ForeignKey("location_checkins.id", ondelete="SET NULL"), nullable=True)
    staff_id = Column(UUID(as_uuid=True), nullable=True)

    # Feedback data
    nps_score = Column(Integer, nullable=True)  # 0-10
    sentiment = Column(String(20), nullable=True)  # "positive", "neutral", "negative"
    comment = Column(String(1000), nullable=True)

    # Tags
    topics = Column(JSONB, default=list)  # e.g., ["staff_friendliness", "product_quality", "wait_time"]

    # Resolution
    requires_followup = Column(Boolean, default=False)
    followup_assigned_to = Column(UUID(as_uuid=True), nullable=True)  # Staff member
    resolved = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    location = relationship("Location", foreign_keys=[location_id])
