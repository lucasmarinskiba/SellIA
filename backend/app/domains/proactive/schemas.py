"""Proactive Outreach Engine Schemas"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# OutreachOpportunity
# ---------------------------------------------------------------------------

class OutreachOpportunityBase(BaseModel):
    opportunity_type: str
    priority: str = "medium"
    trigger_data: dict[str, Any] = {}
    suggested_message: str | None = None
    suggested_channel: str = "whatsapp"
    status: str = "pending"
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    outcome: str | None = None
    revenue_generated: Decimal | None = None


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
    conditions: dict[str, Any] = {}
    message_template: str
    channel: str = "whatsapp"
    is_active: bool = True


class OutreachRuleCreate(OutreachRuleBase):
    pass


class OutreachRuleUpdate(BaseModel):
    rule_name: str | None = None
    rule_type: str | None = None
    conditions: dict[str, Any] | None = None
    message_template: str | None = None
    channel: str | None = None
    is_active: bool | None = None


class OutreachRuleResponse(OutreachRuleBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
