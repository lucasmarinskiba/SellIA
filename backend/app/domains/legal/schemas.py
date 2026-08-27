"""Legal domain schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ComplianceChecklistItemCreate(BaseModel):
    """Create compliance requirement."""
    category: str = Field(..., min_length=1, max_length=100)
    requirement: str = Field(..., min_length=1, max_length=500)
    jurisdiction: str = Field(default="AE", max_length=50)


class ComplianceChecklistItemUpdate(BaseModel):
    """Update compliance requirement status."""
    status: str = Field(..., pattern="^(pending|compliant|non_compliant|waived)$")
    verified_by: str | None = Field(None, max_length=255)
    notes: str | None = None


class ComplianceChecklistItemOut(BaseModel):
    """Compliance requirement response."""
    id: UUID
    business_id: UUID
    category: str
    requirement: str
    jurisdiction: str
    status: str
    verified_at: datetime | None
    verified_by: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ContractTemplateCreate(BaseModel):
    """Create contract template."""
    name: str = Field(..., min_length=1, max_length=255)
    contract_type: str = Field(..., min_length=1, max_length=50)
    template_html: str = Field(..., min_length=1)


class ContractTemplateOut(BaseModel):
    """Contract template response."""
    id: UUID
    business_id: UUID
    name: str
    contract_type: str
    template_html: str
    version: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContractRenderRequest(BaseModel):
    """Render contract with variables."""
    variables: dict[str, str] = Field(..., description="Variables to replace in template")


class ContractRenderOut(BaseModel):
    """Rendered contract."""
    template_id: UUID
    contract_type: str
    rendered_html: str
    created_at: datetime


class AuditLogOut(BaseModel):
    """Audit log response."""
    id: UUID
    business_id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    actor: str
    details: dict | None
    timestamp: datetime

    class Config:
        from_attributes = True


class ComplianceStatusResponse(BaseModel):
    """Compliance status overview."""
    total_requirements: int
    compliant: int
    non_compliant: int
    pending: int
    waived: int
    compliance_pct: float
    non_compliant_items: list[ComplianceChecklistItemOut]
