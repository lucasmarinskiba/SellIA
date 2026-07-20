"""
Social Growth Toolkit Models

Helps users grow their Instagram, TikTok, and other social profiles.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class SocialProfileAudit(Base):
    """Audit of a user's social media profile (Instagram, TikTok, etc.)."""
    __tablename__ = "social_profile_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)

    platform = Column(String(50), nullable=False)  # instagram | tiktok | facebook | linkedin
    handle = Column(String(100), nullable=False)
    profile_url = Column(String(500), nullable=True)

    # Scores (0-100)
    bio_score = Column(Integer, default=0, nullable=False)
    content_score = Column(Integer, default=0, nullable=False)
    engagement_score = Column(Integer, default=0, nullable=False)
    consistency_score = Column(Integer, default=0, nullable=False)
    overall_score = Column(Integer, default=0, nullable=False)

    # Detailed findings
    findings = Column(JSONB, default=list, nullable=False)
    # [{"area": "bio", "issue": "No CTA in bio", "suggestion": "Add 'DM for info'", "priority": "high"}]

    recommendations = Column(JSONB, default=list, nullable=False)
    # [{"action": "Add Linktree", "expected_impact": "+15% click-through"}]

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ContentCalendarSlot(Base):
    """AI-suggested content calendar slot."""
    __tablename__ = "content_calendar_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)

    platform = Column(String(50), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    content_type = Column(String(50), nullable=False)  # reel | carousel | story | post
    topic = Column(String(255), nullable=False)
    caption_draft = Column(Text, nullable=True)
    hashtag_suggestions = Column(JSONB, default=list, nullable=False)
    best_time_reason = Column(Text, nullable=True)

    status = Column(String(20), default="suggested", nullable=False)  # suggested | approved | posted | skipped
    posted_at = Column(DateTime(timezone=True), nullable=True)
    performance_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CompetitorTracking(Base):
    """Track competitor social media accounts."""
    __tablename__ = "competitor_trackings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    platform = Column(String(50), nullable=False)
    competitor_handle = Column(String(100), nullable=False)
    competitor_name = Column(String(255), nullable=True)

    # Snapshot data
    follower_count = Column(Integer, nullable=True)
    avg_likes = Column(Integer, nullable=True)
    avg_comments = Column(Integer, nullable=True)
    post_frequency = Column(String(50), nullable=True)  # daily | 3x_week | weekly
    top_hashtags = Column(JSONB, default=list, nullable=False)
    content_themes = Column(JSONB, default=list, nullable=False)

    # Comparison to user
    user_follower_count = Column(Integer, nullable=True)
    gap_analysis = Column(Text, nullable=True)

    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
