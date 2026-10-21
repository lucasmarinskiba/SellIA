"""CRM Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PipelineStage(BaseModel):
    id: str
    name: str
    order: int
    color: str | None = "#3B82F6"


class PipelineBase(BaseModel):
    name: str
    description: str | None = None
    stages: list[PipelineStage] = Field(default_factory=list)


class PipelineCreate(PipelineBase):
    business_id: UUID


class PipelineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    stages: list[PipelineStage] | None = None
    is_active: bool | None = None


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
    description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    value: float | None = None
    currency: str = "ARS"
    stage: str = "new_lead"
    probability: int = 10
    priority: int = 0
    expected_close_date: datetime | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class DealCreate(DealBase):
    business_id: UUID
    pipeline_id: UUID | None = None
    conversation_id: UUID | None = None


class DealUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    value: float | None = None
    currency: str | None = None
    stage: str | None = None
    probability: int | None = None
    priority: int | None = None
    expected_close_date: datetime | None = None
    actual_close_date: datetime | None = None
    close_reason: str | None = None
    extra_data: dict[str, Any] | None = None
    is_active: bool | None = None


class DealResponse(DealBase):
    id: UUID
    business_id: UUID
    pipeline_id: UUID | None = None
    conversation_id: UUID | None = None
    source_channel: str | None = None
    source_campaign: str | None = None
    actual_close_date: datetime | None = None
    close_reason: str | None = None
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
    commentary: str | None = None
    last_calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MoveDealRequest(BaseModel):
    stage: str
    order: int | None = None


class CRMSummaryResponse(BaseModel):
    total_deals: int
    total_value: float
    deals_by_stage: dict[str, int]
    value_by_stage: dict[str, float]
    avg_deal_value: float
    win_rate: float
    hot_leads: int
    warm_leads: int
    cold_leads: int
