"""Harvey ↔ the rest of SellIA: a prospect who answers becomes a deal in the CRM, and a person is alerted.

Real tables only (``deals`` and ``alerts``). Everything here is best-effort: it runs in a savepoint and a failure
is logged and swallowed, so a CRM or alerts problem can never lose a reply or break the inbox sync.

Deals made here carry ``source_channel="harvey"`` and ``extra_data["harvey_prospect_id"]``, which is also how a later
payment finds the prospect it came from (see ``attribute_payment``).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.alerts.models import Alert, AlertSeverity, AlertStatus
from app.domains.crm.models import Deal, LeadStage
from app.domains.harvey import automation_hooks
from app.domains.harvey.models import HarveyProspect, ReplyClass

logger = get_logger(__name__)

SOURCE = "harvey"

# reply class -> (stage, probability, priority, alert severity or None). 5 = needs a person today.
_RULES: dict[str, tuple[LeadStage, int, int, AlertSeverity | None]] = {
    ReplyClass.INTERESTED.value: (LeadStage.QUALIFIED, 50, 4, AlertSeverity.CRITICAL),
    ReplyClass.HANDOFF.value: (LeadStage.QUALIFIED, 40, 5, AlertSeverity.CRITICAL),
    ReplyClass.QUESTION.value: (LeadStage.CONTACTED, 25, 3, AlertSeverity.WARNING),
    ReplyClass.OBJECTION.value: (LeadStage.CONTACTED, 15, 3, AlertSeverity.WARNING),
    ReplyClass.NOT_INTERESTED.value: (LeadStage.CLOSED_LOST, 0, 0, None),
    ReplyClass.OPT_OUT.value: (LeadStage.CLOSED_LOST, 0, 0, None),
}
_ALERT_TITLE = {
    ReplyClass.INTERESTED.value: "Un prospecto de Harvey quiere avanzar",
    ReplyClass.HANDOFF.value: "Un prospecto de Harvey necesita que lo atiendas vos",
    ReplyClass.QUESTION.value: "Un prospecto de Harvey hizo una pregunta",
    ReplyClass.OBJECTION.value: "Un prospecto de Harvey puso una objeción",
}
_NEXT_STEP = {
    ReplyClass.INTERESTED.value: "Revisá el borrador de respuesta en Prospección → Respuestas y proponé un horario.",
    ReplyClass.HANDOFF.value: "Respondele personalmente: toca precio, contrato u otro tema que Harvey no decide.",
    ReplyClass.QUESTION.value: "Revisá el borrador de respuesta en Prospección → Respuestas.",
    ReplyClass.OBJECTION.value: "Revisá el borrador de respuesta; una objeción bien atendida suele reabrir la conversación.",
}
_OPEN_STAGES = (LeadStage.NEW_LEAD, LeadStage.CONTACTED, LeadStage.QUALIFIED, LeadStage.PROPOSAL_SENT, LeadStage.NEGOTIATING)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def find_deal(db: AsyncSession, business_id: uuid.UUID, email: str) -> Deal | None:
    """The business's open-or-closed Harvey deal for this address (newest first)."""
    rows = await db.execute(
        select(Deal)
        .where(
            Deal.business_id == business_id,
            Deal.source_channel == SOURCE,
            Deal.is_active.is_(True),
            Deal.contact_email == (email or "").strip().lower(),
        )
        .order_by(Deal.created_at.desc())
    )
    return rows.scalars().first()


async def _sync(
    db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect, classification: str, snippet: str, reply_id: uuid.UUID
) -> list[tuple[str, dict[str, Any]]]:
    """Create or advance the deal. Returns the workflow events to fire once it is saved."""
    events: list[tuple[str, dict[str, Any]]] = []
    rule = _RULES.get(classification)
    if rule is None:
        return events
    stage, probability, priority, severity = rule
    email = (prospect.email or "").strip().lower()
    deal = await find_deal(db, business_id, email)
    who = " ".join(p for p in (prospect.first_name, prospect.last_name) if p).strip() or email
    company = prospect.company or ""

    if deal is None:
        if severity is None:  # a rejection with no deal behind it is not worth a CRM row
            return events
        deal = Deal(
            business_id=business_id,
            title=f"{company or who} (Harvey)"[:300],
            description="Prospecto que respondió a la prospección de Harvey.",
            contact_name=who[:255],
            contact_email=email[:255],
            source_channel=SOURCE,
            stage=stage,
            probability=probability,
            priority=priority,
            extra_data={"harvey_prospect_id": str(prospect.id), "company": company},
        )
        db.add(deal)
        await db.flush()
        new_deal = True
    elif deal.stage not in (LeadStage.CLOSED_WON,):
        new_deal = False
        before = deal.stage
        # A reply may move a deal forward, or close it as lost; it never reopens a won one.
        if stage is LeadStage.CLOSED_LOST:
            deal.stage, deal.probability, deal.actual_close_date = stage, 0, _now()
            deal.close_reason = "Pidió que no lo contacten" if classification == ReplyClass.OPT_OUT.value else "No le interesa"
        elif deal.stage in _OPEN_STAGES and _OPEN_STAGES.index(stage) >= _OPEN_STAGES.index(deal.stage):
            deal.stage, deal.probability, deal.priority = stage, probability, max(priority, deal.priority or 0)
    else:
        new_deal = False
        before = deal.stage
    deal.extra_data = {**(deal.extra_data or {}), "last_reply_class": classification, "last_reply_id": str(reply_id)}

    data = {
        "email": email, "name": who, "company": company, "classification": classification, "content": snippet,
        "channel": "email", "deal_id": str(deal.id), "prospect_id": str(prospect.id),
    }
    if new_deal:
        events.append(("new_lead", data))
    elif deal.stage is not before:
        events.append(("stage_changed", {**data, "from": before.value, "to": deal.stage.value}))

    if severity is not None:
        db.add(
            Alert(
                business_id=business_id,
                deal_id=deal.id,
                title=_ALERT_TITLE[classification],
                description=f"{who}{f' ({company})' if company else ''}: «{snippet}»",
                severity=severity,
                status=AlertStatus.UNREAD,
                entity_type="deal",
                entity_id=deal.id,
                recommended_action=_NEXT_STEP[classification],
                alert_metadata={"source": SOURCE, "reply_id": str(reply_id), "prospect_id": str(prospect.id)},
            )
        )
    return events


