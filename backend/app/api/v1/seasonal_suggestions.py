"""Seasonal campaign suggestions for one business. Read-only: these are drafts to review, never sent."""

from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.businesses.location_models import Location
from app.domains.sequences.offline_sequence_jobs import (
    DEFAULT_LANGUAGE,
    render,
    resolve_language,
)
from app.domains.sequences.seasonal import DRAFTS, next_occurrences
from app.domains.users.models import User

router = APIRouter(prefix="/api/v1", tags=["seasonal-suggestions"])

DEFAULT_COUNTRY = "AR"  # the default of Location.country_code


class DraftOut(BaseModel):
    subject: str
    body: str


class SeasonOut(BaseModel):
    key: str
    name: str
    start: date
    end: date
    # "open": the window includes as_of. "upcoming": it starts later.
    status: str
    days_until: int | None
    approximate: bool
    note: str | None
    draft: DraftOut


class SeasonalSuggestionsOut(BaseModel):
    business_id: UUID
    as_of: date
    country: str
    # "locations": most common country among the business's locations. "default": it has none yet.
    country_source: str
    language: str
    coverage_note: str | None
    seasons: list[SeasonOut]


async def _business_country(db: AsyncSession, business_id: UUID) -> tuple[str, str]:
    rows = (
        await db.execute(
            select(Location.country_code, func.count())
            .where(Location.business_id == business_id)
            .group_by(Location.country_code)
            .order_by(func.count().desc(), Location.country_code)
        )
    ).all()
    if not rows:
        return DEFAULT_COUNTRY, "default"
    return rows[0][0], "locations"


@router.get("/businesses/{business_id}/seasonal-suggestions", response_model=SeasonalSuggestionsOut)
async def seasonal_suggestions(
    business_id: UUID,
    as_of: date | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SeasonalSuggestionsOut:
    """Upcoming and open seasons for this business, each with a draft. Any member may read; nothing is sent."""
    business = await require_business_access(db, business_id, user)
    country, source = await _business_country(db, business_id)
    language = resolve_language(business.config)
    today = as_of or datetime.now(timezone.utc).date()

    seasons: list[SeasonOut] = []
    for season, is_open in next_occurrences(country, today):
        subject, name, body = DRAFTS[season.key].get(language, DRAFTS[season.key][DEFAULT_LANGUAGE])
        seasons.append(
            SeasonOut(
                key=season.key,
                name=name,
                start=season.start,
                end=season.end,
                status="open" if is_open else "upcoming",
                days_until=None if is_open else (season.start - today).days,
                approximate=season.approximate,
                note=season.note,
                draft=DraftOut(
                    subject=render(subject, business_name=business.name),
                    body=render(body, business_name=business.name),
                ),
            )
        )

    return SeasonalSuggestionsOut(
        business_id=business_id,
        as_of=today,
        country=country,
        country_source=source,
        language=language,
        coverage_note=None if country == "AR" else f"Para {country} sólo hay calendario de Navidad y Pascua.",
        seasons=seasons,
    )
