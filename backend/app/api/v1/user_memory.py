"""User Memory API — Endpoints para gestionar memoria persistente del usuario"""

from uuid import UUID
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.user_memory.service import UserMemoryService
from app.domains.user_memory.schemas import (
    UserMemoryResponse,
    UserMemoryUpdate,
    UserMemoryEventCreate,
    UserMemoryEventResponse,
    UserPreferenceUpdate,
    UserPreferenceResponse,
)

router = APIRouter()


@router.get("/me", response_model=UserMemoryResponse)
async def get_my_memory(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get memoria del usuario actual"""
    service = UserMemoryService(db)
    memory = await service.get_or_create(current_user.id)

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


@router.patch("/me", response_model=UserMemoryResponse)
async def update_my_memory(
    update_data: UserMemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update memoria del usuario actual"""
    service = UserMemoryService(db)
    memory = await service.update_memory(current_user.id, update_data)

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


@router.post("/events", response_model=UserMemoryEventResponse, status_code=status.HTTP_201_CREATED)
async def log_memory_event(
    event: UserMemoryEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Log un evento de memoria (mensaje enviado, acción tomada, etc.)"""
    service = UserMemoryService(db)
    logged_event = await service.log_event(current_user.id, event)

    return UserMemoryEventResponse(
        id=str(logged_event.id),
        user_id=str(logged_event.user_id),
        event_type=logged_event.event_type,
        event_data=logged_event.event_data or {},
        conversation_id=str(logged_event.conversation_id) if logged_event.conversation_id else None,
        business_id=str(logged_event.business_id) if logged_event.business_id else None,
        agent_id=str(logged_event.agent_id) if logged_event.agent_id else None,
        created_at=logged_event.created_at,
    )


@router.post("/interests/{interest}", response_model=UserMemoryResponse)
async def add_interest(
    interest: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Agregar un interés a la memoria del usuario"""
    service = UserMemoryService(db)
    memory = await service.add_interest(current_user.id, interest)

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


@router.post("/challenges/{challenge}", response_model=UserMemoryResponse)
async def add_challenge(
    challenge: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Agregar un desafío a la memoria del usuario"""
    service = UserMemoryService(db)
    memory = await service.add_challenge(current_user.id, challenge)

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


@router.post("/preferences", response_model=UserPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def set_preference(
    pref_data: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Guardar una preferencia granular del usuario"""
    service = UserMemoryService(db)
    pref = await service.set_preference(current_user.id, pref_data.preference_key, pref_data.preference_value)

    return UserPreferenceResponse(
        id=str(pref.id),
        user_id=str(pref.user_id),
        preference_key=pref.preference_key,
        preference_value=pref.preference_value or {},
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )


@router.get("/preferences/{preference_key}", response_model=Optional[UserPreferenceResponse])
async def get_preference(
    preference_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtener una preferencia granular del usuario"""
    service = UserMemoryService(db)
    pref = await service.get_preference(current_user.id, preference_key)

    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")

    return UserPreferenceResponse(
        id=str(pref.id),
        user_id=str(pref.user_id),
        preference_key=pref.preference_key,
        preference_value=pref.preference_value or {},
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )


@router.get("/events", response_model=List[UserMemoryEventResponse])
async def get_recent_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtener eventos recientes de la memoria del usuario"""
    service = UserMemoryService(db)
    events = await service.get_recent_events(current_user.id, limit=limit)

    return [
        UserMemoryEventResponse(
            id=str(e.id),
            user_id=str(e.user_id),
            event_type=e.event_type,
            event_data=e.event_data or {},
            conversation_id=str(e.conversation_id) if e.conversation_id else None,
            business_id=str(e.business_id) if e.business_id else None,
            agent_id=str(e.agent_id) if e.agent_id else None,
            created_at=e.created_at,
        )
        for e in events
    ]
