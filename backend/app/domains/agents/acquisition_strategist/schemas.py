"""Acquisition Strategist Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChannelRecommendation(BaseModel):
    channel: str
    budget_pct: float
    expected_cac: Optional[float] = None
    expected_volume: Optional[int] = None
    tactics: List[str] = []


class AcquisitionStrategyBase(BaseModel):
    strategy_name: str


class AcquisitionStrategyCreate(AcquisitionStrategyBase):
    goals: Dict[str, Any] = {}  # {target_customers, timeline, market, ...}
    budget: Optional[float] = None


class AcquisitionStrategyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    strategy_name: str
    channels: List[Dict[str, Any]] = []
    funnel_stages: List[Dict[str, Any]] = []
    cac_target: Optional[float] = None
    ltv_target: Optional[float] = None
    sequences: List[Dict[str, Any]] = []
    budget_allocation: Dict[str, Any] = {}
    expected_results: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
