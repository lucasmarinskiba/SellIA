"""SellIA Missions — Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ─── MissionStep ───────────────────────────────────────────────────────────────

class MissionStepBase(BaseModel):
    step_number: int = 1
    title: str
    description: str | None = None
    platform: str  # "instagram", "computer_use", "api"
    action_type: str
    action_params: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class MissionStepCreate(MissionStepBase):
    pass


class MissionStepUpdate(BaseModel):
    status: str | None = None
    result: dict[str, Any] | None = None
    error_message: str | None = None
    approved_by_user: bool | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class MissionStepRead(MissionStepBase):
    id: UUID
    mission_id: UUID
    status: str
    result: dict[str, Any] | None = None
    error_message: str | None = None
    approved_by_user: bool
    computer_use_session_id: UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Mission ───────────────────────────────────────────────────────────────────

class MissionBase(BaseModel):
    title: str
    description: str | None = None
    category: str  # "launch", "seo", "ads", "recovery", "expansion", "branding", "logistics", "automation"
    playbook_slug: str | None = None
    target_platforms: list[str] = Field(default_factory=list)
    expected_impact: dict[str, Any] = Field(default_factory=dict)


class MissionCreate(MissionBase):
    business_id: UUID | None = None
    created_by: str = "ai"
    steps: list[MissionStepCreate] = Field(default_factory=list)


class MissionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    approved_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class MissionRead(MissionBase):
    id: UUID
    user_id: UUID
    business_id: UUID | None = None
    status: str
    created_by: str
    approved_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    steps: list[MissionStepRead] = Field(default_factory=list)
    progress_percent: int = 0

    class Config:
        from_attributes = True


# ─── BusinessDiagnostic ────────────────────────────────────────────────────────

class BusinessDiagnosticBase(BaseModel):
    category: str
    severity: str
    finding: str
    metric_value: str | None = None
    benchmark_value: str | None = None
    recommended_mission_slug: str | None = None
    context_data: dict[str, Any] = Field(default_factory=dict)


class BusinessDiagnosticCreate(BusinessDiagnosticBase):
    business_id: UUID | None = None
    mission_id: UUID | None = None


class BusinessDiagnosticRead(BusinessDiagnosticBase):
    id: UUID
    user_id: UUID
    business_id: UUID | None = None
    mission_id: UUID | None = None
    diagnostic_date: datetime
    is_resolved: bool
    resolved_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Playbook ──────────────────────────────────────────────────────────────────

class PlaybookStep(BaseModel):
    platform: str
    action_type: str
    title: str
    description: str | None = None
    url_template: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class PlaybookRead(BaseModel):
    slug: str
    name: str
    description: str
    category: str
    platforms: list[str]
    estimated_duration_minutes: int
    steps: list[PlaybookStep]


# ─── Mission Launch / Approval ─────────────────────────────────────────────────

class MissionLaunchRequest(BaseModel):
    playbook_slug: str | None = None
    custom_description: str | None = None
    business_id: UUID | None = None
    auto_approve_low_impact: bool = True


class MissionApproveRequest(BaseModel):
    approve_all_steps: bool = False
    approved_step_ids: list[UUID] = Field(default_factory=list)


# ─── Diagnostic Run ────────────────────────────────────────────────────────────

class DiagnosticRunRequest(BaseModel):
    business_id: UUID | None = None
    categories: list[str] = Field(default_factory=list)  # vacío = todas


class DiagnosticRunResponse(BaseModel):
    diagnostics: list[BusinessDiagnosticRead]
    critical_count: int
    warning_count: int
    info_count: int
    recommended_missions: list[PlaybookRead]
