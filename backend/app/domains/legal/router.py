"""Legal API — /api/v1/businesses/{business_id}/legal/*"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.legal.schemas import (
    AuditLogOut,
    ComplianceChecklistItemCreate,
    ComplianceChecklistItemOut,
    ComplianceChecklistItemUpdate,
    ComplianceStatusResponse,
    ContractRenderRequest,
    ContractRenderOut,
    ContractTemplateCreate,
    ContractTemplateOut,
)
from app.domains.legal.service import AuditLogService, ComplianceService, ContractService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/legal", tags=["Legal"])


# Compliance
@router.post("/compliance", response_model=ComplianceChecklistItemOut)
async def add_compliance_requirement(
    business_id: UUID,
    body: ComplianceChecklistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add compliance requirement."""
    svc = ComplianceService(db)
    return await svc.add_requirement(business_id, body.category, body.requirement, body.jurisdiction)


@router.get("/compliance/{item_id}", response_model=ComplianceChecklistItemOut)
async def get_compliance_requirement(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get compliance requirement."""
    svc = ComplianceService(db)
    return await svc.get_requirement(item_id)


@router.patch("/compliance/{item_id}", response_model=ComplianceChecklistItemOut)
async def update_compliance_status(
    business_id: UUID,
    item_id: UUID,
    body: ComplianceChecklistItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update compliance requirement status."""
    svc = ComplianceService(db)
    return await svc.update_status(item_id, body.status, body.verified_by, body.notes)


@router.get("/compliance/status", response_model=ComplianceStatusResponse)
async def get_compliance_status(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get compliance overview."""
    svc = ComplianceService(db)
    status = await svc.compliance_status(business_id)
    return ComplianceStatusResponse(**status)


# Contracts
@router.post("/contracts", response_model=ContractTemplateOut)
async def create_contract_template(
    business_id: UUID,
    body: ContractTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create contract template."""
    svc = ContractService(db)
    return await svc.create_template(business_id, body.name, body.contract_type, body.template_html)


@router.get("/contracts", response_model=list[ContractTemplateOut])
async def list_contract_templates(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List contract templates."""
    svc = ContractService(db)
    return await svc.list_templates(business_id)


@router.post("/contracts/{template_id}/render", response_model=ContractRenderOut)
async def render_contract(
    business_id: UUID,
    template_id: UUID,
    body: ContractRenderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Render contract with variables."""
    svc = ContractService(db)
    return await svc.render_contract(template_id, body.variables)


# Audit Logs
@router.get("/audit", response_model=list[AuditLogOut])
async def get_audit_logs(
    business_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit logs."""
    svc = AuditLogService(db)
    return await svc.get_logs(business_id, limit)
