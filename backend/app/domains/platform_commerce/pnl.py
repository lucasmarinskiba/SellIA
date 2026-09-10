"""Profit and loss per platform, and consolidated.

Revenue is counted from real paid orders. Costs come from what the seller
declared per platform (commission, per-order fee, cost of goods, fixed costs,
ad spend) -- never from an assumed market rate, because MercadoLibre's
commission for one seller is not the same as for another and a plausible
default would quietly become a wrong margin.

Anything not declared is reported as unknown, by name, in `missing`. A margin is
only stated when every component it needs is actually known; otherwise the
screen shows revenue and says what is required to complete the picture. A
half-known cost base rounded into a confident-looking profit number is exactly
the failure mode this codebase keeps removing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

ZERO = Decimal("0")


def _money(value: Optional[Decimal]) -> float:
    return float(round(value or ZERO, 2))


async def _settings_by_platform(
    db: AsyncSession, business_ids: list[uuid.UUID]
) -> dict[str, Any]:
    from .models import PlatformSettings

    if not business_ids:
        return {}
    result = await db.execute(
        select(PlatformSettings).where(
            PlatformSettings.business_id.in_(business_ids),
            PlatformSettings.is_active.is_(True),
        )
    )
    return {s.platform: s for s in result.scalars().all()}


async def platform_pnl(
    db: AsyncSession, business_ids: list[uuid.UUID], days: int = 30
) -> dict[str, Any]:
    """Per-platform and consolidated economics over the window."""
    from app.domains.orders.models import Order, PaymentStatus

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    empty: dict[str, Any] = {
        "period_days": days,
        "platforms": [],
        "consolidated": {
            "revenue": 0.0, "orders": 0, "known_costs": 0.0,
            "margin": None, "margin_complete": False, "currency": None,
        },
        "generated_at": now.isoformat(),
    }
    if not business_ids:
        empty["consolidated"]["note"] = "Todavía no creaste tu negocio."
        return empty

    result = await db.execute(
        select(Order).where(
            Order.business_id.in_(business_ids),
            Order.created_at >= since,
            Order.is_active.is_(True),
        )
    )
    orders = list(result.scalars().all())
    settings = await _settings_by_platform(db, business_ids)

    by_platform: dict[str, list[Any]] = {}
    for order in orders:
        key = order.external_platform or order.source_channel or "directo"
        by_platform.setdefault(key, []).append(order)

    # A platform the seller has connected but that produced no order still
    # deserves a row: "conectado y sin ventas" is information.
    from app.domains.channels.models import ChannelConnection

    connected = await db.execute(
        select(ChannelConnection.platform).where(
            ChannelConnection.business_id.in_(business_ids),
            ChannelConnection.is_active.is_(True),
        )
    )
    for row in connected.all():
        platform = row[0].value if hasattr(row[0], "value") else str(row[0])
        by_platform.setdefault(platform, [])

    rows: list[dict[str, Any]] = []
    total_revenue = ZERO
    total_known_costs = ZERO
    total_orders = 0
    all_complete = True
    currencies: set[str] = set()

    for platform, platform_orders in sorted(by_platform.items()):
        # COMPLETED, not PAID: PaymentStatus has no PAID member, and
        # referencing one raises AttributeError the moment an order exists.
        paid = [o for o in platform_orders if o.payment_status == PaymentStatus.COMPLETED]
        revenue = sum((o.total_amount or ZERO) for o in paid) or ZERO
        shipping = sum((o.shipping_cost or ZERO) for o in paid) or ZERO
        for order in platform_orders:
            if order.currency:
                currencies.add(order.currency)

        config = settings.get(platform)
        missing: list[str] = []
        costs: dict[str, Any] = {"envios": _money(shipping)}
        known_costs = shipping

        # Commission
        if config is not None and config.commission_percent is not None:
            commission = revenue * (Decimal(config.commission_percent) / Decimal(100))
            costs["comision"] = _money(commission)
            known_costs += commission
        else:
            costs["comision"] = None
            missing.append("la comisión que te cobra la plataforma")

        # Per-order fee
        if config is not None and config.fixed_fee_per_order is not None:
            fees = Decimal(config.fixed_fee_per_order) * len(paid)
            costs["cargo_fijo_por_venta"] = _money(fees)
            known_costs += fees
        else:
            costs["cargo_fijo_por_venta"] = None

        # Cost of goods
        if config is not None and config.cogs_percent is not None:
            cogs = revenue * (Decimal(config.cogs_percent) / Decimal(100))
            costs["costo_de_producto"] = _money(cogs)
            known_costs += cogs
        else:
            costs["costo_de_producto"] = None
            missing.append("cuánto te cuesta producir o comprar lo que vendés")

        # Fixed and advertising costs, prorated over the window
        factor = Decimal(days) / Decimal(30)
        if config is not None and config.monthly_fixed_cost is not None:
            fixed = Decimal(config.monthly_fixed_cost) * factor
            costs["costos_fijos"] = _money(fixed)
            known_costs += fixed
        else:
            costs["costos_fijos"] = None

        if config is not None and config.monthly_ad_spend is not None:
            ads = Decimal(config.monthly_ad_spend) * factor
            costs["publicidad"] = _money(ads)
            known_costs += ads
        else:
            costs["publicidad"] = None
            missing.append("cuánto invertís en publicidad")

        complete = not missing
        all_complete = all_complete and (complete or not paid)
        total_revenue += revenue
        total_known_costs += known_costs
        total_orders += len(paid)

        rows.append({
            "platform": platform,
            "orders": len(paid),
            "orders_total": len(platform_orders),
            "revenue": _money(revenue),
            "costs": costs,
            "known_costs": _money(known_costs),
            "margin": _money(revenue - known_costs) if complete else None,
            "margin_percent": (
                round(float((revenue - known_costs) / revenue * 100), 1)
                if complete and revenue else None
            ),
            "margin_complete": complete,
            "missing": missing,
            "currency": next(
                (o.currency for o in platform_orders if o.currency), None
            ),
        })

    # Measure the mix BEFORE consuming the set: a consolidated total across two
    # currencies is not a number, and saying which case we are in matters more
    # than printing a sum of pesos and dollars.
    mixed_currencies = len(currencies) > 1
    currency = next(iter(currencies)) if len(currencies) == 1 else None

    # Nothing sold and nothing declared is not "a margin of zero, computed
    # completely". It is no information, and printing 0 with a green tick
    # invites the seller to believe their books are done.
    nothing_known = total_revenue == ZERO and total_known_costs == ZERO
    consolidated_margin = (
        None if (nothing_known or not all_complete)
        else _money(total_revenue - total_known_costs)
    )

    return {
        "period_days": days,
        "platforms": rows,
        "consolidated": {
            "revenue": _money(total_revenue),
            "orders": total_orders,
            "known_costs": _money(total_known_costs),
            "margin": consolidated_margin,
            "margin_complete": all_complete and not nothing_known,
            "currency": currency,
            "mixed_currencies": mixed_currencies,
        },
        "generated_at": now.isoformat(),
    }
