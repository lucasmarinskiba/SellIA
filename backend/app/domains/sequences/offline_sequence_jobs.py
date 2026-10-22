"""Post-visit messages: queue when a visit is triggered, send from a beat task.

Sending is off unless OFFLINE_SEQUENCE_SEND_ENABLED is set, and a message is never sent without a public base URL,
because every message carries an unsubscribe link built from it.

Each business sends under its own name (from_name), in its own language (businesses.config["language"]: es by
default, or en), and its unsubscribe footer names it. An address that unsubscribes from a business is recorded by
hash and never messaged by that business again.

Marketing consent is not modelled. A visit is queued only when the visitor left an email and the business recorded
that contact was collected.
"""

import hashlib
import hmac
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from html import escape
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.offline_models import OfflineConversion
from app.domains.businesses.models import Business
from app.domains.sequences.offline_sequence_models import (
    OfflineMessageOptOut,
    OfflineSequenceJob,
)

MAX_ATTEMPTS = 3
RETRY_AFTER = timedelta(minutes=15)
SUPPORTED_LANGUAGES = ("es", "en")
DEFAULT_LANGUAGE = "es"
OPT_OUT_PATH = "/api/v1/offline-sequences/opt-out"

# (to, subject, html, from_name) -> delivered
Sender = Callable[[str, str, str, str], Awaitable[bool]]

# Footer copy per language. {negocio} is the business name.
_FOOTER: dict[str, tuple[str, str]] = {
    "es": ("Recibís este mensaje porque visitaste {negocio}.", "Dar de baja de los mensajes de {negocio}"),
    "en": ("You're receiving this message because you visited {negocio}.", "Unsubscribe from {negocio} messages"),
}


@dataclass(frozen=True)
class QueueResult:
    queued: bool
    message: str


def resolve_language(config: Mapping[str, Any] | None) -> str:
    language = (config or {}).get("language")
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def render(text: str, *, business_name: str, location_name: str | None = None) -> str:
    """Fill {negocio} and {sucursal}. Plain replacement, so braces in a business name cannot break it."""
    filled = text.replace("{negocio}", business_name)
    return filled.replace("{sucursal}", location_name or business_name)


def address_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _signature(secret: str, business_id: UUID | str, digest: str) -> str:
    return hmac.new(secret.encode(), f"{business_id}:{digest}".encode(), hashlib.sha256).hexdigest()


def opt_out_url(base_url: str, business_id: UUID, email: str, secret: str) -> str:
    """Unsubscribe link. Carries a hash and a signature, never the address itself."""
    digest = address_hash(email)
    query = urlencode({"b": str(business_id), "h": digest, "s": _signature(secret, business_id, digest)})
    return f"{base_url.rstrip('/')}{OPT_OUT_PATH}?{query}"


def verify_opt_out(secret: str, business_id: UUID, digest: str, signature: str) -> bool:
    return hmac.compare_digest(_signature(secret, business_id, digest), signature)


async def is_opted_out(db: AsyncSession, business_id: UUID, email: str) -> bool:
    row = (
        await db.execute(
            select(OfflineMessageOptOut.id).where(
                OfflineMessageOptOut.business_id == business_id,
                OfflineMessageOptOut.email_hash == address_hash(email),
            )
        )
    ).first()
    return row is not None


async def record_opt_out(db: AsyncSession, business_id: UUID, digest: str) -> None:
    """Idempotent: an address that unsubscribes twice is recorded once."""
    existing = (
        await db.execute(
            select(OfflineMessageOptOut.id).where(
                OfflineMessageOptOut.business_id == business_id,
                OfflineMessageOptOut.email_hash == digest,
            )
        )
    ).first()
    if existing is not None:
        return
    db.add(OfflineMessageOptOut(business_id=business_id, email_hash=digest))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()


