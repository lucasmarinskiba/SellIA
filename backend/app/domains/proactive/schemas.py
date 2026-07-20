"""Proactive Outreach Engine Schemas"""

from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# OutreachOpportunity
# ---------------------------------------------------------------------------

class OutreachOpportunityBase(BaseModel):
    opportunity_type: str
    priority: str = "medium"
    trigger_data: Dict[str, Any] = {}
    suggested_message: Optional[str] = None
    suggested_channel: str = "whatsapp"
    status: str = "pending"
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    outcome: Optional[str] = None
    revenue_generated: Optional[Decimal] = None


class OutreachOpportunityCreate(OutreachOpportunityBase):
    business_id: UUID
    customer_id: UUID


class OutreachOpportunityResponse(OutreachOpportunityBase):
    id: UUID
    business_id: UUID
    customer_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# OutreachRule
# ---------------------------------------------------------------------------

class OutreachRuleBase(BaseModel):
    rule_name: str
    rule_type: str
    conditions: Dict[str, Any] = {}
    message_template: str
    channel: str = "whatsapp"
    is_active: bool = True


class OutreachRuleCreate(OutreachRuleBase):
    pass


class OutreachRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    message_template: Optional[str] = None
    channel: Optional[str] = None
    is_active: Optional[bool] = None


class OutreachRuleResponse(OutreachRuleBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
