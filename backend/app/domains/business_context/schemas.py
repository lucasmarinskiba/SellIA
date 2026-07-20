"""Business Context Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from .models import BusinessType, SalesModel, GeographicReach, PresenceType


class BusinessContextBase(BaseModel):
    business_type: BusinessType = BusinessType.OTHER
    sales_model: SalesModel = SalesModel.B2C
    geographic_reach: GeographicReach = GeographicReach.LOCAL
    presence_type: PresenceType = PresenceType.ONLINE_ONLY
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    value_proposition: Optional[str] = None
    price_range: Optional[str] = None
    average_ticket: Optional[int] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: str = "Argentina"
    address: Optional[str] = None
    has_physical_location: bool = False
    serves_home_office: bool = False
    does_delivery: bool = False
    does_pickup: bool = False
    shipping_radius_km: Optional[int] = None
    channels_configured: Dict[str, bool] = Field(default_factory=dict)
    ads_configured: Dict[str, bool] = Field(default_factory=dict)
    shipping_configured: Dict[str, bool] = Field(default_factory=dict)
    website_configured: bool = False
    seo_configured: bool = False
    email_marketing_configured: bool = False
    primary_goal: Optional[str] = None
    monthly_revenue_goal: Optional[int] = None
    monthly_leads_goal: Optional[int] = None
    target_countries: List[str] = Field(default_factory=list)


class BusinessContextCreate(BusinessContextBase):
    business_id: Optional[UUID] = None


class BusinessContextUpdate(BaseModel):
    business_type: Optional[BusinessType] = None
    sales_model: Optional[SalesModel] = None
    geographic_reach: Optional[GeographicReach] = None
    presence_type: Optional[PresenceType] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    value_proposition: Optional[str] = None
    price_range: Optional[str] = None
    average_ticket: Optional[int] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    has_physical_location: Optional[bool] = None
    serves_home_office: Optional[bool] = None
    does_delivery: Optional[bool] = None
    does_pickup: Optional[bool] = None
    shipping_radius_km: Optional[int] = None
    channels_configured: Optional[Dict[str, bool]] = None
    ads_configured: Optional[Dict[str, bool]] = None
    shipping_configured: Optional[Dict[str, bool]] = None
    website_configured: Optional[bool] = None
    seo_configured: Optional[bool] = None
    email_marketing_configured: Optional[bool] = None
    primary_goal: Optional[str] = None
    monthly_revenue_goal: Optional[int] = None
    monthly_leads_goal: Optional[int] = None
    target_countries: Optional[List[str]] = None


class BusinessContextRead(BusinessContextBase):
    id: UUID
    user_id: UUID
    business_id: Optional[UUID] = None
    ai_recommended_playbooks: List[str] = Field(default_factory=list)
    ai_priority_actions: List[Dict[str, Any]] = Field(default_factory=list)
    ai_brand_voice: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BusinessContextWizardStep(BaseModel):
    step: int
    title: str
    description: str
    fields: List[Dict[str, Any]]
    is_completed: bool


class BusinessContextWizardState(BaseModel):
    current_step: int
    total_steps: int = 5
    steps: List[BusinessContextWizardStep]
    context: BusinessContextRead


class ReachAnalysis(BaseModel):
    current_reach: str
    recommended_reach: str
    local_seo_priority: bool
    cross_border_opportunity: bool
    shipping_recommendations: List[str]
    platform_recommendations: List[str]
    estimated_addressable_market: str


class ChannelGapAnalysis(BaseModel):
    channel: str
    is_configured: bool
    priority: str  # critical, high, medium, low
    impact_estimate: str
    setup_difficulty: str
    recommended_playbook: Optional[str] = None
