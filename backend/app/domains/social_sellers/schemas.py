"""Social Seller Pydantic Schemas"""

import uuid
from datetime import datetime
from typing import Optional, Any, List, Dict
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ========== SocialSeller Schemas ==========

class SocialSellerCreate(BaseModel):
    business_id: uuid.UUID
    platform: str
    name: str
    avatar_url: Optional[str] = None
    personality_slug: Optional[str] = None
    voice_config: Optional[dict] = None
    greeting_message: Optional[str] = None
    closing_message: Optional[str] = None
    ai_auto_reply: bool = True


class SocialSellerUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    personality_slug: Optional[str] = None
    voice_config: Optional[dict] = None
    stats: Optional[dict] = None
    status: Optional[str] = None
    ai_auto_reply: Optional[bool] = None
    greeting_message: Optional[str] = None
    closing_message: Optional[str] = None


class SocialSellerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    platform: str
    name: str
    avatar_url: Optional[str]
    personality_slug: Optional[str]
    voice_config: dict
    stats: dict
    status: str
    ai_auto_reply: bool
    greeting_message: Optional[str]
    closing_message: Optional[str]
    created_at: datetime
    updated_at: datetime


# ========== SellerCustomerRelationship Schemas ==========

class SellerCustomerCreate(BaseModel):
    customer_id: uuid.UUID


class SellerCustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    customer_id: uuid.UUID
    first_contact_at: Optional[datetime]
    last_contact_at: Optional[datetime]
    total_interactions: int
    deals_closed: int
    total_revenue: Decimal
    relationship_stage: str
    loyalty_score: int
    next_best_action: Optional[str]
    created_at: datetime
    updated_at: datetime


class CustomerInsightResponse(BaseModel):
    customer_id: uuid.UUID
    seller_id: uuid.UUID
    relationship_stage: str
    loyalty_score: int
    total_interactions: int
    deals_closed: int
    total_revenue: Decimal
    next_best_action: Optional[str]
    last_contact_at: Optional[datetime]
    first_contact_at: Optional[datetime]


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
    best_performing_hour: Optional[int]
    best_performing_content_type: Optional[str]
    created_at: datetime


# ========== Pipeline & Reports ==========

class PipelineStage(BaseModel):
    stage: str
    count: int
    revenue: Decimal


class SellerPipelineResponse(BaseModel):
    seller_id: uuid.UUID
    stages: List[PipelineStage]
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
    top_seller: Optional[dict] = None


class RecordSaleRequest(BaseModel):
    conversation_id: uuid.UUID
    amount: Decimal


class RecordSaleResponse(BaseModel):
    status: str
    seller_id: uuid.UUID
    conversation_id: uuid.UUID
    amount: Decimal
    new_total_revenue: Decimal
    celebration: Optional[str] = None


class ExecuteActionRequest(BaseModel):
    action: str  # send_message, wait, offer_discount
    payload: Optional[dict] = None


class ExecuteActionResponse(BaseModel):
    status: str
    action: str
    result: Optional[dict] = None


# ========== Loyalty & Wall of Fame Schemas ==========

class LoyaltyBadgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    badge_type: str
    name: str
    description: Optional[str]
    icon_url: Optional[str]
    criteria: dict
    created_at: datetime


class CustomerBadgeResponse(BaseModel):
    id: uuid.UUID
    badge_type: str
    name: str
    description: Optional[str]
    icon_url: Optional[str]
    earned_at: Optional[datetime]


class WallOfFameCustomer(BaseModel):
    customer_id: str
    name: str
    ltv: float
    total_purchases: int
    last_purchase_at: Optional[str]
    first_contact_at: Optional[str]
    platform: str
    badges: List[dict]


class LoyaltySegmentData(BaseModel):
    count: int
    avg_revenue: float


class LoyaltySegmentsResponse(BaseModel):
    business_id: str
    total_customers: int
    segments: Dict[str, LoyaltySegmentData]


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
    display_name: Optional[str] = None
    master_email: Optional[str] = None
    master_phone: Optional[str] = None
    identity_map: dict
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    total_lifetime_value: Decimal
    buying_frequency_days: Optional[int] = None
    preferred_platforms: list
    rfm_segment: Optional[str] = None
    last_purchase_at: Optional[datetime] = None
    total_purchases: int
    created_at: datetime
    updated_at: datetime


class UnifiedCustomerProfileResponse(BaseModel):
    id: str
    business_id: str
    display_name: Optional[str] = None
    master_email: Optional[str] = None
    master_phone: Optional[str] = None
    identity_map: dict
    platforms: list
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    total_lifetime_value: float
    buying_frequency_days: Optional[int] = None
    preferred_platforms: list
    preferred_platform: Optional[str] = None
    rfm_segment: Optional[str] = None
    last_purchase_at: Optional[str] = None
    total_purchases: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
    customer_name: Optional[str] = None
    customer_avatar: Optional[str] = None
    first_contact_at: Optional[datetime] = None
    last_contact_at: Optional[datetime] = None
    total_interactions: int
    deals_closed: int
    total_revenue: Decimal
    relationship_stage: str
    loyalty_score: int
    next_best_action: Optional[str] = None
    unified_customer_id: Optional[uuid.UUID] = None
    unified_display_name: Optional[str] = None
    unified_identity_map: Optional[dict] = None
    unified_total_lifetime_value: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ========== Radar de Oportunidades Schemas ==========

class PredictedPurchase(BaseModel):
    predicted_date: Optional[str] = None
    confidence_score: int
    days_until: Optional[int] = None
    reason: Optional[str] = None
    avg_interval_days: Optional[float] = None


class PurchaseHistory(BaseModel):
    total_orders: int
    total_spent: float
    avg_order_value: float
    last_order_at: Optional[str] = None


class RadarOpportunity(BaseModel):
    conversation_id: str
    customer_name: str
    platform: str
    score: int
    heat_level: str
    signals: List[str]
    seller_id: Optional[str] = None
    seller_name: Optional[str] = None
    seller_avatar: Optional[str] = None
    last_contact_at: Optional[str] = None
    predicted_next_purchase: Optional[PredictedPurchase] = None
    purchase_history: Optional[PurchaseHistory] = None
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
    opportunities: Dict[str, List[RadarOpportunity]]
    top_actions: List[TopAction]


class OpportunityScoreResponse(BaseModel):
    conversation_id: str
    score: int
    heat_level: str
    signals: List[str]
    components: Dict[str, int]


class RadarActRequest(BaseModel):
    action: str  # send_message, offer_discount, view_profile
    payload: Optional[dict] = None


class RadarActResponse(BaseModel):
    status: str
    action: str
    message: Optional[str] = None
    discount_pct: Optional[int] = None
    redirect_url: Optional[str] = None
    conversation_id: str
    detail: Optional[str] = None


# ========== Lookalike Audience Schemas ==========

class IdealCustomerProfile(BaseModel):
    avg_lifetime_value: float
    avg_purchase_frequency_days: float
    preferred_platforms: List[str]
    common_keywords_in_messages: List[str]
    avg_deal_value: float
    best_performing_seller: Optional[str] = None


class LookalikeLead(BaseModel):
    lead_id: str
    name: str
    platform: str
    similarity_score: int
    why: List[str]
    recommended_seller: Optional[str] = None


class LookalikeReportResponse(BaseModel):
    summary: str
    ideal_profile: IdealCustomerProfile
    top_opportunities: List[LookalikeLead]
    total_leads_scored: int
