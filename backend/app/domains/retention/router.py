"""Retention & Loyalty API Router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.retention.models import ReferralProgram, NpsCampaign, CustomerSegment
from app.domains.retention.schemas import (
    ReferralProgramCreate, ReferralProgramResponse, ReferralCodeResponse,
    NpsCampaignCreate, NpsCampaignResponse, NpsScoreResponse,
    CustomerSegmentResponse,
)
from app.domains.retention.services import RetentionService

router = APIRouter(prefix="/{business_id}/retention", tags=["Retention & Loyalty"])


@router.post("/referral-programs", response_model=ReferralProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_referral_program(
    business_id: UUID,
    prog_in: ReferralProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prog = ReferralProgram(business_id=business_id, **prog_in.model_dump())
    db.add(prog)
    await db.commit()
    await db.refresh(prog)
    return prog


@router.get("/referral-programs", response_model=list[ReferralProgramResponse])
async def list_referral_programs(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ReferralProgram).where(ReferralProgram.business_id == business_id, ReferralProgram.is_active == True))
    return result.scalars().all()


@router.post("/nps-campaigns", response_model=NpsCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_nps_campaign(
    business_id: UUID,
    camp_in: NpsCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RetentionService(db)
    camp = await service.create_nps_campaign(business_id=business_id, **camp_in.model_dump())
    return camp


@router.get("/nps-score", response_model=NpsScoreResponse)
async def get_nps_score(
    business_id: UUID,
    campaign_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RetentionService(db)
    return await service.get_nps_score(business_id, campaign_id)


@router.get("/segments", response_model=list[CustomerSegmentResponse])
async def get_customer_segments(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(CustomerSegment).where(CustomerSegment.business_id == business_id, CustomerSegment.is_active == True))
    return result.scalars().all()


@router.post("/calculate-rfm")
async def calculate_rfm(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RetentionService(db)
    await service.calculate_rfm_for_business(business_id)
    return {"status": "RFM calculated"}
