"""Fase B: AI Timing Optimizer Agent — API routes"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_timing_optimizer_agent import AITimingOptimizerAgent
from app.domains.users.models import User

router = APIRouter(prefix="/fomo/ai/timing", tags=["fomo-ai-timing"])


@router.post("/analyze-engagement")
async def analyze_engagement_patterns(
    send_history: Annotated[
        list[dict[str, Any]],
        Body(description='[{"sent_at": iso8601, "opened": bool, "clicked": bool}]'),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Build the hour-of-day / day-of-week engagement heatmap for one customer"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.analyze_engagement_patterns(parsed)


@router.post("/predict-send-time")
async def predict_optimal_send_time(
    send_history: Annotated[list[dict[str, Any]], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Predict the best datetime to send this customer's NEXT FOMO message"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.predict_optimal_send_time(parsed)


@router.post("/optimize-schedule")
async def optimize_automation_schedule(
    automation_type: Annotated[str, Query(description="cart_abandonment | flash_sale")],
    send_history: Annotated[list[dict[str, Any]], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Adjust a fixed automation sequence's delays based on this customer's response latency"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.optimize_automation_schedule(automation_type, parsed)


@router.post("/recommend")
async def get_send_recommendation(
    customer_id: Annotated[str, Query()],
    automation_type: Annotated[str, Query()],
    send_history: Annotated[list[dict[str, Any]], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Full per-customer recommendation: best send window + personalized delays + fatigue check"""
    parsed = _parse_send_history(send_history)
    return AITimingOptimizerAgent.get_send_recommendation(
        customer_id, automation_type, parsed
    )


@router.post("/batch-optimize")
async def batch_optimize(
    automation_type: Annotated[str, Query()],
    customers_history: Annotated[
        dict[str, list[dict[str, Any]]],
        Body(
            description='{"customer_id": [{"sent_at": iso8601, "opened": bool, "clicked": bool}]}'
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Batch timing recommendations across multiple customers"""
    parsed = {cid: _parse_send_history(hist) for cid, hist in customers_history.items()}
    return AITimingOptimizerAgent.batch_optimize(parsed, automation_type)


def _parse_send_history(send_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert ISO date strings to datetime objects for sent_at/opened_at"""
    parsed = []
    for entry in send_history:
        item = dict(entry)
        for key in ("sent_at", "opened_at"):
            val = item.get(key)
            if isinstance(val, str):
                item[key] = datetime.fromisoformat(val)
        parsed.append(item)
    return parsed
