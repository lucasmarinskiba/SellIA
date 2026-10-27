from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileUpdate(BaseModel):
    is_enabled: bool | None = None
    persona_name: str | None = Field(None, max_length=120)
    persona_role: str | None = Field(None, max_length=120)
    tone: str | None = Field(None, max_length=255)
    language: str | None = Field(None, max_length=8)
    offer: str | None = Field(None, max_length=2000)
    benefits: list[str] | None = Field(None, max_length=10)
    icp: dict[str, Any] | None = None
    postal_address: str | None = Field(None, max_length=300)
    opt_out_line: str | None = Field(None, min_length=5, max_length=300)
    do_not_contact: list[str] | None = Field(None, max_length=1000)
    max_daily_drafts: int | None = Field(None, ge=1, le=200)
    max_daily_sends: int | None = Field(None, ge=1, le=500)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    is_enabled: bool
    persona_name: str
    persona_role: str
    tone: str
    language: str
    offer: str
    benefits: list[str]
    icp: dict[str, Any]
    postal_address: str
    opt_out_line: str
    do_not_contact: list[str]
    max_daily_drafts: int
    max_daily_sends: int
    inbox_synced_at: datetime | None


class ProspectIn(BaseModel):
    email: EmailStr
    first_name: str = Field("", max_length=120)
    last_name: str = Field("", max_length=120)
    title: str = Field("", max_length=160)
    company: str = Field("", max_length=255)
    industry: str = Field("", max_length=160)
    website: str = Field("", max_length=500)
    signals: list[dict[str, str]] = Field(default_factory=list, max_length=10)
    notes: str = Field("", max_length=2000)
    is_company_inbox: bool = False


class ProspectsCreate(BaseModel):
    prospects: list[ProspectIn] = Field(min_length=1, max_length=200)


class ProspectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    email: str
    first_name: str
    last_name: str
    title: str
    company: str
    industry: str
    website: str
    signals: list[Any]
    notes: str
    email_status: str
    is_company_inbox: bool
    status: str
    created_at: datetime


class ProspectsCreateResponse(BaseModel):
    created: list[ProspectResponse]
    skipped: list[dict[str, str]]


class OutboxItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    prospect_id: UUID
    step: int
    to_email: str
    subject: str
    body: str
    status: str
    gate_reasons: list[str]
    decided_by: UUID | None
    decided_at: datetime | None
    sent_at: datetime | None
    message_id: str | None
    send_attempts: int
    send_error: str
    created_at: datetime


class ReplyIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class ReplyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    prospect_id: UUID
    body: str
    classification: str
    needs_human: bool
    draft_answer: str
    created_at: datetime


class SummaryResponse(BaseModel):
    """Counters returned by batch operations (send, follow-ups, inbox sync)."""

    counts: dict[str, int]
