"""
Lead Progression Endpoints
- Manual status change (testing)
- No-engagement timeout checks
- Workflow progression monitoring
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.db.models import Lead, WorkflowExecution
from app.services.progression_service import get_progression_service

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/progression", tags=["progression"])

# ============================================================
# ENDPOINTS
# ============================================================
@router.post("/{lead_id}/status")
async def change_lead_status(
    lead_id: int,
    new_status: str,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Manually change lead status (testing/admin)."""
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await session.execute(stmt)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    old_status = lead.status
    lead.status = new_status
    await session.commit()

    logger.info(f"Status changed: {lead_id} {old_status} → {new_status}")

    return {
        "lead_id": lead_id,
        "old_status": old_status,
        "new_status": new_status,
        "updated_at": lead.updated_at.isoformat()
    }

@router.post("/{lead_id}/no-engagement-check")
async def check_no_engagement(
    lead_id: int,
    days_threshold: int = 7,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Check if lead has no engagement for X days."""
    service = await get_progression_service()

    has_timeout = await service.check_no_engagement_timeout(
        session,
        lead_id,
        days_threshold
    )

    stmt = select(Lead).where(Lead.id == lead_id)
    result = await session.execute(stmt)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {
        "lead_id": lead_id,
        "status": lead.status,
        "last_contacted": lead.last_contacted.isoformat() if lead.last_contacted else None,
        "no_engagement_timeout_triggered": has_timeout,
        "threshold_days": days_threshold,
        "days_since_contact": (
            (datetime.now() - lead.last_contacted).days if lead.last_contacted else None
        )
    }

@router.post("/{lead_id}/trigger-no-engagement")
async def trigger_no_engagement_email(
    lead_id: int,
    workflow_id: int,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Trigger no-engagement email sequence."""
    service = await get_progression_service()

    try:
        from app.core.scheduler import get_scheduler
        scheduler = await get_scheduler()

        result = await service.trigger_no_engagement_sequence(
            session,
            lead_id,
            workflow_id,
            scheduler
        )

        return {
            "status": "ok",
            "result": result
        }

    except Exception as e:
        logger.error(f"No-engagement trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{lead_id}/workflow-executions")
async def get_lead_executions(
    lead_id: int,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Get all workflow executions for lead."""
    stmt = select(WorkflowExecution).where(
        WorkflowExecution.lead_id == lead_id
    ).order_by(WorkflowExecution.created_at.desc())

    result = await session.execute(stmt)
    executions = result.scalars().all()

    return {
        "lead_id": lead_id,
        "executions": [
            {
                "id": e.id,
                "workflow_id": e.workflow_id,
                "step_number": e.step_number,
                "email_status": e.email_status,
                "sent_at": e.sent_at.isoformat() if e.sent_at else None,
                "opened_at": e.opened_at.isoformat() if e.opened_at else None,
                "clicked_at": e.clicked_at.isoformat() if e.clicked_at else None,
                "created_at": e.created_at.isoformat()
            }
            for e in executions
        ],
        "total": len(executions)
    }

# ============================================================
# TESTING / SIMULATION
# ============================================================
@router.post("/{lead_id}/simulate-open")
async def simulate_email_opened(
    lead_id: int,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Simulate email open (for testing)."""
    service = await get_progression_service()

    stmt = select(WorkflowExecution).where(
        WorkflowExecution.lead_id == lead_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(1)

    result = await session.execute(stmt)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="No execution found")

    try:
        await service.on_email_opened(session, execution.id, lead_id)
        return {
            "status": "ok",
            "event": "email_opened",
            "lead_id": lead_id,
            "execution_id": execution.id
        }
    except Exception as e:
        logger.error(f"Simulate open failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{lead_id}/simulate-click")
async def simulate_email_clicked(
    lead_id: int,
    url: str = "https://example.com",
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Simulate email click (for testing)."""
    service = await get_progression_service()

    stmt = select(WorkflowExecution).where(
        WorkflowExecution.lead_id == lead_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(1)

    result = await session.execute(stmt)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="No execution found")

    try:
        await service.on_email_clicked(session, execution.id, lead_id, url)
        return {
            "status": "ok",
            "event": "email_clicked",
            "lead_id": lead_id,
            "execution_id": execution.id,
            "url": url
        }
    except Exception as e:
        logger.error(f"Simulate click failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{lead_id}/simulate-bounce")
async def simulate_email_bounced(
    lead_id: int,
    reason: str = "hard_bounce",
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Simulate email bounce (for testing)."""
    service = await get_progression_service()

    try:
        await service.on_email_bounced(session, lead_id, reason)
        return {
            "status": "ok",
            "event": "email_bounced",
            "lead_id": lead_id,
            "reason": reason
        }
    except Exception as e:
        logger.error(f"Simulate bounce failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Import for datetime
from datetime import datetime
