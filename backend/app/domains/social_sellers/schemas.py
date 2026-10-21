"""Social Seller Pydantic Schemas"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

# ========== SocialSeller Schemas ==========

class SocialSellerCreate(BaseModel):
    business_id: uuid.UUID
    platform: str
    name: str
    avatar_url: str | None = None
    personality_slug: str | None = None
    voice_config: dict | None = None
    greeting_message: str | None = None
    closing_message: str | None = None
    ai_auto_reply: bool = True


class SocialSellerUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    personality_slug: str | None = None
    voice_config: dict | None = None
    stats: dict | None = None
    status: str | None = None
    ai_auto_reply: bool | None = None
    greeting_message: str | None = None
    closing_message: str | None = None


class SocialSellerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    platform: str
    name: str
    avatar_url: str | None
    personality_slug: str | None
    voice_config: dict
    stats: dict
    status: str
    ai_auto_reply: bool
    greeting_message: str | None
    closing_message: str | None
    created_at: datetime
    updated_at: datetime


# ========== SellerCustomerRelationship Schemas ==========

class SellerCustomerCreate(BaseModel):
    customer_id: uuid.UUID



class CustomerInsightResponse(BaseModel):
    customer_id: uuid.UUID
    seller_id: uuid.UUID
    relationship_stage: str
    loyalty_score: int
    total_interactions: int
    deals_closed: int
    total_revenue: Decimal
    next_best_action: str | None
    last_contact_at: datetime | None
    first_contact_at: datetime | None


# ========== SellerPerformance Schemas ==========

class SellerPerformanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    period: str
    period_start: datetime
    period_end: datetime
    leads_acquired: int
    messages_sent: int
    conversations_active: int
    deals_won: int
    revenue: Decimal
    conversion_rate: Decimal
    best_performing_hour: int | None
    best_performing_content_type: str | None
    created_at: datetime


# ========== Pipeline & Reports ==========

class PipelineStage(BaseModel):
    stage: str
    count: int
    revenue: Decimal


class SellerPipelineResponse(BaseModel):
    seller_id: uuid.UUID
    stages: list[PipelineStage]
    total_customers: int
    total_revenue: Decimal


class TeamReportResponse(BaseModel):
    business_id: uuid.UUID
    period: str
    total_sellers: int
    total_revenue: Decimal
    total_deals: int
    total_leads: int
    avg_conversion_rate: Decimal
    top_seller: dict | None = None


class RecordSaleRequest(BaseModel):
    conversation_id: uuid.UUID
    amount: Decimal


class RecordSaleResponse(BaseModel):
    status: str
    seller_id: uuid.UUID
    conversation_id: uuid.UUID
    amount: Decimal
    new_total_revenue: Decimal
    celebration: str | None = None


class ExecuteActionRequest(BaseModel):
    action: str  # send_message, wait, offer_discount
    payload: dict | None = None


class ExecuteActionResponse(BaseModel):
    status: str
    action: str
    result: dict | None = None


# ========== Loyalty & Wall of Fame Schemas ==========

class LoyaltyBadgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    badge_type: str
    name: str
    description: str | None
    icon_url: str | None
    criteria: dict
    created_at: datetime


class CustomerBadgeResponse(BaseModel):
    id: uuid.UUID
    badge_type: str
    name: str
    description: str | None
    icon_url: str | None
    earned_at: datetime | None


class WallOfFameCustomer(BaseModel):
    customer_id: str
    name: str
    ltv: float
    total_purchases: int
    last_purchase_at: str | None
    first_contact_at: str | None
    platform: str
    badges: list[dict]


class LoyaltySegmentData(BaseModel):
    count: int
    avg_revenue: float


class LoyaltySegmentsResponse(BaseModel):
    business_id: str
    total_customers: int
    segments: dict[str, LoyaltySegmentData]


class LoyaltyActionRequest(BaseModel):
    action_type: str  # send_gift, offer_vip, request_testimonial, invite_referral


class LoyaltyActionResponse(BaseModel):
    status: str
    action: str
    business_id: str
    customer_id: str
    message: str
    created_at: str


# ========== Unified Customer Schemas ==========

class UnifiedCustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    display_name: str | None = None
    master_email: str | None = None
    master_phone: str | None = None
    identity_map: dict
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    total_lifetime_value: Decimal
    buying_frequency_days: int | None = None
    preferred_platforms: list
    rfm_segment: str | None = None
    last_purchase_at: datetime | None = None
    total_purchases: int
    created_at: datetime
    updated_at: datetime


class UnifiedCustomerProfileResponse(BaseModel):
    id: str
    business_id: str
    display_name: str | None = None
    master_email: str | None = None
    master_phone: str | None = None
    identity_map: dict
    platforms: list
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    total_lifetime_value: float
    buying_frequency_days: int | None = None
    preferred_platforms: list
    preferred_platform: str | None = None
    rfm_segment: str | None = None
    last_purchase_at: str | None = None
    total_purchases: int
    created_at: str | None = None
    updated_at: str | None = None


class MergeSuggestionResponse(BaseModel):
    customer_a_id: uuid.UUID
    customer_b_id: uuid.UUID
    score: int
    reasons: list


class MergeRequest(BaseModel):
    target_id: uuid.UUID
    source_id: uuid.UUID


class MergeResponse(BaseModel):
    status: str
    target_id: uuid.UUID
    merged_source_id: uuid.UUID


class SellerCustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str | None = None
    customer_avatar: str | None = None
    first_contact_at: datetime | None = None
    last_contact_at: datetime | None = None
    total_interactions: int
    deals_closed: int
    total_revenue: Decimal
    relationship_stage: str
    loyalty_score: int
    next_best_action: str | None = None
    unified_customer_id: uuid.UUID | None = None
    unified_display_name: str | None = None
    unified_identity_map: dict | None = None
    unified_total_lifetime_value: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ========== Radar de Oportunidades Schemas ==========

class PredictedPurchase(BaseModel):
    predicted_date: str | None = None
    confidence_score: int
    days_until: int | None = None
    reason: str | None = None
    avg_interval_days: float | None = None


class PurchaseHistory(BaseModel):
    total_orders: int
    total_spent: float
    avg_order_value: float
    last_order_at: str | None = None


class RadarOpportunity(BaseModel):
    conversation_id: str
    customer_name: str
    platform: str
    score: int
    heat_level: str
    signals: list[str]
    seller_id: str | None = None
    seller_name: str | None = None
    seller_avatar: str | None = None
    last_contact_at: str | None = None
    predicted_next_purchase: PredictedPurchase | None = None
    purchase_history: PurchaseHistory | None = None
    recent_messages_count: int = 0


class RadarSummary(BaseModel):
    total_opportunities: int
    hot_count: int
    warm_count: int
    nurture_count: int
    at_risk_count: int
    total_potential_revenue: float


class TopAction(BaseModel):
    priority: str
    target: str
    action: str
    reason: str


class RadarDataResponse(BaseModel):
    business_id: str
    generated_at: str
    summary: RadarSummary
    opportunities: dict[str, list[RadarOpportunity]]
    top_actions: list[TopAction]


class OpportunityScoreResponse(BaseModel):
    conversation_id: str
    score: int
    heat_level: str
    signals: list[str]
    components: dict[str, int]


class RadarActRequest(BaseModel):
    action: str  # send_message, offer_discount, view_profile
    payload: dict | None = None


class RadarActResponse(BaseModel):
    status: str
    action: str
    message: str | None = None
    discount_pct: int | None = None
    redirect_url: str | None = None
    conversation_id: str
    detail: str | None = None


# ========== Lookalike Audience Schemas ==========

class IdealCustomerProfile(BaseModel):
    avg_lifetime_value: float
    avg_purchase_frequency_days: float
    preferred_platforms: list[str]
    common_keywords_in_messages: list[str]
    avg_deal_value: float
    best_performing_seller: str | None = None


class LookalikeLead(BaseModel):
    lead_id: str
    name: str
    platform: str
    similarity_score: int
    why: list[str]
    recommended_seller: str | None = None


class LookalikeReportResponse(BaseModel):
    summary: str
    ideal_profile: IdealCustomerProfile
    top_opportunities: list[LookalikeLead]
    total_leads_scored: int
