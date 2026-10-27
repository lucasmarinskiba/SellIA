"""When the automatic loop may send, and how many emails a young mailbox may send.

Pure functions (no DB) so the rules are easy to test. They apply to the automatic loop only:
a person who clicks "send" on an approved draft decides for themselves.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domains.harvey.models import HarveyProfile

WARMUP_START_CAP = 5
WARMUP_STEP = 5
WARMUP_STEP_DAYS = 2


def _zone(name: str) -> ZoneInfo | timezone:
    try:
        return ZoneInfo(name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return timezone.utc


def in_send_window(profile: HarveyProfile, now: datetime) -> bool:
    """True when ``now`` falls in the business's sending hours (local time, weekdays by default)."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    local = now.astimezone(_zone(profile.send_timezone))
    if profile.send_weekdays_only and local.weekday() >= 5:
        return False
    return profile.send_window_start <= local.hour < profile.send_window_end


def warmup_cap(started_at: datetime, now: datetime) -> int:
    """Daily cap for a mailbox that started sending on ``started_at``: 5, +5 every 2 days."""
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    days = max(0, (now - started_at).days)
    return WARMUP_START_CAP + WARMUP_STEP * (days // WARMUP_STEP_DAYS)


def effective_send_cap(profile: HarveyProfile, now: datetime) -> int:
    """The daily send cap: the business's limit, lowered while the mailbox is warming up."""
    cap = profile.max_daily_sends
    if profile.warmup_started_at is not None:
        cap = min(cap, warmup_cap(profile.warmup_started_at, now))
    return cap