async def queue_post_visit(
    db: AsyncSession,
    *,
    conversion: OfflineConversion,
    template_name: str,
    subject: str,
    body_text: str,
    delay_hours: int,
    enabled: bool,
    now: datetime,
) -> QueueResult:
    if not enabled:
        return QueueResult(False, "El envío de secuencias post-visita está desactivado. No se encoló nada.")
    if conversion.purchased:
        return QueueResult(False, "La visita ya terminó en compra: no corresponde el mensaje post-visita.")
    if not conversion.visitor_email or not conversion.contact_collected:
        return QueueResult(False, "La visita no tiene un email de contacto registrado. No se encoló nada.")

    conversion_id = conversion.id
    business_id = conversion.business_id
    recipient = conversion.visitor_email
    if await is_opted_out(db, business_id, recipient):
        return QueueResult(False, "Esa persona dio de baja los mensajes de este negocio. No se encoló nada.")

    existing = (
        await db.execute(
            select(OfflineSequenceJob.id).where(
                OfflineSequenceJob.conversion_id == conversion_id,
                OfflineSequenceJob.template_name == template_name,
            )
        )
    ).first()
    if existing is not None:
        return QueueResult(True, "Ya estaba encolado para esta visita.")

    due = now + timedelta(hours=delay_hours)
    db.add(
        OfflineSequenceJob(
            business_id=business_id,
            conversion_id=conversion_id,
            template_name=template_name,
            recipient_email=recipient,
            subject=subject,
            body_text=body_text,
            status="pending",
            due_at=due,
            attempts=0,
            created_at=now,
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        # Two triggers raced past the check above; the unique key kept one row.
        await db.rollback()
        return QueueResult(True, "Ya estaba encolado para esta visita.")
    return QueueResult(True, f"Encolado para envío el {due:%Y-%m-%d %H:%M} UTC.")


def _message_html(
    body_text: str, *, business: Business, recipient: str, base_url: str, secret: str
) -> str:
    language = resolve_language(business.config)
    footer_text, link_text = _FOOTER[language]
    url = opt_out_url(base_url, business.id, recipient, secret)
    return (
        f"<p>{escape(body_text)}</p>"
        f'<p style="font-size:12px;color:#666">'
        f'{escape(render(footer_text, business_name=business.name))} '
        f'<a href="{escape(url)}">{escape(render(link_text, business_name=business.name))}</a></p>'
    )


def _mark(job: OfflineSequenceJob, status: str, reason: str) -> None:
    job.status = status
    job.last_error = reason


async def send_due_jobs(
    db: AsyncSession,
    *,
    now: datetime,
    enabled: bool,
    sender: Sender,
    base_url: str | None,
    secret: str,
    limit: int = 50,
) -> dict[str, int]:
    """Send the due pending messages. Each job commits on its own, so one failure does not undo the others.

    Nothing runs unless sending is enabled and a public base URL is set: without one there is no unsubscribe link,
    and a message without it is not sent. Jobs stay pending until the configuration is in place.
    """
    counts = {"sent": 0, "failed": 0, "skipped": 0, "retry": 0}
    if not enabled or not base_url:
        return counts

    jobs = (
        await db.execute(
            select(OfflineSequenceJob)
            .where(OfflineSequenceJob.status == "pending", OfflineSequenceJob.due_at <= now)
            .order_by(OfflineSequenceJob.due_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    ).scalars().all()

    for job in jobs:
        visit = await db.get(OfflineConversion, job.conversion_id)
        business = await db.get(Business, job.business_id)
        if visit is None or visit.purchased or business is None:
            _mark(job, "skipped", "visita o negocio inexistente, o ya comprada")
            counts["skipped"] += 1
            await db.commit()
            continue
        if await is_opted_out(db, job.business_id, job.recipient_email):
            _mark(job, "skipped", "destinatario dado de baja")
            counts["skipped"] += 1
            await db.commit()
            continue

        job.attempts += 1
        error: str | None = None
        try:
            html = _message_html(
                job.body_text,
                business=business,
                recipient=job.recipient_email,
                base_url=base_url,
                secret=secret,
            )
            delivered = await sender(job.recipient_email, job.subject, html, business.name)
            if not delivered:
                error = "el proveedor rechazó el envío"
        except Exception as e:  # noqa: BLE001 -- one bad send must not stop the batch
            delivered = False
            error = str(e)[:500]

        if delivered:
            job.status = "sent"
            job.sent_at = now
            job.last_error = None
            counts["sent"] += 1
        elif job.attempts >= MAX_ATTEMPTS:
            job.status = "failed"
            job.last_error = error
            counts["failed"] += 1
        else:
            job.due_at = now + RETRY_AFTER
            job.last_error = error
            counts["retry"] += 1
        await db.commit()

    return counts
