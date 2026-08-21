"""Acquisition Orchestrator API: X9→X10→X12→X11 funnel automation."""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.acquisition_orchestrator.service import AcquisitionOrchestrator


router = APIRouter(prefix="/api/v1/acquisition-orchestrator", tags=["acquisition-orchestrator"])


@router.post("/run-full-sequence")
async def run_full_acquisition_sequence(
    user_data: dict = Body(...),
    engagement_data: dict = Body(...),
    company_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Execute complete X9→X10→X12→X11 acquisition funnel."""
    return await AcquisitionOrchestrator.run_full_acquisition_sequence(
        user_data, engagement_data, company_data
    )


@router.get("/orchestrator-status/{user_id}")
async def get_orchestrator_status(user_id: str) -> dict:
    """Get real-time status of user's acquisition journey."""
    return AcquisitionOrchestrator.get_orchestrator_status(user_id)


@router.get("/funnel-health")
async def get_funnel_health() -> dict:
    """Get system-wide acquisition metrics."""
    return AcquisitionOrchestrator.calculate_funnel_health()
