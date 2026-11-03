"""Deliver the queued events to feedIA (POST {FEEDIA_BASE_URL}/api/sellia/webhook), with retries.

feedIA de-duplicates by order id, so delivering an event twice is harmless: the loop is at-least-once and never has to
guess whether a timed-out request got through.

What a response means:
  2xx {ok: true}            delivered.
  2xx {ok: false}           feedIA understood the request and refused the data: retrying cannot help -> failed.
  404 unknown-account       the account id on the link is wrong -> failed, and the link shows why.
  401 / 503 / 5xx / network our secret is not (yet) the same as feedIA's, or feedIA is down -> retry with backoff.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.feedia_link.models import FeediaLink, FeediaOutbox
from app.domains.feedia_link.signing import canonical_json, sign_event

logger = get_logger(__name__)

MAX_ATTEMPTS = 8
BATCH = 50
WEBHOOK_PATH = "/api/sellia/webhook"

#: (url, body, headers) -> (http status, parsed json or None). Injected in tests; httpx in production.
Poster = Callable[[str, str, dict[str, str]], Awaitable[tuple[int, Optional[dict[str, Any]]]]]


def backoff(attempts: int) -> timedelta:
    """1 min, 2, 4, 8 ... capped at 6 hours."""
    return timedelta(seconds=min(60 * (2 ** max(attempts - 1, 0)), 6 * 3600))


async def httpx_post(url: str, body: str, headers: dict[str, str]) -> tuple[int, Optional[dict[str, Any]]]:
    import httpx

    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        resp = await client.post(url, content=body.encode("utf-8"), headers=headers)
    try:
        data = resp.json()
    except ValueError:
        data = None
    return resp.status_code, data if isinstance(data, dict) else None


def webhook_url(base_url: str) -> str:
    return base_url.rstrip("/") + WEBHOOK_PATH


def valid_base_url(base_url: str | None) -> bool:
    if not base_url:
        return False
    return base_url.startswith("https://") or base_url.startswith("http://localhost") or base_url.startswith("http://127.0.0.1")


async def deliver_due(
    db: AsyncSession,
    *,
    base_url: str | None,
    secret: str | None,
    now: datetime | None = None,
    post: Poster = httpx_post,
    batch: int = BATCH,
) -> dict[str, int]:
    """Send what is due. With feedIA not configured nothing is touched: the events wait in the outbox."""
    stats = {"sent": 0, "retry": 0, "failed": 0, "skipped": 0, "not_configured": 0}
    if not valid_base_url(base_url) or not secret:
        stats["not_configured"] = 1
        return stats
    now = now or datetime.now(timezone.utc)

    rows = (
        await db.execute(
            select(FeediaOutbox)
            .where(FeediaOutbox.status == "pending", FeediaOutbox.next_attempt_at <= now)
            .order_by(FeediaOutbox.created_at)
            .limit(batch)
            .with_for_update(skip_locked=True)
        )
    ).scalars().all()

    for row in rows:
        link = await db.get(FeediaLink, row.business_id)
        if link is None or not link.enabled:
            row.status, row.last_error = "skipped", "business is not linked to feedIA (or the link is off)"
            stats["skipped"] += 1
            continue

        event = dict(row.payload)
        body_obj = {
            "eventType": row.event_type,
            "event": event,
            "accountId": link.feedia_account_id,
            "signature": sign_event(row.event_type, event, secret),
        }
        # Same key order feedIA expects to re-stringify {eventType, event}; accountId/signature sit beside it.
        body = json.dumps(body_obj, separators=(",", ":"), ensure_ascii=False)
        row.attempts = (row.attempts or 0) + 1
        try:
            status, data = await post(
                webhook_url(base_url),
                body,
                {"Content-Type": "application/json", "X-Sellia-Signature": body_obj["signature"]},
            )
        except Exception as exc:  # noqa: BLE001 - network errors are the normal reason to retry
            status, data = 0, {"error": f"{type(exc).__name__}: {exc}"[:200]}

        if 200 <= status < 300 and data and data.get("ok") is True:
            row.status, row.sent_at, row.last_error = "sent", now, None
            stats["sent"] += 1
            continue

        reason = f"HTTP {status}: {(data or {}).get('error') or 'no detail'}"[:300]
        row.last_error = reason
        permanent = (200 <= status < 300) or (status == 404 and (data or {}).get("error") == "unknown-account")
        if status == 404 and (data or {}).get("error") == "unknown-account":
            link.last_error = "feedIA does not know this account id: check it in the feedIA profile"
        if permanent or row.attempts >= MAX_ATTEMPTS:
            row.status = "failed"
            stats["failed"] += 1
            logger.warning("feedia_link: event %s for order %s failed for good (%s)", row.event_type, row.order_id, reason)
        else:
            row.next_attempt_at = now + backoff(row.attempts)
            stats["retry"] += 1

    await db.commit()
    return stats


async def counts(db: AsyncSession, business_id: Any) -> dict[str, Any]:
    """What the owner sees: how many events are waiting / failed and when the last one went through."""
    rows = (
        await db.execute(
            select(FeediaOutbox.status, FeediaOutbox.sent_at).where(FeediaOutbox.business_id == business_id)
        )
    ).all()
    sent_times = [r[1] for r in rows if r[0] == "sent" and r[1]]
    return {
        "pending": sum(1 for r in rows if r[0] == "pending"),
        "failed": sum(1 for r in rows if r[0] == "failed"),
        "sent": sum(1 for r in rows if r[0] == "sent"),
        "last_sent_at": max(sent_times).isoformat() if sent_times else None,
    }


async def requeue_failed(db: AsyncSession, business_id: Any) -> int:
    """After fixing the account id or the secret: put the failed events back in the queue."""
    result = await db.execute(
        update(FeediaOutbox)
        .where(FeediaOutbox.business_id == business_id, FeediaOutbox.status == "failed")
        .values(status="pending", attempts=0, next_attempt_at=datetime.now(timezone.utc), last_error=None)
    )
    await db.commit()
    return result.rowcount or 0
