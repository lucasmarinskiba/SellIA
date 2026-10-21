"""Tenant management API — isolation, audit, compliance."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.tenancy.tenant_service import TenantIsolationService

router = APIRouter(prefix="/api/v1", tags=["tenant-management"])


class SetupIsolationPolicyRequest(BaseModel):
    isolation_level: str = "row_level"  # row_level, schema_level, database_level
    audit_enabled: bool = True
    gdpr_mode: bool = False
    ccpa_mode: bool = False


class AddTenantUserRequest(BaseModel):
    email: str
    role: str = "member"  # owner, admin, analyst, member
    permissions: list[str] | None = None


class LogDataAccessRequest(BaseModel):
    access_type: str  # export, download, api_access, report_view
    data_type: str  # customers, orders, segments, etc
    rows_accessed: int | None = None
    pii_included: bool = False


@router.post("/businesses/{business_id}/isolation-policy")
def setup_isolation_policy(
    business_id: UUID,
    request: SetupIsolationPolicyRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Configure tenant isolation policy."""
    return TenantIsolationService.setup_isolation_policy(
        business_id=business_id,
        isolation_level=request.isolation_level,
        audit_enabled=request.audit_enabled,
        gdpr_mode=request.gdpr_mode,
        ccpa_mode=request.ccpa_mode,
        db=db
    )


@router.post("/businesses/{business_id}/tenant-users")
def add_tenant_user(
    business_id: UUID,
    request: AddTenantUserRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Add user to business tenant."""
    return TenantIsolationService.add_tenant_user(
        business_id=business_id,
        email=request.email,
        role=request.role,
        permissions=request.permissions,
        db=db
    )


@router.post("/businesses/{business_id}/log-data-access")
def log_data_access(
    business_id: UUID,
    user_email: Annotated[str, Query()],
    db: Annotated[Session, Depends(get_db)],
    request: LogDataAccessRequest = None,
    user_ip: Annotated[str | None, Query()] = None,
):
    """Log data access event."""
    return TenantIsolationService.log_data_access(
        business_id=business_id,
        access_type=request.access_type,
        data_type=request.data_type,
        user_email=user_email,
        user_ip=user_ip,
        rows_accessed=request.rows_accessed,
        pii_included=request.pii_included,
        db=db
    )


@router.get("/businesses/{business_id}/audit-trail")
def get_audit_trail(
    business_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    action_filter: Annotated[str | None, Query()] = None,
    user_filter: Annotated[str | None, Query()] = None,
):
    """Get audit trail for tenant."""
    return TenantIsolationService.get_audit_trail(
        business_id=business_id,
        days=days,
        action_filter=action_filter,
        user_filter=user_filter,
        db=db
    )


@router.post("/businesses/{business_id}/compliance-report")
def generate_compliance_report(
    business_id: UUID,
    report_type: Annotated[str, Query()],  # audit_trail, gdpr_dsar, ccpa_dsar
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    """Generate compliance report."""
    return TenantIsolationService.generate_compliance_report(
        business_id=business_id,
        report_type=report_type,
        days=days,
        db=db
    )
