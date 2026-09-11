"""Sales analysis over the account's real orders.

Companion to service.py, which reads conversations. Same discipline:

* Money is grouped by currency and never summed across currencies.
* Distributions are described with medians and quartiles, not averages — one
  wholesale order distorts a mean ticket and describes no real customer.
* Every proportion carries its denominator, and below MIN_TO_READ observations
  the reading says the sample is too small instead of printing a percentage.
* A funnel step whose source cannot be counted is reported as unknown, not as
  zero. Zero and "not measured" look identical on a chart and mean opposite
  things.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from .stats import MIN_FOR_TREND, MIN_TO_READ, Proportion, describe_change, median, quartiles

logger = get_logger(__name__)

WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def get_sales_analysis(db: AsyncSession, user, days: int = 90) -> dict[str, Any]:
    """Everything the sales charts draw, each with the analyst's reading."""
    from app.domains.businesses.models import Business
    from app.domains.orders.models import Order, OrderStatus, PaymentStatus

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    biz_result = await db.execute(select(Business.id).where(Business.user_id == user.id))
    business_ids = [row[0] for row in biz_result.all()]

    empty = {
        "period_days": days,
        "has_data": False,
        "headline": "Todavía no hay ventas propias para analizar.",
        "currencies": [],
        "revenue_series": [],
        "ticket_distribution": [],
        "by_platform": [],
        "by_weekday": [],
        "by_hour": [],
        "status_funnel": [],
        "repeat_customers": None,
        "concentration": None,
        "readings": [],
        "generated_at": now.isoformat(),
    }
    if not business_ids:
        empty["headline"] = "Todavía no creaste tu negocio, así que no hay ninguna venta tuya que leer."
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
        empty["headline"] = (
            f"No hay órdenes en los últimos {days} días. Cuando entre la primera venta, "
            "acá aparece su análisis."
        )
        return empty

    # ── Currencies, always separate ──
    per_currency: dict[str, list[Order]] = defaultdict(list)
    for order in orders:
        per_currency[order.currency or "?"].append(order)
    # The currency with the most orders leads; the rest are shown beside it.
    main_currency = max(per_currency, key=lambda c: len(per_currency[c]))

    currencies = []
    for currency, rows in sorted(per_currency.items(), key=lambda kv: -len(kv[1])):
        amounts = [float(o.total_amount or 0) for o in rows]
        paid = [o for o in rows if o.payment_status == PaymentStatus.COMPLETED]
        med = median(amounts)
        q1, q3 = quartiles(amounts)
        currencies.append({
            "currency": currency,
            "orders": len(rows),
            "revenue": round(sum(amounts), 2),
            "collected": round(sum(float(o.total_amount or 0) for o in paid), 2),
            "median_ticket": round(med, 2) if med is not None else None,
            "q1_ticket": round(q1, 2) if q1 is not None else None,
            "q3_ticket": round(q3, 2) if q3 is not None else None,
            "is_main": currency == main_currency,
        })

    main_orders = per_currency[main_currency]
    main_amounts = [float(o.total_amount or 0) for o in main_orders]

    # ── Revenue over time (main currency; gaps stay gaps) ──
    daily_revenue: Counter[str] = Counter()
    daily_orders: Counter[str] = Counter()
    for order in main_orders:
        created = _aware(order.created_at)
        if not created:
            continue
        day = created.date().isoformat()
        daily_revenue[day] += float(order.total_amount or 0)
        daily_orders[day] += 1
    revenue_series = []
    for offset in range(days - 1, -1, -1):
        day = (now - timedelta(days=offset)).date().isoformat()
        revenue_series.append({
            "date": day,
            "revenue": round(daily_revenue.get(day, 0.0), 2),
            "orders": daily_orders.get(day, 0),
        })

    # ── Ticket distribution: real buckets, not a smooth curve ──
    ticket_distribution = _histogram(main_amounts)

    # ── Per platform ──
    by_platform = []
    platform_groups: dict[str, list[Order]] = defaultdict(list)
    for order in main_orders:
        platform_groups[order.external_platform or "manual"].append(order)
    for platform, rows in sorted(platform_groups.items(), key=lambda kv: -len(kv[1])):
        amounts = [float(o.total_amount or 0) for o in rows]
        paid = Proportion(
            sum(1 for o in rows if o.payment_status == PaymentStatus.COMPLETED),
            len(rows),
        )
        med = median(amounts)
        by_platform.append({
            "platform": platform,
            "orders": len(rows),
            "revenue": round(sum(amounts), 2),
            "median_ticket": round(med, 2) if med is not None else None,
            "paid_rate": paid.percent,
            "confidence": paid.confidence,
            "reading": paid.reading("órdenes"),
        })

    # ── When people actually buy ──
    weekday_counts: Counter[int] = Counter()
    hour_counts: Counter[int] = Counter()
    for order in main_orders:
        created = _aware(order.created_at)
        if not created:
            continue
        weekday_counts[created.weekday()] += 1
        hour_counts[created.hour] += 1
    by_weekday = [
        {"weekday": WEEKDAYS[index], "orders": weekday_counts.get(index, 0)}
        for index in range(7)
    ]
    by_hour = [{"hour": hour, "orders": hour_counts.get(hour, 0)} for hour in range(24)]

    # ── Status funnel over the orders themselves ──
    status_counts: Counter[str] = Counter()
    for order in orders:
        status_counts[order.status.value if order.status else "pending"] += 1
    reached = {
        "created": len(orders),
        "paid": sum(
            status_counts.get(s, 0)
            for s in (OrderStatus.PAID.value, OrderStatus.SHIPPED.value, OrderStatus.DELIVERED.value)
        ),
        "shipped": sum(
            status_counts.get(s, 0)
            for s in (OrderStatus.SHIPPED.value, OrderStatus.DELIVERED.value)
        ),
        "delivered": status_counts.get(OrderStatus.DELIVERED.value, 0),
    }
    status_funnel = [
        {"step": "Órdenes creadas", "count": reached["created"], "of_created": 100.0},
        {"step": "Pagadas", "count": reached["paid"], "of_created": _pct(reached["paid"], reached["created"])},
        {"step": "Enviadas", "count": reached["shipped"], "of_created": _pct(reached["shipped"], reached["created"])},
        {"step": "Entregadas", "count": reached["delivered"], "of_created": _pct(reached["delivered"], reached["created"])},
    ]
    lost = {
        "cancelled": status_counts.get(OrderStatus.CANCELLED.value, 0),
        "refunded": status_counts.get(OrderStatus.REFUNDED.value, 0),
    }

    # ── Repeat customers (decrypted in Python: the column is encrypted) ──
    repeat_customers = _repeat_customers(orders)

    # ── Revenue concentration: how exposed the business is to a few buyers ──
    concentration = _concentration(main_orders, main_currency)

    readings = _sales_readings(
        orders=orders,
        main_orders=main_orders,
        main_currency=main_currency,
        main_amounts=main_amounts,
        now=now,
        reached=reached,
        lost=lost,
        repeat_customers=repeat_customers,
        concentration=concentration,
        weekday_counts=weekday_counts,
    )

    return {
        "period_days": days,
        "has_data": True,
        "headline": _sales_headline(main_orders, main_currency, reached, now),
        "main_currency": main_currency,
        "currencies": currencies,
        "revenue_series": revenue_series,
        "ticket_distribution": ticket_distribution,
        "by_platform": by_platform,
        "by_weekday": by_weekday,
        "by_hour": by_hour,
        "status_funnel": status_funnel,
        "lost": lost,
        "repeat_customers": repeat_customers,
        "concentration": concentration,
        "readings": readings,
        "generated_at": now.isoformat(),
    }


