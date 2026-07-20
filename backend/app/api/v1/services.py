"""Services API Router"""

from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.services import services as service_services
from app.domains.services.models import ServiceDelivery, Appointment
from app.domains.services.schemas import (
    ServiceDeliveryCreate, ServiceDeliveryUpdate, ServiceDeliveryResponse,
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentListResponse,
    AppointmentActionResponse, ServiceDeliveryActionResponse,
)

router = APIRouter()


# ========== Service Deliveries ==========

@router.get("/deliveries/by-order/{order_id}", response_model=dict)
async def get_delivery_by_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get service delivery and appointments for a specific order."""
    result = await db.execute(
        select(ServiceDelivery).where(ServiceDelivery.order_id == order_id, ServiceDelivery.is_active == True)
    )
    delivery = result.scalar_one_or_none()
    appointments = []
    if delivery:
        appt_result = await db.execute(
            select(Appointment).where(Appointment.service_delivery_id == delivery.id, Appointment.is_active == True)
            .order_by(Appointment.start_time)
        )
        appointments = appt_result.scalars().all()
    return {"delivery": delivery, "appointments": appointments}


@router.get("/deliveries", response_model=dict)
async def list_deliveries(
    business_id: UUID,
    status: Optional[str] = None,
    order_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await service_services.list_service_deliveries(db, business_id, status, order_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/deliveries", response_model=ServiceDeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    data: ServiceDeliveryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await service_services.create_service_delivery(db, data.order_id, data.model_dump())
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error creating delivery")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/deliveries/{delivery_id}", response_model=ServiceDeliveryResponse)
async def get_delivery(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    delivery = await service_services.get_service_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    return delivery


@router.patch("/deliveries/{delivery_id}", response_model=ServiceDeliveryResponse)
async def update_delivery(
    delivery_id: UUID,
    data: ServiceDeliveryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    delivery = await service_services.get_service_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    return await service_services.update_service_delivery(db, delivery, data.model_dump(exclude_unset=True))


@router.post("/deliveries/{delivery_id}/complete", response_model=ServiceDeliveryActionResponse)
async def complete_delivery(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    delivery = await service_services.get_service_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    updated = await service_services.complete_service_delivery(db, delivery)
    return {"success": True, "message": "Servicio completado", "service_delivery": updated}


@router.post("/deliveries/{delivery_id}/cancel", response_model=ServiceDeliveryActionResponse)
async def cancel_delivery(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    delivery = await service_services.get_service_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    updated = await service_services.cancel_service_delivery(db, delivery)
    return {"success": True, "message": "Entrega cancelada", "service_delivery": updated}


# ========== Appointments ==========

@router.get("/appointments", response_model=dict)
async def list_appointments(
    business_id: UUID,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await service_services.list_appointments(db, business_id, status, from_date, to_date, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/appointments/calendar")
async def get_calendar(
    business_id: UUID,
    from_date: datetime,
    to_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await service_services.list_appointments(db, business_id, from_date=from_date, to_date=to_date, limit=500)
    return {"items": items, "total": total}


@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await service_services.create_appointment(db, current_user.businesses[0].id if hasattr(current_user, 'businesses') else data.order_id, data.model_dump())
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).exception("Error creating appointment")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return appt


@router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return await service_services.update_appointment(db, appt, data.model_dump(exclude_unset=True))


@router.post("/appointments/{appointment_id}/confirm", response_model=AppointmentActionResponse)
async def confirm_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    updated = await service_services.confirm_appointment(db, appt)
    return {"success": True, "message": "Cita confirmada", "appointment": updated}


@router.post("/appointments/{appointment_id}/complete", response_model=AppointmentActionResponse)
async def complete_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    updated = await service_services.complete_appointment(db, appt)
    return {"success": True, "message": "Cita completada", "appointment": updated}


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentActionResponse)
async def cancel_appointment(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    updated = await service_services.cancel_appointment(db, appt)
    return {"success": True, "message": "Cita cancelada", "appointment": updated}


@router.post("/appointments/{appointment_id}/no-show", response_model=AppointmentActionResponse)
async def mark_no_show(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    updated = await service_services.mark_no_show(db, appt)
    return {"success": True, "message": "Marcado como no-show", "appointment": updated}


@router.post("/appointments/{appointment_id}/send-reminder")
async def send_reminder(
    appointment_id: UUID,
    channel: Optional[str] = "whatsapp",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return await service_services.send_appointment_reminder(db, appt, channel)


@router.post("/appointments/{appointment_id}/request-confirmation")
async def request_confirmation(
    appointment_id: UUID,
    channel: Optional[str] = "whatsapp",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return await service_services.request_confirmation(db, appt, channel)


@router.post("/appointments/{appointment_id}/request-feedback")
async def request_feedback(
    appointment_id: UUID,
    channel: Optional[str] = "whatsapp",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = await service_services.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return await service_services.request_feedback(db, appt, channel)


# ========== Automated Checks ==========

@router.post("/appointments/run-checks")
async def run_appointment_checks(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Manually trigger automated checks (reminders, no-shows, confirmations)."""
    reminders = await service_services.check_upcoming_appointments(db)
    no_shows = await service_services.process_no_shows(db)
    confirmations = await service_services.request_pending_confirmations(db)
    return {
        "success": True,
        "reminders": reminders,
        "no_shows_processed": no_shows,
        "confirmations_requested": confirmations,
    }



