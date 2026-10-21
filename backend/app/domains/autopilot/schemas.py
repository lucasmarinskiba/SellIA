"""Autopilot Engine Schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.autopilot.models import AutopilotActionStatus, AutopilotActionType

# ---------------------------------------------------------------------------
# AutopilotConfig
# ---------------------------------------------------------------------------

class AutopilotConfigBase(BaseModel):
    auto_qualify_leads: bool = False
    auto_move_deals: bool = False
    auto_send_followups: bool = False
    auto_close_deals: bool = False
    auto_create_orders: bool = False
    auto_request_reviews: bool = False
    auto_activate_recovery_workflows: bool = False
    auto_escalate_to_human: bool = True
    approval_threshold_amount: Decimal = Decimal(5000)
    max_daily_auto_messages: int = 50
    max_daily_auto_closes: int = 10
    max_daily_auto_orders: int = 10
    human_escalation_channels: list[str] = Field(default_factory=list)
    escalation_email: str | None = None
    escalation_whatsapp: str | None = None
    is_active: bool = False
    require_ai_explanation: bool = True
    explanation_language: str = "es"


class AutopilotConfigCreate(AutopilotConfigBase):
    business_id: UUID


class AutopilotConfigUpdate(BaseModel):
    auto_qualify_leads: bool | None = None
    auto_move_deals: bool | None = None
    auto_send_followups: bool | None = None
    auto_close_deals: bool | None = None
    auto_create_orders: bool | None = None
    auto_request_reviews: bool | None = None
    auto_activate_recovery_workflows: bool | None = None
    auto_escalate_to_human: bool | None = None
    approval_threshold_amount: Decimal | None = None
    max_daily_auto_messages: int | None = None
    max_daily_auto_closes: int | None = None
    max_daily_auto_orders: int | None = None
    human_escalation_channels: list[str] | None = None
    escalation_email: str | None = None
    escalation_whatsapp: str | None = None
    is_active: bool | None = None
    is_paused: bool | None = None
    require_ai_explanation: bool | None = None
    explanation_language: str | None = None


class AutopilotConfigResponse(AutopilotConfigBase):
    id: UUID
    business_id: UUID
    is_paused: bool = False
    paused_reason: str | None = None
    paused_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# AutopilotActionLog
# ---------------------------------------------------------------------------

class AutopilotActionLogResponse(BaseModel):
    id: UUID
    business_id: UUID
    action_type: AutopilotActionType
    entity_type: str
    entity_id: UUID
    reason: str
    ai_explanation: str | None = None
    confidence_score: int = 0
    context_data: dict[str, Any] = Field(default_factory=dict)
    status: AutopilotActionStatus
    error_message: str | None = None
    requires_approval: bool = False
    approved_at: datetime | None = None
    approved_by_user_id: UUID | None = None
    rejected_at: datetime | None = None
    rejected_reason: str | None = None
    revenue_impact: Decimal | None = None
    created_at: datetime
    executed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AutopilotActionLogFilter(BaseModel):
    status: AutopilotActionStatus | None = None
    action_type: AutopilotActionType | None = None
    entity_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = 50
    offset: int = 0


class AutopilotActionApproveRequest(BaseModel):
    reason: str | None = None


class AutopilotActionRejectRequest(BaseModel):
    reason: str


# ---------------------------------------------------------------------------
# AutopilotDailyReport
# ---------------------------------------------------------------------------

class AutopilotDailyReportResponse(BaseModel):
    id: UUID
    business_id: UUID
    report_date: datetime
    leads_contacted: int = 0
    deals_moved: int = 0
    deals_closed: int = 0
    orders_created: int = 0
    messages_sent: int = 0
    sequences_started: int = 0
    workflows_activated: int = 0
    revenue_generated: Decimal = Decimal(0)
    deals_value_closed: Decimal = Decimal(0)
    actions_escalated: int = 0
    actions_pending_approval: int = 0
    actions_rejected: int = 0
    ai_summary: str | None = None
    highlights: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Status & Overview
# ---------------------------------------------------------------------------

class AutopilotStatusResponse(BaseModel):
    business_id: UUID
    is_active: bool
    is_paused: bool
    paused_reason: str | None = None
    today_executed: int = 0
    today_pending: int = 0
    today_escalated: int = 0
    today_revenue: Decimal = Decimal(0)
    last_action_at: datetime | None = None


class AutopilotOverviewResponse(BaseModel):
    business_id: UUID
    message: str  # "Mientras dormiste, SellIA..."
    period: str  # "last_24h", "last_7d"
    summary: dict[str, Any]
    pending_actions: list[AutopilotActionLogResponse] = Field(default_factory=list)
    escalations: list[AutopilotActionLogResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Overnight Report (Mientras Dormías)
# ---------------------------------------------------------------------------

class OvernightSaleItem(BaseModel):
    seller_name: str
    seller_avatar: str | None = None
    platform: str
    customer_name: str
    amount: float
    time: str


class OvernightSection(BaseModel):
    emoji: str
    title: str
    count: int
    items: list[dict[str, Any]] = Field(default_factory=list)
    highlight: str | None = None


class OvernightReportResponse(BaseModel):
    greeting: str
    night_period: str  # "23:00 → 07:00"
    summary_stats: dict[str, Any]
    sections: list[OvernightSection] = Field(default_factory=list)
    top_seller: dict[str, Any] | None = None
    prediction: str
    trust_score: int
    recommendation: str
