"""Building owner alerts correctly, and not building them over and over.

Four code paths created ``Alert`` rows for the business owner and every one of them was
broken in the same two ways, hidden by a blanket ``except Exception`` around it:

* they used ``AlertSeverity.HIGH`` / ``MEDIUM`` / ``LOW``; the enum only has INFO, WARNING
  and CRITICAL, so building the alert raised ``AttributeError: LOW``;
* they passed ``message=`` and ``is_read=``; the columns are ``description`` and ``status``.

No alert from any of them was ever created. Fixing only that is not enough: each of those
paths also keeps its own "already done" state in memory of an object Celery rebuilds on every
run, so once they work they fire on every run (that is how the AOC health report produced
~900 identical alerts an hour). The cadence therefore has to live in the table, which survives
between runs: every alert carries a ``kind`` in ``alert_metadata``, and
:func:`alert_sent_recently` asks the table before creating the next one.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.alerts.models import Alert, AlertSeverity

#: Names used by the callers (their own severity vocabularies) -> the three real severities.
_LEVEL_TO_SEVERITY: dict[str, AlertSeverity] = {
    "critical": AlertSeverity.CRITICAL,
    "high": AlertSeverity.WARNING,
    "medium": AlertSeverity.WARNING,
    "warning": AlertSeverity.WARNING,
    "low": AlertSeverity.INFO,
    "info": AlertSeverity.INFO,
}


def _key(value: Any) -> str | None:
    """A dedupe key as plain text (callers pass str-enum members such as FaultType.X)."""
    if value is None:
        return None
    return str(getattr(value, "value", value))


def severity_for(level: str | None, default: AlertSeverity = AlertSeverity.INFO) -> AlertSeverity:
    """Map a caller's level name ("high", "low", ...) to an AlertSeverity that exists."""
    return _LEVEL_TO_SEVERITY.get((level or "").lower(), default)


def build_alert(
    business_id: uuid.UUID,
    title: str,
    body: str,
    *,
    kind: str,
    level: str = "info",
    dedupe_key: str | None = None,
    created_at: datetime | None = None,
    extra: dict[str, Any] | None = None,
) -> Alert:
    """An ``Alert`` with valid columns, tagged so :func:`alert_sent_recently` can find it."""
    metadata: dict[str, Any] = {"kind": kind, **(extra or {})}
    if dedupe_key is not None:
        metadata["dedupe_key"] = _key(dedupe_key)
    alert = Alert(
        business_id=business_id,
        title=title,
        description=body,
        severity=severity_for(level),
        alert_metadata=metadata,
    )
    if created_at is not None:
        alert.created_at = created_at
    return alert


async def alert_sent_recently(
    db: AsyncSession,
    business_id: uuid.UUID,
    kind: str,
    within: timedelta,
    dedupe_key: str | None = None,
) -> bool:
    """Whether this business already got an alert of this ``kind`` (and ``dedupe_key``) lately."""
    since = datetime.now(timezone.utc) - within
    conditions = [
        Alert.business_id == business_id,
        Alert.alert_metadata["kind"].astext == kind,
        Alert.created_at >= since,
    ]
    if dedupe_key is not None:
        conditions.append(Alert.alert_metadata["dedupe_key"].astext == _key(dedupe_key))
    found = await db.execute(select(Alert.id).where(*conditions).limit(1))
    return found.first() is not None
