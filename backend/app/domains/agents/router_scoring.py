"""Deal Scoring Router

Endpoints for deal scores, pipeline funnel, and alerts.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.service_scoring import DealScoringService

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/scores")
async def list_deal_scores(
    category: Optional[str] = Query(None, description="Filter by category: cold, warm, hot, ready"),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List deal scores for the current user's business."""
    service = DealScoringService(db)
    result = await service.get_deal_scores(
        business_id=current_user.business_id,
        category=category,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    return result


@router.get("/scores/{conversation_id}")
async def get_score_history(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get score history for a specific conversation."""
    service = DealScoringService(db)
    history = await service.get_deal_score_history(conversation_id)
    return {"conversation_id": conversation_id, "history": history}


@router.get("/pipeline")
async def get_pipeline_funnel(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pipeline funnel counts by category."""
    service = DealScoringService(db)
    funnel = await service.get_pipeline_funnel(current_user.business_id)
    return funnel


@router.get("/alerts")
async def list_alerts(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List deal alerts for the current user's business."""
    service = DealScoringService(db)
    result = await service.get_alerts(
        business_id=current_user.business_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return result


@router.post("/alerts/{alert_id}/read", status_code=status.HTTP_200_OK)
async def mark_alert_read(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a deal alert as read."""
    service = DealScoringService(db)
    alert = await service.mark_alert_read(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": alert.id, "is_read": alert.is_read}


@router.post("/score/{conversation_id}", status_code=status.HTTP_201_CREATED)
async def trigger_manual_scoring(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger manual deal scoring for a conversation."""
    service = DealScoringService(db)
    score = await service.calculate_and_save_score(
        conversation_id=conversation_id,
        business_id=current_user.business_id,
    )
    return {
        "id": score.id,
        "conversation_id": score.conversation_id,
        "score": score.score,
        "category": score.category,
        "factors": score.factors,
        "recommendation": score.recommendation,
        "previous_score": score.previous_score,
        "score_change": score.score_change,
        "calculated_at": score.calculated_at,
    }
