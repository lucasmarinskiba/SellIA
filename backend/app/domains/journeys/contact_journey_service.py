"""Contact journey service (the implementation behind app/api/v1/customer_journeys.py).

Stage rules, applied to the first touchpoint of each kind:

* ``email_sent`` / ``email_opened``  -> consideration
* ``proximity_check``                -> intent
* ``location_visit``                 -> visit
* ``order_placed``                   -> purchase; every later order counts as a repeat purchase (retention)

A journey starts at awareness (its creation). Stage dates are never moved once set. Every touchpoint is kept
as an event, so the history stays auditable even though the stage dates only record the first occurrence.

Rates are ``None`` when their denominator is zero: an empty funnel is not a 0% conversion.
"""

from datetime import datetime, timedelta, timezone
from itertools import pairwise
from statistics import mean
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.location_models import Location
from app.domains.journeys.contact_journey_models import (
    ContactJourney,
    ContactJourneyTouchpoint,
)

STAGE_BY_TOUCHPOINT = {
    "email_sent": "consideration_date",
    "email_opened": "consideration_date",
    "proximity_check": "intent_date",
    "location_visit": "visit_date",
    "order_placed": "purchase_date",
}


class JourneyNotFound(LookupError):
    """The journey does not exist, or does not belong to the business it was asked under."""


class JourneyInvalid(ValueError):
    """The request breaks a rule (no contact, unknown touchpoint, location of another business...)."""


def _utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def _rate(part: int, whole: int) -> float | None:
    return round(part / whole * 100, 2) if whole else None


