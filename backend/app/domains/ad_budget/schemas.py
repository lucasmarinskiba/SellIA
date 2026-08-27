"""Ad-budget autopilot schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConfigUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_paused: Optional[bool] = None
    paused_reason: Optional[str] = None
    requires_approval: Optional[bool] = None
    total_daily_budget: Optional[Decimal] = None
    optimization_window_days: Optional[int] = Field(None, ge=3, le=90)
    target_roas: Optional[Decimal] = Field(None, gt=0)
    kill_roas: Optional[Decimal] = Field(None, ge=0)
    min_channel_share: Optional[Decimal] = Field(None, ge=0, le=1)
    max_daily_shift_pct: Optional[Decimal] = Field(None, gt=0, le=1)
    aggressiveness: Optional[Decimal] = Field(None, ge=0.5, le=4)
    allow_pause: Optional[bool] = None
    min_data_conversions: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = None


class ConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    business_id: UUID
    is_active: bool
    is_paused: bool
    paused_reason: Optional[str]
    requires_approval: bool
    total_daily_budget: Optional[Decimal]
    optimization_window_days: int
    target_roas: Decimal
    kill_roas: Decimal
    min_channel_share: Decimal
    max_daily_shift_pct: Decimal
    aggressiveness: Decimal
    allow_pause: bool
    min_data_conversions: int
    currency: str
    last_run_at: Optional[datetime]
    last_status: Optional[str]


class ChannelCreate(BaseModel):
    platform: str  # meta | google | tiktok | other
    display_name: str
    channel_connection_id: Optional[UUID] = None
    current_daily_budget: Decimal = Decimal("0")
    min_daily_budget: Optional[Decimal] = None
    max_daily_budget: Optional[Decimal] = None
    is_managed: bool = True
    campaign_refs: list[str] = []
    attribution_match: list[str] = []
    currency: str = "ARS"


class ChannelUpdate(BaseModel):
    display_name: Optional[str] = None
    channel_connection_id: Optional[UUID] = None
    current_daily_budget: Optional[Decimal] = None
    min_daily_budget: Optional[Decimal] = None
    max_daily_budget: Optional[Decimal] = None
    is_managed: Optional[bool] = None
    is_paused: Optional[bool] = None
    campaign_refs: Optional[list[str]] = None
    attribution_match: Optional[list[str]] = None


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    platform: str
    display_name: str
    channel_connection_id: Optional[UUID]
    current_daily_budget: Decimal
    min_daily_budget: Optional[Decimal]
    max_daily_budget: Optional[Decimal]
    is_managed: bool
    is_paused: bool
    campaign_refs: list
    attribution_match: list
    currency: str


class ReallocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    run_id: UUID
    status: str
    blended_roas: Optional[Decimal]
    total_budget_before: Decimal
    total_budget_after: Decimal
    decisions: list
    window_days: int
    notes: Optional[str]
    applied_at: Optional[datetime]
    created_at: datetime


class RunCycleRequest(BaseModel):
    force: bool = False
    auto_apply: Optional[bool] = None
