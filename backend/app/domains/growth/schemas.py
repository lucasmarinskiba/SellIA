"""Growth Domain Pydantic Schemas"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ========== GrowthCampaign ==========

class GrowthCampaignCreate(BaseModel):
    name: str
    campaign_type: str
    description: str | None = ""
    config: dict | None = {}
    target_audience: str | None = ""
    content_pillars: list[str] | None = []
    tone_of_voice: str | None = "educational"


class GrowthCampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    config: dict | None = None
    target_audience: str | None = None
    content_pillars: list[str] | None = None
    tone_of_voice: str | None = None
    is_active: bool | None = None


class GrowthCampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    description: str | None
    campaign_type: str
    status: str
    config: dict
    target_audience: str | None
    content_pillars: list[str]
    tone_of_voice: str
    leads_generated: int
    conversions: int
    revenue_attributed: Decimal
    content_published: int
    engagement_score: Decimal
    metrics_snapshot: dict
    started_at: datetime | None
    ended_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ========== LeadMagnet ==========

class LeadMagnetCreate(BaseModel):
    topic: str
    magnet_format: str | None = "cheat_sheet"
    target_audience: str | None = ""
    campaign_id: uuid.UUID | None = None


class LeadMagnetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    campaign_id: uuid.UUID | None
    title: str
    description: str | None
    format: str
    topic: str
    content: dict
    landing_page_copy: str | None
    delivery_message: str | None
    call_to_action: str | None
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
    conversation_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    lead_magnet_id: uuid.UUID | None = None
    contact_info: dict | None = {}
    source_detail: str | None = ""


class ProspectSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=120, description="Rubro o palabra clave, ej. 'peluquería'")
    location: str | None = Field(None, max_length=120, description="Ciudad o zona, ej. 'Rosario'")
    limit: int = Field(20, ge=1, le=20)


class ProspectSearchResponse(BaseModel):
    found: int
    created: int
    skipped_duplicates: int
    prospects: list[dict]


class InboundLeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    conversation_id: uuid.UUID | None
    campaign_id: uuid.UUID | None
    lead_magnet_id: uuid.UUID | None
    source_type: str
    source_detail: str | None
    contact_info: dict
    nurturing_stage: str
    engagement_score: int
    value_touches_received: int
    sales_touches_received: int
    first_touch_at: datetime
    last_touch_at: datetime
    converted_at: datetime | None
    is_active: bool


# ========== SocialProof ==========

class SocialProofCreate(BaseModel):
    conversation_id: uuid.UUID | None = None
    order_id: uuid.UUID | None = None
    item_type: str
    content: str
    rating: int | None = None
    customer_name: str | None = None
    media_urls: list[str] | None = []


class SocialProofResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    conversation_id: uuid.UUID | None
    order_id: uuid.UUID | None
    item_type: str
    status: str
    content: str
    rating: int | None
    headline: str | None
    customer_name: str | None
    media_urls: list[str]
    sentiment_score: Decimal
    ai_summary: str | None
    key_quotes: list[str]
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
    content_type: str | None = "lifestyle_photo"
    incentive: str | None = ""
    campaign_id: uuid.UUID | None = None


class UgcRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    order_id: uuid.UUID | None
    conversation_id: uuid.UUID | None
    content_type: str
    status: str
    request_message: str
    incentive_offered: str | None
    response_media_urls: list[str]
    response_text: str | None
    responded_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


# ========== ValueSequence ==========

class ValueSequenceCreate(BaseModel):
    name: str
    topic: str
    message_count: int | None = 3
    total_duration_days: int | None = 7
    target_segment: str | None = "cold"
    campaign_id: uuid.UUID | None = None


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
    incentive_type: str | None = "discount_credit"
    reward_value: float | None = 20.0
    max_referrals_per_user: int | None = 10


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
    top_referrers: list[dict]
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
    recommendations: list[str]
