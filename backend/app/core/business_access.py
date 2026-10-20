"""Ownership checks for endpoints that take a business_id / location_id from the client.

A business_id or location_id in a URL or body is only an identifier: nothing in it
proves the caller owns it, so without one of these checks any logged-in user can
read or write any other business's data by changing the id (an IDOR). Same rule
as seo_config's ``verify_business_access``: 404 when the id is unknown, 403 when
it belongs to someone else.
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.users.models import User


async def get_owned_business(db: AsyncSession, business_id: UUID, user: User) -> Business:
    business = await db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    if business.user_id != user.id:
        raise HTTPException(status_code=403, detail="No tenés acceso a este negocio")
    return business


async def get_owned_location(db: AsyncSession, location_id: UUID, user: User) -> Location:
    location = await db.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    await get_owned_business(db, location.business_id, user)
    return location
