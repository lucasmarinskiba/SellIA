"""Post-visit messages: queue when a visit is triggered, send from a beat task.

Sending is off unless OFFLINE_SEQUENCE_SEND_ENABLED is set. The copy in api/v1/offline_sequences.py is placeholder
text: it is in English, and one message promises a 10% discount that no business has confirmed. Nothing reaches a
customer until someone has read that copy and turned the flag on.

Marketing consent is not modelled. A visit is queued only when the visitor left an email and the business recorded
that contact was collected.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from html import escape

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.offline_models import OfflineConversion
from app.domains.sequences.offline_sequence_models import OfflineSequenceJob

MAX_ATTEMPTS = 3
RETRY_AFTER = timedelta(minutes=15)

Sender = Callable[[str, str, str], Awaitable[bool]]


@dataclass(frozen=True)
class QueueResult:
    queued: bool
    message: str


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


def _html(body_text: str) -> str:
    return f"<p>{escape(body_text)}</p>"


async def send_due_jobs(
    db: AsyncSession,
    *,
    now: datetime,
    enabled: bool,
    sender: Sender,
    limit: int = 50,
) -> dict[str, int]:
    """Send the due pending messages. Each job commits on its own, so one failure does not undo the others."""
    counts = {"sent": 0, "failed": 0, "skipped": 0, "retry": 0}
    if not enabled:
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
        if visit is None or visit.purchased:
            job.status = "skipped"
            job.last_error = "visita inexistente o ya comprada"
            counts["skipped"] += 1
            await db.commit()
            continue

        job.attempts += 1
        error: str | None = None
        try:
            delivered = await sender(job.recipient_email, job.subject, _html(job.body_text))
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
