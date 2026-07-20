"""
Competitive Service
"""

import uuid
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.domains.competitive.models import CompetitiveBattlecard


async def list_battlecards(db: AsyncSession, user_id: uuid.UUID) -> List[CompetitiveBattlecard]:
    result = await db.execute(
        select(CompetitiveBattlecard)
        .where(CompetitiveBattlecard.user_id == user_id)
        .order_by(desc(CompetitiveBattlecard.created_at))
    )
    return result.scalars().all()


async def get_battlecard(db: AsyncSession, battlecard_id: uuid.UUID, user_id: uuid.UUID) -> Optional[CompetitiveBattlecard]:
    result = await db.execute(
        select(CompetitiveBattlecard).where(
            CompetitiveBattlecard.id == battlecard_id,
            CompetitiveBattlecard.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_battlecard(db: AsyncSession, user_id: uuid.UUID, data: dict) -> CompetitiveBattlecard:
    battlecard = CompetitiveBattlecard(user_id=user_id, **data)
    db.add(battlecard)
    await db.commit()
    await db.refresh(battlecard)
    return battlecard


async def update_battlecard(db: AsyncSession, battlecard: CompetitiveBattlecard, data: dict) -> CompetitiveBattlecard:
    for field, value in data.items():
        if value is not None and hasattr(battlecard, field):
            setattr(battlecard, field, value)
    await db.commit()
    await db.refresh(battlecard)
    return battlecard


async def delete_battlecard(db: AsyncSession, battlecard: CompetitiveBattlecard) -> None:
    await db.delete(battlecard)
    await db.commit()


async def get_comparison_data(battlecard: CompetitiveBattlecard) -> dict:
    """Return structured comparison data for a battlecard."""
    our_score = len(battlecard.our_strengths or []) - len(battlecard.our_weaknesses or [])
    their_score = len(battlecard.their_strengths or []) - len(battlecard.their_weaknesses or [])

    return {
        "competitor_name": battlecard.competitor_name,
        "competitor_url": battlecard.competitor_url,
        "our_strengths": battlecard.our_strengths or [],
        "our_weaknesses": battlecard.our_weaknesses or [],
        "their_strengths": battlecard.their_strengths or [],
        "their_weaknesses": battlecard.their_weaknesses or [],
        "price_comparison": battlecard.price_comparison,
        "feature_comparison": battlecard.feature_comparison or {},
        "market_share_estimate": battlecard.market_share_estimate,
        "notes": battlecard.notes,
        "comparison_summary": {
            "our_net_score": our_score,
            "their_net_score": their_score,
            "advantage": "us" if our_score > their_score else "them" if their_score > our_score else "tie",
            "strength_gap": abs(our_score - their_score),
        },
    }
