"""Proactive Outreach Engine API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.proactive.service import ProactiveService
from app.domains.proactive.schemas import (
    OutreachOpportunityResponse,
    OutreachRuleCreate,
    OutreachRuleUpdate,
    OutreachRuleResponse,
)

router = APIRouter(prefix="/proactive", tags=["proactive"])


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------

@router.get("/opportunities", response_model=list[OutreachOpportunityResponse])
async def list_opportunities(
    business_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProactiveService(db)
    opportunities = await service.list_opportunities(
        business_id=business_id,
        status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return opportunities


@router.post("/opportunities/{opportunity_id}/send")
async def send_opportunity_now(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProactiveService(db)
    result = await service.execute_outreach(opportunity_id)
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["detail"],
        )
    return result


@router.post("/opportunities/{opportunity_id}/dismiss", response_model=OutreachOpportunityResponse)
async def dismiss_opportunity(
    opportunity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProactiveService(db)
    opp = await service.dismiss_opportunity(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@router.get("/rules", response_model=list[OutreachRuleResponse])
async def list_rules(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProactiveService(db)
    rules = await service.list_rules(business_id, active_only=False)
    return rules


@router.post("/rules", response_model=OutreachRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    business_id: UUID,
    data: OutreachRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProactiveService(db)
    rule = await service.create_rule(
        business_id=business_id,
        rule_data=data.model_dump(),
    )
    return rule


@router.patch("/rules/{rule_id}", response_model=OutreachRuleResponse)
async def update_rule(
    rule_id: UUID,
    data: OutreachRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProactiveService(db)
    update_dict = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    rule = await service.update_rule(rule_id, update_dict)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule
