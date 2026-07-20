"""Auto-Responder Pilot Agent Schemas"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AutoResponderRuleBase(BaseModel):
    rule_name: str
    trigger_type: str  # time_of_day | day_of_week | keyword | inactivity
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    response_template: str
    is_active: bool = True
    priority: int = Field(default=0, ge=0, le=100)


class AutoResponderRuleCreate(AutoResponderRuleBase):
    business_id: UUID


class AutoResponderRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    response_template: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=0, le=100)


class AutoResponderRuleOut(AutoResponderRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime


class AutoResponseLogBase(BaseModel):
    conversation_id: Optional[UUID] = None
    trigger_fired: str
    response_sent: str
    customer_replied: bool = False
    outcome: Optional[str] = None


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
    by_rule: List[Dict[str, Any]] = Field(default_factory=list)
    period_days: int
