"""Journey orchestration API."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.journeys.journey_service import JourneyService
from app.domains.journeys.journey_models import CustomerJourney

router = APIRouter(prefix="/api/v1", tags=["journeys"])


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    """Same convention as websites.py/catalog.py/channels.py/payments.py."""
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.user_id == user.id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


async def _get_owned_journey(journey_id: UUID, user: User, db: AsyncSession) -> CustomerJourney:
    """Look up a journey by id alone and verify it belongs to a business the
    caller owns. create_variant/enroll_customer/get_executions/get_ab_test
    only ever took {journey_id} in the URL -- create_variant and
    enroll_customer additionally took a client-supplied `business_id` query
    param that was never checked against the journey's REAL business_id, so
    passing your own (valid) business_id alongside someone else's journey_id
    would have worked. Deriving business_id from the journey itself instead
    of trusting the caller's query param.
    """
    result = await db.execute(select(CustomerJourney).where(CustomerJourney.id == journey_id))
    journey = result.scalar_one_or_none()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey no encontrado")
    await _get_business_for_user(journey.business_id, user, db)
    return journey


class CreateJourneyRequest(BaseModel):
    name: str
    nodes: dict
    edges: dict


class CreateVariantRequest(BaseModel):
    variant_name: str
    variant_config: dict
    traffic_allocation: float = 50.0


class EnrollCustomerRequest(BaseModel):
    customer_id: UUID
    variant_id: UUID = None


@router.post("/businesses/{business_id}/journeys")
async def create_journey(
    business_id: UUID,
    request: CreateJourneyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await JourneyService.create_journey(business_id, request.name, request.nodes, request.edges, db)


@router.post("/journeys/{journey_id}/variants")
async def create_variant(
    journey_id: UUID,
    request: CreateVariantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    journey = await _get_owned_journey(journey_id, current_user, db)
    return await JourneyService.create_variant(
        journey_id, journey.business_id, request.variant_name, request.variant_config, request.traffic_allocation, db
    )


@router.post("/journeys/{journey_id}/enroll")
async def enroll_customer(
    journey_id: UUID,
    request: EnrollCustomerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    journey = await _get_owned_journey(journey_id, current_user, db)
    return await JourneyService.enroll_customer(journey_id, request.customer_id, journey.business_id, request.variant_id, db)


@router.get("/journeys/{journey_id}/executions")
async def get_executions(
    journey_id: UUID,
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    journey = await _get_owned_journey(journey_id, current_user, db)
    return await JourneyService.get_journey_executions(journey_id, journey.business_id, limit, db)


@router.get("/journeys/{journey_id}/ab-test-result")
async def get_ab_test(
    journey_id: UUID,
    variant_a_id: UUID,
    variant_b_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    journey = await _get_owned_journey(journey_id, current_user, db)
    return await JourneyService.get_ab_test_result(journey_id, journey.business_id, variant_a_id, variant_b_id, db)


@router.get("/businesses/{business_id}/journeys/metrics")
async def get_metrics(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    return await JourneyService.get_metrics(business_id, db)
