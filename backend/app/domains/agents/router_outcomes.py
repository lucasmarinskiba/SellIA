"""Conversation Outcomes Router

Endpoints for recording conversation outcomes, viewing stats,
and getting AI-suggested prompt improvements.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.prompt_optimizer import PromptOptimizer

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def record_outcome(
    conversation_id: UUID,
    agent_type: str,
    outcome: str,
    revenue: Optional[float] = None,
    confidence: float = 0.0,
    feedback: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record the outcome of a conversation."""
    optimizer = PromptOptimizer(db)
    record = await optimizer.record_outcome(
        conversation_id=conversation_id,
        agent_type=agent_type,
        outcome=outcome,
        revenue=revenue,
        confidence=confidence,
        feedback=feedback,
    )

    # Trigger self-reflection and causal analysis for closed/lost conversations
    if outcome in ("lost", "stalled", "objection_unresolved", "no_progress"):
        try:
            from app.domains.agents.reflection import SelfReflection
            from app.domains.agents.causal_engine import CausalAnalyzer

            reflection_result = await SelfReflection.reflect_on_conversation(db, conversation_id)
            if reflection_result:
                await SelfReflection.save_reflection(
                    db=db,
                    conversation_id=conversation_id,
                    agent_type=agent_type,
                    result=reflection_result,
                )

            analyzer = CausalAnalyzer(db)
            causal_result = await analyzer.analyze_failed_deal(conversation_id)
            if causal_result:
                from app.domains.channels.models import Conversation
                from sqlalchemy import select

                conv_result = await db.execute(
                    select(Conversation.business_id).where(Conversation.id == conversation_id)
                )
                business_id = conv_result.scalar_one_or_none()
                if business_id:
                    await analyzer.save_causal_analysis(
                        conversation_id=conversation_id,
                        business_id=business_id,
                        deal_outcome=outcome,
                        result=causal_result,
                    )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Post-outcome analysis failed: {e}")

    return {
        "id": record.id,
        "conversation_id": record.conversation_id,
        "agent_type": record.agent_type,
        "outcome": record.outcome,
        "revenue": float(record.revenue) if record.revenue is not None else None,
        "confidence": record.confidence,
        "feedback": record.feedback,
        "created_at": record.created_at,
    }


@router.get("/stats")
async def get_outcome_stats(
    agent_type: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get outcome statistics by agent type."""
    optimizer = PromptOptimizer(db)
    stats = await optimizer.analyze_prompt_effectiveness(agent_type, days=days)
    return stats


@router.get("/prompt-suggestions")
async def get_prompt_suggestions(
    agent_type: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-suggested prompt improvements based on failed conversations."""
    optimizer = PromptOptimizer(db)
    suggestions = await optimizer.suggest_prompt_improvements(agent_type, days=days)
    return {"agent_type": agent_type, "suggestions": suggestions}