class CustomerJourneyService:
    @staticmethod
    async def start_journey(
        business_id: UUID,
        channel: str,
        db: AsyncSession,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        campaign: str | None = None,
        source: str | None = None,
        now: datetime | None = None,
    ) -> ContactJourney:
        if not (customer_email or customer_phone):
            raise JourneyInvalid("Hace falta un email o un teléfono para identificar al contacto")
        journey = ContactJourney(
            business_id=business_id,
            channel=channel,
            campaign=campaign,
            source=source,
            customer_email=customer_email,
            customer_phone=customer_phone,
            awareness_date=_utc(now or datetime.now(timezone.utc)),
            repeat_purchase_count=0,
        )
        db.add(journey)
        await db.commit()
        await db.refresh(journey)
        return journey

    @staticmethod
    async def record_touchpoint(
        journey_id: UUID,
        business_id: UUID,
        touchpoint_type: str,
        channel: str,
        db: AsyncSession,
        campaign: str | None = None,
        location_id: UUID | None = None,
        order_id: str | None = None,
        now: datetime | None = None,
    ) -> dict:
        journey = await CustomerJourneyService._owned(journey_id, business_id, db)
        if touchpoint_type not in STAGE_BY_TOUCHPOINT:
            raise JourneyInvalid(f"touchpoint_type inválido: {touchpoint_type}")
        if location_id is not None:
            location = await db.get(Location, location_id)
            if location is None or location.business_id != business_id:
                raise JourneyInvalid("La sucursal no pertenece a este negocio")

        when = _utc(now or datetime.now(timezone.utc))
        db.add(ContactJourneyTouchpoint(
            journey_id=journey.id, business_id=business_id, touchpoint_type=touchpoint_type, channel=channel,
            campaign=campaign, location_id=location_id, order_id=order_id, occurred_at=when,
        ))

        stage = STAGE_BY_TOUCHPOINT[touchpoint_type]
        if stage == "purchase_date" and journey.purchase_date is not None:
            journey.repeat_purchase_count = (journey.repeat_purchase_count or 0) + 1
            journey.last_order_id = order_id or journey.last_order_id
        elif getattr(journey, stage) is None:
            setattr(journey, stage, when)
            if stage == "purchase_date":
                journey.last_order_id = order_id

        await db.commit()
        return {"journey_id": str(journey.id), "touchpoint_type": touchpoint_type, "stage": stage.removesuffix("_date")}

    @staticmethod
    async def get_journey_details(journey_id: UUID, business_id: UUID, db: AsyncSession) -> dict:
        journey = await CustomerJourneyService._owned(journey_id, business_id, db)
        rows = (await db.execute(
            select(ContactJourneyTouchpoint)
            .where(ContactJourneyTouchpoint.journey_id == journey.id)
            .order_by(ContactJourneyTouchpoint.occurred_at)
        )).scalars().all()
        return {
            "journey_id": str(journey.id),
            "business_id": str(journey.business_id),
            "channel": journey.channel,
            "campaign": journey.campaign,
            "source": journey.source,
            "stages": {
                "awareness": journey.awareness_date.isoformat(),
                "consideration": journey.consideration_date.isoformat() if journey.consideration_date else None,
                "intent": journey.intent_date.isoformat() if journey.intent_date else None,
                "visit": journey.visit_date.isoformat() if journey.visit_date else None,
                "purchase": journey.purchase_date.isoformat() if journey.purchase_date else None,
            },
            "repeat_purchase_count": journey.repeat_purchase_count,
            "touchpoints": [
                {"type": t.touchpoint_type, "channel": t.channel, "occurred_at": _utc(t.occurred_at).isoformat(),
                 "order_id": t.order_id}
                for t in rows
            ],
        }

    @staticmethod
    async def _journeys_in_window(business_id: UUID, days: int, db: AsyncSession, now: datetime | None):
        end = _utc(now or datetime.now(timezone.utc))
        start = end - timedelta(days=days)
        rows = (await db.execute(
            select(ContactJourney).where(ContactJourney.business_id == business_id)
        )).scalars().all()
        return [j for j in rows if start <= _utc(j.awareness_date) < end]

    @staticmethod
    async def calculate_journey_metrics(business_id: UUID, days: int, db: AsyncSession, now: datetime | None = None) -> dict:
        journeys = await CustomerJourneyService._journeys_in_window(business_id, days, db, now)
        purchased = [j for j in journeys if j.purchase_date is not None]
        days_to_purchase = [
            (_utc(j.purchase_date) - _utc(j.awareness_date)).total_seconds() / 86400 for j in purchased
        ]
        by_channel: dict[str, dict] = {}
        for channel in sorted({j.channel for j in journeys}):
            group = [j for j in journeys if j.channel == channel]
            won = [j for j in group if j.purchase_date is not None]
            by_channel[channel] = {"journeys": len(group), "purchased": len(won), "conversion_rate": _rate(len(won), len(group))}
        return {
            "period_days": days,
            "total_journeys": len(journeys),
            "purchased": len(purchased),
            "conversion_rate": _rate(len(purchased), len(journeys)),
            "avg_days_to_purchase": round(mean(days_to_purchase), 2) if days_to_purchase else None,
            "repeat_purchases": sum(j.repeat_purchase_count or 0 for j in journeys),
            "by_channel": by_channel,
        }

    @staticmethod
    async def funnel(business_id: UUID, days: int, db: AsyncSession, now: datetime | None = None) -> dict:
        journeys = await CustomerJourneyService._journeys_in_window(business_id, days, db, now)
        stages = {
            "awareness": len(journeys),
            "consideration": sum(1 for j in journeys if j.consideration_date),
            "intent": sum(1 for j in journeys if j.intent_date),
            "visit": sum(1 for j in journeys if j.visit_date),
            "purchase": sum(1 for j in journeys if j.purchase_date),
            "retention": sum(1 for j in journeys if (j.repeat_purchase_count or 0) > 0),
        }
        order = list(stages)
        return {
            "business_id": str(business_id),
            "period_days": days,
            "funnel": stages,
            "conversion_rates": {
                f"{a}_to_{b}": _rate(stages[b], stages[a]) for a, b in pairwise(order)
            },
        }

    @staticmethod
    async def _owned(journey_id: UUID, business_id: UUID, db: AsyncSession) -> ContactJourney:
        journey = await db.get(ContactJourney, journey_id)
        if journey is None or journey.business_id != business_id:
            raise JourneyNotFound("Journey no encontrado")
        return journey
