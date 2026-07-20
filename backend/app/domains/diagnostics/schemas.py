from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DiagnosticRunCreate(BaseModel):
    diagnostic_type: str


class DiagnosticRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    diagnostic_type: str
    status: str
    findings: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    severity: str
    created_at: datetime
    completed_at: datetime | None
