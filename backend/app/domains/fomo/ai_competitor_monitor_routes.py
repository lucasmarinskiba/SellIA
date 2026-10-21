"""Fase F: AI Competitor FOMO Monitor — API routes"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_competitor_monitor_agent import (
    AICompetitorMonitorAgent,
    fetch_competitor_page,
)
from app.domains.users.models import User

router = APIRouter(prefix="/fomo/ai/competitor", tags=["fomo-ai-competitor"])


@router.post("/extract-offer")
async def extract_competitor_offer(
    raw_text: Annotated[str, Body(embed=True)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Extract price/discount signals from raw competitor page text"""
    return AICompetitorMonitorAgent.extract_competitor_offer(raw_text)


@router.post("/detect-change")
async def detect_price_change(
    current: Annotated[dict[str, Any], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
    previous: Annotated[dict[str, Any] | None, Body()] = None,
):
    """Compare a new extraction snapshot against the last known one"""
    return AICompetitorMonitorAgent.detect_price_change(current, previous)


@router.get("/competitive-message")
async def generate_competitive_message(
    our_price: Annotated[float, Query()],
    competitor_price: Annotated[float, Query()],
    our_product_name: Annotated[str, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    competitor_name: Annotated[str, Query()] = "la competencia",
):
    """Generate a deterministic 'better than the competition' comparison message"""
    return AICompetitorMonitorAgent.generate_competitive_message(
        our_price, competitor_price, our_product_name, competitor_name
    )


@router.post("/monitor-cycle")
async def full_monitor_cycle(
    raw_text: Annotated[str, Body()],
    competitor_name: Annotated[str, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    previous_snapshot: Annotated[dict[str, Any] | None, Body()] = None,
    our_price: Annotated[float | None, Query()] = None,
    our_product_name: Annotated[str | None, Query()] = None,
    our_recommended_discount_percent: Annotated[float | None, Query()] = None,
):
    """Full pipeline: extract -> detect change -> alert -> competitive messaging"""
    return AICompetitorMonitorAgent.full_monitor_cycle(
        raw_text=raw_text,
        competitor_name=competitor_name,
        previous_snapshot=previous_snapshot,
        our_price=our_price,
        our_product_name=our_product_name,
        our_recommended_discount_percent=our_recommended_discount_percent,
    )


@router.post("/fetch-and-monitor")
async def fetch_and_monitor(
    url: Annotated[
        str, Query(description="A URL the user explicitly configured to monitor")
    ],
    competitor_name: Annotated[str, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    previous_snapshot: Annotated[dict[str, Any] | None, Body()] = None,
    our_price: Annotated[float | None, Query()] = None,
    our_product_name: Annotated[str | None, Query()] = None,
):
    """Fetch a single configured competitor URL and run the full monitor cycle on it"""
    raw_text = await fetch_competitor_page(url)
    if raw_text is None:
        return {"error": "fetch_failed", "url": url}

    return AICompetitorMonitorAgent.full_monitor_cycle(
        raw_text=raw_text,
        competitor_name=competitor_name,
        previous_snapshot=previous_snapshot,
        our_price=our_price,
        our_product_name=our_product_name,
    )
