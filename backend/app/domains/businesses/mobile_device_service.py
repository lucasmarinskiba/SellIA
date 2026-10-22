"""Device tokens for the mobile SDKs.

A token is scoped to one business, or to one location of it; names the SDK operations it may perform; expires
and can be revoked. Only its SHA-256 is stored.

The token still ships inside the host app, so whoever extracts it from the binary can use it until it expires or
is revoked. The scope limits the damage: one location, a few operations, a fixed lifetime. It does not hide the
token. The account login JWT that the SDKs used to send opens everything the account owns, which is the risk
this replaces.
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.mobile_device_models import MobileDeviceToken

TOKEN_PREFIX = "sdt_"
SCOPES = frozenset({"checkin", "checkout", "feedback", "geofence"})
DEFAULT_TTL_DAYS = 90
MAX_TTL_DAYS = 365
# The geofence poll runs every 30-60 s; writing last_used_at on each call would be a write per poll.
LAST_USED_WRITE_EVERY = timedelta(minutes=10)


@dataclass(frozen=True)
class DeviceAccess:
    """Plain values read from a verified token. Taken before any commit, so no ORM instance is touched afterwards."""

    token_id: UUID
    business_id: UUID
    location_id: UUID | None
    scopes: frozenset[str]


def new_token() -> str:
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def visitor_id(device_token_id: UUID, visitor_ref: str) -> UUID:
    """Stable visitor identity for one phone, derived from the device token and the ref the app sends.

    The same token and ref always give the same UUID, so a phone keeps one visitor identity. No personal data is
    stored, and the same ref under another token gives a different identity.
    """
    return uuid5(NAMESPACE_URL, f"sellia-mobile-visitor:{device_token_id}:{visitor_ref}")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})


async def issue(
    db: AsyncSession,
    *,
    business_id: UUID,
    label: str,
    scopes: list[str],
    location_id: UUID | None,
    ttl_days: int,
    created_by_user_id: UUID | None,
) -> tuple[str, MobileDeviceToken]:
    unknown = set(scopes) - SCOPES
    if not scopes or unknown:
        raise ValueError(f"scopes no válidos: {sorted(unknown) if unknown else 'vacío'}")
    raw = new_token()
    row = MobileDeviceToken(
        business_id=business_id,
        location_id=location_id,
        label=label,
        token_hash=hash_token(raw),
        scopes=sorted(set(scopes)),
        created_by_user_id=created_by_user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=ttl_days),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return raw, row


async def resolve(db: AsyncSession, raw: str, scope: str) -> DeviceAccess:
    """Verify a presented token for one operation. Raises 401 when unknown, revoked or expired; 403 out of scope."""
    now = datetime.now(timezone.utc)
    row = (
        await db.execute(select(MobileDeviceToken).where(MobileDeviceToken.token_hash == hash_token(raw)))
    ).scalar_one_or_none()
    if row is None:
        raise _unauthorized("Token de dispositivo inválido")
    if row.revoked_at is not None:
        raise _unauthorized("Token de dispositivo revocado")
    if row.expires_at <= now:
        raise _unauthorized("Token de dispositivo vencido")
    access = DeviceAccess(
        token_id=row.id,
        business_id=row.business_id,
        location_id=row.location_id,
        scopes=frozenset(row.scopes),
    )
    if scope not in access.scopes:
        raise HTTPException(status_code=403, detail="El token no permite esta operación")
    if row.last_used_at is None or now - row.last_used_at >= LAST_USED_WRITE_EVERY:
        row.last_used_at = now
        await db.commit()
    return access


async def revoke(db: AsyncSession, *, business_id: UUID, token_id: UUID) -> MobileDeviceToken | None:
    row = (
        await db.execute(
            select(MobileDeviceToken).where(
                MobileDeviceToken.id == token_id,
                MobileDeviceToken.business_id == business_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    await db.refresh(row)
    return row


async def list_for_business(db: AsyncSession, business_id: UUID) -> list[MobileDeviceToken]:
    result = await db.execute(
        select(MobileDeviceToken)
        .where(MobileDeviceToken.business_id == business_id)
        .order_by(MobileDeviceToken.created_at.desc())
    )
    return list(result.scalars().all())
