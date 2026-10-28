"""The business's week with Harvey: what happened, and what to do next. Counts and rules only, no model.

Every number comes from the business's own rows. The "next steps" are fixed rules over those numbers, so the
summary never says something the data does not support.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.harvey.models import (
    HarveyOutboxItem,
    HarveyProspect,
    HarveyReply,
    OutboxStatus,
    ProspectStatus,
)

WINDOW = timedelta(days=7)
MANY_SENT_NO_REPLY = 20


async def _count(db: AsyncSession, query: Any) -> int:
    return int((await db.execute(query)).scalar_one())


async def _deals(db: AsyncSession, business_id: uuid.UUID, since: datetime) -> dict[str, Any]:
    """CRM deals Harvey brought this week. Tolerates a CRM that is not there: the summary still works."""
    try:
        from app.domains.crm.models import Deal, LeadStage

        async with db.begin_nested():
            base = [Deal.business_id == business_id, Deal.source_channel == "harvey"]
            created = await _count(db, select(func.count()).select_from(Deal).where(*base, Deal.created_at >= since))
            won_q = select(func.count(), func.coalesce(func.sum(Deal.value), 0)).where(
                *base, Deal.stage == LeadStage.CLOSED_WON, Deal.actual_close_date >= since
            )
            won, value = (await db.execute(won_q)).one()
        return {"created": created, "won": int(won), "won_value": float(value or 0)}
    except Exception:  # noqa: BLE001 - extra context must never break the summary
        return {"created": 0, "won": 0, "won_value": 0.0}


async def _meetings(db: AsyncSession, business_id: uuid.UUID, since: datetime) -> int:
    """Meetings booked this week by people Harvey prospected (matched by email)."""
    try:
        from app.domains.channels.models import BookingEvent

        async with db.begin_nested():
            known = select(func.lower(HarveyProspect.email)).where(HarveyProspect.business_id == business_id)
            return await _count(
                db,
                select(func.count()).select_from(BookingEvent).where(
                    BookingEvent.business_id == business_id,
                    BookingEvent.created_at >= since,
                    func.lower(BookingEvent.invitee_email).in_(known),
                ),
            )
    except Exception:  # noqa: BLE001 - extra context must never break the summary
        return 0


def next_steps(s: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    if s["pending_review"]:
        steps.append(f"Tenés {s['pending_review']} borrador(es) esperando tu aprobación en Prospección → Aprobación.")
    if s["needs_you"]:
        steps.append(f"{s['needs_you']} respuesta(s) necesitan que las atiendas vos: precio, contrato u otro tema que Harvey no decide.")
    if s.get("meetings"):
        steps.append(f"Tenés {s['meetings']} reunión(es) agendada(s) con prospectos de Harvey: preparate con su respuesta a mano.")
    if s["deals"]["won"]:
        steps.append(f"Cerraste {s['deals']['won']} venta(s) que vinieron de Harvey. Pedile a esos clientes una reseña o una recomendación.")
    if not s["prospects_total"]:
        steps.append("Todavía no hay prospectos: agregá algunos o activá la búsqueda automática en Configuración.")
    elif s["prospects_new"] and not s["sent"]:
        steps.append(f"Hay {s['prospects_new']} prospecto(s) sin contactar: redactá los primeros emails para empezar.")
    if s["sent"] >= MANY_SENT_NO_REPLY and not s["replies"]["total"]:
        steps.append("Se enviaron muchos emails sin ninguna respuesta: revisá el mensaje y la entrega de tu dominio (Configuración).")
    return steps


async def weekly_summary(db: AsyncSession, business_id: uuid.UUID, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    since = now - WINDOW

    sent = await _count(
        db,
        select(func.count()).select_from(HarveyOutboxItem).where(
            HarveyOutboxItem.business_id == business_id,
            HarveyOutboxItem.status == OutboxStatus.SENT.value,
            HarveyOutboxItem.sent_at >= since,
        ),
    )
    reply_rows = await db.execute(
        select(HarveyReply.classification, func.count())
        .where(HarveyReply.business_id == business_id, HarveyReply.created_at >= since)
        .group_by(HarveyReply.classification)
    )
    by_class = {k: int(n) for k, n in reply_rows.all()}
    answered = exists().where(HarveyOutboxItem.reply_id == HarveyReply.id)
    needs_you = await _count(
        db,
        select(func.count()).select_from(HarveyReply).where(
            HarveyReply.business_id == business_id, HarveyReply.needs_human.is_(True), ~answered
        ),
    )
    pending_review = await _count(
        db,
        select(func.count()).select_from(HarveyOutboxItem).where(
            HarveyOutboxItem.business_id == business_id, HarveyOutboxItem.status == OutboxStatus.PENDING_REVIEW.value
        ),
    )
    prospects_total = await _count(
        db, select(func.count()).select_from(HarveyProspect).where(HarveyProspect.business_id == business_id)
    )
    prospects_new = await _count(
        db,
        select(func.count()).select_from(HarveyProspect).where(
            HarveyProspect.business_id == business_id, HarveyProspect.status == ProspectStatus.NEW.value
        ),
    )
    prospects_added = await _count(
        db,
        select(func.count()).select_from(HarveyProspect).where(
            HarveyProspect.business_id == business_id, HarveyProspect.created_at >= since
        ),
    )
    summary: dict[str, Any] = {
        "since": since.isoformat(),
        "sent": sent,
        "prospects_added": prospects_added,
        "prospects_total": prospects_total,
        "prospects_new": prospects_new,
        "replies": {"total": sum(by_class.values()), "interested": by_class.get("interested", 0), "by_class": by_class},
        "pending_review": pending_review,
        "needs_you": needs_you,
        "deals": await _deals(db, business_id, since),
        "meetings": await _meetings(db, business_id, since),
    }
    summary["next_steps"] = next_steps(summary)
    return summary


def alert_text(s: dict[str, Any]) -> tuple[str, str]:
    """Title and body for the weekly notification."""
    title = "Tu semana con Harvey"
    parts = [
        f"{s['sent']} email(s) enviados",
        f"{s['replies']['total']} respuesta(s) ({s['replies']['interested']} interesadas)",
        f"{s['prospects_added']} prospecto(s) nuevos",
    ]
    if s.get("meetings"):
        parts.append(f"{s['meetings']} reunión(es) agendada(s)")
    if s["deals"]["created"] or s["deals"]["won"]:
        parts.append(f"{s['deals']['created']} oportunidad(es) en el CRM, {s['deals']['won']} ganada(s)")
    body = "Esta semana: " + ", ".join(parts) + "."
    if s["next_steps"]:
        body += " Para hacer ahora: " + " ".join(s["next_steps"][:2])
    return title, body
