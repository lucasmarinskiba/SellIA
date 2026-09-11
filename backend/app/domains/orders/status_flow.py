"""What actually happens when an order changes state.

The PATCH endpoint used to own this logic inline, so a bulk action could only
either duplicate it or skip it — and skipping it means an order marked "pagada"
from the spreadsheet would have no paid_at, no payment_status, and would never
fire the service-paid automation. One function, used by both paths.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.orders.models import Order, OrderStatus, PaymentStatus

logger = get_logger(__name__)

# Which moves the UI offers from each state. Kept here so the buttons and the
# bulk action agree on what is legal instead of each inventing its own list.
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    OrderStatus.PENDING.value: [OrderStatus.PAID.value, OrderStatus.CANCELLED.value],
    OrderStatus.PAID.value: [
        OrderStatus.SHIPPED.value,
        OrderStatus.CANCELLED.value,
        OrderStatus.REFUNDED.value,
    ],
    OrderStatus.SHIPPED.value: [OrderStatus.DELIVERED.value, OrderStatus.REFUNDED.value],
    OrderStatus.DELIVERED.value: [OrderStatus.REFUNDED.value],
    OrderStatus.CANCELLED.value: [],
    OrderStatus.REFUNDED.value: [],
}


def parse_status(raw: Any) -> Optional[OrderStatus]:
    if isinstance(raw, OrderStatus):
        return raw
    if not raw:
        return None
    candidate = str(raw).rsplit(".", 1)[-1].strip().lower()
    for member in OrderStatus:
        if candidate in (member.value.lower(), member.name.lower()):
            return member
    return None


def status_updates(order: Order, new_status: OrderStatus) -> dict[str, Any]:
    """The side fields a status change implies. No DB writes here."""
    now = datetime.now(timezone.utc)
    updates: dict[str, Any] = {"status": new_status}

    if new_status == OrderStatus.PAID:
        if not order.paid_at:
            updates["paid_at"] = now
        updates["payment_status"] = PaymentStatus.COMPLETED
    elif new_status == OrderStatus.SHIPPED and not order.shipped_at:
        updates["shipped_at"] = now
    elif new_status == OrderStatus.DELIVERED:
        if not order.delivered_at:
            updates["delivered_at"] = now
        # An order can be delivered without ever having been marked shipped
        # (a hand delivery, a counter pickup); record the moment anyway.
        if not order.shipped_at:
            updates["shipped_at"] = now
    elif new_status == OrderStatus.CANCELLED:
        updates["payment_status"] = PaymentStatus.FAILED
    elif new_status == OrderStatus.REFUNDED:
        updates["payment_status"] = PaymentStatus.REFUNDED

    return updates


def apply_status(
    order: Order,
    new_status: OrderStatus,
    *,
    enforce_transitions: bool = True,
) -> dict[str, Any]:
    """Move one order in memory. Returns what changed; the caller commits.

    `enforce_transitions` is on for user-driven moves and off for reconciliation
    from a platform webhook, where the remote marketplace is the source of truth
    and may jump straight from pending to delivered.
    """
    current = order.status.value if order.status else OrderStatus.PENDING.value
    if new_status.value == current:
        return {"changed": False, "reason": "La orden ya está en ese estado"}

    if enforce_transitions and new_status.value not in ALLOWED_TRANSITIONS.get(current, []):
        return {
            "changed": False,
            "reason": f"No se puede pasar de '{current}' a '{new_status.value}'",
        }

    updates = status_updates(order, new_status)
    for field, value in updates.items():
        setattr(order, field, value)

    return {
        "changed": True,
        "updates": {k: str(v) for k, v in updates.items()},
        "fires_service_paid": new_status == OrderStatus.PAID and _sells_a_service(order),
    }


def _sells_a_service(order: Order) -> bool:
    items = order.items if isinstance(order.items, list) else []
    return any(isinstance(i, dict) and i.get("type") == "service" for i in items)


def service_paid_payload(order: Order) -> dict[str, Any]:
    """Snapshot the trigger's inputs while the instance is still loaded.

    Read after a commit, these attributes would lazy-load in an async context
    and raise MissingGreenlet; take plain values now.
    """
    return {
        "business_id": order.business_id,
        "conversation_id": order.conversation_id,
        "order_id": str(order.id),
        "total_amount": float(order.total_amount or 0),
    }


async def fire_service_paid(db: AsyncSession, payload: dict[str, Any]) -> None:
    """Run the service-paid workflow. Call this AFTER the status is committed.

    It runs post-commit on purpose: the automation's rollback-on-failure would
    otherwise discard the payment itself, since Postgres poisons the whole
    transaction on the first failed statement and the status change is still
    pending in it.
    """
    try:
        from app.domains.automations.engine import WorkflowEngine

        engine = WorkflowEngine(db)
        await engine.process_trigger(
            trigger_type="service_paid",
            business_id=payload["business_id"],
            conversation_id=payload["conversation_id"],
            trigger_data={
                "order_id": payload["order_id"],
                "total_amount": payload["total_amount"],
            },
        )
    except Exception as e:  # noqa: BLE001 - the payment stands even if the automation does not
        logger.error(f"service_paid trigger failed for order {payload['order_id']}: {e}")
        await db.rollback()
