"""Tenant settings."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.core.security import CurrentUser, get_current_user, require_role
from app.db.models import Tenant
from app.db.session import get_session


router = APIRouter()


class TenantOut(BaseModel):
    id: str
    name: str
    plan: str
    settings: dict


@router.get("/me", response_model=TenantOut)
async def get_my_tenant(user: CurrentUser = Depends(get_current_user)) -> TenantOut:
    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one()
        return TenantOut(
            id=str(tenant.id),
            name=tenant.name,
            plan=tenant.plan,
            settings=tenant.settings or {},
        )


@router.patch("/me", response_model=TenantOut)
async def update_tenant_settings(
    settings: dict,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> TenantOut:
    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one()
        tenant.settings = {**(tenant.settings or {}), **settings}
        await db.flush()
        return TenantOut(
            id=str(tenant.id),
            name=tenant.name,
            plan=tenant.plan,
            settings=tenant.settings,
        )
