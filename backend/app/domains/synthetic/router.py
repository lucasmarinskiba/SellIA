"""
Synthetic Monitoring API

Admin endpoints for health monitoring and uptime checks.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.synthetic import service as synthetic_service

router = APIRouter(prefix="/synthetic", tags=["synthetic"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/health")
async def get_health(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get latest synthetic health snapshot."""
    snapshot = await synthetic_service.get_latest_health(db)
    if not snapshot:
        return {"status": "unknown", "message": "No checks run yet"}
    return {
        "overall_status": snapshot.overall_status,
        "checks_total": snapshot.checks_total,
        "checks_passed": snapshot.checks_passed,
        "avg_response_time_ms": snapshot.avg_response_time_ms,
        "details": snapshot.details,
        "snapshot_at": snapshot.snapshot_at,
    }


@router.post("/run-checks")
async def run_checks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Manually trigger all synthetic checks (admin only)."""
    snapshot = await synthetic_service.run_all_checks(db)
    return {
        "overall_status": snapshot.overall_status,
        "checks_total": snapshot.checks_total,
        "checks_passed": snapshot.checks_passed,
    }
