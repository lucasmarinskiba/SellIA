"""Orders API Router"""

import csv
import io
import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.events import emit_order_created
from app.domains.automations.models import Workflow
from app.domains.orders import status_flow
from app.domains.orders import table as orders_table
from app.domains.orders.models import Order, OrderStatus, PaymentStatus, RevenueEvent
from app.domains.orders.revenue import RevenueAttributionEngine
from app.domains.orders.schemas import (
    AttributionSummary,
    OrderCreate,
    OrderResponse,
    OrderUpdate,
    RevenueSummary,
)
from app.domains.services.models import (
    Appointment,
    ServiceDelivery,
    ServiceDeliveryStatus,
)
from app.domains.users.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    status: str | None = None,
    search: str | None = None,
):
    query = select(Order).where(Order.business_id == business_id, Order.is_active == True)
    if status:
        parsed = status_flow.parse_status(status)
        if not parsed:
            raise HTTPException(status_code=422, detail=f"Estado desconocido: {status}")
        query = query.where(Order.status == parsed)
    if search:
        # customer_name/email/phone are encrypted at rest, so ILIKE compares
        # ciphertext and never matches — searching them needs decryption, which
        # /orders/table does. Here, only the columns stored in clear.
        query = query.where(
            Order.order_number.ilike(f"%{search}%") |
            Order.external_id.ilike(f"%{search}%") |
            Order.tracking_number.ilike(f"%{search}%")
        )
    result = await db.execute(query.order_by(desc(Order.created_at)))
    return result.scalars().all()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    payload = data.model_dump()
    # items arrive as OrderItem models; JSONB needs plain dicts.
    payload["items"] = [
        item if isinstance(item, dict) else dict(item)
        for item in (payload.get("items") or [])
    ]

    # An order created as paid/shipped/delivered without an explicit
    # payment_status kept the PENDING default, so it showed up as sold and not
    # collected: "1 orden, 0 cobradas" for an order whose status says paid.
    # Only filled in when the caller did not state it — an importer that really
    # means "delivered but unpaid" is still believed.
    status_value = payload.get("status")
    if "payment_status" not in data.model_fields_set and status_value in (
        OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED,
    ):
        payload["payment_status"] = PaymentStatus.COMPLETED
        if not payload.get("paid_at"):
            payload.pop("paid_at", None)

    order = Order(**payload)
    if order.payment_status == PaymentStatus.COMPLETED and not order.paid_at:
        order.paid_at = datetime.now(UTC)

    # Run revenue attribution
    engine = RevenueAttributionEngine(db)
    await engine.attrib_order(order)

    db.add(order)
    try:
        await db.commit()
    except IntegrityError as e:
        # Almost always a repeated order_number within this business. Say that,
        # instead of letting the driver error surface as a 500.
        await db.rollback()
        if "uq_orders_business_number" in str(e) or "order_number" in str(e):
            raise HTTPException(
                status_code=409,
                detail=f"Ya tenés una orden con el número '{data.order_number}'",
            )
        raise HTTPException(status_code=409, detail="No se pudo guardar la orden")
    await db.refresh(order)

    # Create revenue event
    revenue_event = RevenueEvent(
        business_id=order.business_id,
        order_id=order.id,
        event_type="order_created",
        amount=order.total_amount,
        currency=order.currency,
        source_channel=order.source_channel,
        source_workflow_id=order.source_workflow_id,
        source_agent_id=order.source_agent_id,
        source_campaign=order.source_campaign,
        touchpoint_data={
            "first_touch": order.first_touch_channel,
            "last_touch": order.last_touch_channel,
            "attribution_model": order.attribution_model,
        },
    )
    db.add(revenue_event)
    await db.commit()

    # Increment workflow conversion_count if attributed to a workflow
    if order.source_workflow_id:
        try:
            wf_result = await db.execute(select(Workflow).where(Workflow.id == order.source_workflow_id))
            wf = wf_result.scalar_one_or_none()
            if wf:
                wf.conversion_count = (wf.conversion_count or 0) + 1
                await db.commit()
        except Exception as e:
            logger.exception("create_order: error inesperado")
            from app.core.logger import get_logger
            get_logger(__name__).error(f"Error updating workflow conversion_count: {e}")

    # Emit event for alert engine
    await emit_order_created(
        business_id=str(order.business_id),
        order_id=str(order.id),
        total_amount=float(order.total_amount),
        status=order.status.value,
        conversation_id=str(order.conversation_id) if order.conversation_id else None,
    )

    return order


