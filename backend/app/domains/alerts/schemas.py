"""Alerts & Recommendations Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AlertRuleBase(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True
    rule_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"
    channels: list[str] = Field(default_factory=list)
    cooldown_minutes: int = 60
    max_alerts_per_day: int = 10


class AlertRuleCreate(AlertRuleBase):
    business_id: UUID


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None
    severity: str | None = None
    channels: list[str] | None = None
    cooldown_minutes: int | None = None
    max_alerts_per_day: int | None = None


class AlertRuleResponse(AlertRuleBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    title: str
    description: str | None = None
    severity: str
    status: str = "unread"
    entity_type: str | None = None
    entity_id: UUID | None = None
    recommended_action: str | None = None
    alert_metadata: dict[str, Any] = Field(default_factory=dict)


class AlertCreate(AlertBase):
    business_id: UUID
    rule_id: UUID | None = None
    conversation_id: UUID | None = None
    deal_id: UUID | None = None
    order_id: UUID | None = None


class AlertResponse(AlertBase):
    id: UUID
    business_id: UUID
    rule_id: UUID | None = None
    conversation_id: UUID | None = None
    deal_id: UUID | None = None
    order_id: UUID | None = None
    created_at: datetime
    read_at: datetime | None = None
    dismissed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AlertStatsResponse(BaseModel):
    total_unread: int
    total_read: int
    total_dismissed: int
    by_severity: dict[str, int]


class RecommendationBase(BaseModel):
    type: str
    title: str
    description: str | None = None
    priority: int = 1
    context_data: dict[str, Any] = Field(default_factory=dict)
    action_type: str
    action_payload: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"


class RecommendationCreate(RecommendationBase):
    business_id: UUID


class RecommendationResponse(RecommendationBase):
    id: UUID
    business_id: UUID
    applied_at: datetime | None = None
    applied_by_user_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationApplyRequest(BaseModel):
    user_id: UUID | None = None
