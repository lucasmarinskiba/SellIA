"""Growth & Organic Acquisition Models

Inbound marketing, lead magnets, SEO content pipeline, value-first outreach,
social proof collection, UGC, and organic growth campaign tracking.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


# ========== Enums ==========

class GrowthCampaignType(str, enum.Enum):
    SEO_CONTENT = "seo_content"
    SOCIAL_ORGANIC = "social_organic"
    LEAD_MAGNET = "lead_magnet"
    REFERRAL_VIRAL = "referral_viral"
    EDUCATIONAL_NURTURE = "educational_nurture"
    UGC_CAMPAIGN = "ugc_campaign"
    COMMUNITY_ENGAGEMENT = "community_engagement"


class GrowthCampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class LeadMagnetFormat(str, enum.Enum):
    CHEAT_SHEET = "cheat_sheet"
    TEMPLATE = "template"
    CALCULATOR = "calculator"
    MINI_GUIDE = "mini_guide"
    QUIZ = "quiz"
    AUDIT = "audit"
    TOOLKIT = "toolkit"
    CHECKLIST = "checklist"
    EBOOK = "ebook"
    VIDEO_MINI = "video_mini"


class InboundLeadSource(str, enum.Enum):
    SEO = "seo"
    SOCIAL_POST = "social_post"
    LEAD_MAGNET = "lead_magnet"
    REFERRAL = "referral"
    COMMENT_DM = "comment_dm"
    STORY_REPLY = "story_reply"
    ORGANIC_SEARCH = "organic_search"
    DIRECT = "direct"
    COMMUNITY = "community"


class NurturingStage(str, enum.Enum):
    NEW = "new"
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    CONVERTED = "converted"
    DORMANT = "dormant"


class SocialProofType(str, enum.Enum):
    TESTIMONIAL = "testimonial"
    REVIEW = "review"
    CASE_STUDY = "case_study"
    RATING = "rating"
    VIDEO_TESTIMONIAL = "video_testimonial"
    BEFORE_AFTER = "before_after"
    UGC_PHOTO = "ugc_photo"
    UGC_VIDEO = "ugc_video"


class SocialProofStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class UgcRequestStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    RECEIVED = "received"
    APPROVED = "approved"
    REJECTED = "rejected"


# ========== Models ==========

class GrowthCampaign(Base):
    """An organic growth campaign with AI-generated content and distribution."""
    __tablename__ = "growth_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(Enum(GrowthCampaignType), nullable=False, index=True)
    status = Column(Enum(GrowthCampaignStatus), default=GrowthCampaignStatus.DRAFT, nullable=False)

    # Campaign configuration
    config = Column(JSONB, default=dict, nullable=False)
    # Example SEO config: {"target_keywords": [...], "content_count": 4, "platforms": ["blog", "linkedin"]}
    # Example referral config: {"incentive_type": "discount_credit", "reward_value": 20}

    # AI generation settings
    target_audience = Column(Text, nullable=True)
    content_pillars = Column(JSONB, default=list, nullable=False)
    tone_of_voice = Column(String(100), default="educational", nullable=False)

    # Metrics (denormalized for fast dashboard queries)
    leads_generated = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    revenue_attributed = Column(Numeric(14, 2), default=0, nullable=False)
    content_published = Column(Integer, default=0, nullable=False)
    engagement_score = Column(Numeric(5, 2), default=0, nullable=False)
    metrics_snapshot = Column(JSONB, default=dict, nullable=False)  # detailed metrics

    # Scheduling
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_growth_campaigns_business_type', 'business_id', 'campaign_type'),
        Index('ix_growth_campaigns_business_status', 'business_id', 'status'),
    )


class LeadMagnet(Base):
    """A lead magnet with auto-generated content, delivery tracking, and performance metrics."""
    __tablename__ = "lead_magnets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("growth_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    format = Column(Enum(LeadMagnetFormat), nullable=False)
    topic = Column(String(200), nullable=False)

    # Generated content
    content = Column(JSONB, default=dict, nullable=False)
    # Example: {"sections": [...], "download_url": "...", "preview_text": "..."}
    landing_page_copy = Column(Text, nullable=True)
    delivery_message = Column(Text, nullable=True)
    call_to_action = Column(String(200), nullable=True)

    # Performance
    times_delivered = Column(Integer, default=0, nullable=False)
    times_downloaded = Column(Integer, default=0, nullable=False)
    times_converted = Column(Integer, default=0, nullable=False)
    conversion_rate = Column(Numeric(5, 2), default=0, nullable=False)  # 0-100
    engagement_score = Column(Numeric(5, 2), default=0, nullable=False)

    # Delivery settings
    auto_deliver = Column(Boolean, default=True, nullable=False)
    delivery_channel = Column(String(50), default="whatsapp", nullable=False)  # whatsapp, instagram, email
    delivery_trigger = Column(String(50), default="new_lead", nullable=False)  # new_lead, keyword, tag_added

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_lead_magnets_business_format', 'business_id', 'format'),
        Index('ix_lead_magnets_business_active', 'business_id', 'is_active'),
    )


class InboundLead(Base):
    """A lead captured through organic channels with full attribution and nurturing tracking."""
    __tablename__ = "inbound_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("growth_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    lead_magnet_id = Column(UUID(as_uuid=True), ForeignKey("lead_magnets.id", ondelete="SET NULL"), nullable=True, index=True)

    # Attribution
    source_type = Column(Enum(InboundLeadSource), nullable=False, index=True)
    source_detail = Column(String(200), nullable=True)  # e.g., "blog_post: como-vender-sin-vender"
    source_campaign_id = Column(UUID(as_uuid=True), ForeignKey("growth_campaigns.id", ondelete="SET NULL"), nullable=True)
    referral_code_id = Column(UUID(as_uuid=True), ForeignKey("referral_codes.id", ondelete="SET NULL"), nullable=True)

    # Contact info (snapshot at capture time)
    contact_info = Column(JSONB, default=dict, nullable=False)
    # {"name": "...", "email": "...", "phone": "...", "instagram": "..."}

    # Nurturing
    nurturing_stage = Column(Enum(NurturingStage), default=NurturingStage.NEW, nullable=False, index=True)
    engagement_score = Column(Integer, default=0, nullable=False)
    value_touches_received = Column(Integer, default=0, nullable=False)  # jab count
    sales_touches_received = Column(Integer, default=0, nullable=False)  # right-hook count

    # Conversion tracking
    first_touch_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_touch_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    converted_at = Column(DateTime(timezone=True), nullable=True)
    converted_to_deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index('ix_inbound_leads_business_source', 'business_id', 'source_type'),
        Index('ix_inbound_leads_business_stage', 'business_id', 'nurturing_stage'),
        Index('ix_inbound_leads_conversation', 'conversation_id'),
    )


class SocialProofItem(Base):
    """Testimonials, reviews, UGC, and case studies collected automatically from customers."""
    __tablename__ = "social_proofs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)

    item_type = Column(Enum(SocialProofType), nullable=False)
    status = Column(Enum(SocialProofStatus), default=SocialProofStatus.PENDING, nullable=False)

    # Content
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 for reviews
    headline = Column(String(300), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_photo_url = Column(String(500), nullable=True)
    media_urls = Column(JSONB, default=list, nullable=False)  # photos, videos

    # AI analysis
    sentiment_score = Column(Numeric(4, 3), default=0, nullable=False)  # -1.0 to 1.0
    ai_summary = Column(Text, nullable=True)
    key_quotes = Column(JSONB, default=list, nullable=False)
    themes_detected = Column(JSONB, default=list, nullable=False)

    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    used_in_campaigns = Column(JSONB, default=list, nullable=False)

    # Moderation
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # user_id or null for auto
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_social_proofs_business_type', 'business_id', 'item_type'),
        Index('ix_social_proofs_business_status', 'business_id', 'status'),
        Index('ix_social_proofs_business_sentiment', 'business_id', 'sentiment_score'),
    )


class UgcRequest(Base):
    """Tracks user-generated content requests sent to customers."""
    __tablename__ = "ugc_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("growth_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)

    # Request
    content_type = Column(String(50), nullable=False)  # unboxing, before_after, testimonial_video, lifestyle_photo, story
    request_message = Column(Text, nullable=False)
    incentive_offered = Column(String(200), nullable=True)  # e.g., "10% off next purchase"

    # Response
    status = Column(Enum(UgcRequestStatus), default=UgcRequestStatus.PENDING, nullable=False)
    response_media_urls = Column(JSONB, default=list, nullable=False)
    response_text = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Linked social proof item (if approved)
    social_proof_id = Column(UUID(as_uuid=True), ForeignKey("social_proofs.id", ondelete="SET NULL"), nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_ugc_requests_business_status', 'business_id', 'status'),
        Index('ix_ugc_requests_order', 'order_id'),
    )


class ValueSequence(Base):
    """An educational/value-first nurturing sequence (Jab-Jab-Jab-Right-Hook)."""
    __tablename__ = "value_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("growth_campaigns.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(200), nullable=False)
    topic = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Sequence configuration
    messages = Column(JSONB, default=list, nullable=False)
    # [{"order": 1, "content": "...", "delay_hours": 24, "type": "value"}, ...]
    message_count = Column(Integer, default=3, nullable=False)
    total_duration_days = Column(Integer, default=7, nullable=False)

    # Targeting
    target_segment = Column(String(50), default="cold", nullable=False)  # cold, warm, hot
    target_source = Column(String(50), nullable=True)  # filter by source_type

    # Performance
    times_started = Column(Integer, default=0, nullable=False)
    times_completed = Column(Integer, default=0, nullable=False)
    conversion_rate = Column(Numeric(5, 2), default=0, nullable=False)
    avg_engagement_score = Column(Numeric(5, 2), default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_value_sequences_business_active', 'business_id', 'is_active'),
    )


class ValueSequenceEnrollment(Base):
    """Tracks individual contact enrollment in a value sequence."""
    __tablename__ = "value_sequence_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("value_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    inbound_lead_id = Column(UUID(as_uuid=True), ForeignKey("inbound_leads.id", ondelete="SET NULL"), nullable=True)

    current_step = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, default=3, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, completed, paused, cancelled

    # Engagement
    messages_sent = Column(Integer, default=0, nullable=False)
    messages_read = Column(Integer, default=0, nullable=False)
    messages_replied = Column(Integer, default=0, nullable=False)
    last_engagement_at = Column(DateTime(timezone=True), nullable=True)

    # Conversion
    converted_at = Column(DateTime(timezone=True), nullable=True)
    converted_to_deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_value_enrollments_sequence', 'sequence_id', 'status'),
        Index('ix_value_enrollments_conversation', 'conversation_id'),
    )
