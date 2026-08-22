"""Phase X12: Conversion & Attraction Agent API.

Antes: cada endpoint devolvía un dict armado en el momento - ConversionSequence
y AttractionMagnet estaban definidos en models.py pero nunca se instanciaban
(cero db.add/db.commit en todo el router). closing-effectiveness devolvía
SIEMPRE los mismos números fijos sin importar qué user_id se pidiera, y
win-deal "registraba" un deal sin persistir nada - dos llamadas seguidas
no dejaban rastro de haber pasado. Ahora start-closing-sequence crea una fila
real, closing-effectiveness la lee de verdad (404 si no existe, no inventa
datos), y win-deal actualiza esa misma fila en vez de solo devolver un cálculo.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.conversion_engine.models import ConversionSequence, AttractionMagnet


router = APIRouter(prefix="/api/v1/conversion-engine", tags=["conversion-engine"])


CLOSING_SEQUENCES = {
    "pragmatist": {
        "touch_1": {"type": "email", "delay_hours": 0, "subject": "ROI breakdown: $2.3M revenue increase in 6 months", "focus": "Financial impact + payback period"},
        "touch_2": {"type": "demo_invite", "delay_hours": 24, "subject": "30-min walkthrough: Your use case, your data", "focus": "Personalized demo for their industry"},
        "touch_3": {"type": "objection_handling", "delay_hours": 72, "subject": "Questions about implementation timeline?", "focus": "Risk reduction + timeline proof"},
        "touch_4": {"type": "close", "delay_hours": 168, "subject": "Ready to lock in your pricing?", "focus": "Limited time offer + contract ready"},
    },
    "skeptic": {
        "touch_1": {"type": "social_proof", "delay_hours": 0, "subject": "Gartner Leader + Forrester Wave - Here's why", "focus": "Third-party validation"},
        "touch_2": {"type": "case_study", "delay_hours": 24, "subject": "Enterprise case study: Similar company, 150% ROI", "focus": "Peer success + metrics"},
        "touch_3": {"type": "technical_dive", "delay_hours": 72, "subject": "Security, compliance, integration deep-dive", "focus": "Technical proof + risk mitigation"},
        "touch_4": {"type": "close", "delay_hours": 168, "subject": "Executive briefing + pilot pricing", "focus": "Low-risk pilot + flexible terms"},
    },
    "impulse_buyer": {
        "touch_1": {"type": "scarcity", "delay_hours": 0, "subject": "⏰ LAST 3 SEATS: Founding member pricing ($99/mo) expires Friday 5pm", "focus": "Urgency + loss aversion"},
        "touch_2": {"type": "demo_live", "delay_hours": 6, "subject": "Live demo in 2 hours (3 spots left)", "focus": "Immediate action"},
        "touch_3": {"type": "countdown", "delay_hours": 24, "subject": "24 hours left: Lock in founding price", "focus": "Deadline pressure"},
        "touch_4": {"type": "final", "delay_hours": 36, "subject": "LAST CHANCE: Pricing reverts in 12 hours", "focus": "Final urgency push"},
    },
}

MAGNET_STATS = {
    "ebook": {"estimated_conversion": 0.18, "average_lead_quality": 0.62, "typical_follow_up": "3-day email sequence"},
    "calculator": {"estimated_conversion": 0.25, "average_lead_quality": 0.78, "typical_follow_up": "1-hour follow-up call offer"},
    "template": {"estimated_conversion": 0.22, "average_lead_quality": 0.65, "typical_follow_up": "5-email nurture sequence"},
    "webinar": {"estimated_conversion": 0.15, "average_lead_quality": 0.85, "typical_follow_up": "2-week demo pipeline"},
    "audit": {"estimated_conversion": 0.12, "average_lead_quality": 0.92, "typical_follow_up": "Custom proposal + 1-on-1"},
}


@router.post("/start-closing-sequence/{user_id}")
async def start_closing_sequence(
    user_id: str,
    email: str = Body(...),
    personality_type: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start 4-touch multi-channel closing sequence - persiste la secuencia real."""
    sequence_content = CLOSING_SEQUENCES.get(personality_type, CLOSING_SEQUENCES["pragmatist"])

    record = ConversionSequence(
        id=str(uuid.uuid4()),
        user_id=user_id,
        email=email,
        deal_stage="considering",
        touch_1_type=sequence_content["touch_1"]["type"],
        touch_2_type=sequence_content["touch_2"]["type"],
        touch_3_type=sequence_content["touch_3"]["type"],
        touch_4_type=sequence_content["touch_4"]["type"],
        last_closing_angle=personality_type,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "sequence_id": record.id,
        "user_id": user_id,
        "sequence_type": f"closing_{personality_type}",
        "total_touches": 4,
        "sequence": sequence_content,
        "estimated_close_rate": 0.42,
        "average_deal_cycle": "14 days",
    }


