"""HR API — /api/v1/businesses/{business_id}/hr/*"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.hr.schemas import (
    CandidateCreate,
    CandidateOut,
    EmployeeOut,
    OfferCreate,
    OnboardingItemOut,
    PayrollCalcRequest,
    PayrollOut,
)
from app.domains.hr.service import OnboardingService, PayrollService, RecruitmentService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/hr", tags=["HR"])


# Recruitment
@router.post("/candidates", response_model=CandidateOut)
async def add_candidate(
    business_id: UUID,
    body: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RecruitmentService(db)
    return await svc.add_candidate(business_id, body.full_name, body.email, body.position, body.sourced_via)


@router.post("/candidates/{candidate_id}/score", response_model=CandidateOut)
async def score_candidate(
    business_id: UUID,
    candidate_id: UUID,
    score: float = Query(..., ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from decimal import Decimal
    svc = RecruitmentService(db)
    return await svc.score_screening(candidate_id, Decimal(str(score)))


@router.post("/candidates/{candidate_id}/offer", response_model=CandidateOut)
async def send_offer(
    business_id: UUID,
    candidate_id: UUID,
    body: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RecruitmentService(db)
    return await svc.send_offer(candidate_id, body.salary_aed)


@router.post("/candidates/{candidate_id}/accept", response_model=EmployeeOut)
async def accept_offer(
    business_id: UUID,
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RecruitmentService(db)
    return await svc.accept_offer(candidate_id)


# Onboarding
@router.post("/employees/{employee_id}/onboarding/init", response_model=list[OnboardingItemOut])
async def init_onboarding(
    business_id: UUID,
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = OnboardingService(db)
    return await svc.create_checklist(employee_id, business_id)


@router.post("/onboarding-items/{item_id}/complete", response_model=OnboardingItemOut)
async def complete_onboarding_item(
    business_id: UUID,
    item_id: UUID,
    notes: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = OnboardingService(db)
    return await svc.complete_item(item_id, notes)


@router.get("/employees/{employee_id}/onboarding/status")
async def onboarding_status(
    business_id: UUID,
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = OnboardingService(db)
    return await svc.onboarding_status(employee_id)


# Payroll
@router.post("/payroll", response_model=PayrollOut)
async def calculate_payroll(
    business_id: UUID,
    employee_id: UUID,
    payroll_date: date = Query(...),
    body: PayrollCalcRequest = PayrollCalcRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = PayrollService(db)
    return await svc.calculate_payroll(employee_id, payroll_date, body.allowances_aed)


@router.post("/payroll/batch")
async def batch_payroll(
    business_id: UUID,
    payroll_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = PayrollService(db)
    return await svc.process_payroll_batch(business_id, payroll_date)


@router.get("/payroll/summary")
async def payroll_summary(
    business_id: UUID,
    payroll_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = PayrollService(db)
    return await svc.payroll_summary(business_id, payroll_date)
