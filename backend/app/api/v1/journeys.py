"""Journey orchestration API."""

from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domains.journeys.journey_service import JourneyService

router = APIRouter(prefix="/api/v1", tags=["journeys"])


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
def create_journey(business_id: UUID, request: CreateJourneyRequest, db: Session = Depends(get_db)):
    return JourneyService.create_journey(business_id, request.name, request.nodes, request.edges, db)


@router.post("/journeys/{journey_id}/variants")
def create_variant(journey_id: UUID, business_id: UUID, request: CreateVariantRequest, db: Session = Depends(get_db)):
    return JourneyService.create_variant(journey_id, business_id, request.variant_name, request.variant_config, request.traffic_allocation, db)


@router.post("/journeys/{journey_id}/enroll")
def enroll_customer(journey_id: UUID, business_id: UUID, request: EnrollCustomerRequest, db: Session = Depends(get_db)):
    return JourneyService.enroll_customer(journey_id, request.customer_id, business_id, request.variant_id, db)


@router.get("/journeys/{journey_id}/executions")
def get_executions(journey_id: UUID, limit: int = Query(50), db: Session = Depends(get_db)):
    return JourneyService.get_journey_executions(journey_id, limit, db)


@router.get("/journeys/{journey_id}/ab-test-result")
def get_ab_test(journey_id: UUID, variant_a_id: UUID, variant_b_id: UUID, db: Session = Depends(get_db)):
    return JourneyService.get_ab_test_result(journey_id, variant_a_id, variant_b_id, db)


@router.get("/businesses/{business_id}/journeys/metrics")
def get_metrics(business_id: UUID, db: Session = Depends(get_db)):
    return JourneyService.get_metrics(business_id, db)
