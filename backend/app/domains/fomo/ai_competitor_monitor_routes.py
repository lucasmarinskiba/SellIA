"""Fase F: AI Competitor FOMO Monitor — API routes"""

from typing import Dict, Optional, Any

from fastapi import APIRouter, Depends, Body, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_competitor_monitor_agent import (
    AICompetitorMonitorAgent,
    fetch_competitor_page,
)

router = APIRouter(prefix="/fomo/ai/competitor", tags=["fomo-ai-competitor"])


@router.post("/extract-offer")
async def extract_competitor_offer(
    raw_text: str = Body(..., embed=True),
    current_user=Depends(get_current_user),
):
    """Extract price/discount signals from raw competitor page text"""
    return AICompetitorMonitorAgent.extract_competitor_offer(raw_text)


@router.post("/detect-change")
async def detect_price_change(
    current: Dict[str, Any] = Body(...),
    previous: Optional[Dict[str, Any]] = Body(None),
    current_user=Depends(get_current_user),
):
    """Compare a new extraction snapshot against the last known one"""
    return AICompetitorMonitorAgent.detect_price_change(current, previous)


@router.get("/competitive-message")
async def generate_competitive_message(
    our_price: float = Query(...),
    competitor_price: float = Query(...),
    our_product_name: str = Query(...),
    competitor_name: str = Query("la competencia"),
    current_user=Depends(get_current_user),
):
    """Generate a deterministic 'better than the competition' comparison message"""
    return AICompetitorMonitorAgent.generate_competitive_message(
        our_price, competitor_price, our_product_name, competitor_name
    )


@router.post("/monitor-cycle")
async def full_monitor_cycle(
    raw_text: str = Body(...),
    competitor_name: str = Query(...),
    previous_snapshot: Optional[Dict[str, Any]] = Body(None),
    our_price: Optional[float] = Query(None),
    our_product_name: Optional[str] = Query(None),
    our_recommended_discount_percent: Optional[float] = Query(None),
    current_user=Depends(get_current_user),
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
    url: str = Query(..., description="A URL the user explicitly configured to monitor"),
    competitor_name: str = Query(...),
    previous_snapshot: Optional[Dict[str, Any]] = Body(None),
    our_price: Optional[float] = Query(None),
    our_product_name: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
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
