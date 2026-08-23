"""User Memory API - Minimal implementation"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token
from app.domains.users.models import User
from app.domains.user_memory.service import UserMemoryService
from app.domains.user_memory.schemas import UserMemoryResponse

router = APIRouter()


async def get_user_from_token(authorization: str = Header(None)) -> str:
    """Extract user_id from Bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization[7:]
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload["sub"]


@router.get("/me")
async def get_my_memory(
    user_id: str = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Get user memory"""
    try:
        service = UserMemoryService(db)
        memory = await service.get_or_create(user_id)

        return UserMemoryResponse(
            id=str(memory.id),
            user_id=str(memory.user_id),
            preferred_language=memory.preferred_language,
            preferred_tone=memory.preferred_tone,
            industry_focus=memory.industry_focus,
            business_stage=memory.business_stage,
            primary_business_type=memory.primary_business_type,
            target_audience_summary=memory.target_audience_summary,
            key_challenges=memory.key_challenges or [],
            key_interests=memory.key_interests or [],
            technologies_used=memory.technologies_used or [],
            total_conversations=memory.total_conversations,
            total_messages=memory.total_messages,
            favorite_agents=memory.favorite_agents or [],
            frequently_asked_topics=memory.frequently_asked_topics or [],
            engagement_score=memory.engagement_score,
            satisfaction_score=memory.satisfaction_score,
            churn_risk_score=memory.churn_risk_score,
            lifetime_value_estimate=memory.lifetime_value_estimate,
            last_active_business_id=str(memory.last_active_business_id) if memory.last_active_business_id else None,
            last_active_conversation_id=str(memory.last_active_conversation_id) if memory.last_active_conversation_id else None,
            last_active_agent_id=str(memory.last_active_agent_id) if memory.last_active_agent_id else None,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            last_activity_at=memory.last_activity_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.patch("/me")
async def update_my_memory(
    data: dict,
    user_id: str = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Update user memory"""
    try:
        from app.domains.user_memory.schemas import UserMemoryUpdate

        service = UserMemoryService(db)
        update_data = UserMemoryUpdate(**data)
        memory = await service.update_memory(user_id, update_data)

        return UserMemoryResponse(
            id=str(memory.id),
            user_id=str(memory.user_id),
            preferred_language=memory.preferred_language,
            preferred_tone=memory.preferred_tone,
            industry_focus=memory.industry_focus,
            business_stage=memory.business_stage,
            primary_business_type=memory.primary_business_type,
            target_audience_summary=memory.target_audience_summary,
            key_challenges=memory.key_challenges or [],
            key_interests=memory.key_interests or [],
            technologies_used=memory.technologies_used or [],
            total_conversations=memory.total_conversations,
            total_messages=memory.total_messages,
            favorite_agents=memory.favorite_agents or [],
            frequently_asked_topics=memory.frequently_asked_topics or [],
            engagement_score=memory.engagement_score,
            satisfaction_score=memory.satisfaction_score,
            churn_risk_score=memory.churn_risk_score,
            lifetime_value_estimate=memory.lifetime_value_estimate,
            last_active_business_id=str(memory.last_active_business_id) if memory.last_active_business_id else None,
            last_active_conversation_id=str(memory.last_active_conversation_id) if memory.last_active_conversation_id else None,
            last_active_agent_id=str(memory.last_active_agent_id) if memory.last_active_agent_id else None,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            last_activity_at=memory.last_activity_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
