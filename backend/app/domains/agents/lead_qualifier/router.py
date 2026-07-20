"""Lead Qualifier Auto-Agent Router"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.lead_qualifier import service as lq_service
from app.domains.agents.lead_qualifier.schemas import (
    QualifyLeadOut,
    LeadQualificationOut,
    QualifyingQuestionOut,
    RouteLeadIn,
    RouteLeadOut,
)

router = APIRouter(prefix="/lead-qualifier", tags=["lead-qualifier"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/qualify/{conversation_id}", response_model=QualifyLeadOut)
async def qualify_lead(
    conversation_id: UUID,
    business_id: UUID = Query(...),
    customer_id: Optional[UUID] = Query(None),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Run BANT qualification on a conversation."""
    try:
        result = await lq_service.qualify_lead(
            db=db,
            conversation_id=conversation_id,
            business_id=business_id,
            customer_id=customer_id,
        )
        return QualifyLeadOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/leads", response_model=list[LeadQualificationOut])
async def list_leads(
    business_id: UUID = Query(...),
    min_score: float = Query(70.0, ge=0.0, le=100.0),
    limit: int = Query(100, ge=1, le=500),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """List qualified leads for a business."""
    leads = await lq_service.get_qualified_leads(db, business_id, min_score, limit)
    return leads


@router.get("/leads/{qualification_id}", response_model=LeadQualificationOut)
async def get_lead(
    qualification_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get qualification details for a lead."""
    lead = await lq_service.get_qualification(db, qualification_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado")
    return lead


@router.post("/leads/{qualification_id}/route", response_model=RouteLeadOut)
async def route_lead(
    qualification_id: UUID,
    data: RouteLeadIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Manually route a lead to a destination."""
    try:
        lead = await lq_service.route_lead(db, qualification_id, data.routing_destination)
        return RouteLeadOut(
            qualification_id=lead.id,
            routing_destination=lead.routing_destination or "",
            status=lead.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/question/{conversation_id}", response_model=QualifyingQuestionOut)
async def get_next_question(
    conversation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Suggest the next BANT question to ask."""
    question = await lq_service.ask_qualifying_question(db, conversation_id)
    # Infer dimension from question text
    dimension = "need"
    for dim, q_text in lq_service.BANT_QUESTIONS.items():
        if q_text == question:
            dimension = dim
            break
    return QualifyingQuestionOut(
        conversation_id=conversation_id,
        question=question,
        bant_dimension=dimension,
    )
