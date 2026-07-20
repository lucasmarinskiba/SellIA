"""Reflection and Chain-of-Thought Router

Endpoints for viewing and triggering self-reflections and chain-of-thought logs.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.reflection import SelfReflection, ChainOfThought
from app.domains.agents.models_reflection import AgentReflection, ChainOfThoughtLog

router = APIRouter(prefix="/reflections", tags=["reflection"])


@router.get("/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_reflection(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the self-reflection for a conversation."""
    result = await db.execute(
        select(AgentReflection)
        .where(AgentReflection.conversation_id == conversation_id)
        .order_by(AgentReflection.created_at.desc())
    )
    reflection = result.scalars().first()
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    return {
        "id": reflection.id,
        "conversation_id": reflection.conversation_id,
        "agent_type": reflection.agent_type,
        "what_went_well": reflection.what_went_well,
        "what_could_improve": reflection.what_could_improve,
        "customer_insights": reflection.customer_insights,
        "future_recommendations": reflection.future_recommendations,
        "score": reflection.score,
        "created_at": reflection.created_at,
    }


@router.post("/{conversation_id}/generate", status_code=status.HTTP_201_CREATED)
async def generate_reflection(
    conversation_id: UUID,
    agent_type: str = "sellia",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger self-reflection generation for a conversation."""
    result = await SelfReflection.reflect_on_conversation(db, conversation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate reflection (no transcript or LLM unavailable)",
        )

    record = await SelfReflection.save_reflection(
        db=db,
        conversation_id=conversation_id,
        agent_type=agent_type,
        result=result,
    )
    return {
        "id": record.id,
        "conversation_id": record.conversation_id,
        "agent_type": record.agent_type,
        "what_went_well": record.what_went_well,
        "what_could_improve": record.what_could_improve,
        "customer_insights": record.customer_insights,
        "future_recommendations": record.future_recommendations,
        "score": record.score,
        "created_at": record.created_at,
    }


@router.get("/thoughts/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_thought_logs(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chain-of-thought logs for a conversation."""
    result = await db.execute(
        select(ChainOfThoughtLog)
        .where(ChainOfThoughtLog.conversation_id == conversation_id)
        .order_by(ChainOfThoughtLog.created_at.desc())
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "conversation_id": log.conversation_id,
            "message_id": log.message_id,
            "thought_steps": log.thought_steps,
            "created_at": log.created_at,
        }
        for log in logs
    ]
