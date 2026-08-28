"""Fase B: AI Timing Optimizer Agent — API routes"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, Body, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_timing_optimizer_agent import AITimingOptimizerAgent

router = APIRouter(prefix="/fomo/ai/timing", tags=["fomo-ai-timing"])


@router.post("/analyze-engagement")
async def analyze_engagement_patterns(
    send_history: List[Dict[str, Any]] = Body(
        ..., description='[{"sent_at": iso8601, "opened": bool, "clicked": bool}]'
    ),
    current_user=Depends(get_current_user),
):
    """Build the hour-of-day / day-of-week engagement heatmap for one customer"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.analyze_engagement_patterns(parsed)


@router.post("/predict-send-time")
async def predict_optimal_send_time(
    send_history: List[Dict[str, Any]] = Body(...),
    current_user=Depends(get_current_user),
):
    """Predict the best datetime to send this customer's NEXT FOMO message"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.predict_optimal_send_time(parsed)


@router.post("/optimize-schedule")
async def optimize_automation_schedule(
    automation_type: str = Query(..., description="cart_abandonment | flash_sale"),
    send_history: List[Dict[str, Any]] = Body(...),
    current_user=Depends(get_current_user),
):
    """Adjust a fixed automation sequence's delays based on this customer's response latency"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.optimize_automation_schedule(automation_type, parsed)


@router.post("/recommend")
async def get_send_recommendation(
    customer_id: str = Query(...),
    automation_type: str = Query(...),
    send_history: List[Dict[str, Any]] = Body(...),
    current_user=Depends(get_current_user),
):
    """Full per-customer recommendation: best send window + personalized delays + fatigue check"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.get_send_recommendation(customer_id, automation_type, parsed)


@router.post("/batch-optimize")
async def batch_optimize(
    automation_type: str = Query(...),
    customers_history: Dict[str, List[Dict[str, Any]]] = Body(
        ..., description='{"customer_id": [{"sent_at": iso8601, "opened": bool, "clicked": bool}]}'
    ),
    current_user=Depends(get_current_user),
):
    """Batch timing recommendations across multiple customers"""
    parsed = {cid: _parse_send_history(hist) for cid, hist in customers_history.items()}
    return AITimingOptimizerAgent.batch_optimize(parsed, automation_type)


def _parse_send_history(send_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert ISO date strings to datetime objects for sent_at/opened_at"""
    parsed = []
    for entry in send_history:
        item = dict(entry)
        for key in ("sent_at", "opened_at"):
            val = item.get(key)
            if isinstance(val, str):
                item[key] = datetime.fromisoformat(val.replace("Z", "+00:00"))
        parsed.append(item)
    return parsed
