"""Access checks for endpoints that take a business_id / location_id from the client.

A business_id or location_id in a URL or body is only an identifier: nothing in it
proves the caller may touch it, so without one of these checks any logged-in user
can read or write any other business's data by changing the id (an IDOR). 404 when
the id is unknown, 403 when it belongs to someone else.

Two flavours:

* ``get_owned_*`` -- owner only (Business.user_id). Used by the inventory, geofence
  and dashboard routers.
* ``require_*_access`` -- the owner, or an active BusinessMember. ``manage=True``
  narrows that to the owner and members with the ADMIN role. Used by the routers
  whose callers are the business's staff (tasks, alerts, pricing).
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.users.models import User

_NO_ACCESS = "No tenés acceso a este negocio"


async def get_owned_business(
    db: AsyncSession, business_id: UUID, user: User
) -> Business:
    business = await db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    if business.user_id != user.id:
        raise HTTPException(status_code=403, detail=_NO_ACCESS)
    return business


async def get_owned_location(
    db: AsyncSession, location_id: UUID, user: User
) -> Location:
    location = await db.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    await get_owned_business(db, location.business_id, user)
    return location


async def _active_membership(db: AsyncSession, business_id: UUID, user_id: UUID) -> BusinessMember | None:
    return (
        await db.execute(
            select(BusinessMember).where(
                BusinessMember.business_id == business_id,
                BusinessMember.user_id == user_id,
                BusinessMember.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()


async def require_business_access(
    db: AsyncSession, business_id: UUID, user: User, *, manage: bool = False
) -> Business:
    """The owner, or an active member (an ADMIN member when ``manage``)."""
    business = await db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    if business.user_id == user.id:
        return business
    member = await _active_membership(db, business_id, user.id)
    if member is None:
        raise HTTPException(status_code=403, detail=_NO_ACCESS)
    if manage and member.role != BusinessMemberRole.ADMIN:
        raise HTTPException(status_code=403, detail="Necesitás ser administrador de este negocio")
    return business


async def require_location_access(
    db: AsyncSession, location_id: UUID, user: User, *, manage: bool = False
) -> Location:
    location = await db.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    await require_business_access(db, location.business_id, user, manage=manage)
    return location


async def is_business_participant(db: AsyncSession, business_id: UUID, user_id: UUID) -> bool:
    """Is this user the owner or an active member? (e.g. before assigning them work)"""
    business = await db.get(Business, business_id)
    if business is None:
        return False
    if business.user_id == user_id:
        return True
    return await _active_membership(db, business_id, user_id) is not None


async def accessible_business_ids(db: AsyncSession, user: User, *, manage: bool = False) -> set[UUID]:
    """Every business the user may act in: the ones they own plus their active memberships
    (ADMIN-only when ``manage``). Used to narrow lists that span businesses."""
    member_roles = [BusinessMemberRole.ADMIN] if manage else list(BusinessMemberRole)
    rows = await db.execute(
        select(Business.id)
        .outerjoin(
            BusinessMember,
            (BusinessMember.business_id == Business.id)
            & (BusinessMember.user_id == user.id)
            & (BusinessMember.is_active.is_(True))
            & (BusinessMember.role.in_(member_roles)),
        )
        .where(or_(Business.user_id == user.id, BusinessMember.id.is_not(None)))
    )
    return set(rows.scalars().all())


async def staff_scope(db: AsyncSession, staff_id: UUID, user: User) -> set[UUID]:
    """Businesses in which ``user`` may look at ``staff_id``'s work.

    Yourself: every business you belong to. Someone else: only the ones you manage --
    a staff member can work for several businesses and must not leak across them.
    """
    if staff_id == user.id:
        return await accessible_business_ids(db, user)
    scope = await accessible_business_ids(db, user, manage=True)
    if not scope:
        raise HTTPException(status_code=403, detail="No tenés acceso al trabajo de esta persona")
    return scope
