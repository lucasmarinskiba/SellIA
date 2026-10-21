"""Ad-budget autopilot schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConfigUpdate(BaseModel):
    is_active: bool | None = None
    is_paused: bool | None = None
    paused_reason: str | None = None
    requires_approval: bool | None = None
    total_daily_budget: Decimal | None = None
    optimization_window_days: int | None = Field(None, ge=3, le=90)
    target_roas: Decimal | None = Field(None, gt=0)
    kill_roas: Decimal | None = Field(None, ge=0)
    min_channel_share: Decimal | None = Field(None, ge=0, le=1)
    max_daily_shift_pct: Decimal | None = Field(None, gt=0, le=1)
    aggressiveness: Decimal | None = Field(None, ge=0.5, le=4)
    allow_pause: bool | None = None
    min_data_conversions: int | None = Field(None, ge=0)
    currency: str | None = None


class ConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    business_id: UUID
    is_active: bool
    is_paused: bool
    paused_reason: str | None
    requires_approval: bool
    total_daily_budget: Decimal | None
    optimization_window_days: int
    target_roas: Decimal
    kill_roas: Decimal
    min_channel_share: Decimal
    max_daily_shift_pct: Decimal
    aggressiveness: Decimal
    allow_pause: bool
    min_data_conversions: int
    currency: str
    last_run_at: datetime | None
    last_status: str | None


class ChannelCreate(BaseModel):
    platform: str  # meta | google | tiktok | other
    display_name: str
    channel_connection_id: UUID | None = None
    current_daily_budget: Decimal = Decimal(0)
    min_daily_budget: Decimal | None = None
    max_daily_budget: Decimal | None = None
    is_managed: bool = True
    campaign_refs: list[str] = []
    attribution_match: list[str] = []
    currency: str = "ARS"


class ChannelUpdate(BaseModel):
    display_name: str | None = None
    channel_connection_id: UUID | None = None
    current_daily_budget: Decimal | None = None
    min_daily_budget: Decimal | None = None
    max_daily_budget: Decimal | None = None
    is_managed: bool | None = None
    is_paused: bool | None = None
    campaign_refs: list[str] | None = None
    attribution_match: list[str] | None = None


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    platform: str
    display_name: str
    channel_connection_id: UUID | None
    current_daily_budget: Decimal
    min_daily_budget: Decimal | None
    max_daily_budget: Decimal | None
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
    blended_roas: Decimal | None
    total_budget_before: Decimal
    total_budget_after: Decimal
    decisions: list
    window_days: int
    notes: str | None
    applied_at: datetime | None
    created_at: datetime


class RunCycleRequest(BaseModel):
    force: bool = False
    auto_apply: bool | None = None
