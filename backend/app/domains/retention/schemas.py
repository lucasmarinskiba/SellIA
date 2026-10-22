"""Retention & Loyalty Pydantic Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReferralProgramBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = None
    reward_type: str = "discount_percent"
    reward_value: float = 10.0
    max_referrals_per_user: int = 10
    expiry_days: int = 30


class ReferralProgramCreate(ReferralProgramBase):
    pass


class ReferralProgramResponse(ReferralProgramBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    is_active: bool
    created_at: datetime


class ReferralCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    program_id: UUID
    code: str
    referrer_name: str | None = None
    referrer_email: str | None = None
    total_uses: int
    total_conversions: int
    total_revenue: float
    expires_at: datetime | None = None
    is_active: bool
    created_at: datetime


class NpsCampaignBase(BaseModel):
    name: str = Field(..., max_length=200)
    trigger_type: str = "post_purchase"
    trigger_days: int = 14
    question_text: str | None = None
    thank_you_message: str | None = None


class NpsCampaignCreate(NpsCampaignBase):
    pass


class NpsCampaignResponse(NpsCampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    status: str
    is_active: bool
    created_at: datetime


class NpsScoreResponse(BaseModel):
    nps: int
    promoters: int
    passives: int
    detractors: int
    total: int


class CustomerSegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    conversation_id: UUID
    segment: str
    r_score: int
    f_score: int
    m_score: int
    rfm_score: int
    total_orders: int
    total_revenue: float
    avg_order_value: float
    calculated_at: datetime
