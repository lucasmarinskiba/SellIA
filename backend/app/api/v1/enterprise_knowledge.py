"""Conversation pattern insights -- business-facing API.

Real pattern analysis over a business's own won/lost deal conversations
(app.domains.enterprise.knowledge_base.ConversationPatternAnalyzer). Replaces
the previous "knowledge base" mock -- manual note-taking with a fabricated
confidence_score=random.uniform(60, 95) and estimated_impact=
random.randint(5, 25) -- with real counts: message volume, time to close,
and word frequency, compared between conversations that closed a deal and
ones that didn't. No ML/embeddings, per the product decision this replaces
(simple pattern counts, not real learning).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.enterprise.knowledge_base import ConversationPatternAnalyzer

router = APIRouter(tags=["knowledge"])


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id, Business.user_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.get("/knowledge/patterns/{business_id}")
async def get_win_loss_patterns(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare conversations that led to a won deal vs a lost one: message
    volume, time to close, and win rate by which sales-agent voice/personality
    was used (from the A/B testing engine's assignment tracking, when present)."""
    await _get_business_for_user(business_id, current_user, db)
    patterns = await ConversationPatternAnalyzer.get_win_loss_patterns(db, business_id)
    return {"business_id": str(business_id), "patterns": patterns}


@router.get("/knowledge/winning-phrases/{business_id}")
async def get_winning_phrases(
    business_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Word-frequency count of the sales agent's own messages in won vs lost
    conversations -- what words show up more often in conversations that
    closed. Real counts, not a language model."""
    await _get_business_for_user(business_id, current_user, db)
    phrases = await ConversationPatternAnalyzer.get_winning_phrases(db, business_id, limit)
    return {"business_id": str(business_id), "phrases": phrases}


@router.get("/knowledge/summary/{business_id}")
async def get_summary(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Combined dashboard view: win/loss patterns + top winning/losing phrases."""
    await _get_business_for_user(business_id, current_user, db)
    patterns = await ConversationPatternAnalyzer.get_win_loss_patterns(db, business_id)
    phrases = await ConversationPatternAnalyzer.get_winning_phrases(db, business_id, limit=10)
    return {"business_id": str(business_id), "patterns": patterns, "phrases": phrases}
