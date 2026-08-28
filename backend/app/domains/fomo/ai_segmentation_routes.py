"""Fase D: AI Customer Segmentation Agent — API routes"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, Body, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_segmentation_agent import (
    AICustomerSegmentationAgent,
    CustomerSegment,
    SEGMENT_FOMO_STRATEGY,
)

router = APIRouter(prefix="/fomo/ai/segmentation", tags=["fomo-ai-segmentation"])


@router.post("/segment")
async def segment_customers(
    customers: List[Dict[str, Any]] = Body(
        ..., description='[{"customer_id": str, "purchases": [{"date": iso8601, "amount": float}]}]'
    ),
    use_clustering: bool = Query(True, description="Use KMeans when data allows, else RFM rules"),
    current_user=Depends(get_current_user),
):
    """Segment customers via RFM (+ optional KMeans clustering when enough data)"""
    parsed_customers = _parse_purchase_dates(customers)
    result = AICustomerSegmentationAgent.segment_customers(
        parsed_customers, use_clustering=use_clustering
    )
    return result


@router.post("/analyze-and-recommend")
async def analyze_and_recommend(
    customers: List[Dict[str, Any]] = Body(...),
    fatigue_data: Optional[Dict[str, List[Dict[str, Any]]]] = Body(
        None,
        description='{"customer_id": [{"sent_at": iso8601, "opened": bool, "clicked": bool}]}',
    ),
    use_clustering: bool = Query(True),
    current_user=Depends(get_current_user),
):
    """Full pipeline: segment + recommend FOMO campaign per customer + fatigue exclusion"""
    parsed_customers = _parse_purchase_dates(customers)
    result = AICustomerSegmentationAgent.analyze_and_recommend(
        parsed_customers,
        fatigue_data=fatigue_data,
        use_clustering=use_clustering,
    )
    return result


@router.get("/strategies")
async def list_segment_strategies(current_user=Depends(get_current_user)):
    """List the FOMO strategy (campaign_type/tone/lift) mapped to each segment"""
    return {
        "strategies": [
            {"segment": segment.value, **data}
            for segment, data in SEGMENT_FOMO_STRATEGY.items()
        ]
    }


@router.get("/strategies/{segment}")
async def get_segment_strategy(segment: str, current_user=Depends(get_current_user)):
    """Get the recommended FOMO strategy for one named segment"""
    return AICustomerSegmentationAgent.get_segment_strategy(segment)


def _parse_purchase_dates(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert ISO date strings in purchase history to datetime objects"""
    parsed = []
    for customer in customers:
        purchases = []
        for p in customer.get("purchases", []):
            date_val = p.get("date")
            if isinstance(date_val, str):
                date_val = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            purchases.append({"date": date_val, "amount": p.get("amount", 0)})
        parsed.append({"customer_id": customer["customer_id"], "purchases": purchases})
    return parsed
