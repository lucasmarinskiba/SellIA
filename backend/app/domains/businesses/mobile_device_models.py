"""Device tokens for the mobile SDKs. Only the SHA-256 of a token is stored; the raw value is shown once, at issue."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MobileDeviceToken(Base):
    __tablename__ = "mobile_device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    # NULL: valid for every location of the business. Set: valid for that location only.
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=True)
    label = Column(String(120), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)
    scopes = Column(JSON, nullable=False, default=list)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
