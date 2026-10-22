"""Audit Log Schemas — API request/response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: str
    user_id: str
    session_id: str | None = None

    created_at: datetime
    executed_at: datetime | None = None
    duration_ms: int

    platform: str
    action_type: str

    agent_name: str | None = None
    strategy_name: str | None = None
    tactics: list[str] | None = None

    confidence_score: float
    status: str  # success, pending_approval, failed, escalated

    input_data: str | None = None
    output_data: str | None = None
    error_message: str | None = None

    user_approved: bool | None = None
    approval_at: datetime | None = None

    extra_data: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs with pagination."""

    logs: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditLogSearchRequest(BaseModel):
    """Search/filter request."""

    platform: str | None = None
    action_type: str | None = None
    agent_name: str | None = None
    status: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class AuditLogApprovalRequest(BaseModel):
    """Approve/reject an action."""

    log_id: str
    approved: bool
    reason: str | None = None


class AuditLogSummaryResponse(BaseModel):
    """Summary statistics."""

    period_days: int
    total_actions: int
    by_platform: dict[str, dict[str, Any]]
    by_action: dict[str, dict[str, Any]]
    by_status: dict[str, int]
