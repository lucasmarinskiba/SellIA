"""CRM Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PipelineStage(BaseModel):
    id: str
    name: str
    order: int
    color: Optional[str] = "#3B82F6"


class PipelineBase(BaseModel):
    name: str
    description: Optional[str] = None
    stages: List[PipelineStage] = Field(default_factory=list)


class PipelineCreate(PipelineBase):
    business_id: UUID


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stages: Optional[List[PipelineStage]] = None
    is_active: Optional[bool] = None


class PipelineResponse(PipelineBase):
    id: UUID
    business_id: UUID
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealBase(BaseModel):
    title: str
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    value: Optional[float] = None
    currency: str = "ARS"
    stage: str = "new_lead"
    probability: int = 10
    priority: int = 0
    expected_close_date: Optional[datetime] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class DealCreate(DealBase):
    business_id: UUID
    pipeline_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    value: Optional[float] = None
    currency: Optional[str] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    priority: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    close_reason: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DealResponse(DealBase):
    id: UUID
    business_id: UUID
    pipeline_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    source_channel: Optional[str] = None
    source_campaign: Optional[str] = None
    actual_close_date: Optional[datetime] = None
    close_reason: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadScoreResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    total_score: int
    engagement_score: int
    intent_score: int
    demographic_score: int
    behavioral_score: int
    recency_score: int
    classification: str
    commentary: Optional[str] = None
    last_calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MoveDealRequest(BaseModel):
    stage: str
    order: Optional[int] = None


class CRMSummaryResponse(BaseModel):
    total_deals: int
    total_value: float
    deals_by_stage: Dict[str, int]
    value_by_stage: Dict[str, float]
    avg_deal_value: float
    win_rate: float
    hot_leads: int
    warm_leads: int
    cold_leads: int
