"""API endpoints for location check-in/checkout + feedback.

Every route needs a login. The mobile SDKs (iOS/Android) send ``Authorization: Bearer`` on check-in,
check-out and feedback, and the QR codes are ``selliaapp://`` deep links that only the app opens, so there
is no anonymous flow to keep open.

Who may do what (see app.core.business_access):

* visitor check-in / check-out / feedback, the check-in summary -> the owner or any active member of the
  location's business (the staff tablet at the door);
* staff check-in / check-out and a staff member's performance -> that person themselves, or a manager
  (owner / ADMIN member) of the business; whoever is checked in must belong to the business.

The services are sync (Session.query / commit) while get_db yields an AsyncSession, so every DB touch runs
inside ``await db.run_sync(...)``. Access checks run before the try block: a 403/404/409 must not be turned
into a 400 by the broad except. The business a row belongs to always comes from its location -- never from
the client.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import (
    is_business_participant,
    require_business_access,
    require_location_access,
)
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.locations.checkin_models import (
    CheckinStatus,
    CheckinType,
    LocationCheckin,
    StaffCheckin,
)
from app.domains.locations.checkin_service import LocationCheckinService
from app.domains.users.models import User

router = APIRouter(prefix="", tags=["location-checkin"])


class VisitorCheckinRequest(BaseModel):
    location_id: UUID
    checkin_type: str = Field(max_length=32)
    visitor_phone: str | None = Field(default=None, max_length=20)
    visitor_email: str | None = Field(default=None, max_length=255)
    visitor_name: str | None = Field(default=None, max_length=255)
    qr_code: str | None = Field(default=None, max_length=255)


class VisitorCheckoutRequest(BaseModel):
    checkin_id: UUID
    visited_sections: list[str] | None = Field(default=None, max_length=50)


class FeedbackRequest(BaseModel):
    location_id: UUID
    nps_score: int | None = Field(default=None, ge=0, le=10)
    comment: str | None = Field(default=None, max_length=1000)
    topics: list[str] | None = Field(default=None, max_length=20)
    checkin_id: UUID | None = None


class StaffCheckinRequest(BaseModel):
    location_id: UUID
    staff_id: UUID
    staff_name: str = Field(min_length=1, max_length=255)
    staff_role: str = Field(min_length=1, max_length=100)


class StaffCheckoutRequest(BaseModel):
    staff_checkin_id: UUID
    visitors_engaged: int = Field(default=0, ge=0)
    demos_conducted: int = Field(default=0, ge=0)
    sales_assisted: int = Field(default=0, ge=0)


@router.post("/locations/checkin")
async def visitor_checkin(
    request: VisitorCheckinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Visitor check-in (walk-in, QR, geofence, appointment)."""
    location = await require_location_access(db, request.location_id, current_user)
    business_id = location.business_id
    if not location.is_active:
        raise HTTPException(status_code=400, detail="La sucursal está inactiva")
    try:
        checkin_type = CheckinType[request.checkin_type.upper()]
    except KeyError:
        raise HTTPException(
            status_code=422, detail=f"checkin_type inválido: {request.checkin_type}"
        ) from None
    if checkin_type == CheckinType.STAFF_CHECKIN:
        raise HTTPException(
            status_code=422, detail="El personal ficha en /staff/checkin"
        )

    try:
        checkin = await db.run_sync(
            lambda sync_db: LocationCheckinService.checkin_visitor(
                location_id=request.location_id,
                business_id=business_id,
                checkin_type=checkin_type,
                visitor_phone=request.visitor_phone,
                visitor_email=request.visitor_email,
                visitor_name=request.visitor_name,
                qr_code=request.qr_code,
                db=sync_db,
            )
        )
        return {
            "status": "checked_in",
            "checkin_id": str(checkin.id),
            "checkin_time": checkin.checkin_time.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/checkout")
async def visitor_checkout(
    request: VisitorCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Visitor check-out, record dwell time."""
    existing = await db.get(LocationCheckin, request.checkin_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Check-in no encontrado")
    await require_location_access(db, existing.location_id, current_user)
    # The service recomputes the dwell time on every call: a second check-out would silently inflate it.
    if existing.status != CheckinStatus.CHECKED_IN:
        raise HTTPException(status_code=409, detail="Este check-in ya tiene check-out")

    try:
        checkin = await db.run_sync(
            lambda sync_db: LocationCheckinService.checkout_visitor(
                checkin_id=request.checkin_id,
                visited_sections=request.visited_sections,
                db=sync_db,
            )
        )
        return {
            "status": "checked_out",
            "dwell_seconds": checkin.dwell_seconds,
            "dwell_minutes": (
                checkin.dwell_seconds // 60 if checkin.dwell_seconds else 0
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit visitor feedback (NPS, sentiment, topics)."""
    location = await require_location_access(db, request.location_id, current_user)
    business_id = location.business_id
    if request.checkin_id is not None:
        checkin = await db.get(LocationCheckin, request.checkin_id)
        if checkin is None or checkin.location_id != request.location_id:
            raise HTTPException(
                status_code=404, detail="Check-in no encontrado en esta sucursal"
            )

    try:
        feedback = await db.run_sync(
            lambda sync_db: LocationCheckinService.submit_feedback(
                location_id=request.location_id,
                business_id=business_id,
                nps_score=request.nps_score,
                comment=request.comment,
                topics=request.topics,
                checkin_id=request.checkin_id,
                db=sync_db,
            )
        )
        return {
            "status": "feedback_submitted",
            "feedback_id": str(feedback.id),
            "sentiment": feedback.sentiment,
            "requires_followup": feedback.requires_followup,
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
    # Checking yourself in takes membership; checking someone else in takes a manager.
    location = await require_location_access(
        db,
        request.location_id,
        current_user,
        manage=request.staff_id != current_user.id,
    )
    business_id = location.business_id
    if not await is_business_participant(db, business_id, request.staff_id):
        raise HTTPException(
            status_code=400, detail="La persona no pertenece a este negocio"
        )

    try:
        checkin = await db.run_sync(
            lambda sync_db: LocationCheckinService.staff_checkin(
                location_id=request.location_id,
                business_id=business_id,
                staff_id=request.staff_id,
                staff_name=request.staff_name,
                staff_role=request.staff_role,
                db=sync_db,
            )
        )
        return {
            "status": "staff_checked_in",
            "staff_checkin_id": str(checkin.id),
            "checkin_time": checkin.checkin_time.isoformat(),
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
    shift = await db.get(StaffCheckin, request.staff_checkin_id)
    if shift is None:
        raise HTTPException(
            status_code=404, detail="Check-in de personal no encontrado"
        )
    await require_business_access(
        db, shift.business_id, current_user, manage=shift.staff_id != current_user.id
    )
    # A second check-out would overwrite the shift's end time and its performance counters.
    if shift.checkout_time is not None:
        raise HTTPException(status_code=409, detail="Este turno ya tiene check-out")

    try:
        checkin = await db.run_sync(
            lambda sync_db: LocationCheckinService.staff_checkout(
                staff_checkin_id=request.staff_checkin_id,
                visitors_engaged=request.visitors_engaged,
                demos_conducted=request.demos_conducted,
                sales_assisted=request.sales_assisted,
                db=sync_db,
            )
        )
        dwell = (
            (checkin.checkout_time - checkin.checkin_time).total_seconds() / 3600
            if checkin.checkout_time
            else 0
        )
        return {
            "status": "staff_checked_out",
            "hours_worked": round(dwell, 2),
            "visitors_engaged": checkin.visitors_engaged,
            "demos": checkin.demos_conducted,
            "sales": checkin.sales_assisted,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/checkin-summary")
async def get_checkin_summary(
    location_id: UUID,
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get real-time check-in activity for location."""
    await require_location_access(db, location_id, current_user)

    try:
        return await db.run_sync(
            lambda sync_db: LocationCheckinService.get_location_checkin_summary(
                location_id=location_id, hours=hours, db=sync_db
            )
        )
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
    await require_location_access(
        db, location_id, current_user, manage=staff_id != current_user.id
    )

    try:
        return await db.run_sync(
            lambda sync_db: LocationCheckinService.get_staff_performance(
                location_id=location_id, staff_id=staff_id, days=days, db=sync_db
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
