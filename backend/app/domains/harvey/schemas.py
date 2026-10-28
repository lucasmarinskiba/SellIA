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
    auto_draft: bool | None = None
    auto_discover: bool | None = None
    max_daily_discoveries: int | None = Field(None, ge=1, le=100)
    send_window_start: int | None = Field(None, ge=0, le=23)
    send_window_end: int | None = Field(None, ge=1, le=24)
    send_timezone: str | None = Field(None, max_length=64)
    send_weekdays_only: bool | None = None


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
    auto_draft: bool
    auto_discover: bool
    max_daily_discoveries: int
    send_window_start: int
    send_window_end: int
    send_timezone: str
    send_weekdays_only: bool
    warmup_started_at: datetime | None
    inbox_synced_at: datetime | None
    last_cycle_at: datetime | None
    last_cycle: dict[str, Any]
    last_discovery_at: datetime | None


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
    source: str
    source_url: str
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
    kind: str
    reply_id: UUID | None
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


class OutboxEdit(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=4000)


class VerifyIn(BaseModel):
    prospect_ids: list[UUID] = Field(min_length=1, max_length=200)
    verified: bool = True


class DiscoverIn(BaseModel):
    urls: list[str] = Field(default_factory=list, max_length=20)
    queries: list[str] = Field(default_factory=list, max_length=3)
    limit: int | None = Field(None, ge=1, le=50)


class DiscoverSite(BaseModel):
    url: str
    outcome: str
    detail: str


class DiscoverResponse(BaseModel):
    counts: dict[str, int]
    sites: list[DiscoverSite]


class StatusResponse(BaseModel):
    """What the Harvey screen needs in one call: readiness, today's numbers and queue sizes."""

    email_connected: bool
    model_available: bool
    search_available: bool
    search_provider: str | None
    has_brave_key: bool
    has_google_key: bool
    in_send_window: bool
    sent_today: int
    send_cap_today: int
    drafts_today: int
    discovered_today: int
    prospects: dict[str, int]
    outbox: dict[str, int]
    replies: int


class DiscoveryKeysIn(BaseModel):
    """Keys are write-only: ``None`` leaves one as it is, an empty string removes it."""

    brave_api_key: str | None = Field(None, max_length=300)
    google_places_api_key: str | None = Field(None, max_length=300)
    search_provider: str | None = Field(None, pattern="^(brave|google)$")


class ImportCsvResponse(BaseModel):
    rows: int
    created: int
    skipped: list[dict[str, str]]
    rejected: list[dict[str, str]]


class CompetitorIn(BaseModel):
    url: str = Field(min_length=3, max_length=500)
    kind: str = Field("direct", pattern="^(direct|indirect|own)$")
    name: str = Field("", max_length=160)


class CompetitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    kind: str
    snapshot: dict[str, Any]
    last_scanned_at: datetime | None
    last_error: str


class BriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    brief: dict[str, Any]
    generated_at: datetime | None = None