@router.post("/add-attraction-magnet")
async def create_attraction_magnet(
    magnet_type: str = Body(...),
    magnet_title: str = Body(...),
    magnet_promise: str = Body(...),
    ideal_customer_profile: str = Body(...),
    cta_copy: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create lead magnet optimized for conversion - persiste el magnet real."""
    stats = MAGNET_STATS.get(magnet_type, MAGNET_STATS["ebook"])

    magnet = AttractionMagnet(
        id=str(uuid.uuid4()),
        magnet_type=magnet_type,
        magnet_title=magnet_title,
        magnet_promise=magnet_promise,
        ideal_customer_profile=ideal_customer_profile,
        cta_copy=cta_copy,
        estimated_conversion_rate=stats["estimated_conversion"],
    )
    db.add(magnet)
    await db.commit()
    await db.refresh(magnet)

    return {
        "magnet_id": magnet.id,
        "magnet_type": magnet.magnet_type,
        "magnet_title": magnet.magnet_title,
        "magnet_promise": magnet.magnet_promise,
        "ideal_for": magnet.ideal_customer_profile,
        "cta_copy": magnet.cta_copy,
        "estimated_conversion_rate": stats["estimated_conversion"],
        "average_lead_quality_score": stats["average_lead_quality"],
        "follow_up_sequence": stats["typical_follow_up"],
    }


@router.get("/closing-effectiveness/{user_id}")
async def get_closing_effectiveness(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Track which closing tactics work for this prospect - lee la secuencia real, 404 si no existe."""
    result = await db.execute(
        select(ConversionSequence)
        .where(ConversionSequence.user_id == user_id)
        .order_by(ConversionSequence.created_at.desc())
    )
    record = result.scalars().first()
    if record is None:
        raise HTTPException(status_code=404, detail=f"No hay closing sequence para user_id={user_id}")

    touches_sent = sum(1 for t in [record.touch_1_sent, record.touch_2_sent, record.touch_3_sent, record.touch_4_sent] if t is not None)

    return {
        "user_id": user_id,
        "sequence_id": record.id,
        "deal_stage": record.deal_stage,
        "probability_to_close": record.probability_to_close,
        "estimated_deal_value": record.estimated_deal_value,
        "touches_sent": touches_sent,
        "touch_1_opened": record.touch_1_opened,
        "objections_raised": record.objection_handling or [],
        "demo_scheduled": record.demo_scheduled,
        "demo_date": record.demo_date.isoformat() if record.demo_date else None,
        "last_closing_angle": record.last_closing_angle,
        "closed_value": record.closed_value,
    }


@router.post("/win-deal/{user_id}")
async def record_deal_won(
    user_id: str,
    deal_value: float = Body(...),
    contract_term_months: int = Body(...),
    which_touch_converted: int = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record won deal and attribution - actualiza la secuencia real, no solo calcula."""
    result = await db.execute(
        select(ConversionSequence)
        .where(ConversionSequence.user_id == user_id)
        .order_by(ConversionSequence.created_at.desc())
    )
    record = result.scalars().first()
    if record is None:
        raise HTTPException(status_code=404, detail=f"No hay closing sequence activa para user_id={user_id}")

    attribution = ["scarcity_fomo", "personality_targeting", "personalized_demo", "objection_handling"][which_touch_converted - 1]

    record.deal_stage = "closed"
    record.contract_signed = True
    record.closed_value = deal_value
    record.which_touch_converted = which_touch_converted
    record.conversion_attributed_to_tactic = attribution
    record.closed_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "user_id": user_id,
        "sequence_id": record.id,
        "deal_closed": True,
        "deal_value": deal_value,
        "contract_term": f"{contract_term_months} months",
        "annual_revenue": deal_value * (12 / contract_term_months),
        "which_touch_converted": which_touch_converted,
        "conversion_attributed_to": attribution,
        "lifetime_value_projected": deal_value * 3,
        "next_upsell_opportunity": "enterprise_add_ons",
    }
