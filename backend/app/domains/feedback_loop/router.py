"""Feedback loop API: Conversion data improves X9 profiles."""
from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.feedback_loop.service import FeedbackLoopAgent

router = APIRouter(prefix="/api/v1/feedback-loop", tags=["feedback-loop"])


@router.post("/update-profile-from-conversion")
async def update_profile_from_conversion(
    user_id: Annotated[str, Body()],
    deal_closed: Annotated[bool, Body()],
    deal_value: Annotated[float, Body()],
    which_touch_converted: Annotated[int, Body()],
    conversion_attributed_to: Annotated[str, Body()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Update X9 profile based on X12 conversion attribution."""
    return await FeedbackLoopAgent.update_profile_from_conversion(
        db, user_id, deal_closed, deal_value, which_touch_converted, conversion_attributed_to
    )


@router.post("/recalculate-segment-profiles")
async def recalculate_segment_profiles(
    personality_type: Annotated[str, Body()],
    num_conversions: Annotated[int, Body()],
    num_attempts: Annotated[int, Body()],
) -> dict:
    """Recalculate conversion benchmarks by personality type."""
    return await FeedbackLoopAgent.recalculate_segment_profiles(
        None, personality_type, num_conversions, num_attempts
    )


@router.get("/feedback-metrics")
async def get_feedback_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 7,
) -> dict:
    """Get system-wide feedback loop metrics."""
    return await FeedbackLoopAgent.get_feedback_metrics(db, days)


@router.post("/correlate-fomo-effectiveness")
async def correlate_fomo_effectiveness(
    fomo_campaign_id: Annotated[str, Body()],
    conversions: Annotated[int, Body()],
    impressions: Annotated[int, Body()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Correlate FOMO types with personality conversion rates."""
    return await FeedbackLoopAgent.correlate_fomo_effectiveness(
        db, fomo_campaign_id, conversions, impressions
    )
