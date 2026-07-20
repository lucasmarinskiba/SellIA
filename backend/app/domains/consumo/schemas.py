"""
Consumo Schemas
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ===== Cost Attribution =====

class AICallLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    model: str
    task_type: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    latency_ms: Optional[float]
    cache_hit: bool
    was_batched: bool
    created_at: datetime


class CostAttributionSummary(BaseModel):
    total_calls: int
    total_cost_usd: float
    total_tokens_input: int
    total_tokens_output: int
    avg_latency_ms: Optional[float]
    cache_hit_rate: float
    by_provider: list[dict[str, Any]]
    by_model: list[dict[str, Any]]
    by_task_type: list[dict[str, Any]]
    period_days: int = 30


class UserMarginOut(BaseModel):
    user_id: UUID
    email: str
    plan_name: str
    plan_price_usd: float
    ai_cost_usd: float
    margin_usd: float
    margin_percent: float
    risk_level: str  # healthy | warning | danger


# ===== Quality Gate =====

class QualityGateConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    min_confidence_threshold: float
    auto_escalate_on_low_confidence: bool
    max_ai_messages_before_human: int


class QualityGateConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    min_confidence_threshold: Optional[float] = None
    auto_escalate_on_low_confidence: Optional[bool] = None
    max_ai_messages_before_human: Optional[int] = None


# ===== Plan Recommendation =====

class PlanRecommendationOut(BaseModel):
    current_plan: str
    current_plan_price: float
    current_limit: int
    usage_percent: float
    recommendation: str  # keep | upgrade | downgrade
    suggested_plan: Optional[str]
    suggested_plan_price: Optional[float]
    reason: str
    estimated_savings_or_extra_cost: Optional[float]


# ===== Onboarding =====

class OnboardingProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_created: bool
    business_created: bool
    channel_connected: bool
    agent_configured: bool
    first_conversation: bool
    catalog_added: bool
    automation_created: bool
    current_step: str
    stuck_minutes: int
    ai_interventions_count: int
    progress_percent: int


class OnboardingHelpRequest(BaseModel):
    current_step: str
    context: Optional[str] = None


class OnboardingHelpResponse(BaseModel):
    message: str
    suggested_action: str
    resources: list[str]