# ========== Spreadsheet ==========
# Declared before /{order_id}: FastAPI matches in order, and "table" would
# otherwise be parsed as a UUID path param.


def _table_query(
    search: str | None,
    status_in: str | None,
    payment_status: str | None,
    platform: str | None,
    channel: str | None,
    currency: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    amount_min: float | None,
    amount_max: float | None,
    has_tracking: bool | None,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> orders_table.TableQuery:
    def split(raw: str | None) -> list[str]:
        return [part.strip() for part in raw.split(",") if part.strip()] if raw else []

    return orders_table.TableQuery(
        search=search,
        status=split(status_in),
        payment_status=split(payment_status),
        platform=split(platform),
        channel=split(channel),
        currency=split(currency),
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        has_tracking=has_tracking,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


@router.get("/table")
async def orders_spreadsheet(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    search: str | None = None,
    status_in: Annotated[str | None, Query(description="Lista separada por comas")] = None,
    payment_status: str | None = None,
    platform: str | None = None,
    channel: str | None = None,
    currency: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    has_tracking: bool | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = 50,
):
    """A page of the orders sheet, with totals and facets over the whole filter."""
    query = _table_query(
        search, status_in, payment_status, platform, channel, currency,
        date_from, date_to, amount_min, amount_max, has_tracking,
        sort_by, sort_dir, page, page_size,
    )
    data = await orders_table.fetch_table(db, business_id, query)
    data["columns"] = [
        {"key": key, "label": label, "sortable": key in orders_table.SORTABLE}
        for key, label in orders_table.EXPORT_COLUMNS
    ]
    data["transitions"] = status_flow.ALLOWED_TRANSITIONS
    return data


@router.get("/export.csv")
async def export_orders_csv(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    search: str | None = None,
    status_in: str | None = None,
    payment_status: str | None = None,
    platform: str | None = None,
    channel: str | None = None,
    currency: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    has_tracking: bool | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    limit: Annotated[int, Query(ge=1, le=20000)] = 5000,
):
    """The same filtered sheet as a CSV Excel opens directly.

    Customer columns come out masked, exactly as they render on screen: the
    export is a copy of the view, not a way around the masking policy.
    """
    query = _table_query(
        search, status_in, payment_status, platform, channel, currency,
        date_from, date_to, amount_min, amount_max, has_tracking,
        sort_by, sort_dir, 1, limit,
    )
    data = await orders_table.fetch_table(db, business_id, query)

    buffer = io.StringIO()
    # Excel in es-AR reads ; as the column separator; BOM so it detects UTF-8.
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([label for _, label in orders_table.EXPORT_COLUMNS])
    for row in data["rows"]:
        writer.writerow([row.get(key, "") if row.get(key) is not None else "" for key, _ in orders_table.EXPORT_COLUMNS])
    writer.writerow([])
    for total in data["totals"]:
        writer.writerow([
            f"TOTAL {total['currency']}", "", "", "", "", "", "",
            total["orders"], total["revenue"], total["currency"],
        ])
    if data["total"] > len(data["rows"]):
        writer.writerow([f"Exportadas {len(data['rows'])} de {data['total']} órdenes del filtro"])

    payload = "﻿" + buffer.getvalue()
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ordenes-{stamp}.csv"'},
    )


class BulkStatusRequest(BaseModel):
    order_ids: list[UUID] = Field(..., min_length=1, max_length=200)
    status: str


@router.post("/bulk-status")
async def bulk_update_status(
    data: BulkStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Move many orders at once, one verdict per order.

    Orders whose current state does not allow the move are reported as skipped
    with the reason — a bulk action that says "50 actualizadas" when 12 were
    illegal is the kind of number this product does not print.
    """
    new_status = status_flow.parse_status(data.status)
    if not new_status:
        raise HTTPException(status_code=422, detail=f"Estado desconocido: {data.status}")

    result = await db.execute(select(Order).where(Order.id.in_(data.order_ids)))
    orders = result.scalars().all()
    found = {order.id for order in orders}

    outcomes: list[dict] = []
    pending_triggers: list[dict] = []
    changed = 0
    for order in orders:
        verdict = status_flow.apply_status(order, new_status)
        if verdict["changed"]:
            changed += 1
            if verdict.get("fires_service_paid"):
                pending_triggers.append(status_flow.service_paid_payload(order))
        outcomes.append({
            "order_id": str(order.id),
            "changed": verdict["changed"],
            "reason": verdict.get("reason"),
        })
    for missing in data.order_ids:
        if missing not in found:
            outcomes.append({"order_id": str(missing), "changed": False, "reason": "No encontrada"})

    if changed:
        await db.commit()
    for payload in pending_triggers:
        await status_flow.fire_service_paid(db, payload)

    return {
        "requested": len(data.order_ids),
        "updated": changed,
        "skipped": len(outcomes) - changed,
        "status": new_status.value,
        "results": outcomes,
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    data: OrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    update_data = data.model_dump(exclude_unset=True)

    # The status change and everything it implies (timestamps, payment status,
    # the service-paid automation) live in status_flow, so the bulk action and
    # this endpoint cannot drift apart.
    trigger_payload = None
    raw_status = update_data.pop("status", None)
    if raw_status is not None:
        new_status = status_flow.parse_status(raw_status)
        if not new_status:
            raise HTTPException(status_code=422, detail=f"Estado desconocido: {raw_status}")
        verdict = status_flow.apply_status(order, new_status)
        if not verdict["changed"] and verdict.get("reason") and new_status.value != (order.status.value if order.status else None):
            raise HTTPException(status_code=409, detail=verdict["reason"])
        if verdict.get("fires_service_paid"):
            trigger_payload = status_flow.service_paid_payload(order)

    for field, value in update_data.items():
        setattr(order, field, value)
    await db.commit()
    await db.refresh(order)

    if trigger_payload:
        await status_flow.fire_service_paid(db, trigger_payload)
    return order


@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    order.is_active = False
    await db.commit()
    return {"message": "Orden eliminada"}


# ========== Revenue & Analytics ==========

@router.get("/revenue/summary", response_model=RevenueSummary)
async def get_revenue_summary(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    since = datetime.now(UTC) - timedelta(days=days)

    # Total revenue
    total_result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0), func.count(Order.id))
        .where(Order.business_id == business_id, Order.is_active == True, Order.created_at >= since)
    )
    total_revenue, total_orders = total_result.one()

    # Paid orders
    paid_result = await db.execute(
        select(func.count(Order.id))
        .where(Order.business_id == business_id, Order.status == OrderStatus.PAID, Order.created_at >= since)
    )
    paid_orders = paid_result.scalar() or 0

    # Pending orders
    pending_result = await db.execute(
        select(func.count(Order.id))
        .where(Order.business_id == business_id, Order.status == OrderStatus.PENDING, Order.created_at >= since)
    )
    pending_orders = pending_result.scalar() or 0

    # Refunded
    refunded_result = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.business_id == business_id, Order.status == OrderStatus.REFUNDED, Order.created_at >= since)
    )
    refunded_amount = refunded_result.scalar() or 0

    # By channel
    channel_result = await db.execute(
        select(Order.source_channel, func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.business_id == business_id, Order.is_active == True, Order.created_at >= since)
        .group_by(Order.source_channel)
    )
    revenue_by_channel = {row[0] or "unknown": float(row[1]) for row in channel_result.all()}

    # By platform
    platform_result = await db.execute(
        select(Order.external_platform, func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.business_id == business_id, Order.is_active == True, Order.created_at >= since)
        .group_by(Order.external_platform)
    )
    revenue_by_platform = {row[0] or "manual": float(row[1]) for row in platform_result.all()}

    # By status
    status_result = await db.execute(
        select(Order.status, func.count(Order.id))
        .where(Order.business_id == business_id, Order.is_active == True, Order.created_at >= since)
        .group_by(Order.status)
    )
    orders_by_status = {row[0]: row[1] for row in status_result.all()}

    # Trend
    trend_result = await db.execute(
        select(func.date(Order.created_at), func.coalesce(func.sum(Order.total_amount), 0), func.count(Order.id))
        .where(Order.business_id == business_id, Order.is_active == True, Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    revenue_trend = [
        {"date": str(row[0]), "revenue": float(row[1]), "orders": row[2]}
        for row in trend_result.all()
    ]

    return RevenueSummary(
        period_days=days,
        total_revenue=float(total_revenue or 0),
        total_orders=total_orders or 0,
        avg_order_value=float(total_revenue or 0) / (total_orders or 1),
        paid_orders=paid_orders,
        pending_orders=pending_orders,
        refunded_amount=float(refunded_amount),
        revenue_by_channel=revenue_by_channel,
        revenue_by_platform=revenue_by_platform,
        orders_by_status=orders_by_status,
        revenue_trend=revenue_trend,
    )


@router.get("/revenue/attribution", response_model=AttributionSummary)
async def get_attribution_summary(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    since = datetime.now(UTC) - timedelta(days=days)

    # Total
    total_result = await db.execute(
        select(func.coalesce(func.sum(RevenueEvent.amount), 0), func.count(RevenueEvent.id))
        .where(RevenueEvent.business_id == business_id, RevenueEvent.created_at >= since)
    )
    total_revenue, total_events = total_result.one()

    # By channel
    channel_result = await db.execute(
        select(RevenueEvent.source_channel, func.coalesce(func.sum(RevenueEvent.amount), 0), func.count(RevenueEvent.id))
        .where(RevenueEvent.business_id == business_id, RevenueEvent.created_at >= since)
        .group_by(RevenueEvent.source_channel)
        .order_by(desc(func.sum(RevenueEvent.amount)))
    )
    by_channel = [
        {"channel": row[0] or "unknown", "revenue": float(row[1]), "orders": row[2]}
        for row in channel_result.all()
    ]

    # By workflow
    wf_result = await db.execute(
        select(RevenueEvent.source_workflow_id, func.coalesce(func.sum(RevenueEvent.amount), 0), func.count(RevenueEvent.id))
        .where(RevenueEvent.business_id == business_id, RevenueEvent.created_at >= since)
        .group_by(RevenueEvent.source_workflow_id)
        .order_by(desc(func.sum(RevenueEvent.amount)))
    )
    by_workflow = [
        {"workflow_id": str(row[0]) if row[0] else None, "revenue": float(row[1]), "orders": row[2]}
        for row in wf_result.all()
    ]

    # By agent
    agent_result = await db.execute(
        select(RevenueEvent.source_agent_id, func.coalesce(func.sum(RevenueEvent.amount), 0), func.count(RevenueEvent.id))
        .where(RevenueEvent.business_id == business_id, RevenueEvent.created_at >= since)
        .group_by(RevenueEvent.source_agent_id)
        .order_by(desc(func.sum(RevenueEvent.amount)))
    )
    by_agent = [
        {"agent_id": str(row[0]) if row[0] else None, "revenue": float(row[1]), "orders": row[2]}
        for row in agent_result.all()
    ]

    # First vs Last touch from orders
    first_touch_result = await db.execute(
        select(Order.first_touch_channel, func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.business_id == business_id, Order.is_active == True, Order.created_at >= since)
        .group_by(Order.first_touch_channel)
    )
    first_touch_revenue = {row[0] or "unknown": float(row[1]) for row in first_touch_result.all()}

    last_touch_result = await db.execute(
        select(Order.last_touch_channel, func.coalesce(func.sum(Order.total_amount), 0))
        .where(Order.business_id == business_id, Order.is_active == True, Order.created_at >= since)
        .group_by(Order.last_touch_channel)
    )
    last_touch_revenue = {row[0] or "unknown": float(row[1]) for row in last_touch_result.all()}

    return AttributionSummary(
        total_revenue=float(total_revenue or 0),
        total_orders=total_events or 0,
        by_channel=by_channel,
        by_workflow=by_workflow,
        by_agent=by_agent,
        first_touch_revenue=first_touch_revenue,
        last_touch_revenue=last_touch_revenue,
    )



# ========== Service Lifecycle Endpoints ==========

@router.get("/{order_id}/service-delivery", response_model=dict)
async def get_order_service_delivery(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get service delivery and appointments linked to an order."""
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

    return {
        "delivery": delivery,
        "appointments": appointments,
    }


@router.post("/{order_id}/schedule-service", response_model=dict)
async def schedule_service_for_order(
    order_id: UUID,
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Schedule a service delivery + appointment for a service order."""
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    from app.domains.services.services import (
        create_appointment,
        create_service_delivery,
    )

    # Create service delivery
    delivery_data = {
        "order_id": order_id,
        "catalog_item_id": data.get("catalog_item_id"),
        "conversation_id": order.conversation_id,
        "scheduled_at": data.get("scheduled_at"),
        "modality": data.get("modality"),
        "solution_type": data.get("solution_type"),
        "location_address": data.get("location_address", {}),
        "meeting_url": data.get("meeting_url"),
        "estimated_duration_minutes": data.get("estimated_duration_minutes", 60),
    }
    delivery = await create_service_delivery(db, order.business_id, delivery_data)

    # Create appointment linked to delivery
    from datetime import timedelta
    start = data.get("scheduled_at")
    if start:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) if isinstance(start, str) else start
        end_dt = start_dt + timedelta(minutes=data.get("estimated_duration_minutes", 60))
        appt_data = {
            "service_delivery_id": delivery.id,
            "order_id": order_id,
            "conversation_id": order.conversation_id,
            "client_name": order.customer_name or data.get("client_name"),
            "client_email": order.customer_email or data.get("client_email"),
            "client_phone": order.customer_phone or data.get("client_phone"),
            "start_time": start_dt,
            "end_time": end_dt,
            "modality": data.get("modality"),
            "solution_type": data.get("solution_type"),
            "service_name": data.get("service_name", order.items[0].get("name") if order.items else "Servicio"),
            "location_address": data.get("location_address", {}),
            "meeting_url": data.get("meeting_url"),
        }
        appointment = await create_appointment(db, order.business_id, appt_data)
    else:
        appointment = None

    # Update order status
    if order.status == OrderStatus.PAID:
        order.status = OrderStatus.SHIPPED
        order.shipped_at = datetime.now(UTC)
    await db.commit()

    return {
        "success": True,
        "message": "Servicio agendado correctamente",
        "delivery": delivery,
        "appointment": appointment,
    }


@router.post("/{order_id}/start-service", response_model=dict)
async def start_service_for_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Mark service as in-progress for an order."""
    result = await db.execute(
        select(ServiceDelivery).where(ServiceDelivery.order_id == order_id, ServiceDelivery.is_active == True)
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="No hay entrega de servicio para esta orden")

    delivery.status = ServiceDeliveryStatus.IN_PROGRESS
    delivery.started_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(delivery)

    return {"success": True, "message": "Servicio iniciado", "delivery": delivery}


@router.post("/{order_id}/complete-service", response_model=dict)
async def complete_service_for_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Mark service as completed for an order."""
    result = await db.execute(
        select(ServiceDelivery).where(ServiceDelivery.order_id == order_id, ServiceDelivery.is_active == True)
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="No hay entrega de servicio para esta orden")

    from app.domains.services.services import complete_service_delivery
    await complete_service_delivery(db, delivery)

    # Update order
    order = await db.get(Order, order_id)
    if order and order.status == OrderStatus.SHIPPED:
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.now(UTC)
        await db.commit()

    return {"success": True, "message": "Servicio completado", "delivery": delivery}


@router.post("/{order_id}/add-service-notes", response_model=dict)
async def add_service_notes(
    order_id: UUID,
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Add provider notes, diagnosis, materials to a service delivery."""
    result = await db.execute(
        select(ServiceDelivery).where(ServiceDelivery.order_id == order_id, ServiceDelivery.is_active == True)
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="No hay entrega de servicio para esta orden")

    if data.get("provider_notes"):
        delivery.provider_notes = data["provider_notes"]
    if data.get("diagnosis"):
        delivery.diagnosis = data["diagnosis"]
    if data.get("materials_used"):
        delivery.materials_used = data["materials_used"]
    if data.get("client_feedback"):
        delivery.client_feedback = data["client_feedback"]
    if data.get("client_rating") is not None:
        delivery.client_rating = data["client_rating"]
    if data.get("follow_up_required") is not None:
        delivery.follow_up_required = data["follow_up_required"]
    if data.get("follow_up_notes"):
        delivery.follow_up_notes = data["follow_up_notes"]
    if data.get("actual_duration_minutes"):
        delivery.actual_duration_minutes = data["actual_duration_minutes"]

    await db.commit()
    await db.refresh(delivery)
    return {"success": True, "message": "Notas actualizadas", "delivery": delivery}
