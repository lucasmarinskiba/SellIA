"""Autopilot Engine Schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.domains.autopilot.models import AutopilotActionType, AutopilotActionStatus


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
    approval_threshold_amount: Decimal = Decimal("5000")
    max_daily_auto_messages: int = 50
    max_daily_auto_closes: int = 10
    max_daily_auto_orders: int = 10
    human_escalation_channels: list[str] = Field(default_factory=list)
    escalation_email: Optional[str] = None
    escalation_whatsapp: Optional[str] = None
    is_active: bool = False
    require_ai_explanation: bool = True
    explanation_language: str = "es"


class AutopilotConfigCreate(AutopilotConfigBase):
    business_id: UUID


class AutopilotConfigUpdate(BaseModel):
    auto_qualify_leads: Optional[bool] = None
    auto_move_deals: Optional[bool] = None
    auto_send_followups: Optional[bool] = None
    auto_close_deals: Optional[bool] = None
    auto_create_orders: Optional[bool] = None
    auto_request_reviews: Optional[bool] = None
    auto_activate_recovery_workflows: Optional[bool] = None
    auto_escalate_to_human: Optional[bool] = None
    approval_threshold_amount: Optional[Decimal] = None
    max_daily_auto_messages: Optional[int] = None
    max_daily_auto_closes: Optional[int] = None
    max_daily_auto_orders: Optional[int] = None
    human_escalation_channels: Optional[list[str]] = None
    escalation_email: Optional[str] = None
    escalation_whatsapp: Optional[str] = None
    is_active: Optional[bool] = None
    is_paused: Optional[bool] = None
    require_ai_explanation: Optional[bool] = None
    explanation_language: Optional[str] = None


class AutopilotConfigResponse(AutopilotConfigBase):
    id: UUID
    business_id: UUID
    is_paused: bool = False
    paused_reason: Optional[str] = None
    paused_at: Optional[datetime] = None
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
    ai_explanation: Optional[str] = None
    confidence_score: int = 0
    context_data: dict[str, Any] = Field(default_factory=dict)
    status: AutopilotActionStatus
    error_message: Optional[str] = None
    requires_approval: bool = False
    approved_at: Optional[datetime] = None
    approved_by_user_id: Optional[UUID] = None
    rejected_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    revenue_impact: Optional[Decimal] = None
    created_at: datetime
    executed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AutopilotActionLogFilter(BaseModel):
    status: Optional[AutopilotActionStatus] = None
    action_type: Optional[AutopilotActionType] = None
    entity_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class AutopilotActionApproveRequest(BaseModel):
    reason: Optional[str] = None


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
    revenue_generated: Decimal = Decimal("0")
    deals_value_closed: Decimal = Decimal("0")
    actions_escalated: int = 0
    actions_pending_approval: int = 0
    actions_rejected: int = 0
    ai_summary: Optional[str] = None
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
    paused_reason: Optional[str] = None
    today_executed: int = 0
    today_pending: int = 0
    today_escalated: int = 0
    today_revenue: Decimal = Decimal("0")
    last_action_at: Optional[datetime] = None


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
    seller_avatar: Optional[str] = None
    platform: str
    customer_name: str
    amount: float
    time: str


class OvernightSection(BaseModel):
    emoji: str
    title: str
    count: int
    items: list[dict[str, Any]] = Field(default_factory=list)
    highlight: Optional[str] = None


class OvernightReportResponse(BaseModel):
    greeting: str
    night_period: str  # "23:00 → 07:00"
    summary_stats: dict[str, Any]
    sections: list[OvernightSection] = Field(default_factory=list)
    top_seller: Optional[dict[str, Any]] = None
    prediction: str
    trust_score: int
    recommendation: str
