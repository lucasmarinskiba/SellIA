"""
Analytics Endpoints
- Funnel metrics
- Email performance
- Lead source ROI
- Workflow performance
- Lead health segmentation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db import get_db
from app.services.analytics_service import get_analytics_service

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# ============================================================
# ENDPOINTS
# ============================================================
@router.get("/funnel")
async def get_funnel(session: AsyncSession = Depends(get_db)) -> dict:
    """Sales funnel: new → contacted → engaged → qualified → won."""
    try:
        service = await get_analytics_service()
        funnel = await service.get_lead_funnel(session)
        return {"status": "ok", "data": funnel}
    except Exception as e:
        logger.error(f"Funnel error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email-metrics")
async def get_email_metrics(session: AsyncSession = Depends(get_db)) -> dict:
    """Email delivery: sent, delivered, open rate, click rate."""
    try:
        service = await get_analytics_service()
        metrics = await service.get_email_metrics(session)
        return {"status": "ok", "data": metrics}
    except Exception as e:
        logger.error(f"Email metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lead-sources")
async def get_lead_source_analytics(session: AsyncSession = Depends(get_db)) -> dict:
    """Lead source ROI: leads, engagement, conversion by source."""
    try:
        service = await get_analytics_service()
        analytics = await service.get_lead_source_analytics(session)
        return {"status": "ok", "data": analytics}
    except Exception as e:
        logger.error(f"Lead source analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow-performance")
async def get_workflow_performance(session: AsyncSession = Depends(get_db)) -> dict:
    """Workflow step performance: open rates, click rates, bounce rates."""
    try:
        service = await get_analytics_service()
        performance = await service.get_workflow_performance(session)
        return {"status": "ok", "data": performance}
    except Exception as e:
        logger.error(f"Workflow performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lead-score-distribution")
async def get_lead_score_distribution(session: AsyncSession = Depends(get_db)) -> dict:
    """Lead score histogram: distribution by score buckets."""
    try:
        service = await get_analytics_service()
        distribution = await service.get_lead_score_distribution(session)
        return {"status": "ok", "data": distribution}
    except Exception as e:
        logger.error(f"Score distribution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/time-series")
async def get_time_series(
    days: int = 30,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Time series: leads created and emails sent per day."""
    try:
        service = await get_analytics_service()
        metrics = await service.get_time_series_metrics(session, days)
        return {"status": "ok", "data": metrics}
    except Exception as e:
        logger.error(f"Time series error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lead-health")
async def get_lead_health(session: AsyncSession = Depends(get_db)) -> dict:
    """Lead segmentation: hot, warm, cold, dead leads."""
    try:
        service = await get_analytics_service()
        health = await service.get_lead_health_scores(session)
        return {"status": "ok", "data": health}
    except Exception as e:
        logger.error(f"Lead health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_analytics_summary(session: AsyncSession = Depends(get_db)) -> dict:
    """Complete dashboard: funnel, email, sources, workflows, health."""
    try:
        service = await get_analytics_service()

        funnel = await service.get_lead_funnel(session)
        email = await service.get_email_metrics(session)
        sources = await service.get_lead_source_analytics(session)
        workflows = await service.get_workflow_performance(session)
        health = await service.get_lead_health_scores(session)

        return {
            "status": "ok",
            "data": {
                "funnel": funnel,
                "email_metrics": email,
                "lead_sources": sources,
                "workflow_performance": workflows,
                "lead_health": health,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
