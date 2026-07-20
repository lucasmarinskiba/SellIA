"""Growth Domain Pydantic Schemas"""

import uuid
from datetime import datetime
from typing import Optional, Any, List
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ========== GrowthCampaign ==========

class GrowthCampaignCreate(BaseModel):
    name: str
    campaign_type: str
    description: Optional[str] = ""
    config: Optional[dict] = {}
    target_audience: Optional[str] = ""
    content_pillars: Optional[List[str]] = []
    tone_of_voice: Optional[str] = "educational"


class GrowthCampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None
    target_audience: Optional[str] = None
    content_pillars: Optional[List[str]] = None
    tone_of_voice: Optional[str] = None
    is_active: Optional[bool] = None


class GrowthCampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    description: Optional[str]
    campaign_type: str
    status: str
    config: dict
    target_audience: Optional[str]
    content_pillars: List[str]
    tone_of_voice: str
    leads_generated: int
    conversions: int
    revenue_attributed: Decimal
    content_published: int
    engagement_score: Decimal
    metrics_snapshot: dict
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ========== LeadMagnet ==========

class LeadMagnetCreate(BaseModel):
    topic: str
    magnet_format: Optional[str] = "cheat_sheet"
    target_audience: Optional[str] = ""
    campaign_id: Optional[uuid.UUID] = None


class LeadMagnetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    campaign_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    format: str
    topic: str
    content: dict
    landing_page_copy: Optional[str]
    delivery_message: Optional[str]
    call_to_action: Optional[str]
    times_delivered: int
    times_downloaded: int
    times_converted: int
    conversion_rate: Decimal
    engagement_score: Decimal
    auto_deliver: bool
    delivery_channel: str
    delivery_trigger: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LeadMagnetPerformance(BaseModel):
    magnet_id: uuid.UUID
    title: str
    format: str
    times_delivered: int
    times_downloaded: int
    times_converted: int
    conversion_rate: float
    engagement_score: float
    is_active: bool


# ========== InboundLead ==========

class InboundLeadCreate(BaseModel):
    source_type: str
    conversation_id: Optional[uuid.UUID] = None
    campaign_id: Optional[uuid.UUID] = None
    lead_magnet_id: Optional[uuid.UUID] = None
    contact_info: Optional[dict] = {}
    source_detail: Optional[str] = ""


class InboundLeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    conversation_id: Optional[uuid.UUID]
    campaign_id: Optional[uuid.UUID]
    lead_magnet_id: Optional[uuid.UUID]
    source_type: str
    source_detail: Optional[str]
    contact_info: dict
    nurturing_stage: str
    engagement_score: int
    value_touches_received: int
    sales_touches_received: int
    first_touch_at: datetime
    last_touch_at: datetime
    converted_at: Optional[datetime]
    is_active: bool


# ========== SocialProof ==========

class SocialProofCreate(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    order_id: Optional[uuid.UUID] = None
    item_type: str
    content: str
    rating: Optional[int] = None
    customer_name: Optional[str] = None
    media_urls: Optional[List[str]] = []


class SocialProofResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    conversation_id: Optional[uuid.UUID]
    order_id: Optional[uuid.UUID]
    item_type: str
    status: str
    content: str
    rating: Optional[int]
    headline: Optional[str]
    customer_name: Optional[str]
    media_urls: List[str]
    sentiment_score: Decimal
    ai_summary: Optional[str]
    key_quotes: List[str]
    usage_count: int
    is_active: bool
    created_at: datetime


class SocialProofStats(BaseModel):
    total_collected: int
    approved: int
    pending: int
    approval_rate: float
    average_sentiment: float


# ========== UGC ==========

class UgcRequestCreate(BaseModel):
    order_id: uuid.UUID
    conversation_id: uuid.UUID
    content_type: Optional[str] = "lifestyle_photo"
    incentive: Optional[str] = ""
    campaign_id: Optional[uuid.UUID] = None


class UgcRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    order_id: Optional[uuid.UUID]
    conversation_id: Optional[uuid.UUID]
    content_type: str
    status: str
    request_message: str
    incentive_offered: Optional[str]
    response_media_urls: List[str]
    response_text: Optional[str]
    responded_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime


# ========== ValueSequence ==========

class ValueSequenceCreate(BaseModel):
    name: str
    topic: str
    message_count: Optional[int] = 3
    total_duration_days: Optional[int] = 7
    target_segment: Optional[str] = "cold"
    campaign_id: Optional[uuid.UUID] = None


class ValueSequenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    topic: str
    message_count: int
    total_duration_days: int
    target_segment: str
    times_started: int
    times_completed: int
    conversion_rate: Decimal
    avg_engagement_score: Decimal
    is_active: bool
    created_at: datetime


class ValueSequencePerformance(BaseModel):
    sequence_id: uuid.UUID
    name: str
    topic: str
    total_enrollments: int
    completed: int
    converted: int
    completion_rate: float
    conversion_rate: float


# ========== Referral ==========

class ReferralCampaignCreate(BaseModel):
    name: str
    incentive_type: Optional[str] = "discount_credit"
    reward_value: Optional[float] = 20.0
    max_referrals_per_user: Optional[int] = 10


class ReferralMetrics(BaseModel):
    business_id: uuid.UUID
    unique_referrers: int
    total_signups: int
    total_conversions: int
    signups_per_referrer: float
    conversion_rate: float
    k_factor: float
    k_interpretation: str
    total_revenue: float
    exponential_growth: bool


class ReferralCampaignReport(ReferralMetrics):
    top_referrers: List[dict]
    generated_at: str


# ========== Dashboard ==========

class GrowthDashboardMetrics(BaseModel):
    leads_this_week: int
    total_organic_leads: int
    total_conversions: int
    conversion_rate: float
    active_campaigns: int
    sources_breakdown: dict
    period: str


class CampaignEvaluation(BaseModel):
    campaign_id: uuid.UUID
    name: str
    type: str
    status: str
    total_leads: int
    converted_leads: int
    conversion_rate: float
    revenue_attributed: float
    content_published: int
    recommendations: List[str]
