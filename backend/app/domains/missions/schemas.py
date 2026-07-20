"""SellIA Missions — Schemas"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# ─── MissionStep ───────────────────────────────────────────────────────────────

class MissionStepBase(BaseModel):
    step_number: int = 1
    title: str
    description: Optional[str] = None
    platform: str  # "instagram", "computer_use", "api"
    action_type: str
    action_params: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class MissionStepCreate(MissionStepBase):
    pass


class MissionStepUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    approved_by_user: Optional[bool] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MissionStepRead(MissionStepBase):
    id: UUID
    mission_id: UUID
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    approved_by_user: bool
    computer_use_session_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Mission ───────────────────────────────────────────────────────────────────

class MissionBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str  # "launch", "seo", "ads", "recovery", "expansion", "branding", "logistics", "automation"
    playbook_slug: Optional[str] = None
    target_platforms: List[str] = Field(default_factory=list)
    expected_impact: Dict[str, Any] = Field(default_factory=dict)


class MissionCreate(MissionBase):
    business_id: Optional[UUID] = None
    created_by: str = "ai"
    steps: List[MissionStepCreate] = Field(default_factory=list)


class MissionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MissionRead(MissionBase):
    id: UUID
    user_id: UUID
    business_id: Optional[UUID] = None
    status: str
    created_by: str
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    steps: List[MissionStepRead] = Field(default_factory=list)
    progress_percent: int = 0

    class Config:
        from_attributes = True


# ─── BusinessDiagnostic ────────────────────────────────────────────────────────

class BusinessDiagnosticBase(BaseModel):
    category: str
    severity: str
    finding: str
    metric_value: Optional[str] = None
    benchmark_value: Optional[str] = None
    recommended_mission_slug: Optional[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)


class BusinessDiagnosticCreate(BusinessDiagnosticBase):
    business_id: Optional[UUID] = None
    mission_id: Optional[UUID] = None


class BusinessDiagnosticRead(BusinessDiagnosticBase):
    id: UUID
    user_id: UUID
    business_id: Optional[UUID] = None
    mission_id: Optional[UUID] = None
    diagnostic_date: datetime
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Playbook ──────────────────────────────────────────────────────────────────

class PlaybookStep(BaseModel):
    platform: str
    action_type: str
    title: str
    description: Optional[str] = None
    url_template: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class PlaybookRead(BaseModel):
    slug: str
    name: str
    description: str
    category: str
    platforms: List[str]
    estimated_duration_minutes: int
    steps: List[PlaybookStep]


# ─── Mission Launch / Approval ─────────────────────────────────────────────────

class MissionLaunchRequest(BaseModel):
    playbook_slug: Optional[str] = None
    custom_description: Optional[str] = None
    business_id: Optional[UUID] = None
    auto_approve_low_impact: bool = True


class MissionApproveRequest(BaseModel):
    approve_all_steps: bool = False
    approved_step_ids: List[UUID] = Field(default_factory=list)


# ─── Diagnostic Run ────────────────────────────────────────────────────────────

class DiagnosticRunRequest(BaseModel):
    business_id: Optional[UUID] = None
    categories: List[str] = Field(default_factory=list)  # vacío = todas


class DiagnosticRunResponse(BaseModel):
    diagnostics: List[BusinessDiagnosticRead]
    critical_count: int
    warning_count: int
    info_count: int
    recommended_missions: List[PlaybookRead]
