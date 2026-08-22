"""Phase X11: Loyalty & Retention Engine API.

Antes: cada endpoint devolvía un dict fijo - enroll-loyalty "inscribía" sin
persistir nada, loyalty-status devolvía SIEMPRE "silver, 2450 points" sin
importar el user_id, y unlock-vip "actualizaba a platinum" sin tocar la
base. LoyaltyProgram y RetentionSequence estaban definidos en models.py
pero nunca instanciados. Ahora enroll crea/actualiza una fila real,
loyalty-status la lee (404 si nunca se inscribió), y unlock-vip actualiza
esa misma fila.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.loyalty_engine.models import LoyaltyProgram, RetentionSequence


router = APIRouter(prefix="/api/v1/loyalty-engine", tags=["loyalty-engine"])


TIER_THRESHOLDS = [
    ("bronze", 0, 999),
    ("silver", 1000, 4999),
    ("gold", 5000, 9999),
    ("platinum", 10000, None),
]

RETENTION_SEQUENCES = {
    "win_back": {
        "step_1": "Day 0: 'We miss you' + 50% discount offer",
        "step_2": "Day 3: Success story from similar company",
        "step_3": "Day 7: Product update highlights",
        "step_4": "Day 14: VIP onboarding offer",
        "step_5": "Day 30: Executive briefing invitation",
    },
    "expansion": {
        "step_1": "Day 0: Usage analytics - 'You're using X, try Y'",
        "step_2": "Day 3: 2-person ROI impact from new feature",
        "step_3": "Day 7: Free upgrade offer (limited time)",
        "step_4": "Day 14: Peer success with expansion",
        "step_5": "Day 30: Enterprise upgrade bonus",
    },
    "vip_nurture": {
        "step_1": "Day 0: Personal note from CEO",
        "step_2": "Day 3: Exclusive feature roadmap preview",
        "step_3": "Day 7: VIP training session invitation",
        "step_4": "Day 14: Custom integration consultation",
        "step_5": "Day 30: Annual QBR with success plan",
    },
    "churn_prevention": {
        "step_1": "Day 0: Usage drop detected - 'How can we help?'",
        "step_2": "Day 3: 1-on-1 call with success manager",
        "step_3": "Day 7: Personalized implementation plan",
        "step_4": "Day 14: ROI analysis specific to their use case",
        "step_5": "Day 30: Executive briefing + custom features",
    },
}


def _tier_for_points(points: float) -> str:
    for tier, low, high in TIER_THRESHOLDS:
        if high is None or (low <= points <= high):
            if points >= low:
                return tier
    return "bronze"


def _progress_to_next_tier(points: float) -> dict:
    for i, (tier, low, high) in enumerate(TIER_THRESHOLDS):
        if high is not None and low <= points <= high:
            next_tier, next_low, _ = TIER_THRESHOLDS[i + 1]
            return {"points_to_next_tier": next_low - points, "progress_to_next": (points - low) / (next_low - low)}
    return {"points_to_next_tier": 0, "progress_to_next": 1.0}


async def _get_or_create_program(db: AsyncSession, user_id: str, email: str | None = None) -> LoyaltyProgram:
    result = await db.execute(select(LoyaltyProgram).where(LoyaltyProgram.user_id == user_id))
    program = result.scalars().first()
    if program is None:
        program = LoyaltyProgram(id=str(uuid.uuid4()), user_id=user_id, email=email or f"{user_id}@unknown")
        db.add(program)
        await db.commit()
        await db.refresh(program)
    return program


@router.post("/enroll-loyalty/{user_id}")
async def enroll_loyalty_program(
    user_id: str,
    email: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Enroll customer in loyalty program - crea la fila real, idempotente."""
    program = await _get_or_create_program(db, user_id, email)

    return {
        "user_id": user_id,
        "tier": program.tier,
        "points_balance": program.points_balance,
        "tier_progression": {
            "bronze": "0-999 points",
            "silver": "1000-4999 points (unlock priority support)",
            "gold": "5000-9999 points (unlock dedicated manager)",
            "platinum": "10000+ points (VIP treatment)",
        },
        "referral_bonus_available": program.referral_bonus_available,
        "referral_reward": "$500 credit per qualified referral",
    }


@router.post("/trigger-retention-sequence/{user_id}/{sequence_type}")
async def trigger_retention_sequence(
    user_id: str,
    sequence_type: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger automated retention sequence - persiste la secuencia real."""
    steps = RETENTION_SEQUENCES.get(sequence_type, {})

    record = RetentionSequence(
        id=str(uuid.uuid4()),
        user_id=user_id,
        sequence_type=sequence_type,
        total_steps=5,
        step_1_message=steps.get("step_1"),
        step_2_message=steps.get("step_2"),
        step_3_message=steps.get("step_3"),
        step_4_message=steps.get("step_4"),
        step_5_message=steps.get("step_5"),
        started_at=datetime.now(timezone.utc),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "sequence_id": record.id,
        "user_id": user_id,
        "sequence_type": sequence_type,
        "total_steps": 5,
        "sequence": steps,
        "expected_engagement_lift": 0.45,
        "expected_churn_reduction": 0.65,
    }


@router.get("/loyalty-status/{user_id}")
async def get_loyalty_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get customer loyalty tier + progress - lee la fila real, 404 si nunca se inscribió."""
    result = await db.execute(select(LoyaltyProgram).where(LoyaltyProgram.user_id == user_id))
    program = result.scalars().first()
    if program is None:
        raise HTTPException(status_code=404, detail=f"user_id={user_id} no está inscripto en el programa de loyalty")

    progress = _progress_to_next_tier(program.points_balance)

    return {
        "user_id": user_id,
        "tier": program.tier,
        "points_balance": program.points_balance,
        "points_to_next_tier": progress["points_to_next_tier"],
        "progress_to_next_tier": round(progress["progress_to_next"], 2),
        "exclusive_perks_unlocked": program.exclusive_perks or [],
        "dedicated_account_manager": program.dedicated_account_manager,
        "referral_bonus_available": program.referral_bonus_available,
        "churn_risk_score": program.churn_risk_score,
    }


@router.post("/unlock-vip/{user_id}")
async def unlock_vip_tier(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upgrade high-value customer to VIP - actualiza la fila real a platinum."""
    program = await _get_or_create_program(db, user_id)

    vip_perks = [
        "24/7 priority support (dedicated Slack channel)",
        "Dedicated success manager + quarterly QBR",
        "Custom training & onboarding",
        "Early access to all new features",
        "Annual company visit & strategy session",
        "50% discount on add-ons & integrations",
        "Custom contract terms",
    ]

    program.tier = "platinum"
    program.exclusive_perks = vip_perks
    program.dedicated_account_manager = "VP of Customer Success"
    program.personal_success_plan = "Custom plan created"
    await db.commit()

    return {
        "user_id": user_id,
        "tier": program.tier,
        "vip_benefits": vip_perks,
        "personal_success_plan": program.personal_success_plan,
        "account_manager": program.dedicated_account_manager,
    }
