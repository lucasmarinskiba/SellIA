"""Offline BI metrics computed from the raw visit and proximity rows.

Every number here comes from ``offline_conversions`` and ``geo_proximity_events``. The daily aggregate table
``location_visit_metrics`` is deliberately not read: nothing writes to it (``update_daily_metrics`` has no
caller), so reading it would report zeros as if they were data.

Conventions:
* a visit belongs to a period by ``entry_time``; a proximity event by ``created_at``;
* hours, weekdays and days are local to the location (``locations.timezone``, UTC when unset); a business
  summary uses each visit's own location, and a visit with no location is UTC;
* a metric with no underlying rows is ``None``, not zero, when zero would be misleading (averages, peaks);
* nothing here estimates ROI or writes insight text: those need data this codebase does not record.

All functions are sync and take a ``Session``; the routers run them through ``run_sync``. ``now`` is a
parameter so the windows are testable.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.domains.analytics.offline_models import (
    GeoProximityEvent,
    OfflineConversion,
    VisitType,
)
from app.domains.businesses.location_models import Location

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
SCHEDULED = frozenset({VisitType.SCHEDULED_DEMO, VisitType.SCHEDULED_TOUR, VisitType.SCHEDULED_APPOINTMENT})
CENTS = Decimal("0.01")


def _utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def _zone(name: str | None) -> tzinfo:
    """A location's own zone. Unset or unknown names fall back to UTC, the behaviour before zones existed."""
    if not name:
        return timezone.utc
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, OSError, ValueError):
        return timezone.utc


def _location_zone(db: Session, location_id: UUID) -> tzinfo:
    location = db.get(Location, location_id)
    return _zone(location.timezone if location else None)


def _dec(amount) -> Decimal:
    return Decimal(str(amount)) if amount is not None else Decimal(0)


def _windows(now: datetime, days: int) -> tuple[datetime, datetime, datetime]:
    """(previous_start, current_start, end) for a ``days``-long current period and the one before it."""
    end = _utc(now)
    current_start = end - timedelta(days=days)
    return current_start - timedelta(days=days), current_start, end


def _between(moment_of, rows, start: datetime, end: datetime) -> list:
    return [row for row in rows if start <= _utc(moment_of(row)) < end]


def _visit_time(visit: OfflineConversion) -> datetime:
    return visit.entry_time


def _local(visit: OfflineConversion, zones: dict[UUID | None, tzinfo]) -> datetime:
    return _utc(_visit_time(visit)).astimezone(zones.get(visit.location_id, timezone.utc))


def _event_time(event: GeoProximityEvent) -> datetime:
    return event.created_at


def _trend(current: float, previous: float) -> str:
    """'↑ +15%' style comparison; says so plainly when there is nothing to compare with."""
    if not previous:
        return "sin datos del periodo anterior" if not current else "nuevo: sin datos del periodo anterior"
    change = (current - previous) / previous * 100
    if abs(change) < 0.5:
        return "sin cambios"
    return f"{'↑' if change > 0 else '↓'} {change:+.0f}%"


def _hour_label(hour: int) -> str:
    return f"{hour:02d}:00-{(hour + 1) % 24:02d}:00"


def traffic_profile(visits: list[OfflineConversion], zones: dict[UUID | None, tzinfo]) -> dict:
    local = [_local(v, zones) for v in visits]
    hours = Counter(moment.hour for moment in local)
    weekdays = Counter(WEEKDAYS[moment.weekday()] for moment in local)
    peak_hour = peak_day = None
    if hours:
        top = max(hours.values())
        peak_hour = _hour_label(min(hour for hour, count in hours.items() if count == top))
    if weekdays:
        top = max(weekdays.values())
        peak_day = next(day for day in WEEKDAYS if weekdays.get(day) == top)
    dwell = [v.dwell_minutes for v in visits if v.dwell_minutes is not None]
    return {
        "total_visits": len(visits),
        "walk_in_visits": sum(1 for v in visits if v.visit_type == VisitType.WALK_IN),
        "qr_scans": sum(1 for v in visits if v.visit_type == VisitType.QR_SCAN),
        "scheduled_visits": sum(1 for v in visits if v.visit_type in SCHEDULED),
        "hourly_breakdown": {f"{hour:02d}": count for hour, count in sorted(hours.items())},
        "peak_hour": peak_hour,
        "peak_day": peak_day,
        "avg_dwell_minutes": round(sum(dwell) / len(dwell)) if dwell else None,
    }


