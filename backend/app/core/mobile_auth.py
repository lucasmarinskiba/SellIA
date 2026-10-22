"""Who may call the mobile endpoints: a scoped device token, or the signed-in user while the legacy path is open.

The SDKs used to send the account's login JWT, which opens everything that account owns. A device token is issued
per business or location, names only the operations the SDK needs, and expires or can be revoked.

MOBILE_LEGACY_USER_JWT_ENABLED keeps the JWT path open for apps already installed. Turn it off once the apps have
moved to device tokens; with it off, a JWT is refused on these routes.
"""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_location_access
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.domains.businesses.location_models import Location
from app.domains.businesses.mobile_device_service import TOKEN_PREFIX, resolve
from app.domains.users.models import User


@dataclass(frozen=True)
class MobileCaller:
    user: User | None = None
    device_token_id: UUID | None = None
    business_id: UUID | None = None
    # None on a device token means every location of its business.
    location_id: UUID | None = None

    @property
    def is_device(self) -> bool:
        return self.user is None


def require_mobile_caller(scope: str):
    """Dependency factory: the caller must hold a device token with ``scope``, or be a signed-in user (legacy)."""

    async def _caller(
        request: Request,
        user: User | None = Depends(get_current_user_optional),
        db: AsyncSession = Depends(get_db),
    ) -> MobileCaller:
        scheme, _, credential = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() == "bearer" and credential.startswith(TOKEN_PREFIX):
            access = await resolve(db, credential, scope)
            return MobileCaller(
                device_token_id=access.token_id,
                business_id=access.business_id,
                location_id=access.location_id,
            )
        if user is not None and get_settings().MOBILE_LEGACY_USER_JWT_ENABLED:
            return MobileCaller(user=user)
        raise HTTPException(
            status_code=401,
            detail="Se requiere un token de dispositivo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _caller


async def authorize_location(db: AsyncSession, location_id: UUID, caller: MobileCaller) -> Location:
    """The location, when the caller may act on it. Device tokens need the same business and, if bound, the same location."""
    if caller.user is not None:
        return await require_location_access(db, location_id, caller.user)
    location = await db.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    if location.business_id != caller.business_id or caller.location_id not in (None, location.id):
        raise HTTPException(status_code=403, detail="El token no tiene acceso a esta sucursal")
    return location
