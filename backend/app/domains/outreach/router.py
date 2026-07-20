"""Outreach Cadence API Router."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.outreach.models import OutreachCadenceRule, ContactFatigueScore, OutreachLog
from app.domains.outreach.schemas import (
    OutreachCadenceRuleResponse,
    OutreachCadenceRuleCreate,
    OutreachCadenceRuleUpdate,
    ContactFatigueScoreResponse,
    OutreachLogResponse,
    CanContactRequest,
    CanContactResponse,
    CadenceNextActionResponse,
)
from app.domains.outreach.service import FatigueScoringService, CadenceEngine

router = APIRouter(prefix="/outreach", tags=["Outreach Cadence"])


# ---------------------------------------------------------------------------
# Cadence Rules
# ---------------------------------------------------------------------------

@router.get("/rules/{business_id}", response_model=OutreachCadenceRuleResponse)
async def get_cadence_rule(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FatigueScoringService(db)
    rule = await service.get_or_create_rule(business_id)
    return OutreachCadenceRuleResponse.model_validate(rule)


@router.patch("/rules/{business_id}", response_model=OutreachCadenceRuleResponse)
async def update_cadence_rule(
    business_id: UUID,
    update: OutreachCadenceRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FatigueScoringService(db)
    rule = await service.get_or_create_rule(business_id)

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)
    return OutreachCadenceRuleResponse.model_validate(rule)


# ---------------------------------------------------------------------------
# Fatigue Scores
# ---------------------------------------------------------------------------

@router.get("/fatigue/{business_id}", response_model=list[ContactFatigueScoreResponse])
async def list_fatigue_scores(
    business_id: UUID,
    level: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ContactFatigueScore).where(ContactFatigueScore.business_id == business_id)
    if level:
        query = query.where(ContactFatigueScore.fatigue_level == level)
    query = query.order_by(desc(ContactFatigueScore.updated_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    scores = result.scalars().all()
    return [ContactFatigueScoreResponse.model_validate(s) for s in scores]


@router.get("/fatigue/{business_id}/{conversation_id}", response_model=ContactFatigueScoreResponse)
async def get_fatigue_score(
    business_id: UUID,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FatigueScoringService(db)
    score = await service.get_or_create_score(business_id, conversation_id)
    return ContactFatigueScoreResponse.model_validate(score)


# ---------------------------------------------------------------------------
# Can Contact?
# ---------------------------------------------------------------------------

@router.post("/can-contact", response_model=CanContactResponse)
async def can_contact(
    req: CanContactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FatigueScoringService(db)
    # Need business_id from conversation
    from app.domains.channels.models import Conversation
    conv_result = await db.execute(select(Conversation).where(Conversation.id == req.conversation_id))
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await service.can_contact_now(conv.business_id, req.conversation_id, req.channel, req.message_type)
    return CanContactResponse(
        can_contact=result["can_contact"],
        reason=result["reason"],
        recommended_channel=result.get("recommended_channel"),
        recommended_wait_hours=result.get("recommended_wait_hours"),
        fatigue_level=result["fatigue_level"],
        contacts_this_week=result["contacts_this_week"],
        ai_recommendation=result.get("ai_recommendation"),
    )


# ---------------------------------------------------------------------------
# Next Action
# ---------------------------------------------------------------------------

@router.get("/next-action/{business_id}/{conversation_id}", response_model=CadenceNextActionResponse)
async def get_next_action(
    business_id: UUID,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = CadenceEngine(db)
    result = await engine.get_next_action_for_lead(business_id, conversation_id)
    return CadenceNextActionResponse(
        conversation_id=conversation_id,
        recommended_action=result["recommended_action"],
        recommended_channel=result.get("recommended_channel"),
        recommended_message_type=result.get("recommended_message_type"),
        recommended_delay_hours=result.get("recommended_delay_hours"),
        reason=result["reason"],
        fatigue_level=result["fatigue_level"],
    )


# ---------------------------------------------------------------------------
# Outreach Logs
# ---------------------------------------------------------------------------

@router.get("/logs/{business_id}", response_model=list[OutreachLogResponse])
async def list_outreach_logs(
    business_id: UUID,
    conversation_id: UUID | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(OutreachLog).where(OutreachLog.business_id == business_id)
    if conversation_id:
        query = query.where(OutreachLog.conversation_id == conversation_id)
    query = query.order_by(desc(OutreachLog.sent_at)).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [OutreachLogResponse.model_validate(log) for log in logs]