def daily_trend(visits: list[OfflineConversion], start: datetime, days: int, zone: tzinfo) -> list[dict]:
    """One entry per local day of the period, zero-filled, so charts do not skip quiet days."""
    counts = Counter(_utc(_visit_time(v)).astimezone(zone).date() for v in visits)
    first = start.astimezone(zone).date()
    return [
        {"date": (first + timedelta(days=i)).isoformat(), "visits": counts.get(first + timedelta(days=i), 0)}
        for i in range(days)
    ]


def _conversion_block(visits: list[OfflineConversion]) -> dict:
    converted = [v for v in visits if v.purchased]
    revenue = sum((_dec(v.purchase_amount) for v in converted), Decimal(0))
    return {
        "total_visits": len(visits),
        "visits_converted": len(converted),
        "conversion_rate": len(converted) / len(visits) if visits else 0.0,
        "total_revenue": revenue.quantize(CENTS),
        "avg_order_value": (revenue / len(converted)).quantize(CENTS) if converted else None,
    }


def location_foot_traffic(db: Session, location_id: UUID, days: int, now: datetime) -> dict:
    zone = _location_zone(db, location_id)
    _, start, end = _windows(now, days)
    rows = db.query(OfflineConversion).filter(OfflineConversion.location_id == location_id).all()
    visits = _between(_visit_time, rows, start, end)
    return {
        **traffic_profile(visits, {location_id: zone}),
        "period_days": days,
        "date_range": f"{start.astimezone(zone):%Y-%m-%d} to {end.astimezone(zone):%Y-%m-%d}",
        "daily_visits_trend": daily_trend(visits, start, days, zone),
    }


def location_conversions(db: Session, location_id: UUID, days: int, now: datetime) -> dict:
    _, start, end = _windows(now, days)
    rows = db.query(OfflineConversion).filter(OfflineConversion.location_id == location_id).all()
    visits = _between(_visit_time, rows, start, end)
    block = _conversion_block(visits)

    by_type: dict[str, dict] = {}
    for visit_type in VisitType:
        typed = [v for v in visits if v.visit_type == visit_type]
        if typed:
            sub = _conversion_block(typed)
            by_type[visit_type.value] = {
                "visits": sub["total_visits"],
                "converted": sub["visits_converted"],
                "rate": sub["conversion_rate"],
                "revenue": float(sub["total_revenue"]),
            }
    return {**block, "by_visit_type": by_type}


def _best_trigger(events: list[GeoProximityEvent]) -> str | None:
    """Trigger whose events most often led to an executed automation. Not an ROI: there is no cost data."""
    by_name: dict[str, list[GeoProximityEvent]] = defaultdict(list)
    for event in events:
        by_name[event.trigger_name].append(event)
    if not by_name:
        return None
    ranked = sorted(
        by_name.items(),
        key=lambda item: (
            -sum(1 for e in item[1] if e.automation_triggered) / len(item[1]),
            -len(item[1]),
            item[0],
        ),
    )
    return ranked[0][0]


def business_summary(db: Session, business_id: UUID, days: int, now: datetime) -> dict:
    prev_start, start, end = _windows(now, days)
    rows = db.query(OfflineConversion).filter(OfflineConversion.business_id == business_id).all()
    current = _between(_visit_time, rows, start, end)
    previous = _between(_visit_time, rows, prev_start, start)
    cur, prev = _conversion_block(current), _conversion_block(previous)
    locations = db.query(Location).filter(Location.business_id == business_id).all()
    zones = {location.id: _zone(location.timezone) for location in locations}
    profile = traffic_profile(current, zones)

    per_location = Counter(v.location_id for v in current if v.location_id is not None)
    top_location_name = None
    top_location_visits = 0
    if per_location:
        top_location_id, top_location_visits = min(per_location.items(), key=lambda kv: (-kv[1], str(kv[0])))
        location = db.get(Location, top_location_id)
        top_location_name = location.name if location else None

    events = db.query(GeoProximityEvent).filter(GeoProximityEvent.business_id == business_id).all()
    events_now = _between(_event_time, events, start, end)

    return {
        "total_visits": cur["total_visits"],
        "visit_trend": _trend(cur["total_visits"], prev["total_visits"]),
        "total_conversions": cur["visits_converted"],
        "conversion_rate": cur["conversion_rate"],
        "conversion_trend": _trend(cur["visits_converted"], prev["visits_converted"]),
        "total_revenue": cur["total_revenue"],
        "revenue_trend": _trend(float(cur["total_revenue"]), float(prev["total_revenue"])),
        "top_location": top_location_name,
        "top_location_visits": top_location_visits,
        "best_trigger": _best_trigger(events_now),
        "peak_hour": profile["peak_hour"],
        "peak_day": profile["peak_day"],
        "avg_dwell_minutes": profile["avg_dwell_minutes"],
    }
