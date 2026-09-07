"""Compliance API."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.compliance.compliance_service import ComplianceService

router = APIRouter(prefix="/api/v1", tags=["compliance"])


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    """Same convention as websites.py/catalog.py/channels.py/conversations.py.

    Every route below had zero authentication until this fix -- anyone
    could set/read consent, or file an export/deletion request, for any
    customer under any business_id. Fairly ironic for the GDPR/CCPA
    compliance module specifically: the endpoints meant to protect
    customer privacy were themselves the leak.
    """
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.user_id == user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


class SetConsentRequest(BaseModel):
    consent_type: str
    consented: bool


class ExportRequest(BaseModel):
    export_format: str = "json"


class DeletionRequest(BaseModel):
    deletion_type: str = "full"


@router.post("/customers/{customer_id}/consent")
async def set_consent(
    customer_id: UUID,
    business_id: UUID,
    request: SetConsentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await ComplianceService.set_consent(business_id, customer_id, request.consent_type, request.consented, db)


@router.post("/customers/{customer_id}/export-data")
async def request_export(
    customer_id: UUID,
    business_id: UUID,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await ComplianceService.request_data_export(business_id, customer_id, request.export_format, db)


@router.post("/customers/{customer_id}/delete-data")
async def request_deletion(
    customer_id: UUID,
    business_id: UUID,
    request: DeletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await ComplianceService.request_data_deletion(business_id, customer_id, request.deletion_type, db)


@router.get("/customers/{customer_id}/consent-status")
async def get_consent_status(
    customer_id: UUID,
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await ComplianceService.get_consent_status(business_id, customer_id, db)
