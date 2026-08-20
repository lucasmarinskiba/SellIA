"""Phase 5C: Location Channel Integration (Google Business Profile, Maps, etc)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base


class GoogleBusinessProfileConnection(Base):
    __tablename__ = "google_business_profile_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    google_business_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    account_name = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    sync_enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class GoogleMapsLocation(Base):
    __tablename__ = "google_maps_locations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    place_id = Column(String(255), nullable=False)
    rating = Column(Float, default=0)
    review_count = Column(Integer, default=0)
    phone = Column(String(20), nullable=True)
    website = Column(String(500), nullable=True)
    photos_count = Column(Integer, default=0)
    average_visit_duration_minutes = Column(Integer, default=0)
    popular_times_json = Column(JSONB, nullable=True)  # {mon: [9,10,11], tue: [14,15,16], ...}
    last_updated = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class LocationMessage(Base):
    __tablename__ = "location_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False)  # sms, whatsapp, email
    trigger_type = Column(String(50), nullable=False)  # proximity, visit_reminder, post_visit, offer
    template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))


class LocationMessageExecution(Base):
    __tablename__ = "location_message_executions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("location_messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    channel = Column(String(50), nullable=False)
    message_content = Column(Text, nullable=False)
    status = Column(String(50), default="sent")  # sent, delivered, opened, clicked, failed
    sent_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime(timezone.utc), nullable=True)
    opened_at = Column(DateTime(timezone.utc), nullable=True)
    clicked_at = Column(DateTime(timezone.utc), nullable=True)


class LocationReview(Base):
    __tablename__ = "location_reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location_profiles.id", ondelete="CASCADE"), nullable=False)
    reviewer_name = Column(String(255), nullable=False)
    rating = Column(Float, nullable=False)  # 1-5
    review_text = Column(Text, nullable=True)
    platform = Column(String(50), nullable=False)  # google, facebook, trustpilot, etc
    review_url = Column(String(500), nullable=True)
    review_date = Column(DateTime(timezone.utc), nullable=True)
    response_text = Column(Text, nullable=True)
    response_date = Column(DateTime(timezone.utc), nullable=True)
    synced_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
