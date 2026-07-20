"""Intelligence API Router."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.intelligence.models import MessageAnalysis, ConversationIntelligence
from app.domains.intelligence.schemas import (
    MessageAnalysisResponse,
    ConversationIntelligenceResponse,
    ConversationIntelligenceFilter,
)
from app.domains.intelligence.service import MessageIntelligenceService, ConversationIntelligenceService

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/message-analysis/{message_id}", response_model=MessageAnalysisResponse)
async def get_message_analysis(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MessageAnalysis).where(MessageAnalysis.message_id == message_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return MessageAnalysisResponse.model_validate(analysis)


@router.get("/conversation/{conversation_id}", response_model=ConversationIntelligenceResponse)
async def get_conversation_intelligence(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationIntelligenceService(db)
    intel = await service.get_by_conversation(conversation_id)
    if not intel:
        raise HTTPException(status_code=404, detail="Intelligence not found")
    return ConversationIntelligenceResponse.model_validate(intel)


@router.get("/hot-leads/{business_id}", response_model=list[ConversationIntelligenceResponse])
async def get_hot_leads(
    business_id: UUID,
    min_readiness: int = 60,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationIntelligenceService(db)
    leads = await service.get_hot_leads(business_id, min_readiness)
    return [ConversationIntelligenceResponse.model_validate(l) for l in leads]


@router.get("/at-risk/{business_id}", response_model=list[ConversationIntelligenceResponse])
async def get_at_risk_conversations(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationIntelligenceService(db)
    conversations = await service.get_at_risk_conversations(business_id)
    return [ConversationIntelligenceResponse.model_validate(c) for c in conversations]


@router.post("/analyze/{message_id}", response_model=MessageAnalysisResponse)
async def analyze_message_manual(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MessageIntelligenceService(db)
    analysis = await service.analyze_message(message_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Message not found or already analyzed")
    return MessageAnalysisResponse.model_validate(analysis)
