"""Alerts & Recommendations Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    rule_type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"
    channels: List[str] = Field(default_factory=list)
    cooldown_minutes: int = 60
    max_alerts_per_day: int = 10


class AlertRuleCreate(AlertRuleBase):
    business_id: UUID


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    channels: Optional[List[str]] = None
    cooldown_minutes: Optional[int] = None
    max_alerts_per_day: Optional[int] = None


class AlertRuleResponse(AlertRuleBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str
    status: str = "unread"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    recommended_action: Optional[str] = None
    alert_metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertCreate(AlertBase):
    business_id: UUID
    rule_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    order_id: Optional[UUID] = None


class AlertResponse(AlertBase):
    id: UUID
    business_id: UUID
    rule_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertStatsResponse(BaseModel):
    total_unread: int
    total_read: int
    total_dismissed: int
    by_severity: Dict[str, int]


class RecommendationBase(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    priority: int = 1
    context_data: Dict[str, Any] = Field(default_factory=dict)
    action_type: str
    action_payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"


class RecommendationCreate(RecommendationBase):
    business_id: UUID


class RecommendationResponse(RecommendationBase):
    id: UUID
    business_id: UUID
    applied_at: Optional[datetime] = None
    applied_by_user_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationApplyRequest(BaseModel):
    user_id: Optional[UUID] = None
