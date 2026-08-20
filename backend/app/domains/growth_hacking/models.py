"""Phase 50: Growth Hacking Engine - Viral Campaigns & Traffic Generation."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base

class ViralCampaign(Base):
    __tablename__ = "viral_campaigns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # hashtag, challenge, meme, giveaway
    platforms = Column(ARRAY(String), nullable=True)
    target_audience = Column(String(255), nullable=False)
    budget = Column(Float, default=0)
    expected_reach = Column(Integer, default=0)
    expected_engagement_rate = Column(Float, default=0)
    actual_reach = Column(Integer, default=0)
    actual_engagement_rate = Column(Float, default=0)
    shares = Column(Integer, default=0)
    mentions = Column(Integer, default=0)
    virality_score = Column(Float, default=0)
    status = Column(String(50), default="planning")
    started_at = Column(DateTime(timezone.utc), nullable=True)
    ended_at = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class TrafficSource(Base):
    __tablename__ = "traffic_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)  # organic, paid, social, referral, direct
    source_name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    monthly_visitors = Column(Integer, default=0)
    monthly_conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0)
    average_order_value = Column(Float, default=0)
    monthly_revenue = Column(Float, default=0)
    cost_per_acquisition = Column(Float, default=0)
    roi = Column(Float, default=0)
    growth_rate = Column(Float, default=0)
    tracked_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class FollowerGrowthHacking(Base):
    __tablename__ = "follower_growth_hacking"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    platform = Column(String(50), nullable=False)
    growth_tactic = Column(String(100), nullable=False)  # hashtag_strategy, engagement_pods, viral_content, etc
    monthly_target = Column(Integer, default=0)
    actual_growth = Column(Integer, default=0)
    engagement_increase = Column(Float, default=0)
    reach_increase = Column(Float, default=0)
    conversion_to_sales = Column(Integer, default=0)
    cost_per_follower = Column(Float, default=0)
    effectiveness_score = Column(Float, default=0)
    month = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ReferralProgram(Base):
    __tablename__ = "referral_programs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    program_name = Column(String(255), nullable=False)
    reward_type = Column(String(50), nullable=False)  # commission, discount, credit
    reward_amount = Column(Float, default=0)
    referrer_reward = Column(Float, default=0)
    referee_reward = Column(Float, default=0)
    active_referrers = Column(Integer, default=0)
    total_referrals = Column(Integer, default=0)
    successful_conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0)
    total_revenue_generated = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class GrowthMetrics(Base):
    __tablename__ = "growth_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    monthly_revenue = Column(Float, default=0)
    monthly_growth_rate = Column(Float, default=0)
    quarterly_growth = Column(Float, default=0)
    yearly_growth = Column(Float, default=0)
    customer_acquisition_rate = Column(Integer, default=0)
    customer_retention_rate = Column(Float, default=0)
    viral_coefficient = Column(Float, default=0)
    doubling_time_days = Column(Integer, default=0)
    market_penetration = Column(Float, default=0)
    revenue_per_channel = Column(JSONB, nullable=True)
    top_performing_tactics = Column(ARRAY(String), nullable=True)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PartnershipProgram(Base):
    __tablename__ = "partnership_programs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    partner_name = Column(String(255), nullable=False)
    partner_type = Column(String(50), nullable=False)  # influencer, affiliate, co-marketing, distribution
    partner_audience_size = Column(Integer, default=0)
    partnership_value = Column(Float, default=0)
    expected_reach = Column(Integer, default=0)
    actual_reach = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0)
    roi = Column(Float, default=0)
    satisfaction_rating = Column(Float, default=0)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
