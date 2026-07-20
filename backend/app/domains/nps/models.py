"""
NPS & Feedback Widget Models
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class FeedbackNPSResponse(Base):
    """Net Promoter Score response."""
    __tablename__ = "feedback_nps_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)

    score = Column(Integer, nullable=False)  # 0-10
    feedback = Column(Text(), nullable=True)
    category = Column(String(50), nullable=True)  # product | support | onboarding | pricing

    # Follow-up
    follow_up_allowed = Column(Boolean, default=False, nullable=False)
    follow_up_email = Column(String(255), nullable=True)
    follow_up_done = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FeedbackItem(Base):
    """General feedback item."""
    __tablename__ = "general_feedback_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    feedback_type = Column(String(50), nullable=False)  # feature_request | bug | praise | complaint | other
    message = Column(Text(), nullable=False)
    context = Column(Text(), nullable=True)  # Where in the app
    screenshot_url = Column(String(500), nullable=True)

    status = Column(String(20), default="new", nullable=False)  # new | reviewed | in_progress | resolved | closed
    admin_response = Column(Text(), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