def _pct(part: int, whole: int) -> Optional[float]:
    return round(100 * part / whole, 1) if whole else None


def _histogram(amounts: list[float], buckets: int = 6) -> list[dict[str, Any]]:
    """Equal-width buckets over the real range. Empty buckets are kept.

    Dropping an empty bucket would hide the gap between a cluster of small
    tickets and one large one, which is usually the most interesting thing in
    the chart.
    """
    values = [a for a in amounts if a > 0]
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [{"from": round(low, 2), "to": round(high, 2), "orders": len(values)}]
    width = (high - low) / buckets
    out = []
    for index in range(buckets):
        start = low + index * width
        end = high if index == buckets - 1 else start + width
        count = sum(
            1 for value in values
            if (value >= start and value < end) or (index == buckets - 1 and value == high)
        )
        out.append({"from": round(start, 2), "to": round(end, 2), "orders": count})
    return out


def _repeat_customers(orders: list[Any]) -> dict[str, Any]:
    """How many buyers came back.

    Identity is the customer's email or phone, which are encrypted at rest and
    therefore only comparable here, after the ORM decrypts them. Orders with
    neither are counted as unidentifiable rather than as separate people —
    calling them all "new customers" would invent a retention problem.
    """
    per_customer: Counter[str] = Counter()
    unidentified = 0
    for order in orders:
        key = (order.customer_email or "").strip().lower() or (order.customer_phone or "").strip()
        if not key:
            unidentified += 1
            continue
        per_customer[key] += 1

    identified = len(per_customer)
    returning = sum(1 for count in per_customer.values() if count > 1)
    proportion = Proportion(returning, identified)
    return {
        "identified_customers": identified,
        "returning_customers": returning,
        "orders_without_identity": unidentified,
        "repeat_rate": proportion.percent,
        "confidence": proportion.confidence,
        "reading": (
            proportion.reading("clientes identificados")
            + (
                f" Además hay {unidentified} órdenes sin email ni teléfono: no se puede saber "
                "si son de alguien que ya compró."
                if unidentified else ""
            )
        ),
    }


