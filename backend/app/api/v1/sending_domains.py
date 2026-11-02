"""A business's own sending domain: register it, show the DNS records to add, and ask for verification.

Read by members; changed by owners and ADMIN members. Post-visit mail is sent from this domain only once it is
verified (app/domains/sequences/sending_identity.py).
"""

import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.integrations.resend_domains import (
    ResendError,
    ResendNotConfigured,
    create_domain,
    get_domain,
    verify_domain,
)
from app.domains.sequences.sending_domain_models import BusinessSendingDomain
from app.domains.users.models import User

router = APIRouter(prefix="/api/v1", tags=["sending-domains"])

# Lowercase host name with at least one dot, e.g. concesionaria.com.ar. No IP literals, no single labels.
DOMAIN_RE = re.compile(r"^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
# The local part of the sending address, e.g. "ventas" in ventas@concesionaria.com.ar.
LOCAL_PART_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

# Resend statuses that mean something to us; anything else is still pending.
_VERIFIED = "verified"
_FAILED = {"failed", "temporary_failure"}


class SendingDomainIn(BaseModel):
    domain: str = Field(min_length=4, max_length=253)
    local_part: str = Field(default="ventas", min_length=1, max_length=64)


class SendingDomainOut(BaseModel):
    configured: bool
    domain: str | None = None
    local_part: str | None = None
    from_address: str | None = None
    status: str | None = None
    records: list[dict] = Field(default_factory=list)
    verified_at: datetime | None = None


def _out(row: BusinessSendingDomain | None) -> SendingDomainOut:
    if row is None:
        return SendingDomainOut(configured=False)
    return SendingDomainOut(
        configured=True,
        domain=row.domain,
        local_part=row.local_part,
        from_address=f"{row.local_part}@{row.domain}",
        status=row.status,
        records=list(row.records or []),
        verified_at=row.verified_at,
    )


def _map_status(raw: str | None) -> str:
    if raw == _VERIFIED:
        return "verified"
    if raw in _FAILED:
        return "failed"
    return "pending"


async def _current(db: AsyncSession, business_id: UUID) -> BusinessSendingDomain | None:
    return (
        await db.execute(select(BusinessSendingDomain).where(BusinessSendingDomain.business_id == business_id))
    ).scalars().first()


def _resend_error(error: Exception) -> HTTPException:
    if isinstance(error, ResendNotConfigured):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo hablar con el proveedor de email")


@router.get("/businesses/{business_id}/sending-domain", response_model=SendingDomainOut)
async def read_sending_domain(
    business_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendingDomainOut:
    await require_business_access(db, business_id, user)
    return _out(await _current(db, business_id))


@router.put("/businesses/{business_id}/sending-domain", response_model=SendingDomainOut)
async def register_sending_domain(
    business_id: UUID,
    body: SendingDomainIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendingDomainOut:
    await require_business_access(db, business_id, user, manage=True)
    domain = body.domain.strip().lower()
    local_part = body.local_part.strip().lower()
    if not DOMAIN_RE.match(domain):
        raise HTTPException(status_code=422, detail="Dominio no válido, por ejemplo concesionaria.com.ar")
    if not LOCAL_PART_RE.match(local_part):
        raise HTTPException(status_code=422, detail="El alias sólo lleva letras, números, punto, guion y guion bajo")

    row = await _current(db, business_id)
    if row is None or row.domain != domain or not row.resend_domain_id:
        try:
            created = await create_domain(domain)
        except (ResendNotConfigured, ResendError) as error:
            raise _resend_error(error) from None
        if row is None:
            row = BusinessSendingDomain(business_id=business_id)
            db.add(row)
        row.domain = domain
        row.resend_domain_id = created.get("id")
        row.records = created.get("records") or []
        row.status = _map_status(created.get("status"))
        row.verified_at = None
    row.local_part = local_part
    await db.commit()
    return _out(row)


@router.post("/businesses/{business_id}/sending-domain/verify", response_model=SendingDomainOut)
async def verify_sending_domain(
    business_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SendingDomainOut:
    """Ask Resend to check the DNS records, then read back the status. Verification can take a while to propagate."""
    await require_business_access(db, business_id, user, manage=True)
    row = await _current(db, business_id)
    if row is None or not row.resend_domain_id:
        raise HTTPException(status_code=404, detail="Este negocio todavía no registró un dominio de envío")
    try:
        await verify_domain(row.resend_domain_id)
        data = await get_domain(row.resend_domain_id)
    except (ResendNotConfigured, ResendError) as error:
        raise _resend_error(error) from None
    row.status = _map_status(data.get("status"))
    row.records = data.get("records") or row.records
    if row.status == "verified" and row.verified_at is None:
        row.verified_at = datetime.now(timezone.utc)
    if row.status != "verified":
        row.verified_at = None
    await db.commit()
    return _out(row)
