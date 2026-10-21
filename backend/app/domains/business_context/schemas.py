"""Business Context Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from .models import BusinessType, GeographicReach, PresenceType, SalesModel


class BusinessContextBase(BaseModel):
    business_type: BusinessType = BusinessType.OTHER
    sales_model: SalesModel = SalesModel.B2C
    geographic_reach: GeographicReach = GeographicReach.LOCAL
    presence_type: PresenceType = PresenceType.ONLINE_ONLY
    industry: str | None = None
    target_audience: str | None = None
    value_proposition: str | None = None
    price_range: str | None = None
    average_ticket: int | None = None
    city: str | None = None
    state_province: str | None = None
    country: str = "Argentina"
    address: str | None = None
    has_physical_location: bool = False
    serves_home_office: bool = False
    does_delivery: bool = False
    does_pickup: bool = False
    shipping_radius_km: int | None = None
    channels_configured: dict[str, bool] = Field(default_factory=dict)
    ads_configured: dict[str, bool] = Field(default_factory=dict)
    shipping_configured: dict[str, bool] = Field(default_factory=dict)
    website_configured: bool = False
    seo_configured: bool = False
    email_marketing_configured: bool = False
    primary_goal: str | None = None
    monthly_revenue_goal: int | None = None
    monthly_leads_goal: int | None = None
    target_countries: list[str] = Field(default_factory=list)
    scheduling_link: str | None = None
    llm_daily_call_limit: int | None = None  # None = unlimited


class BusinessContextCreate(BusinessContextBase):
    business_id: UUID | None = None


class BusinessContextUpdate(BaseModel):
    business_type: BusinessType | None = None
    sales_model: SalesModel | None = None
    geographic_reach: GeographicReach | None = None
    presence_type: PresenceType | None = None
    industry: str | None = None
    target_audience: str | None = None
    value_proposition: str | None = None
    price_range: str | None = None
    average_ticket: int | None = None
    city: str | None = None
    state_province: str | None = None
    country: str | None = None
    address: str | None = None
    has_physical_location: bool | None = None
    serves_home_office: bool | None = None
    does_delivery: bool | None = None
    does_pickup: bool | None = None
    shipping_radius_km: int | None = None
    channels_configured: dict[str, bool] | None = None
    ads_configured: dict[str, bool] | None = None
    shipping_configured: dict[str, bool] | None = None
    website_configured: bool | None = None
    seo_configured: bool | None = None
    email_marketing_configured: bool | None = None
    primary_goal: str | None = None
    monthly_revenue_goal: int | None = None
    monthly_leads_goal: int | None = None
    target_countries: list[str] | None = None
    scheduling_link: str | None = None
    llm_daily_call_limit: int | None = None


class CommunicationAngle(BaseModel):
    angle: str
    hook: str
    pain_point: str
    cta: str


class BusinessContextRead(BusinessContextBase):
    id: UUID
    user_id: UUID
    business_id: UUID | None = None
    ai_recommended_playbooks: list[str] = Field(default_factory=list)
    ai_priority_actions: list[dict[str, Any]] = Field(default_factory=list)
    ai_brand_voice: str | None = None
    communication_angles: list[CommunicationAngle] = Field(default_factory=list)
    winning_offer_summary: str | None = None
    llm_daily_call_limit: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BusinessContextWizardStep(BaseModel):
    step: int
    title: str
    description: str
    fields: list[dict[str, Any]]
    is_completed: bool


class BusinessContextWizardState(BaseModel):
    current_step: int
    total_steps: int = 5
    steps: list[BusinessContextWizardStep]
    context: BusinessContextRead


class ReachAnalysis(BaseModel):
    current_reach: str
    recommended_reach: str
    local_seo_priority: bool
    cross_border_opportunity: bool
    shipping_recommendations: list[str]
    platform_recommendations: list[str]
    estimated_addressable_market: str


class ChannelGapAnalysis(BaseModel):
    channel: str
    is_configured: bool
    priority: str  # critical, high, medium, low
    impact_estimate: str
    setup_difficulty: str
    recommended_playbook: str | None = None
