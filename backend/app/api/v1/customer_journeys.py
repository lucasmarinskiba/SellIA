"""Contact journey API endpoints (the path of a lead from first contact to repeat purchase).

Who may do what (see app.core.business_access):

* start a journey and record its touchpoints -> any active member (the staff who talk to the lead);
* read one journey's history -> any active member of the journey's business;
* the metrics and the funnel are dashboards -> the owner or an ADMIN member.

The service is async (AsyncSession), so there is no run_sync here. Access checks run before the try block, so a
403/404 is never turned into a 400 by the broad except.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.journeys.contact_journey_models import ContactJourney
from app.domains.journeys.contact_journey_service import (
    CustomerJourneyService,
    JourneyInvalid,
    JourneyNotFound,
)
from app.domains.users.models import User

router = APIRouter(prefix="/api/v1", tags=["customer-journeys"])


class StartJourneyRequest(BaseModel):
    business_id: UUID
    channel: str = Field(min_length=1, max_length=50)
    customer_email: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=20)
    campaign: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=255)


class RecordTouchpointRequest(BaseModel):
    journey_id: UUID
    business_id: UUID
    touchpoint_type: str = Field(min_length=1, max_length=50)  # email_sent, email_opened, proximity_check, location_visit, order_placed
    channel: str = Field(min_length=1, max_length=50)
    campaign: str | None = Field(default=None, max_length=255)
    location_id: UUID | None = None
    order_id: str | None = Field(default=None, max_length=255)


@router.post("/journeys/start", status_code=status.HTTP_201_CREATED)
async def start_journey(
    request: StartJourneyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start a contact journey (awareness)."""
    await require_business_access(db, request.business_id, current_user)

    try:
        journey = await CustomerJourneyService.start_journey(
            business_id=request.business_id,
            channel=request.channel,
            db=db,
            customer_email=request.customer_email,
            customer_phone=request.customer_phone,
            campaign=request.campaign,
            source=request.source,
        )
    except JourneyInvalid as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {"journey_id": str(journey.id), "awareness_date": journey.awareness_date.isoformat()}


@router.post("/journeys/touchpoint")
async def record_touchpoint(
    request: RecordTouchpointRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record a touchpoint in a journey and advance its stage."""
    await require_business_access(db, request.business_id, current_user)

    try:
        return await CustomerJourneyService.record_touchpoint(
            journey_id=request.journey_id,
            business_id=request.business_id,
            touchpoint_type=request.touchpoint_type,
            channel=request.channel,
            db=db,
            campaign=request.campaign,
            location_id=request.location_id,
            order_id=request.order_id,
        )
    except JourneyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except JourneyInvalid as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/journeys/{journey_id}")
async def get_journey(
    journey_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Full history of one journey."""
    journey = await db.get(ContactJourney, journey_id)
    if journey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey no encontrado")
    await require_business_access(db, journey.business_id, current_user)

    try:
        return await CustomerJourneyService.get_journey_details(journey_id, journey.business_id, db)
    except JourneyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/businesses/{business_id}/journey-metrics")
async def calculate_journey_metrics(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Aggregate journey metrics for the period (a dashboard: owner or admin)."""
    await require_business_access(db, business_id, current_user, manage=True)
    return await CustomerJourneyService.calculate_journey_metrics(business_id, days, db)


@router.get("/businesses/{business_id}/journey-funnel")
async def get_journey_funnel(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Funnel from awareness to retention (a dashboard: owner or admin)."""
    await require_business_access(db, business_id, current_user, manage=True)
    return await CustomerJourneyService.funnel(business_id, days, db)
