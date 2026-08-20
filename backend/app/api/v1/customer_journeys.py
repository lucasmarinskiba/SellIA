"""Customer journey API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.users.models import User
from app.domains.journeys.journey_service import CustomerJourneyService

router = APIRouter(prefix="/api/v1", tags=["customer-journeys"])


class StartJourneyRequest(BaseModel):
    business_id: UUID
    channel: str  # organic_search, paid_search, social_media, email, direct, referral, proximity_invite
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    campaign: Optional[str] = None
    source: Optional[str] = None


class RecordTouchpointRequest(BaseModel):
    journey_id: UUID
    business_id: UUID
    touchpoint_type: str  # email_sent, email_opened, proximity_check, location_visit, order_placed
    channel: str
    campaign: Optional[str] = None
    location_id: Optional[UUID] = None
    order_id: Optional[str] = None


@router.post("/journeys/start")
async def start_journey(
    request: StartJourneyRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Start new customer journey."""
    try:
        result = CustomerJourneyService.start_journey(
            business_id=request.business_id,
            channel=request.channel,
            customer_email=request.customer_email,
            customer_phone=request.customer_phone,
            campaign=request.campaign,
            source=request.source,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/journeys/touchpoint")
async def record_touchpoint(
    request: RecordTouchpointRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Record touchpoint in journey."""
    try:
        result = CustomerJourneyService.record_touchpoint(
            journey_id=request.journey_id,
            business_id=request.business_id,
            touchpoint_type=request.touchpoint_type,
            channel=request.channel,
            campaign=request.campaign,
            location_id=request.location_id,
            order_id=request.order_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/journeys/{journey_id}")
async def get_journey(
    journey_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Get complete journey details."""
    try:
        result = CustomerJourneyService.get_journey_details(journey_id, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/businesses/{business_id}/journey-metrics")
async def calculate_journey_metrics(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """Calculate aggregate journey metrics."""
    try:
        result = CustomerJourneyService.calculate_journey_metrics(
            business_id=business_id,
            days=days,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/businesses/{business_id}/journey-funnel")
async def get_journey_funnel(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """Get journey funnel visualization data."""
    try:
        from app.domains.journeys.journey_models import CustomerJourney
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        journeys = db.query(CustomerJourney).filter(
            CustomerJourney.business_id == business_id,
            CustomerJourney.awareness_date >= cutoff
        ).all()

        stages = {
            "awareness": len(journeys),
            "consideration": len([j for j in journeys if j.consideration_date]),
            "intent": len([j for j in journeys if j.intent_date]),
            "visit": len([j for j in journeys if j.visit_date]),
            "purchase": len([j for j in journeys if j.purchase_date]),
            "retention": len([j for j in journeys if j.repeat_purchase_count > 0])
        }

        return {
            "business_id": str(business_id),
            "period_days": days,
            "funnel": stages,
            "conversion_rates": {
                "awareness_to_consideration": (stages["consideration"] / max(stages["awareness"], 1)) * 100,
                "consideration_to_intent": (stages["intent"] / max(stages["consideration"], 1)) * 100,
                "intent_to_visit": (stages["visit"] / max(stages["intent"], 1)) * 100,
                "visit_to_purchase": (stages["purchase"] / max(stages["visit"], 1)) * 100,
                "purchase_to_retention": (stages["retention"] / max(stages["purchase"], 1)) * 100
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
