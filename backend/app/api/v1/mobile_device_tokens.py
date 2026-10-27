"""Issue, list and revoke device tokens for the mobile SDKs. Owners and ADMIN members only.

The token value is returned once, on issue. Listing shows metadata only.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.businesses.location_models import Location
from app.domains.businesses.mobile_device_models import MobileDeviceToken
from app.domains.businesses.mobile_device_service import (
    DEFAULT_TTL_DAYS,
    MAX_TTL_DAYS,
    issue,
    list_for_business,
    revoke,
)
from app.domains.users.models import User

router = APIRouter(prefix="/api/v1", tags=["mobile-device-tokens"])

ScopeName = Literal["checkin", "checkout", "feedback", "geofence"]


class DeviceTokenCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    location_id: UUID | None = None
    scopes: list[ScopeName] = Field(min_length=1, max_length=4)
    expires_in_days: int = Field(default=DEFAULT_TTL_DAYS, ge=1, le=MAX_TTL_DAYS)


class DeviceTokenOut(BaseModel):
    id: UUID
    label: str
    location_id: UUID | None
    scopes: list[str]
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class DeviceTokenIssued(DeviceTokenOut):
    token: str = Field(description="Shown once. Store it in the app; it cannot be retrieved later.")


def _out(row: MobileDeviceToken) -> DeviceTokenOut:
    return DeviceTokenOut(
        id=row.id,
        label=row.label,
        location_id=row.location_id,
        scopes=list(row.scopes),
        created_at=row.created_at,
        expires_at=row.expires_at,
        last_used_at=row.last_used_at,
        revoked_at=row.revoked_at,
    )


@router.post(
    "/businesses/{business_id}/mobile-device-tokens",
    response_model=DeviceTokenIssued,
    status_code=status.HTTP_201_CREATED,
)
async def issue_device_token(
    business_id: UUID,
    body: DeviceTokenCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceTokenIssued:
    await require_business_access(db, business_id, user, manage=True)
    if body.location_id is not None:
        location = await db.get(Location, body.location_id)
        if location is None or location.business_id != business_id:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada en este negocio")
    raw, row = await issue(
        db,
        business_id=business_id,
        label=body.label,
        scopes=list(body.scopes),
        location_id=body.location_id,
        ttl_days=body.expires_in_days,
        created_by_user_id=user.id,
    )
    return DeviceTokenIssued(**_out(row).model_dump(), token=raw)


@router.get("/businesses/{business_id}/mobile-device-tokens", response_model=list[DeviceTokenOut])
async def list_device_tokens(
    business_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DeviceTokenOut]:
    await require_business_access(db, business_id, user, manage=True)
    return [_out(row) for row in await list_for_business(db, business_id)]


@router.post(
    "/businesses/{business_id}/mobile-device-tokens/{token_id}/revoke",
    response_model=DeviceTokenOut,
)
async def revoke_device_token(
    business_id: UUID,
    token_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceTokenOut:
    await require_business_access(db, business_id, user, manage=True)
    row = await revoke(db, business_id=business_id, token_id=token_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Token no encontrado")
    return _out(row)
