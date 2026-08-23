"""API endpoints for location check-in/checkout + feedback."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.auth.models import User
from app.domains.locations.checkin_service import LocationCheckinService
from app.domains.locations.checkin_models import CheckinType

router = APIRouter(prefix="/api/v1", tags=["location-checkin"])


class VisitorCheckinRequest(BaseModel):
    location_id: UUID
    checkin_type: str
    visitor_phone: Optional[str] = None
    visitor_email: Optional[str] = None
    visitor_name: Optional[str] = None
    qr_code: Optional[str] = None


class VisitorCheckoutRequest(BaseModel):
    checkin_id: UUID
    visited_sections: Optional[list[str]] = None


class FeedbackRequest(BaseModel):
    location_id: UUID
    nps_score: Optional[int] = Query(None, ge=0, le=10)
    comment: Optional[str] = None
    topics: Optional[list[str]] = None
    checkin_id: Optional[UUID] = None


class StaffCheckinRequest(BaseModel):
    location_id: UUID
    staff_id: UUID
    staff_name: str
    staff_role: str


class StaffCheckoutRequest(BaseModel):
    staff_checkin_id: UUID
    visitors_engaged: int = 0
    demos_conducted: int = 0
    sales_assisted: int = 0


@router.post("/locations/checkin")
async def visitor_checkin(
    request: VisitorCheckinRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Visitor check-in (walk-in, QR, geofence, appointment)."""
    try:
        checkin = LocationCheckinService.checkin_visitor(
            location_id=request.location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: from location
            checkin_type=CheckinType[request.checkin_type.upper()],
            visitor_phone=request.visitor_phone,
            visitor_email=request.visitor_email,
            visitor_name=request.visitor_name,
            qr_code=request.qr_code,
            db=db
        )
        return {
            "status": "checked_in",
            "checkin_id": str(checkin.id),
            "checkin_time": checkin.checkin_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/checkout")
async def visitor_checkout(
    request: VisitorCheckoutRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Visitor check-out, record dwell time."""
    try:
        checkin = LocationCheckinService.checkout_visitor(
            checkin_id=request.checkin_id,
            visited_sections=request.visited_sections,
            db=db
        )
        return {
            "status": "checked_out",
            "dwell_seconds": checkin.dwell_seconds,
            "dwell_minutes": checkin.dwell_seconds // 60 if checkin.dwell_seconds else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit visitor feedback (NPS, sentiment, topics)."""
    try:
        feedback = LocationCheckinService.submit_feedback(
            location_id=request.location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),
            nps_score=request.nps_score,
            comment=request.comment,
            topics=request.topics,
            checkin_id=request.checkin_id,
            db=db
        )
        return {
            "status": "feedback_submitted",
            "feedback_id": str(feedback.id),
            "sentiment": feedback.sentiment,
            "requires_followup": feedback.requires_followup
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/staff/checkin")
async def staff_checkin(
    request: StaffCheckinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Staff shift start."""
    try:
        checkin = LocationCheckinService.staff_checkin(
            location_id=request.location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),
            staff_id=request.staff_id,
            staff_name=request.staff_name,
            staff_role=request.staff_role,
            db=db
        )
        return {
            "status": "staff_checked_in",
            "staff_checkin_id": str(checkin.id),
            "checkin_time": checkin.checkin_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/staff/checkout")
async def staff_checkout(
    request: StaffCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Staff shift end, record performance."""
    try:
        checkin = LocationCheckinService.staff_checkout(
            staff_checkin_id=request.staff_checkin_id,
            visitors_engaged=request.visitors_engaged,
            demos_conducted=request.demos_conducted,
            sales_assisted=request.sales_assisted,
            db=db
        )
        dwell = (checkin.checkout_time - checkin.checkin_time).total_seconds() / 3600 if checkin.checkout_time else 0
        return {
            "status": "staff_checked_out",
            "hours_worked": round(dwell, 2),
            "visitors_engaged": checkin.visitors_engaged,
            "demos": checkin.demos_conducted,
            "sales": checkin.sales_assisted
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/checkin-summary")
async def get_checkin_summary(
    location_id: UUID,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get real-time check-in activity for location."""
    try:
        summary = LocationCheckinService.get_location_checkin_summary(
            location_id=location_id,
            hours=hours,
            db=db
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/performance")
async def get_staff_performance(
    staff_id: UUID,
    location_id: UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get staff member's performance metrics."""
    try:
        performance = LocationCheckinService.get_staff_performance(
            location_id=location_id,
            staff_id=staff_id,
            days=days,
            db=db
        )
        return performance
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
