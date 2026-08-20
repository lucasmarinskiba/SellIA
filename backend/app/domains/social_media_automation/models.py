"""Phase 46: Social Media Automation (Instagram, TikTok, Facebook)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class SocialMediaAccount(Base):
    __tablename__ = "social_media_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # instagram, tiktok, facebook, youtube
    account_handle = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=False)
    follower_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0)
    access_token = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class SocialPost(Base):
    __tablename__ = "social_posts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("social_media_accounts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    content = Column(Text, nullable=False)
    media_urls = Column(JSONB, nullable=True)
    hashtags = Column(JSONB, nullable=True)
    mentions = Column(JSONB, nullable=True)
    scheduled_at = Column(DateTime(timezone.utc), nullable=True)
    published_at = Column(DateTime(timezone.utc), nullable=True)
    status = Column(String(50), default="draft")  # draft, scheduled, published
    post_id = Column(String(255), nullable=True)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class FollowerGrowth(Base):
    __tablename__ = "follower_growth"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("social_media_accounts.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    follower_count = Column(Integer, default=0)
    daily_growth = Column(Integer, default=0)
    weekly_growth = Column(Integer, default=0)
    monthly_growth = Column(Integer, default=0)
    growth_rate = Column(Float, default=0)
    engagement_score = Column(Float, default=0)
    recorded_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ContentCalendar(Base):
    __tablename__ = "content_calendar"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("social_media_accounts.id", ondelete="CASCADE"), nullable=False)
    month = Column(String(50), nullable=False)
    planned_posts = Column(Integer, default=0)
    published_posts = Column(Integer, default=0)
    engagement_target = Column(Float, default=0)
    engagement_actual = Column(Float, default=0)
    reach_target = Column(Integer, default=0)
    reach_actual = Column(Integer, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class InfluencerCollaboration(Base):
    __tablename__ = "influencer_collaborations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    influencer_handle = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    follower_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0)
    niche = Column(String(255), nullable=False)
    collaboration_type = Column(String(50), nullable=False)  # sponsored_post, affiliate, product_gifting
    product_id = Column(UUID(as_uuid=True), nullable=True)
    budget = Column(Float, default=0)
    expected_reach = Column(Integer, default=0)
    status = Column(String(50), default="outreach")
    results = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
