"""Fase E: AI Autonomous Campaign Manager — API routes"""

from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_autonomous_campaign_manager import AIAutonomousCampaignManager

router = APIRouter(prefix="/fomo/ai/autonomous", tags=["fomo-ai-autonomous"])


@router.get("/scan-opportunities")
async def scan_for_opportunities(
    real_stock: int | None = Query(None),
    product_id: str | None = Query(None),
    competitor_discount_percent: float | None = Query(None),
    competitor_name: str | None = Query(None),
    current_user=Depends(get_current_user),
):
    """Scan for campaign-worthy opportunities: low stock, seasonal events, competitor activity"""
    competitor_signal = None
    if competitor_discount_percent is not None:
        competitor_signal = {
            "competitor_name": competitor_name or "unknown",
            "discount_percent": competitor_discount_percent,
        }
    return AIAutonomousCampaignManager.scan_for_opportunities(
        real_stock=real_stock, product_id=product_id, competitor_signal=competitor_signal
    )


@router.post("/create-campaign")
async def create_campaign_from_opportunity(
    opportunity: dict[str, Any] = Body(...),
    discount_historical_data: list[dict[str, float]] | None = Body(None),
    current_user=Depends(get_current_user),
):
    """Build a concrete campaign plan from a detected opportunity"""
    return AIAutonomousCampaignManager.create_campaign_from_opportunity(
        opportunity, discount_historical_data
    )


@router.post("/monitor-and-decide")
async def monitor_and_decide(
    today_metrics: dict[str, float] = Body(..., description='{"impressions", "conversions", "revenue", "cost"}'),
    metrics_history: list[dict[str, float]] | None = Body(None),
    current_budget: float | None = Query(None),
    current_user=Depends(get_current_user),
):
    """Evaluate live campaign health and decide pause/scale/continue"""
    return AIAutonomousCampaignManager.monitor_and_decide(today_metrics, metrics_history, current_budget)


@router.post("/daily-cycle")
async def run_daily_cycle(
    campaign_id: str = Query(...),
    today_metrics: dict[str, float] = Body(...),
    metrics_history: list[dict[str, float]] | None = Body(None),
    current_budget: float | None = Query(None),
    current_user=Depends(get_current_user),
):
    """Full daily cycle for a running campaign: monitor -> decide -> generate report"""
    return AIAutonomousCampaignManager.run_daily_cycle(
        campaign_id, today_metrics, metrics_history, current_budget
    )


@router.post("/full-cycle")
async def full_autonomous_cycle(
    real_stock: int | None = Query(None),
    product_id: str | None = Query(None),
    competitor_discount_percent: float | None = Query(None),
    competitor_name: str | None = Query(None),
    discount_historical_data: list[dict[str, float]] | None = Body(None),
    current_user=Depends(get_current_user),
):
    """Scan opportunities and build a plan for the highest-priority one in a single call"""
    competitor_signal = None
    if competitor_discount_percent is not None:
        competitor_signal = {
            "competitor_name": competitor_name or "unknown",
            "discount_percent": competitor_discount_percent,
        }
    return AIAutonomousCampaignManager.full_autonomous_cycle(
        real_stock=real_stock,
        product_id=product_id,
        competitor_signal=competitor_signal,
        discount_historical_data=discount_historical_data,
    )