# ========== Service Analytics ==========

@router.get("/analytics")
async def get_service_analytics(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get service delivery and appointment analytics."""
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total deliveries
    total_result = await db.execute(
        select(func.count(ServiceDelivery.id))
        .where(ServiceDelivery.business_id == business_id, ServiceDelivery.is_active == True)
    )
    total_deliveries = total_result.scalar() or 0

    # By status
    status_result = await db.execute(
        select(ServiceDelivery.status, func.count(ServiceDelivery.id))
        .where(ServiceDelivery.business_id == business_id, ServiceDelivery.is_active == True)
        .group_by(ServiceDelivery.status)
    )
    by_status = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in status_result.all()}

    # Completed in period
    completed_result = await db.execute(
        select(func.count(ServiceDelivery.id))
        .where(
            ServiceDelivery.business_id == business_id,
            ServiceDelivery.status == ServiceDeliveryStatus.COMPLETED,
            ServiceDelivery.completed_at >= since,
        )
    )
    completed_count = completed_result.scalar() or 0

    # No-shows in period
    no_show_result = await db.execute(
        select(func.count(ServiceDelivery.id))
        .where(
            ServiceDelivery.business_id == business_id,
            ServiceDelivery.status == ServiceDeliveryStatus.NO_SHOW,
            ServiceDelivery.updated_at >= since,
        )
    )
    no_show_count = no_show_result.scalar() or 0

    # Cancelled in period
    cancelled_result = await db.execute(
        select(func.count(ServiceDelivery.id))
        .where(
            ServiceDelivery.business_id == business_id,
            ServiceDelivery.status == ServiceDeliveryStatus.CANCELLED,
            ServiceDelivery.cancelled_at >= since,
        )
    )
    cancelled_count = cancelled_result.scalar() or 0

    # Appointments stats
    appt_total = await db.execute(
        select(func.count(Appointment.id))
        .where(Appointment.business_id == business_id, Appointment.is_active == True)
    )
    total_appointments = appt_total.scalar() or 0

    # By modality
    modality_result = await db.execute(
        select(ServiceDelivery.modality, func.count(ServiceDelivery.id))
        .where(ServiceDelivery.business_id == business_id, ServiceDelivery.is_active == True, ServiceDelivery.modality.isnot(None))
        .group_by(ServiceDelivery.modality)
    )
    by_modality = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in modality_result.all()}

    # By solution type
    solution_result = await db.execute(
        select(ServiceDelivery.solution_type, func.count(ServiceDelivery.id))
        .where(ServiceDelivery.business_id == business_id, ServiceDelivery.is_active == True, ServiceDelivery.solution_type.isnot(None))
        .group_by(ServiceDelivery.solution_type)
    )
    by_solution = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in solution_result.all()}

    # Average rating
    rating_result = await db.execute(
        select(func.coalesce(func.avg(ServiceDelivery.client_rating), 0))
        .where(ServiceDelivery.business_id == business_id, ServiceDelivery.client_rating.isnot(None))
    )
    avg_rating = float(rating_result.scalar() or 0)

    # Attendance rate
    checked_count = completed_count + no_show_count + cancelled_count
    attendance_rate = (completed_count / checked_count * 100) if checked_count > 0 else 0

    return {
        "period_days": days,
        "total_deliveries": total_deliveries,
        "total_appointments": total_appointments,
        "completed_count": completed_count,
        "no_show_count": no_show_count,
        "cancelled_count": cancelled_count,
        "attendance_rate": round(attendance_rate, 2),
        "average_rating": round(avg_rating, 2),
        "by_status": by_status,
        "by_modality": by_modality,
        "by_solution_type": by_solution,
    }
