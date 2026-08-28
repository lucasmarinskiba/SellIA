"""Fase G: AI Predictive Churn-to-FOMO Agent — API routes"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, Body, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_churn_prevention_agent import (
    AIChurnPreventionAgent,
    WinBackTriggerEngine,
)

router = APIRouter(prefix="/fomo/ai/churn", tags=["fomo-ai-churn"])


@router.post("/score")
async def score_customer(
    purchases: List[Dict[str, Any]] = Body(..., description='[{"date": iso8601, "amount": float}]'),
    send_history: Optional[List[Dict[str, Any]]] = Body(None),
    current_user=Depends(get_current_user),
):
    """Score one customer's churn risk (heuristic — no labeled training data needed)"""
    parsed_purchases = _parse_dates(purchases, "date")
    parsed_history = _parse_dates(send_history or [], "sent_at")
    return AIChurnPreventionAgent.score_customer(parsed_purchases, parsed_history or None)


@router.post("/evaluate-and-trigger")
async def evaluate_and_trigger(
    customer_id: str = Query(...),
    purchases: List[Dict[str, Any]] = Body(...),
    batch_monetary_values: List[float] = Body(...),
    send_history: Optional[List[Dict[str, Any]]] = Body(None),
    threshold: float = Query(WinBackTriggerEngine.DEFAULT_THRESHOLD, ge=0.0, le=1.0),
    current_user=Depends(get_current_user),
):
    """Score risk, decide win-back trigger, size a personalized offer if triggered"""
    parsed_purchases = _parse_dates(purchases, "date")
    parsed_history = _parse_dates(send_history or [], "sent_at")
    return AIChurnPreventionAgent.evaluate_and_trigger(
        customer_id=customer_id,
        purchases=parsed_purchases,
        batch_monetary_values=batch_monetary_values,
        send_history=parsed_history or None,
        threshold=threshold,
    )


@router.post("/batch-evaluate")
async def batch_evaluate(
    customers: List[Dict[str, Any]] = Body(
        ..., description='[{"customer_id": str, "purchases": [{"date": iso8601, "amount": float}]}]'
    ),
    fatigue_data: Optional[Dict[str, List[Dict[str, Any]]]] = Body(None),
    threshold: float = Query(WinBackTriggerEngine.DEFAULT_THRESHOLD, ge=0.0, le=1.0),
    current_user=Depends(get_current_user),
):
    """Batch churn-risk scoring + win-back trigger across all customers"""
    parsed_customers = []
    for c in customers:
        parsed_customers.append({
            "customer_id": c["customer_id"],
            "purchases": _parse_dates(c.get("purchases", []), "date"),
        })

    parsed_fatigue = None
    if fatigue_data:
        parsed_fatigue = {
            cid: _parse_dates(hist, "sent_at") for cid, hist in fatigue_data.items()
        }

    return AIChurnPreventionAgent.batch_evaluate(
        parsed_customers, threshold=threshold, fatigue_data=parsed_fatigue
    )


def _parse_dates(records: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    parsed = []
    for r in records:
        item = dict(r)
        val = item.get(key)
        if isinstance(val, str):
            item[key] = datetime.fromisoformat(val.replace("Z", "+00:00"))
        parsed.append(item)
    return parsed
