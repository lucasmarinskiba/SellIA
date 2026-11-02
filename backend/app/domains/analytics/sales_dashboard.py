"""Sales dashboard numbers for one business, computed from its own CRM deals.

Every figure comes from the ``deals`` table. A new account with no deals gets
zeros, never another account's or invented numbers (the enterprise and seller
dashboards this replaces served random or hard-coded values to everyone).

Money is added up in a single currency, the one the business uses most. Deals
in other currencies are only counted (``other_currency_deals``), because adding
ARS to USD gives a wrong total.
"""

import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.crm.models import Deal, LeadStage

TimeRange = Literal["today", "week", "month", "quarter", "year"]

WINDOW_DAYS: dict[TimeRange, int] = {"today": 1, "week": 7, "month": 30, "quarter": 90, "year": 365}
FORECAST_HORIZON_DAYS = 30
DEFAULT_CURRENCY = "ARS"
_CLOSED = {LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST}


def _aware(moment: datetime) -> datetime:
    # SQLite (used by the tests) returns naive datetimes; Postgres returns aware ones.
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=timezone.utc)


def _main_currency(rows: list[Any]) -> str:
    counts = Counter(row.currency for row in rows if row.currency)
    return counts.most_common(1)[0][0] if counts else DEFAULT_CURRENCY


def _weighted(deals: list[Any]) -> float:
    return sum(float(d.value) * d.probability / 100 for d in deals)


async def build_sales_dashboard(db: AsyncSession, business_id: uuid.UUID, time_range: TimeRange) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=WINDOW_DAYS[time_range])
    horizon = now + timedelta(days=FORECAST_HORIZON_DAYS)

    rows = (
        await db.execute(
            select(
                Deal.value,
                Deal.currency,
                Deal.stage,
                Deal.probability,
                Deal.expected_close_date,
                Deal.actual_close_date,
            ).where(Deal.business_id == business_id, Deal.is_active.is_(True))
        )
    ).all()

    currency = _main_currency(rows)
    same = [r for r in rows if r.currency == currency and r.value is not None]
    open_deals = [r for r in same if r.stage not in _CLOSED]
    closed_in_window = [
        r for r in same if r.actual_close_date is not None and _aware(r.actual_close_date) >= since
    ]
    won = [r for r in closed_in_window if r.stage == LeadStage.CLOSED_WON]
    lost = [r for r in closed_in_window if r.stage == LeadStage.CLOSED_LOST]
    due_soon = [
        r for r in open_deals if r.expected_close_date is not None and _aware(r.expected_close_date) <= horizon
    ]

    total_pipeline = sum(float(r.value) for r in open_deals)
    revenue_forecast = _weighted(open_deals)
    avg_deal_value = sum(float(r.value) for r in won) / len(won) if won else 0.0
    closed_count = len(won) + len(lost)
    close_rate = len(won) / closed_count if closed_count else 0.0
    stages = Counter(r.stage.value for r in open_deals)
    stamp = now.isoformat()

    return {
        "time_range": time_range,
        "currency": currency,
        "other_currency_deals": sum(1 for r in rows if r.currency != currency),
        "generated_at": stamp,
        # Top-level keys the mobile app reads. ``deals_this_month`` counts the selected window.
        "total_pipeline": round(total_pipeline, 2),
        "deals_this_month": len(won),
        "avg_deal_value": round(avg_deal_value, 2),
        "close_rate": round(close_rate, 4),
        "revenue_forecast": round(revenue_forecast, 2),
        # Shape the enterprise web reads. A null trend means "no history yet", shown as nothing.
        "kpi_cards": [
            {"label": "Pipeline abierto", "current_value": round(total_pipeline, 2), "unit": currency,
             "target": None, "trend": None, "trend_direction": "neutral"},
            {"label": "Ventas cerradas", "current_value": len(won), "unit": "ventas",
             "target": None, "trend": None, "trend_direction": "neutral"},
            {"label": "Ticket promedio", "current_value": round(avg_deal_value, 2), "unit": currency,
             "target": None, "trend": None, "trend_direction": "neutral"},
            {"label": "Tasa de cierre", "current_value": round(close_rate * 100, 1), "unit": "%",
             "target": None, "trend": None, "trend_direction": "neutral"},
            {"label": "Forecast ponderado", "current_value": round(revenue_forecast, 2), "unit": currency,
             "target": None, "trend": None, "trend_direction": "neutral"},
        ],
        "pipeline": {
            "total_value": round(total_pipeline, 2),
            "stages": dict(stages),
            "projected_revenue_30d": round(_weighted(due_soon), 2),
            "forecast_confidence": None,  # not computed yet; the UI hides it
        },
        "agent_performance": [],  # no per-agent data source yet
        "segment_benchmarks": None,  # would need cross-tenant aggregates; not built
    }
