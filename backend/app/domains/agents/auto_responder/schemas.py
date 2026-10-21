"""Auto-Responder Pilot Agent Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AutoResponderRuleBase(BaseModel):
    rule_name: str
    trigger_type: str  # time_of_day | day_of_week | keyword | inactivity
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    response_template: str
    is_active: bool = True
    priority: int = Field(default=0, ge=0, le=100)


class AutoResponderRuleCreate(AutoResponderRuleBase):
    business_id: UUID


class AutoResponderRuleUpdate(BaseModel):
    rule_name: str | None = None
    trigger_type: str | None = None
    trigger_config: dict[str, Any] | None = None
    response_template: str | None = None
    is_active: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=100)


class AutoResponderRuleOut(AutoResponderRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime


class AutoResponseLogBase(BaseModel):
    conversation_id: UUID | None = None
    trigger_fired: str
    response_sent: str
    customer_replied: bool = False
    outcome: str | None = None


class AutoResponseLogOut(AutoResponseLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    created_at: datetime


class AutoResponderStatsOut(BaseModel):
    business_id: UUID
    total_sent: int
    total_replied: int
    conversion_rate: float
    by_rule: list[dict[str, Any]] = Field(default_factory=list)
    period_days: int
