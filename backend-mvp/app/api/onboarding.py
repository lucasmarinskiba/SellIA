"""Tenant onboarding · claim subdomain · public lookup."""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.security import CurrentUser, require_role
from app.db.models import Tenant
from app.db.session import get_session


router = APIRouter()

SUBDOMAIN_REGEX = re.compile(r"^[a-z][a-z0-9-]{1,61}[a-z0-9]$")
RESERVED_SUBDOMAINS = {
    "www", "api", "app", "admin", "dashboard", "auth", "login", "signup",
    "billing", "docs", "blog", "help", "status", "mail", "ftp", "stripe",
    "webhook", "webhooks", "static", "cdn", "assets", "sellia",
}


def _validate_subdomain(sub: str) -> str:
    s = sub.strip().lower()
    if not SUBDOMAIN_REGEX.match(s):
        raise HTTPException(status_code=422, detail="Subdomain must be 3-63 chars · lowercase · letters/digits/hyphens · start with letter")
    if s in RESERVED_SUBDOMAINS:
        raise HTTPException(status_code=409, detail=f"Subdomain '{s}' is reserved")
    return s


class SubdomainCheckResponse(BaseModel):
    subdomain: str
    available: bool
    reason: str | None = None


@router.get("/subdomain/check", response_model=SubdomainCheckResponse)
async def check_subdomain(subdomain: str) -> SubdomainCheckResponse:
    """Public endpoint · returns availability of subdomain."""
    try:
        s = _validate_subdomain(subdomain)
    except HTTPException as e:
        return SubdomainCheckResponse(subdomain=subdomain, available=False, reason=e.detail)

    async with get_session() as db:
        result = await db.execute(select(Tenant.id).where(Tenant.subdomain == s))
        taken = result.scalar_one_or_none()

    if taken:
        return SubdomainCheckResponse(subdomain=s, available=False, reason="Subdomain already taken")
    return SubdomainCheckResponse(subdomain=s, available=True)


class SubdomainClaimRequest(BaseModel):
    subdomain: str = Field(min_length=3, max_length=63)


@router.post("/subdomain", response_model=SubdomainCheckResponse, status_code=201)
async def claim_subdomain(
    payload: SubdomainClaimRequest,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> SubdomainCheckResponse:
    """Claim subdomain for current tenant. One-shot · only first time."""
    s = _validate_subdomain(payload.subdomain)

    async with get_session(tenant_id=user.tenant_id) as db:
        # Check global uniqueness
        result = await db.execute(select(Tenant).where(Tenant.subdomain == s))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Subdomain already taken")

        # Get tenant + claim
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one()
        if tenant.subdomain:
            raise HTTPException(status_code=409, detail=f"Tenant already has subdomain: {tenant.subdomain}")

        tenant.subdomain = s
        await db.flush()

    return SubdomainCheckResponse(subdomain=s, available=False, reason="Claimed")


class TenantPublicInfo(BaseModel):
    id: str
    name: str
    plan: str


@router.get("/by-subdomain/{subdomain}", response_model=TenantPublicInfo)
async def get_tenant_by_subdomain(subdomain: str) -> TenantPublicInfo:
    """Public lookup · used by frontend middleware to resolve {subdomain}.sellia.app."""
    s = subdomain.strip().lower()
    async with get_session() as db:
        result = await db.execute(select(Tenant).where(Tenant.subdomain == s))
        tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantPublicInfo(id=str(tenant.id), name=tenant.name, plan=tenant.plan)
