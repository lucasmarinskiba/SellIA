"""Phase 41: Marketing Intelligence - Department Orchestration."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class MarketSegment(Base):
    __tablename__ = "market_segments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_name = Column(String(255), nullable=False)
    target_profile = Column(JSONB, nullable=True)
    market_size = Column(Integer, default=0)
    growth_rate = Column(Float, default=0)
    market_share = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class CampaignOrchestration(Base):
    __tablename__ = "campaign_orchestration"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    campaign_type = Column(String(100), nullable=False)  # email, social, content, paid_ads, etc
    target_segment = Column(String(255), nullable=True)
    budget_allocated = Column(Float, default=0)
    expected_roi = Column(Float, default=0)
    channels = Column(JSONB, nullable=True)
    messaging = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class ContentStrategy(Base):
    __tablename__ = "content_strategy"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    content_type = Column(String(100), nullable=False)  # blog, video, whitepaper, case_study, webinar
    topic = Column(String(255), nullable=False)
    target_stage = Column(String(50), nullable=False)  # awareness, consideration, decision
    target_audience = Column(String(255), nullable=True)
    key_messages = Column(JSONB, nullable=True)
    content_url = Column(String(500), nullable=True)
    engagement_metrics = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class BrandDifferentiation(Base):
    __tablename__ = "brand_differentiation"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    unique_value_proposition = Column(Text, nullable=True)
    key_differentiators = Column(JSONB, nullable=True)
    competitor_comparison = Column(JSONB, nullable=True)
    brand_positioning = Column(Text, nullable=True)
    messaging_framework = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class LeadNurturing(Base):
    __tablename__ = "lead_nurturing"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nurture_track = Column(String(100), nullable=False)
    current_step = Column(Integer, default=0)
    engagement_score = Column(Float, default=0)
    next_action = Column(String(255), nullable=True)
    last_interaction = Column(DateTime(timezone.utc), nullable=True)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

class MarketingMetrics(Base):
    __tablename__ = "marketing_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_campaigns = Column(Integer, default=0)
    total_leads_generated = Column(Integer, default=0)
    cost_per_lead = Column(Float, default=0)
    lead_to_sql_conversion = Column(Float, default=0)
    marketing_attribution_revenue = Column(Float, default=0)
    campaign_roi = Column(Float, default=0)
    customer_acquisition_cost = Column(Float, default=0)
    marketing_qualified_leads = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PromoStrategy(Base):
    __tablename__ = "promo_strategy"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    promo_type = Column(String(100), nullable=False)  # discount, bundle, loyalty, limited_time
    description = Column(Text, nullable=True)
    discount_percentage = Column(Float, default=0)
    valid_until = Column(DateTime(timezone.utc), nullable=True)
    target_segment = Column(String(255), nullable=True)
    expected_lift = Column(Float, default=0)
    revenue_impact = Column(Float, default=0)
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
