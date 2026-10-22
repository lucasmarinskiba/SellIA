"""NPS feedback alert API endpoints.

Who may do what (see app.core.business_access):

* acknowledge / escalate an alert, recompute NPS metrics or sentiment trend -> the owner
  or an ADMIN member of the alert's business;
* resolve an alert -> the person it was escalated to (while still in the business) or a
  manager;
* evaluate feedback, read a location's alerts or NPS dashboard -> any member;
* read someone's assigned alerts -> that person, or a manager (only within the
  businesses the manager manages).

The services are sync (Session.query / commit) while get_db yields an AsyncSession, so
every DB touch runs inside ``await db.run_sync(...)``. Access checks run before the try
block: a 403/404 must not be turned into a 400 by the broad except.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.business_access import (
    is_business_participant,
    require_business_access,
    require_location_access,
    staff_scope,
)
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.feedback.feedback_alert_models import AlertStatus, NPSAlert
from app.domains.feedback.feedback_alert_service import (
    FeedbackAlertService,
    NPSDashboardService,
)
from app.domains.locations.checkin_models import LocationFeedback
from app.domains.users.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["feedback-alerts"])


class EvaluateFeedbackRequest(BaseModel):
    location_id: UUID
    feedback_id: UUID
    nps_score: int = Field(ge=0, le=10)
    sentiment: str
    comment: str | None = None
    topics: list[str] | None = None
    visitor_email: str | None = None
    visitor_phone: str | None = None
    visitor_name: str | None = None


class AlertActionRequest(BaseModel):
    alert_id: UUID
    action: str  # acknowledge, escalate, resolve


async def _get_alert(db: AsyncSession, alert_id: UUID) -> NPSAlert:
    alert = await db.get(NPSAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.post("/feedback/evaluate")
async def evaluate_feedback(
    request: EvaluateFeedbackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Evaluate feedback. Alert if NPS < 6."""
    location = await require_location_access(db, request.location_id, current_user)
    business_id = location.business_id
    # nps_alerts.feedback_id is a foreign key, which only proves the row exists -- not that it belongs to
    # this location. Without this check a member of business A could pin an alert to business B's feedback.
    feedback = await db.get(LocationFeedback, request.feedback_id)
    if feedback is None or feedback.location_id != request.location_id:
        raise HTTPException(
            status_code=404, detail="Feedback no encontrado en esta sucursal"
        )

    try:
        return await db.run_sync(
            lambda sync_db: FeedbackAlertService.evaluate_feedback_and_alert(
                feedback_id=request.feedback_id,
                location_id=request.location_id,
                business_id=business_id,
                nps_score=request.nps_score,
                sentiment=request.sentiment,
                comment=request.comment,
                topics=request.topics,
                visitor_email=request.visitor_email,
                visitor_phone=request.visitor_phone,
                visitor_name=request.visitor_name,
                db=sync_db,
            )
        )
    except Exception as e:
        logger.exception("evaluate_feedback: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Manager acknowledges alert."""
    alert = await _get_alert(db, alert_id)
    await require_business_access(db, alert.business_id, current_user, manage=True)

    try:
        return await db.run_sync(
            lambda sync_db: FeedbackAlertService.acknowledge_alert(
                alert_id=alert_id, manager_id=current_user.id, db=sync_db
            )
        )
    except Exception as e:
        logger.exception("acknowledge_alert: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/escalate")
async def escalate_alert(
    alert_id: UUID,
    assigned_to_staff_id: Annotated[UUID, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    resolution_plan: Annotated[str | None, Query()] = None,
) -> dict:
    """Assign staff to resolve alert."""
    alert = await _get_alert(db, alert_id)
    await require_business_access(db, alert.business_id, current_user, manage=True)
    if not await is_business_participant(db, alert.business_id, assigned_to_staff_id):
        raise HTTPException(
            status_code=400, detail="La persona asignada no pertenece a este negocio"
        )

    try:
        return await db.run_sync(
            lambda sync_db: FeedbackAlertService.escalate_alert(
                alert_id=alert_id,
                assigned_to_staff_id=assigned_to_staff_id,
                resolution_plan=resolution_plan,
                db=sync_db,
            )
        )
    except Exception as e:
        logger.exception("escalate_alert: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    resolution_notes: Annotated[str | None, Query()] = None,
) -> dict:
    """Mark alert as resolved."""
    alert = await _get_alert(db, alert_id)
    # Whoever the alert was escalated to can close it; otherwise it takes a manager.
    await require_business_access(
        db,
        alert.business_id,
        current_user,
        manage=alert.assigned_to_staff_id != current_user.id,
    )

    try:
        return await db.run_sync(
            lambda sync_db: FeedbackAlertService.resolve_alert(
                alert_id=alert_id, resolution_notes=resolution_notes, db=sync_db
            )
        )
    except Exception as e:
        logger.exception("resolve_alert: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/alerts")
async def get_location_alerts(
    location_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[str | None, Query()] = None,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict:
    """Get NPS alerts for location."""
    await require_location_access(db, location_id, current_user)

    try:
        return await db.run_sync(
            lambda sync_db: FeedbackAlertService.get_location_alerts(
                location_id=location_id, status_filter=status, days=days, db=sync_db
            )
        )
    except Exception as e:
        logger.exception("get_location_alerts: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/nps-metrics/update")
async def update_nps_metrics(
    location_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Update hourly NPS snapshot."""
    location = await require_location_access(db, location_id, current_user, manage=True)
    business_id = location.business_id

    try:
        return await db.run_sync(
            lambda sync_db: NPSDashboardService.update_nps_metrics(
                location_id=location_id, business_id=business_id, db=sync_db
            )
        )
    except Exception as e:
        logger.exception("update_nps_metrics: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/nps-dashboard")
async def get_nps_dashboard(
    location_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict:
    """Get NPS dashboard data."""
    await require_location_access(db, location_id, current_user)

    try:
        return await db.run_sync(
            lambda sync_db: NPSDashboardService.get_nps_dashboard(
                location_id=location_id, days=days, db=sync_db
            )
        )
    except Exception as e:
        logger.exception("get_nps_dashboard: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/sentiment-trend")
async def calculate_sentiment_trend(
    location_id: UUID,
    date: Annotated[str, Query()],  # YYYY-MM-DD
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Calculate daily sentiment trend."""
    location = await require_location_access(db, location_id, current_user, manage=True)
    business_id = location.business_id

    try:
        return await db.run_sync(
            lambda sync_db: NPSDashboardService.calculate_sentiment_trend(
                location_id=location_id, date=date, db=sync_db, business_id=business_id
            )
        )
    except Exception as e:
        logger.exception("calculate_sentiment_trend: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/staff/{staff_id}/assigned-alerts")
async def get_staff_assigned_alerts(
    staff_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get alerts assigned to staff for follow-up."""
    scope = await staff_scope(db, staff_id, current_user)

    try:

        def _load(sync_db: Session) -> list:
            return (
                sync_db.query(NPSAlert)
                .filter(
                    NPSAlert.assigned_to_staff_id == staff_id,
                    NPSAlert.business_id.in_(scope),
                    NPSAlert.status.in_([AlertStatus.ESCALATED, AlertStatus.ACTIVE]),
                )
                .order_by(NPSAlert.created_at.desc())
                .all()
            )

        alerts = await db.run_sync(_load)

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
            "alerts": alert_list,
        }
    except Exception as e:
        logger.exception("get_staff_assigned_alerts: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))