def _concentration(orders: list[Any], currency: str) -> Optional[dict[str, Any]]:
    """Share of revenue held by the top buyers — a risk number, not a vanity one."""
    per_customer: dict[str, float] = defaultdict(float)
    for order in orders:
        key = (order.customer_email or "").strip().lower() or (order.customer_phone or "").strip()
        if not key:
            continue
        per_customer[key] += float(order.total_amount or 0)
    if len(per_customer) < 3:
        return {
            "customers": len(per_customer),
            "top_share": None,
            "reading": (
                "Hacen falta al menos 3 clientes identificados para hablar de concentración. "
                f"Por ahora hay {len(per_customer)}."
            ),
        }

    total = sum(per_customer.values())
    ranked = sorted(per_customer.values(), reverse=True)
    top_n = max(1, round(len(ranked) * 0.2))
    top_share = round(100 * sum(ranked[:top_n]) / total, 1) if total else None
    return {
        "customers": len(per_customer),
        "top_customers": top_n,
        "top_share": top_share,
        "currency": currency,
        "reading": (
            f"Tus {top_n} mejores clientes ({top_n} de {len(ranked)}) explican el {top_share}% "
            f"de la facturación en {currency}. "
            + (
                "Es una dependencia alta: si uno se va, se nota en el mes."
                if top_share and top_share >= 60
                else "La facturación está razonablemente repartida."
            )
        ),
    }


