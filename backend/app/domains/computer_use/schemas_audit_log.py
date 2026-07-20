"""Audit Log Schemas — API request/response models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: str
    user_id: str
    session_id: Optional[str] = None

    created_at: datetime
    executed_at: Optional[datetime] = None
    duration_ms: int

    platform: str
    action_type: str

    agent_name: Optional[str] = None
    strategy_name: Optional[str] = None
    tactics: Optional[List[str]] = None

    confidence_score: float
    status: str  # success, pending_approval, failed, escalated

    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None

    user_approved: Optional[bool] = None
    approval_at: Optional[datetime] = None

    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs with pagination."""

    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditLogSearchRequest(BaseModel):
    """Search/filter request."""

    platform: Optional[str] = None
    action_type: Optional[str] = None
    agent_name: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class AuditLogApprovalRequest(BaseModel):
    """Approve/reject an action."""

    log_id: str
    approved: bool
    reason: Optional[str] = None


class AuditLogSummaryResponse(BaseModel):
    """Summary statistics."""

    period_days: int
    total_actions: int
    by_platform: Dict[str, Dict[str, Any]]
    by_action: Dict[str, Dict[str, Any]]
    by_status: Dict[str, int]
