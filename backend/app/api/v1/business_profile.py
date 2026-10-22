"""The profile of one business: what it sells, to whom, and in which language. Read by members, edited by managers."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.business_context.business_profile import (
    get_or_create_profile,
    update_profile,
)
from app.domains.business_context.models import (
    BusinessType,
    GeographicReach,
    PresenceType,
    SalesModel,
)
from app.domains.businesses.location_models import Location
from app.domains.sequences.offline_sequence_jobs import resolve_language
from app.domains.users.models import User

router = APIRouter(prefix="/api/v1", tags=["business-profile"])


class ProfileLocations(BaseModel):
    count: int
    countries: list[str]
    cities: list[str]


class ProfileOut(BaseModel):
    business_id: UUID
    name: str
    language: str
    business_type: BusinessType
    sales_model: SalesModel
    geographic_reach: GeographicReach
    presence_type: PresenceType
    industry: str | None
    target_audience: str | None
    value_proposition: str | None
    price_range: str | None
    primary_goal: str | None
    has_physical_location: bool
    does_delivery: bool
    does_pickup: bool
    locations: ProfileLocations


class ProfileUpdate(BaseModel):
    """Every field optional. Omitted or null means no change."""

    language: Literal["es", "en"] | None = None
    business_type: BusinessType | None = None
    sales_model: SalesModel | None = None
    geographic_reach: GeographicReach | None = None
    presence_type: PresenceType | None = None
    industry: str | None = Field(default=None, max_length=100)
    target_audience: str | None = Field(default=None, max_length=2000)
    value_proposition: str | None = Field(default=None, max_length=2000)
    price_range: Literal["low", "medium", "premium", "luxury"] | None = None
    primary_goal: Literal["more_sales", "more_leads", "more_traffic", "brand_awareness", "expansion"] | None = None
    has_physical_location: bool | None = None
    does_delivery: bool | None = None
    does_pickup: bool | None = None


async def _locations_summary(db: AsyncSession, business_id: UUID) -> ProfileLocations:
    rows = (
        await db.execute(select(Location.country_code, Location.city).where(Location.business_id == business_id))
    ).all()
    return ProfileLocations(
        count=len(rows),
        countries=sorted({country for country, _ in rows if country}),
        cities=sorted({city for _, city in rows if city}),
    )


def _out(business, row, locations: ProfileLocations) -> ProfileOut:
    return ProfileOut(
        business_id=business.id,
        name=business.name,
        language=resolve_language(business.config),
        business_type=row.business_type,
        sales_model=row.sales_model,
        geographic_reach=row.geographic_reach,
        presence_type=row.presence_type,
        industry=row.industry,
        target_audience=row.target_audience,
        value_proposition=row.value_proposition,
        price_range=row.price_range,
        primary_goal=row.primary_goal,
        has_physical_location=bool(row.has_physical_location),
        does_delivery=bool(row.does_delivery),
        does_pickup=bool(row.does_pickup),
        locations=locations,
    )


@router.get("/businesses/{business_id}/profile", response_model=ProfileOut)
async def read_profile(
    business_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    business = await require_business_access(db, business_id, user)
    row = await get_or_create_profile(db, business)
    return _out(business, row, await _locations_summary(db, business_id))


@router.patch("/businesses/{business_id}/profile", response_model=ProfileOut)
async def edit_profile(
    business_id: UUID,
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileOut:
    business = await require_business_access(db, business_id, user, manage=True)
    changes = body.model_dump(exclude_unset=True)
    row = await update_profile(db, business, changes)
    return _out(business, row, await _locations_summary(db, business_id))
