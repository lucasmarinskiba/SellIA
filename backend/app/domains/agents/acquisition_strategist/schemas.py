"""Acquisition Strategist Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChannelRecommendation(BaseModel):
    channel: str
    budget_pct: float
    expected_cac: float | None = None
    expected_volume: int | None = None
    tactics: list[str] = []


class AcquisitionStrategyBase(BaseModel):
    strategy_name: str


class AcquisitionStrategyCreate(AcquisitionStrategyBase):
    goals: dict[str, Any] = {}  # {target_customers, timeline, market, ...}
    budget: float | None = None


class AcquisitionStrategyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    strategy_name: str
    channels: list[dict[str, Any]] = []
    funnel_stages: list[dict[str, Any]] = []
    cac_target: float | None = None
    ltv_target: float | None = None
    sequences: list[dict[str, Any]] = []
    budget_allocation: dict[str, Any] = {}
    expected_results: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
