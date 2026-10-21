"""A/B Testing Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PromptExperimentCreate(BaseModel):
    name: str = Field(..., max_length=200)
    agent_type: str = Field(..., max_length=50)
    metric: str = Field(default="conversion", max_length=20)
    variant_a_name: str = Field(..., max_length=100)
    variant_a_prompt: str
    variant_b_name: str = Field(..., max_length=100)
    variant_b_prompt: str
    confidence_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    min_samples: int = Field(default=100, ge=1)


class PromptExperimentUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    status: str | None = Field(None, max_length=20)
    confidence_threshold: float | None = Field(None, ge=0.0, le=1.0)
    min_samples: int | None = Field(None, ge=1)


class PromptExperimentResponse(BaseModel):
    id: UUID
    business_id: UUID | None = None
    name: str
    agent_type: str
    metric: str
    variant_a_name: str
    variant_a_prompt: str
    variant_b_name: str
    variant_b_prompt: str
    status: str
    confidence_threshold: float
    min_samples: int
    winner_variant: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptExperimentResultResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    variant: str
    conversation_id: UUID
    outcome: str | None = None
    revenue: float | None = None
    engagement_score: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptExperimentAnalysis(BaseModel):
    experiment_id: UUID
    n_a: int
    n_b: int
    conversions_a: int
    conversions_b: int
    rate_a: float
    rate_b: float
    z_score: float
    p_value: float
    winner: str | None = None
    is_significant: bool


class PromptExperimentListResponse(BaseModel):
    total: int
    experiments: list[PromptExperimentResponse]
