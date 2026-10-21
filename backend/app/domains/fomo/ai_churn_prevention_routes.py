"""Fase G: AI Predictive Churn-to-FOMO Agent — API routes"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_churn_prevention_agent import (
    AIChurnPreventionAgent,
    WinBackTriggerEngine,
)
from app.domains.users.models import User

router = APIRouter(prefix="/fomo/ai/churn", tags=["fomo-ai-churn"])


@router.post("/score")
async def score_customer(
    purchases: Annotated[list[dict[str, Any]], Body(description='[{"date": iso8601, "amount": float}]')],
    current_user: Annotated[User, Depends(get_current_user)],
    send_history: Annotated[list[dict[str, Any]] | None, Body()] = None,
):
    """Score one customer's churn risk (heuristic — no labeled training data needed)"""
    parsed_purchases = _parse_dates(purchases, "date")
    parsed_history = _parse_dates(send_history or [], "sent_at")
    return AIChurnPreventionAgent.score_customer(parsed_purchases, parsed_history or None)


@router.post("/evaluate-and-trigger")
async def evaluate_and_trigger(
    customer_id: Annotated[str, Query()],
    purchases: Annotated[list[dict[str, Any]], Body()],
    batch_monetary_values: Annotated[list[float], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
    send_history: Annotated[list[dict[str, Any]] | None, Body()] = None,
    threshold: Annotated[float, Query(ge=0.0, le=1.0)] = WinBackTriggerEngine.DEFAULT_THRESHOLD,
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
    customers: Annotated[list[dict[str, Any]], Body(description='[{"customer_id": str, "purchases": [{"date": iso8601, "amount": float}]}]')],
    current_user: Annotated[User, Depends(get_current_user)],
    fatigue_data: Annotated[dict[str, list[dict[str, Any]]] | None, Body()] = None,
    threshold: Annotated[float, Query(ge=0.0, le=1.0)] = WinBackTriggerEngine.DEFAULT_THRESHOLD,
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


def _parse_dates(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    parsed = []
    for r in records:
        item = dict(r)
        val = item.get(key)
        if isinstance(val, str):
            item[key] = datetime.fromisoformat(val)
        parsed.append(item)
    return parsed
