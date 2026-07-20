"""
Product Tour & Interactive Onboarding Models
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class TourStep(Base):
    """A single step in a product tour."""
    __tablename__ = "tour_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(String(50), nullable=False, index=True)  # onboarding_v2 | new_feature_x
    step_order = Column(Integer, nullable=False)

    title = Column(String(255), nullable=False)
    content = Column(Text(), nullable=False)
    target_element = Column(String(255), nullable=True)  # CSS selector
    placement = Column(String(20), default="bottom", nullable=False)  # top | bottom | left | right | center

    # Actions
    action_type = Column(String(50), nullable=True)  # click | input | wait | none
    action_target = Column(String(255), nullable=True)
    delay_ms = Column(Integer, default=0, nullable=False)

    # Visual
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    accent_color = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class UserTourProgress(Base):
    """Tracks which tours a user has completed."""
    __tablename__ = "user_tour_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tour_id = Column(String(50), nullable=False, index=True)

    current_step = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    is_skipped = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Context
    started_from_page = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
