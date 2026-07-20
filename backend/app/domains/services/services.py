"""Services & Appointments Services

Lógica de negocio para entregas de servicios y agenda.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from app.domains.services.models import ServiceDelivery, Appointment, ServiceDeliveryStatus, AppointmentStatus
from app.domains.orders.models import Order, OrderStatus
from app.domains.channels.services import send_outbound_message
from app.core.events import emit_event


# ============================================================
# SERVICE DELIVERIES
# ============================================================

async def list_service_deliveries(
    db: AsyncSession,
    business_id: uuid.UUID,
    status: Optional[str] = None,
    order_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[ServiceDelivery], int]:
    query = select(ServiceDelivery).where(
        ServiceDelivery.business_id == business_id,
        ServiceDelivery.is_active == True,
    )
    if status:
        query = query.where(ServiceDelivery.status == status)
    if order_id:
        query = query.where(ServiceDelivery.order_id == order_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    query = query.order_by(desc(ServiceDelivery.scheduled_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_service_delivery(db: AsyncSession, delivery_id: uuid.UUID) -> Optional[ServiceDelivery]:
    return await db.get(ServiceDelivery, delivery_id)


async def create_service_delivery(db: AsyncSession, business_id: uuid.UUID, data: Dict[str, Any]) -> ServiceDelivery:
    delivery = ServiceDelivery(
        business_id=business_id,
        order_id=data["order_id"],
        catalog_item_id=data.get("catalog_item_id"),
        conversation_id=data.get("conversation_id"),
        scheduled_at=data.get("scheduled_at"),
        modality=data.get("modality"),
        solution_type=data.get("solution_type"),
        location_address=data.get("location_address", {}),
        meeting_url=data.get("meeting_url"),
        estimated_duration_minutes=data.get("estimated_duration_minutes"),
    )
    db.add(delivery)
    await db.commit()
    await db.refresh(delivery)

    await emit_event("service_delivery_created", {
        "delivery_id": str(delivery.id),
        "order_id": str(delivery.order_id),
        "business_id": str(business_id),
    })
    return delivery


async def update_service_delivery(db: AsyncSession, delivery: ServiceDelivery, data: Dict[str, Any]) -> ServiceDelivery:
    for field, value in data.items():
        if value is not None and hasattr(delivery, field):
            setattr(delivery, field, value)

    await db.commit()
    await db.refresh(delivery)
    return delivery


async def complete_service_delivery(db: AsyncSession, delivery: ServiceDelivery) -> ServiceDelivery:
    delivery.status = ServiceDeliveryStatus.COMPLETED
    delivery.completed_at = datetime.now(timezone.utc)

    # Update order if applicable
    order = await db.get(Order, delivery.order_id)
    if order and order.status == OrderStatus.SHIPPED:
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(delivery)

    await emit_event("service_completed", {
        "delivery_id": str(delivery.id),
        "order_id": str(delivery.order_id),
    })
    return delivery


async def cancel_service_delivery(db: AsyncSession, delivery: ServiceDelivery) -> ServiceDelivery:
    delivery.status = ServiceDeliveryStatus.CANCELLED
    delivery.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(delivery)
    return delivery


# ============================================================
# APPOINTMENTS
# ============================================================

async def list_appointments(
    db: AsyncSession,
    business_id: uuid.UUID,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[Appointment], int]:
    query = select(Appointment).where(
        Appointment.business_id == business_id,
        Appointment.is_active == True,
    )
    if status:
        query = query.where(Appointment.status == status)
    if from_date:
        query = query.where(Appointment.start_time >= from_date)
    if to_date:
        query = query.where(Appointment.start_time <= to_date)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    query = query.order_by(Appointment.start_time).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_appointment(db: AsyncSession, appointment_id: uuid.UUID) -> Optional[Appointment]:
    return await db.get(Appointment, appointment_id)


async def create_appointment(db: AsyncSession, business_id: uuid.UUID, data: Dict[str, Any]) -> Appointment:
    appt = Appointment(
        business_id=business_id,
        service_delivery_id=data.get("service_delivery_id"),
        order_id=data.get("order_id"),
        conversation_id=data.get("conversation_id"),
        client_name=data.get("client_name"),
        client_email=data.get("client_email"),
        client_phone=data.get("client_phone"),
        start_time=data["start_time"],
        end_time=data["end_time"],
        timezone=data.get("timezone", "America/Argentina/Buenos_Aires"),
        modality=data.get("modality"),
        solution_type=data.get("solution_type"),
        service_name=data.get("service_name"),
        location_address=data.get("location_address", {}),
        meeting_url=data.get("meeting_url"),
        preparation_notes=data.get("preparation_notes"),
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)

    # Link to service delivery if exists
    if appt.service_delivery_id:
        delivery = await db.get(ServiceDelivery, appt.service_delivery_id)
        if delivery:
            delivery.scheduled_at = appt.start_time
            delivery.modality = appt.modality
            await db.commit()

    await emit_event("appointment_scheduled", {
        "appointment_id": str(appt.id),
        "business_id": str(business_id),
        "start_time": appt.start_time.isoformat(),
    })
    return appt


async def update_appointment(db: AsyncSession, appt: Appointment, data: Dict[str, Any]) -> Appointment:
    for field, value in data.items():
        if value is not None and hasattr(appt, field):
            setattr(appt, field, value)

    await db.commit()
    await db.refresh(appt)
    return appt


async def confirm_appointment(db: AsyncSession, appt: Appointment) -> Appointment:
    appt.status = AppointmentStatus.CONFIRMED
    appt.confirmation_received_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(appt)

    # Update linked service delivery
    if appt.service_delivery_id:
        delivery = await db.get(ServiceDelivery, appt.service_delivery_id)
        if delivery:
            delivery.status = ServiceDeliveryStatus.CONFIRMED
            await db.commit()

    return appt


async def complete_appointment(db: AsyncSession, appt: Appointment) -> Appointment:
    appt.status = AppointmentStatus.COMPLETED
    await db.commit()
    await db.refresh(appt)

    # Complete linked service delivery
    if appt.service_delivery_id:
        delivery = await db.get(ServiceDelivery, appt.service_delivery_id)
        if delivery:
            await complete_service_delivery(db, delivery)

    return appt


async def cancel_appointment(db: AsyncSession, appt: Appointment) -> Appointment:
    appt.status = AppointmentStatus.CANCELLED
    await db.commit()
    await db.refresh(appt)

    if appt.service_delivery_id:
        delivery = await db.get(ServiceDelivery, appt.service_delivery_id)
        if delivery:
            await cancel_service_delivery(db, delivery)

    return appt


async def mark_no_show(db: AsyncSession, appt: Appointment) -> Appointment:
    appt.status = AppointmentStatus.NO_SHOW
    await db.commit()
    await db.refresh(appt)

    if appt.service_delivery_id:
        delivery = await db.get(ServiceDelivery, appt.service_delivery_id)
        if delivery:
            delivery.status = ServiceDeliveryStatus.NO_SHOW
            await db.commit()

    await emit_event("appointment_no_show", {
        "appointment_id": str(appt.id),
        "business_id": str(appt.business_id),
    })
    return appt


async def send_appointment_reminder(db: AsyncSession, appt: Appointment, channel: str = "whatsapp") -> Dict[str, Any]:
    """Send reminder to client about upcoming appointment."""
    message = (
        f"¡Hola {appt.client_name or ''}! 👋\n\n"
        f"Te recordamos tu cita para *{appt.service_name or 'nuestro servicio'}*.\n\n"
        f"📅 Fecha: {appt.start_time.strftime('%d/%m/%Y')}\n"
        f"⏰ Hora: {appt.start_time.strftime('%H:%M')}\n"
    )

    if appt.modality:
        message += f"📍 Modalidad: {appt.modality.value.replace('_', ' ')}\n"
    if appt.meeting_url:
        message += f"🔗 Link: {appt.meeting_url}\n"
    if appt.location_address and appt.location_address.get("street"):
        message += f"📍 Dirección: {appt.location_address.get('street')}, {appt.location_address.get('city', '')}\n"

    message += "\nPor favor confirma tu asistencia respondiendo *SI*."

    # Try to send via channel
    try:
        if channel == "email" and appt.client_email:
            # TODO: send email
            pass
        elif channel in ("whatsapp", "sms", "telegram") and appt.client_phone:
            from app.domains.channels.models import ChannelConnection, ChannelPlatform
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == appt.business_id,
                    ChannelConnection.platform == ChannelPlatform.WHATSAPP,
                    ChannelConnection.is_active == True,
                )
            )
            conn = result.scalar_one_or_none()
            if conn:
                await send_outbound_message(
                    db=db,
                    channel_id=conn.id,
                    recipient=appt.client_phone,
                    content=message,
                )

        appt.reminder_sent_at = datetime.now(timezone.utc)
        await db.commit()

        return {"success": True, "channel": channel, "message": "Recordatorio enviado"}
    except Exception as e:
        return {"success": False, "channel": channel, "message": f"Error: {str(e)}"}


async def request_confirmation(db: AsyncSession, appt: Appointment, channel: str = "whatsapp") -> Dict[str, Any]:
    message = (
        f"¡Hola {appt.client_name or ''}! 👋\n\n"
        f"Necesitamos que confirmes tu asistencia a la cita del {appt.start_time.strftime('%d/%m/%Y')} a las {appt.start_time.strftime('%H:%M')}.\n\n"
        f"Servicio: {appt.service_name or 'nuestro servicio'}\n"
        f"Responde *CONFIRMAR* para confirmar o *CANCELAR* si no podrás asistir."
    )

    try:
        if channel in ("whatsapp", "sms") and appt.client_phone:
            from app.domains.channels.models import ChannelConnection, ChannelPlatform
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == appt.business_id,
                    ChannelConnection.platform == ChannelPlatform.WHATSAPP,
                    ChannelConnection.is_active == True,
                )
            )
            conn = result.scalar_one_or_none()
            if conn:
                await send_outbound_message(
                    db=db,
                    channel_id=conn.id,
                    recipient=appt.client_phone,
                    content=message,
                )

        appt.confirmation_sent_at = datetime.now(timezone.utc)
        await db.commit()
        return {"success": True, "channel": channel, "message": "Solicitud de confirmación enviada"}
    except Exception as e:
        return {"success": False, "channel": channel, "message": f"Error: {str(e)}"}


async def request_feedback(db: AsyncSession, appt: Appointment, channel: str = "whatsapp") -> Dict[str, Any]:
    message = (
        f"¡Hola {appt.client_name or ''}! 🙏\n\n"
        f"Gracias por confiar en nosotros para *{appt.service_name or 'nuestro servicio'}*.\n\n"
        f"¿Cómo fue tu experiencia? Responde con una calificación del 1 al 5 y cualquier comentario que quieras dejar.\n\n"
        f"Tu opinión nos ayuda a mejorar."
    )

    try:
        if channel in ("whatsapp", "sms") and appt.client_phone:
            from app.domains.channels.models import ChannelConnection, ChannelPlatform
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == appt.business_id,
                    ChannelConnection.platform == ChannelPlatform.WHATSAPP,
                    ChannelConnection.is_active == True,
                )
            )
            conn = result.scalar_one_or_none()
            if conn:
                await send_outbound_message(
                    db=db,
                    channel_id=conn.id,
                    recipient=appt.client_phone,
                    content=message,
                )

        appt.feedback_sent_at = datetime.now(timezone.utc)
        await db.commit()
        return {"success": True, "channel": channel, "message": "Solicitud de feedback enviada"}
    except Exception as e:
        return {"success": False, "channel": channel, "message": f"Error: {str(e)}"}


# ============================================================
# AUTOMATED CHECKS
# ============================================================

async def check_upcoming_appointments(db: AsyncSession) -> Dict[str, Any]:
    """Find appointments in next 24h and 1h that haven't been reminded."""
    now = datetime.now(timezone.utc)
    in_24h = now + timedelta(hours=24)
    in_1h = now + timedelta(hours=1)

    # 24h reminders
    result = await db.execute(
        select(Appointment).where(
            Appointment.start_time <= in_24h,
            Appointment.start_time > now,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            Appointment.reminder_sent_at.is_(None),
            Appointment.is_active == True,
        )
    )
    appts_24h = result.scalars().all()

    for appt in appts_24h:
        await send_appointment_reminder(db, appt)

    # 1h reminders (re-remind)
    result = await db.execute(
        select(Appointment).where(
            Appointment.start_time <= in_1h,
            Appointment.start_time > now,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            Appointment.is_active == True,
        )
    )
    appts_1h = result.scalars().all()

    for appt in appts_1h:
        # Only re-remind if last reminder was more than 30 min ago
        if appt.reminder_sent_at and (now - appt.reminder_sent_at).total_seconds() > 1800:
            await send_appointment_reminder(db, appt)

    return {
        "reminders_24h": len(appts_24h),
        "reminders_1h": len(appts_1h),
    }


async def process_no_shows(db: AsyncSession) -> int:
    """Mark appointments that passed without completion as no-show."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Appointment).where(
            Appointment.end_time < now,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            Appointment.is_active == True,
        )
    )
    appts = result.scalars().all()

    for appt in appts:
        await mark_no_show(db, appt)

    return len(appts)


async def request_pending_confirmations(db: AsyncSession) -> int:
    """Send confirmation requests for appointments scheduled within 48h that are still pending."""
    now = datetime.now(timezone.utc)
    in_48h = now + timedelta(hours=48)

    result = await db.execute(
        select(Appointment).where(
            Appointment.start_time <= in_48h,
            Appointment.start_time > now,
            Appointment.status == AppointmentStatus.PENDING,
            Appointment.confirmation_sent_at.is_(None),
            Appointment.is_active == True,
        )
    )
    appts = result.scalars().all()

    for appt in appts:
        await request_confirmation(db, appt)

    return len(appts)