def _sales_readings(**kwargs: Any) -> list[dict[str, Any]]:
    """The analyst's notes on the charts above."""
    orders = kwargs["orders"]
    main_orders = kwargs["main_orders"]
    currency = kwargs["main_currency"]
    amounts = kwargs["main_amounts"]
    now = kwargs["now"]
    reached = kwargs["reached"]
    lost = kwargs["lost"]
    weekday_counts = kwargs["weekday_counts"]

    readings: list[dict[str, Any]] = []

    # Ticket
    med = median(amounts)
    if med is not None:
        q1, q3 = quartiles(amounts)
        spread = (
            f" La mitad del medio de tus ventas está entre {round(q1)} y {round(q3)} {currency}."
            if q1 is not None and q3 is not None else ""
        )
        readings.append({
            "key": "median_ticket",
            "title": f"Ticket mediano ({currency})",
            "value": round(med, 2),
            "unit": currency,
            "confidence": "solid" if len(amounts) >= MIN_FOR_TREND
                          else "preliminary" if len(amounts) >= MIN_TO_READ else "insufficient",
            "reading": (
                f"La venta típica es de {round(med)} {currency} (n={len(amounts)}).{spread} "
                "Se usa la mediana: un solo pedido grande levanta el promedio y deja de describir "
                "a ningún cliente real."
            ),
            "why_it_matters": (
                "Es la base de cualquier cuenta: cuántas ventas necesitás para cubrir costos, y "
                "cuánto podés gastar para conseguir un cliente."
            ),
        })

    # Payment conversion
    paid = Proportion(reached["paid"], reached["created"])
    readings.append({
        "key": "paid_rate",
        "title": "Órdenes que terminaron pagadas",
        "value": paid.percent,
        "unit": "%",
        "confidence": paid.confidence,
        "reading": paid.reading("órdenes")
        + (
            f" Se cancelaron {lost['cancelled']} y se reembolsaron {lost['refunded']}."
            if lost["cancelled"] or lost["refunded"] else ""
        ),
        "why_it_matters": (
            "Una orden creada y no pagada es una venta perdida después del sí: suele arreglarse "
            "con recordatorios, no con más tráfico."
        ),
    })

    # Time to payment
    delays = []
    for order in orders:
        created, paid_at = _aware(order.created_at), _aware(order.paid_at)
        if created and paid_at and paid_at >= created:
            delays.append((paid_at - created).total_seconds() / 3600)
    delay_median = median(delays)
    if delay_median is not None:
        readings.append({
            "key": "hours_to_payment",
            "title": "Horas hasta el pago (mediana)",
            "value": round(delay_median, 1),
            "unit": "h",
            "confidence": "solid" if len(delays) >= MIN_FOR_TREND
                          else "preliminary" if len(delays) >= MIN_TO_READ else "insufficient",
            "reading": (
                f"La mitad de las órdenes se pagó en {round(delay_median, 1)} horas o menos "
                f"(n={len(delays)})."
            ),
            "why_it_matters": (
                "Cuanto más tarda el pago, más chances hay de que no llegue: el recordatorio "
                "rinde justo después de la mediana."
            ),
        })

    # Week over week, on real dates
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    this_week = sum(1 for o in main_orders if _aware(o.created_at) and _aware(o.created_at) >= week_ago)
    last_week = sum(
        1 for o in main_orders
        if _aware(o.created_at) and two_weeks_ago <= _aware(o.created_at) < week_ago
    )
    change = describe_change(this_week, last_week, "órdenes")
    readings.append({
        "key": "weekly_orders",
        "title": "Órdenes esta semana",
        "value": this_week,
        "unit": "",
        "confidence": "solid" if this_week + last_week >= MIN_FOR_TREND
                      else "preliminary" if this_week + last_week >= MIN_TO_READ else "insufficient",
        "reading": change["reading"],
        "direction": change["direction"],
        "why_it_matters": "El volumen manda: un ticket que sube con el volumen cayendo no es una mejora.",
    })

    # Best day — only when there is enough to distinguish one
    total_orders = sum(weekday_counts.values())
    if total_orders >= MIN_TO_READ and weekday_counts:
        best_day, best_count = max(weekday_counts.items(), key=lambda kv: kv[1])
        share = Proportion(best_count, total_orders)
        readings.append({
            "key": "best_weekday",
            "title": "Día que más vende",
            "value": WEEKDAYS[best_day],
            "unit": "",
            "confidence": share.confidence,
            "reading": (
                f"{WEEKDAYS[best_day]} concentra {best_count} de {total_orders} órdenes "
                f"({share.percent}%). {share.reading('órdenes')}"
            ),
            "why_it_matters": "Es cuándo conviene publicar, mandar la campaña y tener a alguien atento.",
        })
    elif weekday_counts:
        readings.append({
            "key": "best_weekday",
            "title": "Día que más vende",
            "value": None,
            "unit": "",
            "confidence": "insufficient",
            "reading": (
                f"Con {total_orders} órdenes no se puede distinguir un día de otro: la diferencia "
                "que se vea es ruido."
            ),
            "why_it_matters": "Es cuándo conviene publicar, mandar la campaña y tener a alguien atento.",
        })

    readings.append(kwargs["repeat_customers"] | {
        "key": "repeat_rate",
        "title": "Clientes que volvieron a comprar",
        "value": kwargs["repeat_customers"]["repeat_rate"],
        "unit": "%",
        "why_it_matters": (
            "Traer un cliente nuevo cuesta varias veces más que vender de nuevo a uno que ya "
            "te compró: esta es la métrica que decide si crecés o reponés."
        ),
    })

    concentration = kwargs["concentration"]
    if concentration:
        readings.append({
            "key": "concentration",
            "title": "Concentración de la facturación",
            "value": concentration.get("top_share"),
            "unit": "%",
            "confidence": "insufficient" if concentration.get("top_share") is None else "preliminary",
            "reading": concentration["reading"],
            "why_it_matters": "Mide a cuánto riesgo estás si se va un solo cliente.",
        })

    return readings


def _sales_headline(
    main_orders: list[Any],
    currency: str,
    reached: dict[str, int],
    now: datetime,
) -> str:
    revenue = sum(float(o.total_amount or 0) for o in main_orders)
    week_ago = now - timedelta(days=7)
    this_week = sum(1 for o in main_orders if _aware(o.created_at) and _aware(o.created_at) >= week_ago)
    paid_pct = _pct(reached["paid"], reached["created"])
    pieces = [
        f"{len(main_orders)} órdenes en {currency} por {round(revenue)} {currency}",
        f"{this_week} en los últimos 7 días",
    ]
    if paid_pct is not None:
        pieces.append(f"{paid_pct}% terminó pagada")
    return ". ".join(pieces) + "."