async def on_reply(
    db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect, classification: str, body: str, reply_id: uuid.UUID
) -> None:
    """Create or advance the deal for this reply and alert a person. Never raises."""
    snippet = " ".join((body or "").split())[:160]
    try:
        async with db.begin_nested():  # a savepoint: only this sync is undone if it fails
            events = await _sync(db, business_id, prospect, classification, snippet, reply_id)
        await db.commit()
    except Exception:  # noqa: BLE001 - CRM trouble must never lose a reply
        logger.warning("harvey: CRM sync failed for a reply; the reply itself is saved", exc_info=True)
        return
    for trigger, data in events:  # after the commit: an automation problem cannot undo the deal
        await automation_hooks.fire(db, trigger, business_id, data)


async def attribute_payment(db: AsyncSession, business_id: uuid.UUID, payer_email: str, amount: Any, currency: str = "ARS") -> bool:
    """A paid order from an address Harvey prospected closes that deal as won. Returns True when one was credited."""
    if not payer_email:
        return False
    try:
        async with db.begin_nested():
            deal = await find_deal(db, business_id, payer_email)
            if deal is None or deal.stage is LeadStage.CLOSED_WON:
                return False
            deal.stage, deal.probability, deal.actual_close_date = LeadStage.CLOSED_WON, 100, _now()
            deal.close_reason = "Compró (pago acreditado)"
            deal.value = Decimal(str(amount)) if amount is not None else deal.value
            deal.currency = (currency or "ARS")[:3]
            data = {
                "email": (payer_email or "").strip().lower(), "name": deal.contact_name or "", "deal_id": str(deal.id),
                "value": float(deal.value) if deal.value is not None else None, "currency": deal.currency,
                "channel": "email",
            }
        await db.commit()
        await automation_hooks.fire(db, "revenue_event", business_id, data)
        return True
    except Exception:  # noqa: BLE001
        logger.warning("harvey: payment attribution failed", exc_info=True)
        return False


async def on_booking(db: AsyncSession, business_id: uuid.UUID, invitee_email: str, scheduled_at: datetime | None) -> bool:
    """Someone Harvey prospected booked a meeting: move their deal forward and alert a person. Never raises."""
    if not invitee_email:
        return False
    try:
        async with db.begin_nested():
            deal = await find_deal(db, business_id, invitee_email)
            if deal is None or deal.stage in (LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST):
                return False
            before = deal.stage
            deal.stage, deal.probability = LeadStage.NEGOTIATING, max(deal.probability or 0, 60)
            deal.priority = max(deal.priority or 0, 4)
            when = scheduled_at.astimezone(timezone.utc).strftime("%d/%m %H:%M UTC") if scheduled_at else "fecha a confirmar"
            deal.extra_data = {**(deal.extra_data or {}), "meeting_at": scheduled_at.isoformat() if scheduled_at else None}
            db.add(
                Alert(
                    business_id=business_id,
                    deal_id=deal.id,
                    title="Un prospecto de Harvey agendó una reunión",
                    description=f"{deal.contact_name or invitee_email} agendó para {when}.",
                    severity=AlertSeverity.CRITICAL,
                    status=AlertStatus.UNREAD,
                    entity_type="deal",
                    entity_id=deal.id,
                    recommended_action="Preparate para la reunión: mirá su respuesta en Prospección → Respuestas.",
                    alert_metadata={"source": SOURCE, "kind": "meeting", "invitee_email": invitee_email},
                )
            )
            data = {
                "email": invitee_email.strip().lower(), "name": deal.contact_name or "", "deal_id": str(deal.id),
                "scheduled_at": scheduled_at.isoformat() if scheduled_at else None, "channel": "email",
                "from": before.value, "to": deal.stage.value,
            }
        await db.commit()
        await automation_hooks.fire(db, "appointment_scheduled", business_id, data)
        return True
    except Exception:  # noqa: BLE001 - CRM trouble must never fail the booking webhook
        logger.warning("harvey: booking sync failed", exc_info=True)
        return False
