"""Rankings of the seller's own business, and the queue of who to answer first.

The leaderboard this replaces ranked a seller against other SellIA accounts.
Knowing you are 47th of 300 strangers changes nothing about your business; and
the comparison was not even real, since the endpoint behind it does not exist in
this deployment. What a seller can act on is which of THEIR products, customers
and channels is carrying the business — and which buyer has been waiting longest.

Everything here is counted from their own rows, grouped by currency, and shown
with the denominator. A ranking over two orders says so instead of crowning a
"best seller".
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

#: Below this many orders a ranking is noise, and says so.
MIN_FOR_RANKING = 5


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _item_lines(items: Any) -> list[tuple[str, int, float]]:
    """(name, units, revenue) per line, across the two shapes really stored."""
    out: list[tuple[str, int, float]] = []
    if not isinstance(items, list):
        return out
    for raw in items:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or raw.get("title") or "").strip()
        if not name:
            continue
        try:
            qty = int(raw.get("qty", raw.get("quantity", 1)) or 1)
        except (TypeError, ValueError):
            qty = 1
        try:
            price = float(raw.get("price", raw.get("unit_price", 0)) or 0)
        except (TypeError, ValueError):
            price = 0.0
        total = raw.get("total_price")
        try:
            revenue = float(total) if total is not None else price * qty
        except (TypeError, ValueError):
            revenue = price * qty
        out.append((name, qty, revenue))
    return out


async def business_ranking(
    db: AsyncSession, user: Any, days: int = 90
) -> dict[str, Any]:
    """What is carrying this business: products, customers, channels, days."""
    from app.domains.businesses.models import Business
    from app.domains.orders.models import Order, PaymentStatus

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    biz = await db.execute(select(Business.id).where(Business.user_id == user.id))
    business_ids = [row[0] for row in biz.all()]
    empty = {
        "period_days": days,
        "has_data": False,
        "note": "Todavía no hay ventas propias para ordenar.",
        "products": [],
        "customers": [],
        "platforms": [],
        "enough_data": False,
        "orders_counted": 0,
        "generated_at": now.isoformat(),
    }
    if not business_ids:
        empty["note"] = "Todavía no creaste tu negocio."
        return empty

    result = await db.execute(
        select(Order).where(
            Order.business_id.in_(business_ids),
            Order.is_active.is_(True),
            Order.created_at >= since,
        )
    )
    orders = list(result.scalars().all())
    if not orders:
        empty["note"] = f"No hay órdenes en los últimos {days} días."
        return empty

    # Products: units and revenue per currency, plus how many orders included it.
    product_units: dict[str, int] = defaultdict(int)
    product_revenue: dict[tuple[str, str], float] = defaultdict(float)
    product_orders: dict[str, int] = defaultdict(int)
    customer_revenue: dict[tuple[str, str], float] = defaultdict(float)
    customer_orders: dict[str, int] = defaultdict(int)
    customer_label: dict[str, str] = {}
    customer_last: dict[str, datetime] = {}
    platform_revenue: dict[tuple[str, str], float] = defaultdict(float)
    platform_orders: dict[str, int] = defaultdict(int)
    platform_paid: dict[str, int] = defaultdict(int)
    unnamed_items = 0

    from app.core.pii_masking import mask_email, mask_name

    for order in orders:
        currency = order.currency or "?"
        lines = _item_lines(order.items)
        if not lines:
            unnamed_items += 1
        seen_in_order: set[str] = set()
        for name, qty, revenue in lines:
            product_units[name] += qty
            product_revenue[(name, currency)] += revenue
            if name not in seen_in_order:
                product_orders[name] += 1
                seen_in_order.add(name)

        key = (order.customer_email or "").strip().lower() or (order.customer_phone or "").strip()
        if key:
            customer_revenue[(key, currency)] += float(order.total_amount or 0)
            customer_orders[key] += 1
            customer_label[key] = (
                mask_name(order.customer_name) or mask_email(order.customer_email) or "cliente"
            )
            created = _aware(order.created_at)
            if created and (key not in customer_last or created > customer_last[key]):
                customer_last[key] = created

        platform = order.external_platform or "manual"
        platform_revenue[(platform, currency)] += float(order.total_amount or 0)
        platform_orders[platform] += 1
        if order.payment_status == PaymentStatus.COMPLETED:
            platform_paid[platform] += 1

    def group_by_currency(
        values: dict[tuple[str, str], float]
    ) -> dict[str, dict[str, float]]:
        grouped: dict[str, dict[str, float]] = defaultdict(dict)
        for (name, currency), amount in values.items():
            grouped[name][currency] = round(amount, 2)
        return grouped

    product_money = group_by_currency(product_revenue)
    products = sorted(
        (
            {
                "name": name,
                "units": units,
                "orders": product_orders[name],
                "revenue": product_money.get(name, {}),
            }
            for name, units in product_units.items()
        ),
        key=lambda row: (-max(row["revenue"].values(), default=0), -row["units"]),
    )[:10]

    customer_money = group_by_currency(customer_revenue)
    customers = sorted(
        (
            {
                "label": customer_label[key],
                "orders": count,
                "revenue": customer_money.get(key, {}),
                "last_purchase": customer_last[key].isoformat() if key in customer_last else None,
                "days_since": (now - customer_last[key]).days if key in customer_last else None,
            }
            for key, count in customer_orders.items()
        ),
        key=lambda row: (-max(row["revenue"].values(), default=0), -row["orders"]),
    )[:10]

    platform_money = group_by_currency(platform_revenue)
    platforms = sorted(
        (
            {
                "platform": platform,
                "orders": count,
                "paid": platform_paid.get(platform, 0),
                "revenue": platform_money.get(platform, {}),
            }
            for platform, count in platform_orders.items()
        ),
        key=lambda row: -max(row["revenue"].values(), default=0),
    )

    enough = len(orders) >= MIN_FOR_RANKING
    return {
        "period_days": days,
        "has_data": True,
        "enough_data": enough,
        "orders_counted": len(orders),
        "note": (
            None
            if enough
            else (
                f"Con {len(orders)} órdenes este orden es provisorio: hacen falta al menos "
                f"{MIN_FOR_RANKING} para que el primer puesto signifique algo."
            )
        ),
        "orders_without_named_items": unnamed_items,
        "products": products,
        "customers": customers,
        "platforms": platforms,
        "generated_at": now.isoformat(),
    }


async def attention_queue(db: AsyncSession, user: Any, limit: int = 25) -> dict[str, Any]:
    """Open conversations, ordered by who has been waiting and what is at stake.

    The order is explained per row rather than hidden in a score: a seller
    deciding who to answer first deserves to know why this one is on top.
    """
    from app.domains.businesses.models import Business
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )
    from app.domains.orders.models import Order

    now = datetime.now(timezone.utc)
    biz = await db.execute(select(Business.id).where(Business.user_id == user.id))
    business_ids = [row[0] for row in biz.all()]
    if not business_ids:
        return {"items": [], "waiting": 0, "generated_at": now.isoformat()}

    convs = await db.execute(
        select(
            Conversation.id,
            Conversation.lead_name,
            Conversation.extra_data,
            ChannelConnection.platform,
        )
        .join(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(Conversation.business_id.in_(business_ids), Conversation.is_active.is_(True))
    )
    rows = convs.all()
    if not rows:
        return {"items": [], "waiting": 0, "generated_at": now.isoformat()}

    info = {
        row[0]: {
            "lead_name": row[1],
            "extra": row[2] if isinstance(row[2], dict) else {},
            "platform": row[3].value if hasattr(row[3], "value") else str(row[3]),
        }
        for row in rows
    }

    messages = await db.execute(
        select(Message.conversation_id, Message.direction, Message.content, Message.created_at)
        .where(Message.conversation_id.in_(list(info)))
        .order_by(Message.created_at.asc())
    )
    last_inbound: dict[Any, tuple[str, datetime]] = {}
    last_direction: dict[Any, Any] = {}
    inbound_count: dict[Any, int] = defaultdict(int)
    for conv_id, direction, content, created in messages.all():
        last_direction[conv_id] = direction
        if direction == MessageDirection.INBOUND:
            inbound_count[conv_id] += 1
            created = _aware(created)
            if created:
                last_inbound[conv_id] = (content or "", created)

    # Past purchases, to tell a returning customer from a stranger.
    orders = await db.execute(
        select(Order.conversation_id, Order.total_amount, Order.currency)
        .where(Order.business_id.in_(business_ids), Order.is_active.is_(True))
    )
    spent: dict[Any, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for conv_id, amount, currency in orders.all():
        if conv_id is not None:
            spent[conv_id][currency or "?"] += float(amount or 0)

    #: Words that mean the buyer is at the decision, not browsing. Deliberately
    #: few and literal — a long list of "intent keywords" would be guesswork.
    BUYING_SIGNALS = ("precio", "cuánto", "cuanto", "sale", "stock", "disponible", "envío", "envio", "comprar")

    items: list[dict[str, Any]] = []
    for conv_id, meta in info.items():
        if last_direction.get(conv_id) != MessageDirection.INBOUND:
            continue  # already answered: not in the queue
        content, when = last_inbound.get(conv_id, ("", None))
        if when is None:
            continue
        hours = round((now - when).total_seconds() / 3600, 1)
        reasons: list[str] = [f"espera hace {hours} h"]
        lowered = (content or "").lower()
        asked_to_buy = any(signal in lowered for signal in BUYING_SIGNALS)
        if asked_to_buy:
            reasons.append("preguntó por precio, stock o envío")
        if spent.get(conv_id):
            amounts = " · ".join(
                f"{round(total)} {currency}" for currency, total in spent[conv_id].items()
            )
            reasons.append(f"ya te compró por {amounts}")
        if meta["extra"].get("awaiting_human"):
            reasons.append(f"marcada para una persona: {meta['extra'].get('handoff_reason') or 'sin motivo'}")
        if inbound_count.get(conv_id, 0) > 2:
            reasons.append(f"escribió {inbound_count[conv_id]} veces")

        items.append({
            "conversation_id": str(conv_id),
            "platform": meta["platform"],
            "who": meta["lead_name"] or "sin nombre",
            "last_message": (content or "")[:180],
            "waiting_hours": hours,
            "asked_to_buy": asked_to_buy,
            "is_customer": bool(spent.get(conv_id)),
            "spent": {k: round(v, 2) for k, v in spent.get(conv_id, {}).items()},
            "awaiting_human": bool(meta["extra"].get("awaiting_human")),
            "reasons": reasons,
        })

    # Ordered by what is at stake, then by how long they have waited. Both are
    # facts; neither is a predicted probability of closing.
    items.sort(
        key=lambda row: (
            not row["awaiting_human"],
            not row["is_customer"],
            not row["asked_to_buy"],
            -row["waiting_hours"],
        )
    )
    return {
        "items": items[:limit],
        "waiting": len(items),
        "criteria": (
            "Primero las marcadas para una persona, después quienes ya te compraron, "
            "después quienes preguntaron precio, stock o envío, y dentro de cada grupo "
            "la que espera desde más tiempo."
        ),
        "generated_at": now.isoformat(),
    }
