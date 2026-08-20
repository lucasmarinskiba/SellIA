"""Loyalty program API — customer retention + rewards."""

from uuid import UUID
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.loyalty.loyalty_service import LoyaltyProgramService

router = APIRouter(prefix="/api/v1", tags=["loyalty-program"])


class CreateProgramRequest(BaseModel):
    name: str
    points_per_dollar: Decimal = Decimal("1.0")
    welcome_bonus: int = 50


class EnrollMemberRequest(BaseModel):
    customer_id: UUID
    loyalty_program_id: UUID


class AwardPointsRequest(BaseModel):
    member_id: UUID
    points: int
    transaction_type: str = "earn"
    description: Optional[str] = None
    order_id: Optional[str] = None


class RedeemRewardRequest(BaseModel):
    member_id: UUID
    reward_id: UUID


class CreateRewardRequest(BaseModel):
    reward_name: str
    reward_type: str
    points_required: int
    value: Optional[Decimal] = None


@router.post("/businesses/{business_id}/loyalty-program")
def create_loyalty_program(
    business_id: UUID,
    request: CreateProgramRequest,
    db: Session = Depends(get_db)
):
    """Create loyalty program."""
    return LoyaltyProgramService.create_loyalty_program(
        business_id=business_id,
        name=request.name,
        points_per_dollar=request.points_per_dollar,
        welcome_bonus=request.welcome_bonus,
        db=db
    )


@router.post("/loyalty-program/enroll")
def enroll_member(
    business_id: UUID = Query(...),
    request: EnrollMemberRequest = None,
    db: Session = Depends(get_db)
):
    """Enroll customer in loyalty program."""
    return LoyaltyProgramService.enroll_member(
        business_id=business_id,
        customer_id=request.customer_id,
        loyalty_program_id=request.loyalty_program_id,
        db=db
    )


@router.post("/loyalty/points/award")
def award_points(
    business_id: UUID = Query(...),
    request: AwardPointsRequest = None,
    db: Session = Depends(get_db)
):
    """Award points to member."""
    return LoyaltyProgramService.award_points(
        member_id=request.member_id,
        business_id=business_id,
        points=request.points,
        transaction_type=request.transaction_type,
        description=request.description,
        order_id=request.order_id,
        db=db
    )


@router.post("/loyalty/rewards/redeem")
def redeem_reward(
    business_id: UUID = Query(...),
    request: RedeemRewardRequest = None,
    db: Session = Depends(get_db)
):
    """Redeem reward for member."""
    return LoyaltyProgramService.redeem_reward(
        member_id=request.member_id,
        reward_id=request.reward_id,
        business_id=business_id,
        db=db
    )


@router.post("/loyalty-program/{program_id}/rewards")
def create_reward_offer(
    program_id: UUID,
    business_id: UUID = Query(...),
    request: CreateRewardRequest = None,
    db: Session = Depends(get_db)
):
    """Create reward offer."""
    return LoyaltyProgramService.create_reward_offer(
        loyalty_program_id=program_id,
        business_id=business_id,
        reward_name=request.reward_name,
        reward_type=request.reward_type,
        points_required=request.points_required,
        value=request.value,
        db=db
    )


@router.get("/loyalty/members/{member_id}")
def get_member_details(
    member_id: UUID,
    db: Session = Depends(get_db)
):
    """Get member profile + points balance."""
    return LoyaltyProgramService.get_member_details(
        member_id=member_id,
        db=db
    )


@router.get("/businesses/{business_id}/loyalty-metrics")
def get_loyalty_metrics(
    business_id: UUID,
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Get loyalty program metrics."""
    return LoyaltyProgramService.calculate_loyalty_metrics(
        business_id=business_id,
        date=date,
        db=db
    )
