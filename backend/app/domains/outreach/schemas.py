"""Outreach Cadence Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domains.outreach.models import FatigueLevel, OutreachLogStatus

# ---------------------------------------------------------------------------
# ContactFatigueScore
# ---------------------------------------------------------------------------

class ContactFatigueScoreResponse(BaseModel):
    id: UUID
    business_id: UUID
    conversation_id: UUID
    total_contacts_last_7d: int = 0
    total_contacts_last_30d: int = 0
    contacts_by_channel: dict[str, int] = Field(default_factory=dict)
    last_contact_at: datetime | None = None
    last_response_at: datetime | None = None
    consecutive_no_replies: int = 0
    fatigue_level: FatigueLevel = FatigueLevel.RELAXED
    recommended_cooldown_until: datetime | None = None
    ai_recommendation: str | None = None
    recommended_channel: str | None = None
    recommended_message_type: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# OutreachCadenceRule
# ---------------------------------------------------------------------------

class OutreachCadenceRuleBase(BaseModel):
    max_messages_per_week: int = 3
    max_messages_per_channel_per_week: int = 2
    min_hours_between_contacts: int = 24
    cooldown_after_no_reply_days: int = 3
    cooldown_after_no_reply_count: int = 3
    long_cooldown_days: int = 14
    channel_priority: list[str] = Field(default_factory=lambda: ["whatsapp", "email", "instagram"])
    respect_local_hours: bool = True
    allowed_hours_start: int = 9
    allowed_hours_end: int = 20
    avoid_weekends: bool = False
    hot_lead_override: bool = True
    hot_lead_max_per_week: int = 5
    is_active: bool = True


class OutreachCadenceRuleCreate(OutreachCadenceRuleBase):
    business_id: UUID


class OutreachCadenceRuleUpdate(BaseModel):
    max_messages_per_week: int | None = None
    max_messages_per_channel_per_week: int | None = None
    min_hours_between_contacts: int | None = None
    cooldown_after_no_reply_days: int | None = None
    cooldown_after_no_reply_count: int | None = None
    long_cooldown_days: int | None = None
    channel_priority: list[str] | None = None
    respect_local_hours: bool | None = None
    allowed_hours_start: int | None = None
    allowed_hours_end: int | None = None
    avoid_weekends: bool | None = None
    hot_lead_override: bool | None = None
    hot_lead_max_per_week: int | None = None
    is_active: bool | None = None


class OutreachCadenceRuleResponse(OutreachCadenceRuleBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# OutreachLog
# ---------------------------------------------------------------------------

class OutreachLogResponse(BaseModel):
    id: UUID
    business_id: UUID
    conversation_id: UUID
    channel: str
    message_type: str
    cadence_step: int = 1
    message_content: str | None = None
    status: OutreachLogStatus = OutreachLogStatus.SENT
    sent_at: datetime
    responded_at: datetime | None = None
    response_type: str | None = None
    ai_generated: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CanContact / Recommendations
# ---------------------------------------------------------------------------

class CanContactRequest(BaseModel):
    conversation_id: UUID
    channel: str | None = None  # If None, asks for best channel
    message_type: str | None = None


class CanContactResponse(BaseModel):
    can_contact: bool
    reason: str
    recommended_channel: str | None = None
    recommended_wait_hours: int | None = None
    fatigue_level: FatigueLevel = FatigueLevel.RELAXED
    contacts_this_week: int = 0
    ai_recommendation: str | None = None


class CadenceNextActionResponse(BaseModel):
    conversation_id: UUID
    recommended_action: str  # "send_message", "wait", "escalate", "change_channel"
    recommended_channel: str | None = None
    recommended_message_type: str | None = None
    recommended_delay_hours: int | None = None
    reason: str
    fatigue_level: FatigueLevel = FatigueLevel.RELAXED
