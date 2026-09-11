"""The orders spreadsheet: filtering, sorting, paging and totals over real rows.

Two constraints shape this module and neither is cosmetic.

First, customer_name/email/phone are EncryptedString columns. Their ciphertext
is what Postgres holds, so `WHERE customer_name ILIKE '%ana%'` can never match —
the old list endpoint did exactly that and silently returned nothing for every
name search. Anything that touches those three fields has to happen in Python,
after decryption, which is why a text search walks rows instead of pushing the
predicate down. The walk is capped and the response says when the cap was hit.

Second, money. Totals are grouped by currency and never summed across them: a
business selling in ARS and USD has two totals, not one meaningless number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import Select, and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pii_masking import mask_email, mask_name, mask_phone
from app.domains.orders.models import Order, OrderStatus, PaymentStatus

# Columns a client may sort by. Anything outside this map is rejected rather
# than interpolated into SQL.
SORTABLE_SQL: dict[str, Any] = {
    "created_at": Order.created_at,
    "updated_at": Order.updated_at,
    "order_number": Order.order_number,
    "total_amount": Order.total_amount,
    "currency": Order.currency,
    "status": Order.status,
    "payment_status": Order.payment_status,
    "payment_method": Order.payment_method,
    "external_platform": Order.external_platform,
    "source_channel": Order.source_channel,
    "source_campaign": Order.source_campaign,
    "paid_at": Order.paid_at,
    "shipped_at": Order.shipped_at,
    "delivered_at": Order.delivered_at,
    "tracking_number": Order.tracking_number,
}

# Sortable, but only after decryption or derivation — these are ordered in
# Python over the filtered set.
SORTABLE_PYTHON = {
    "customer_name",
    "customer_email",
    "customer_phone",
    "items_count",
    "units",
    "age_days",
    "hours_to_payment",
}

SORTABLE = set(SORTABLE_SQL) | SORTABLE_PYTHON

# How many rows a text search over encrypted fields is willing to decrypt.
SEARCH_SCAN_CAP = 4000


@dataclass
class TableQuery:
    """Everything the spreadsheet can be narrowed by."""

    search: Optional[str] = None
    status: list[str] = field(default_factory=list)
    payment_status: list[str] = field(default_factory=list)
    platform: list[str] = field(default_factory=list)
    channel: list[str] = field(default_factory=list)
    currency: list[str] = field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    has_tracking: Optional[bool] = None
    sort_by: str = "created_at"
    sort_dir: str = "desc"
    page: int = 1
    page_size: int = 50


def _coerce_enum(raw: str, enum_cls: Any) -> Optional[Any]:
    """Accept 'paid', 'PAID' or 'OrderStatus.PAID'; drop anything else.

    A typo used to reach Postgres and come back as a raw 500. Silently dropping
    an unknown member would be worse — it would widen the filter without saying
    so — so the caller is told which values were ignored.
    """
    candidate = raw.strip()
    if "." in candidate:
        candidate = candidate.rsplit(".", 1)[-1]
    for member in enum_cls:
        if candidate.lower() in (member.value.lower(), member.name.lower()):
            return member
    return None


def _sql_conditions(business_id: Any, q: TableQuery) -> tuple[list[Any], list[str]]:
    """Build the predicates Postgres can evaluate. Returns (conditions, ignored)."""
    conditions: list[Any] = [Order.business_id == business_id, Order.is_active.is_(True)]
    ignored: list[str] = []

    statuses = [s for s in (_coerce_enum(v, OrderStatus) for v in q.status) if s]
    ignored += [v for v in q.status if _coerce_enum(v, OrderStatus) is None]
    if statuses:
        conditions.append(Order.status.in_(statuses))

    pay = [s for s in (_coerce_enum(v, PaymentStatus) for v in q.payment_status) if s]
    ignored += [v for v in q.payment_status if _coerce_enum(v, PaymentStatus) is None]
    if pay:
        conditions.append(Order.payment_status.in_(pay))

    if q.platform:
        # "manual" is how the UI labels an order with no external platform.
        wanted = [p for p in q.platform if p != "manual"]
        clauses = []
        if wanted:
            clauses.append(Order.external_platform.in_(wanted))
        if "manual" in q.platform:
            clauses.append(Order.external_platform.is_(None))
        if clauses:
            conditions.append(or_(*clauses))

    if q.channel:
        wanted = [c for c in q.channel if c != "unknown"]
        clauses = []
        if wanted:
            clauses.append(Order.source_channel.in_(wanted))
        if "unknown" in q.channel:
            clauses.append(Order.source_channel.is_(None))
        if clauses:
            conditions.append(or_(*clauses))

    if q.currency:
        conditions.append(Order.currency.in_(q.currency))
    if q.date_from:
        conditions.append(Order.created_at >= q.date_from)
    if q.date_to:
        conditions.append(Order.created_at <= q.date_to)
    if q.amount_min is not None:
        conditions.append(Order.total_amount >= Decimal(str(q.amount_min)))
    if q.amount_max is not None:
        conditions.append(Order.total_amount <= Decimal(str(q.amount_max)))
    if q.has_tracking is True:
        conditions.append(Order.tracking_number.isnot(None))
    elif q.has_tracking is False:
        conditions.append(Order.tracking_number.is_(None))

    return conditions, ignored


def _items_summary(items: Any) -> tuple[int, int, str]:
    """Count lines and units across the item shapes the connectors actually write.

    Shopify/MercadoLibre/Hotmart imports store {'name','qty','price'}; the
    manual create path stores {'name','quantity','unit_price'}. Both are real.
    """
    if not isinstance(items, list):
        return 0, 0, ""
    units = 0
    names: list[str] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        qty = raw.get("qty", raw.get("quantity", 1))
        try:
            units += int(qty)
        except (TypeError, ValueError):
            units += 1
        name = raw.get("name") or raw.get("title")
        if name:
            names.append(str(name))
    label = names[0] if len(names) == 1 else (f"{names[0]} +{len(names) - 1}" if names else "")
    return len(items), units, label


def _hours_between(start: Optional[datetime], end: Optional[datetime]) -> Optional[float]:
    if not start or not end:
        return None
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return round((end - start).total_seconds() / 3600, 1)


def serialize_row(order: Order, *, now: Optional[datetime] = None) -> dict[str, Any]:
    """One spreadsheet row.

    Customer fields stay masked, the same as every other orders read in this
    API — the spreadsheet is not a side door around that policy.
    """
    now = now or datetime.now(timezone.utc)
    items_count, units, items_label = _items_summary(order.items)
    created = order.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    return {
        "id": str(order.id),
        "order_number": order.order_number or f"#{str(order.id)[:8]}",
        "created_at": created.isoformat() if created else None,
        "customer_name": mask_name(order.customer_name),
        "customer_email": mask_email(order.customer_email),
        "customer_phone": mask_phone(order.customer_phone),
        "items_count": items_count,
        "units": units,
        "items_label": items_label,
        "total_amount": float(order.total_amount or 0),
        "currency": order.currency,
        "status": order.status.value if order.status else None,
        "payment_status": order.payment_status.value if order.payment_status else None,
        "payment_method": order.payment_method,
        "external_platform": order.external_platform or "manual",
        "source_channel": order.source_channel or "unknown",
        "source_campaign": order.source_campaign,
        "tracking_number": order.tracking_number,
        "shipping_provider": order.shipping_provider,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "age_days": round((now - created).total_seconds() / 86400, 1) if created else None,
        "hours_to_payment": _hours_between(order.created_at, order.paid_at),
        "notes": order.notes,
    }


def _matches_search(row: dict[str, Any], order: Order, needle: str) -> bool:
    """Search the decrypted values, not the masked ones.

    Typing a customer's full name has to find them even though the column that
    comes back to the UI reads "A*** P***".
    """
    haystack = " ".join(
        str(v or "")
        for v in (
            order.order_number,
            order.customer_name,
            order.customer_email,
            order.customer_phone,
            order.external_id,
            order.tracking_number,
            row["items_label"],
            order.notes,
        )
    ).lower()
    return needle in haystack


def _python_sort_key(row: dict[str, Any], column: str) -> tuple[int, Any]:
    value = row.get(column)
    if value is None or value == "":
        # Empty always sinks to the bottom, in both directions — an unpaid
        # order should not lead a "fastest payment" sort.
        return (1, "")
    if isinstance(value, (int, float)):
        return (0, value)
    return (0, str(value).lower())


async def fetch_table(
    db: AsyncSession,
    business_id: Any,
    q: TableQuery,
) -> dict[str, Any]:
    """Page of rows plus the totals and facets for the whole filtered set."""
    conditions, ignored = _sql_conditions(business_id, q)
    if q.sort_by not in SORTABLE:
        q.sort_by = "created_at"
    descending = q.sort_dir.lower() != "asc"
    page_size = max(1, min(q.page_size, 500))
    page = max(1, q.page)
    needle = (q.search or "").strip().lower()
    notes: list[str] = []
    if ignored:
        notes.append("Se ignoraron filtros desconocidos: " + ", ".join(sorted(set(ignored))))

    base: Select = select(Order).where(and_(*conditions))
    now = datetime.now(timezone.utc)

    if needle or q.sort_by in SORTABLE_PYTHON:
        # Either the filter or the ordering depends on a decrypted or derived
        # value, so the filtered set has to be materialised. Cap the scan and
        # say so rather than quietly truncating.
        scan = await db.execute(base.order_by(Order.created_at.desc()).limit(SEARCH_SCAN_CAP + 1))
        orders = list(scan.scalars().all())
        truncated = len(orders) > SEARCH_SCAN_CAP
        if truncated:
            orders = orders[:SEARCH_SCAN_CAP]
            notes.append(
                f"La búsqueda recorrió las {SEARCH_SCAN_CAP} órdenes más recientes: "
                "los datos del cliente están cifrados y no se pueden filtrar en la base."
            )
        rows = [serialize_row(o, now=now) for o in orders]
        if needle:
            pairs = [(r, o) for r, o in zip(rows, orders) if _matches_search(r, o, needle)]
            rows = [r for r, _ in pairs]
        rows.sort(key=lambda r: _python_sort_key(r, q.sort_by), reverse=descending)
        total = len(rows)
        page_rows = rows[(page - 1) * page_size : page * page_size]
        totals = _totals_from_rows(rows)
        facets = _facets_from_rows(rows)
    else:
        count_result = await db.execute(select(func.count()).select_from(Order).where(and_(*conditions)))
        total = count_result.scalar() or 0
        column = SORTABLE_SQL[q.sort_by]
        ordered = base.order_by(column.desc() if descending else column.asc())
        # A stable tiebreaker: two orders created in the same second must not
        # swap places between pages and duplicate or hide a row.
        ordered = ordered.order_by(Order.id)
        result = await db.execute(ordered.offset((page - 1) * page_size).limit(page_size))
        page_rows = [serialize_row(o, now=now) for o in result.scalars().all()]
        totals = await _totals_from_sql(db, conditions)
        facets = await _facets_from_sql(db, conditions)

    return {
        "rows": page_rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
        "sort_by": q.sort_by,
        "sort_dir": "desc" if descending else "asc",
        "totals": totals,
        "facets": facets,
        "notes": notes,
        "generated_at": now.isoformat(),
    }


def _totals_from_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        cur = row["currency"] or "?"
        bucket = buckets.setdefault(cur, {"currency": cur, "orders": 0, "revenue": 0.0, "paid_revenue": 0.0})
        bucket["orders"] += 1
        bucket["revenue"] += row["total_amount"]
        if row["payment_status"] == PaymentStatus.COMPLETED.value:
            bucket["paid_revenue"] += row["total_amount"]
    return _finish_totals(buckets)


async def _totals_from_sql(db: AsyncSession, conditions: list[Any]) -> list[dict[str, Any]]:
    result = await db.execute(
        select(
            Order.currency,
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0),
            func.coalesce(
                func.sum(
                    case(
                        (Order.payment_status == PaymentStatus.COMPLETED, Order.total_amount),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .where(and_(*conditions))
        .group_by(Order.currency)
    )
    buckets = {
        row[0] or "?": {
            "currency": row[0] or "?",
            "orders": row[1],
            "revenue": float(row[2]),
            "paid_revenue": float(row[3]),
        }
        for row in result.all()
    }
    return _finish_totals(buckets)


def _finish_totals(buckets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for bucket in buckets.values():
        bucket["revenue"] = round(bucket["revenue"], 2)
        bucket["paid_revenue"] = round(bucket["paid_revenue"], 2)
        bucket["avg_order"] = round(bucket["revenue"] / bucket["orders"], 2) if bucket["orders"] else 0.0
        out.append(bucket)
    # Biggest currency first; the seller's main market should lead.
    return sorted(out, key=lambda b: b["revenue"], reverse=True)


FACET_COLUMNS = {
    "status": Order.status,
    "payment_status": Order.payment_status,
    "external_platform": Order.external_platform,
    "source_channel": Order.source_channel,
    "currency": Order.currency,
}

FACET_FALLBACK = {"external_platform": "manual", "source_channel": "unknown"}


async def _facets_from_sql(db: AsyncSession, conditions: list[Any]) -> dict[str, list[dict[str, Any]]]:
    facets: dict[str, list[dict[str, Any]]] = {}
    for name, column in FACET_COLUMNS.items():
        result = await db.execute(
            select(column, func.count(Order.id)).where(and_(*conditions)).group_by(column)
        )
        facets[name] = _sorted_facet(
            {
                (row[0].value if hasattr(row[0], "value") else row[0]) or FACET_FALLBACK.get(name, "—"): row[1]
                for row in result.all()
            }
        )
    return facets


def _facets_from_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    facets: dict[str, list[dict[str, Any]]] = {}
    for name in FACET_COLUMNS:
        counts: dict[str, int] = {}
        for row in rows:
            key = row.get(name) or FACET_FALLBACK.get(name, "—")
            counts[key] = counts.get(key, 0) + 1
        facets[name] = _sorted_facet(counts)
    return facets


def _sorted_facet(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"value": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
    ]


# Column order and labels for the CSV export, kept next to the row builder so
# a new field cannot appear in the UI and go missing from the download.
EXPORT_COLUMNS: list[tuple[str, str]] = [
    ("order_number", "Orden"),
    ("created_at", "Fecha"),
    ("customer_name", "Cliente"),
    ("customer_email", "Email"),
    ("customer_phone", "Telefono"),
    ("items_label", "Productos"),
    ("items_count", "Lineas"),
    ("units", "Unidades"),
    ("total_amount", "Total"),
    ("currency", "Moneda"),
    ("status", "Estado"),
    ("payment_status", "Pago"),
    ("payment_method", "Medio de pago"),
    ("external_platform", "Plataforma"),
    ("source_channel", "Canal"),
    ("source_campaign", "Campana"),
    ("tracking_number", "Tracking"),
    ("shipping_provider", "Transporte"),
    ("paid_at", "Pagada"),
    ("shipped_at", "Enviada"),
    ("delivered_at", "Entregada"),
    ("age_days", "Antiguedad (dias)"),
    ("hours_to_payment", "Horas hasta el pago"),
]
