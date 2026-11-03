"""Queue a sale/refund for feedIA whenever an order's status moves, whichever code path moved it.

Orders change state in many places (the PATCH endpoint, bulk actions, marketplace webhooks, shipments), and only some of
them go through orders/status_flow.apply_status. Hooking the model instead catches all of them, and the outbox row is
written on the same connection and transaction as the order, so the two commit or roll back together.

This runs inside every order write, so it must never be able to break one: any failure is swallowed (and logged) inside a
SAVEPOINT, so even a database error cannot poison the order's own transaction.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import event, inspect, insert, select

from app.core.logger import get_logger
from app.domains.feedia_link.models import FeediaLink, FeediaOutbox
from app.domains.feedia_link.signing import refund_event, sale_event
from app.domains.orders.models import Order, OrderStatus

logger = get_logger(__name__)

#: Statuses in which the money is in: a sale for feedIA.
COUNTED = {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED}
#: Money that was counted and then given back (or never kept).
REVERSED = {OrderStatus.REFUNDED, OrderStatus.CANCELLED}


def _status(value: Any) -> OrderStatus | None:
    if isinstance(value, OrderStatus):
        return value
    try:
        return OrderStatus(str(value).rsplit(".", 1)[-1].lower()) if value else None
    except ValueError:
        return None


def event_for_transition(previous: Any, new: Any) -> str | None:
    """'sale', 'refund' or None for a status change (previous is None when the order is being created)."""
    prev, cur = _status(previous), _status(new)
    if cur in COUNTED and prev not in COUNTED:
        return "sale"
    if cur in REVERSED and prev in COUNTED:
        return "refund"
    return None


def _secret_key() -> str:
    from app.core.config import get_settings

    return get_settings().SECRET_KEY


def enqueue(connection: Any, order: Any, event_type: str) -> bool:
    """Write the outbox row for `order` if its business is linked. Returns whether one was written."""
    link = connection.execute(
        select(FeediaLink.enabled).where(FeediaLink.business_id == order.business_id)
    ).first()
    if link is None or not link[0]:
        return False
    exists = connection.execute(
        select(FeediaOutbox.id).where(
            FeediaOutbox.business_id == order.business_id,
            FeediaOutbox.event_type == event_type,
            FeediaOutbox.order_id == str(order.id),
        )
    ).first()
    if exists:
        return False
    if event_type == "sale":
        payload = sale_event(
            order_id=order.id,
            total=order.total_amount,
            when=order.paid_at or order.created_at or datetime.now(timezone.utc),
            business_id=order.business_id,
            email=order.customer_email,  # read through the ORM so the encrypted column is already decrypted
            key=_secret_key(),
        )
    else:
        payload = refund_event(order_id=order.id)
    connection.execute(
        insert(FeediaOutbox).values(
            id=uuid.uuid4(),
            business_id=order.business_id,
            event_type=event_type,
            order_id=str(order.id),
            payload=payload,
            status="pending",
            attempts=0,
            next_attempt_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
    )
    return True


def _on_order_write(mapper: Any, connection: Any, order: Any) -> None:
    try:
        history = inspect(order).attrs.status.history
        if not history.added:  # status untouched in this flush
            return
        previous = history.deleted[0] if history.deleted else None
        kind = event_for_transition(previous, history.added[0])
        if kind is None:
            return
        with connection.begin_nested():  # a failure here rolls back only this savepoint, never the order
            enqueue(connection, order, kind)
    except Exception:  # noqa: BLE001 - feeding feedIA is best effort; the order write is what matters
        logger.exception("feedia_link: could not queue an event for order %s", getattr(order, "id", "?"))


event.listen(Order, "after_insert", _on_order_write)
event.listen(Order, "after_update", _on_order_write)
