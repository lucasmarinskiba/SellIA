"""Real-time feedback alerts API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.users.models import User
from app.domains.feedback.feedback_alert_service import FeedbackAlertService, NPSDashboardService

router = APIRouter(prefix="/api/v1", tags=["feedback-alerts"])


class EvaluateFeedbackRequest(BaseModel):
    location_id: UUID
    feedback_id: UUID
    nps_score: int
    sentiment: str
    comment: Optional[str] = None
    topics: Optional[list[str]] = None
    visitor_email: Optional[str] = None
    visitor_phone: Optional[str] = None
    visitor_name: Optional[str] = None


class AlertActionRequest(BaseModel):
    alert_id: UUID
    action: str  # acknowledge, escalate, resolve


@router.post("/feedback/evaluate")
async def evaluate_feedback(
    request: EvaluateFeedbackRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Evaluate feedback. Alert if NPS < 6."""
    try:
        result = FeedbackAlertService.evaluate_feedback_and_alert(
            feedback_id=request.feedback_id,
            location_id=request.location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: from location
            nps_score=request.nps_score,
            sentiment=request.sentiment,
            comment=request.comment,
            topics=request.topics,
            visitor_email=request.visitor_email,
            visitor_phone=request.visitor_phone,
            visitor_name=request.visitor_name,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Manager acknowledges alert."""
    try:
        result = FeedbackAlertService.acknowledge_alert(
            alert_id=alert_id,
            manager_id=current_user.id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/escalate")
async def escalate_alert(
    alert_id: UUID,
    assigned_to_staff_id: UUID = Query(...),
    resolution_plan: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Assign staff to resolve alert."""
    try:
        result = FeedbackAlertService.escalate_alert(
            alert_id=alert_id,
            assigned_to_staff_id=assigned_to_staff_id,
            resolution_plan=resolution_plan,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolution_notes: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Mark alert as resolved."""
    try:
        result = FeedbackAlertService.resolve_alert(
            alert_id=alert_id,
            resolution_notes=resolution_notes,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/alerts")
async def get_location_alerts(
    location_id: UUID,
    status: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """Get NPS alerts for location."""
    try:
        result = FeedbackAlertService.get_location_alerts(
            location_id=location_id,
            status_filter=status,
            days=days,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/nps-metrics/update")
async def update_nps_metrics(
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Update hourly NPS snapshot."""
    try:
        result = NPSDashboardService.update_nps_metrics(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/nps-dashboard")
async def get_nps_dashboard(
    location_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """Get NPS dashboard data."""
    try:
        result = NPSDashboardService.get_nps_dashboard(
            location_id=location_id,
            days=days,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/sentiment-trend")
async def calculate_sentiment_trend(
    location_id: UUID,
    date: str = Query(...),  # YYYY-MM-DD
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Calculate daily sentiment trend."""
    try:
        result = NPSDashboardService.calculate_sentiment_trend(
            location_id=location_id,
            date=date,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/assigned-alerts")
async def get_staff_assigned_alerts(
    staff_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Get alerts assigned to staff for follow-up."""
    try:
        from app.domains.feedback.feedback_alert_models import NPSAlert, AlertStatus

        alerts = db.query(NPSAlert).filter(
            NPSAlert.assigned_to_staff_id == staff_id,
            NPSAlert.status.in_([AlertStatus.ESCALATED, AlertStatus.ACTIVE])
        ).order_by(NPSAlert.created_at.desc()).all()

        alert_list = [
            {
                "alert_id": str(a.id),
                "nps_score": a.nps_score,
                "sentiment": a.sentiment.value,
                "comment": a.comment,
                "visitor_email": a.visitor_email,
                "visitor_phone": a.visitor_phone,
                "visitor_name": a.visitor_name,
                "status": a.status.value,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]

        return {
            "staff_id": str(staff_id),
            "assigned_alerts": len(alert_list),
            "alerts": alert_list
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
