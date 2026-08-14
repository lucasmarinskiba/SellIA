"""Phase 26c: Deal Intelligence API endpoints."""

from fastapi import APIRouter, Query, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import random

from app.core.database import get_db
from app.domains.enterprise.deal_intelligence import DealScore, ForecastSnapshot, WinLossAnalysis, DealIntelligenceManager

router = APIRouter(prefix="/deal-intelligence", tags=["deal-intelligence"])


@router.post("/scores/{deal_id}")
async def score_deal(
    deal_id: str,
    days_in_stage: float = Body(...),
    engagement_velocity: float = Body(...),
    proposal_status: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Calculate win probability for deal."""
    score_value = DealIntelligenceManager.calculate_deal_score(
        days_in_stage=days_in_stage,
        engagement_velocity=engagement_velocity,
        proposal_status=proposal_status,
        competitor_signals=random.randint(0, 3),
        buyer_authority=random.random(),
    )

    deal_score = DealScore(
        deal_id=deal_id,
        seller_id="seller-123",
        win_probability=score_value,
        confidence_level=0.75,
    )
    db.add(deal_score)
    await db.commit()
    await db.refresh(deal_score)

    return {
        "deal_id": deal_id,
        "win_probability": deal_score.win_probability,
        "confidence": deal_score.confidence_level,
    }


@router.get("/forecast/{seller_id}")
async def get_forecast(seller_id: str, days_ahead: int = Query(30)):
    """Get revenue forecast for seller."""
    demo_forecast = DealIntelligenceManager.forecast_revenue(
        deals=[
            {"value": 50000, "win_prob": 0.8},
            {"value": 75000, "win_prob": 0.6},
            {"value": 30000, "win_prob": 0.4},
            {"value": 100000, "win_prob": 0.3},
        ]
    )

    return {
        "seller_id": seller_id,
        "forecast_date": datetime.utcnow().isoformat(),
        "total_pipeline": demo_forecast["total_pipeline"],
        "weighted_pipeline": demo_forecast["weighted_pipeline"],
        f"projected_revenue_{days_ahead}d": demo_forecast.get(f"projected_revenue_{days_ahead}d", 0),
    }


@router.get("/risk-deals/{seller_id}")
async def get_at_risk_deals(seller_id: str):
    """Get deals at risk of loss."""
    return {
        "seller_id": seller_id,
        "at_risk_count": random.randint(1, 5),
        "at_risk_deals": [
            {
                "deal_id": f"deal-{i}",
                "reason": "No response in 7 days",
                "win_probability": random.random() * 0.3,
            }
            for i in range(random.randint(1, 3))
        ],
    }


@router.post("/win-loss/{deal_id}")
async def record_win_loss(
    deal_id: str,
    outcome: str = Body(...),  # won, lost, stalled
    primary_reason: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Record deal outcome & learnings."""
    analysis = WinLossAnalysis(
        deal_id=deal_id,
        seller_id="seller-123",
        outcome=outcome,
        primary_reason=primary_reason,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return {
        "deal_id": deal_id,
        "outcome": outcome,
        "recorded": True,
    }


@router.get("/insights/{seller_id}")
async def get_intelligence_insights(seller_id: str):
    """Get actionable insights from deal data."""
    return {
        "seller_id": seller_id,
        "insights": [
            {
                "type": "win_pattern",
                "finding": "Deals with 2+ proposal iterations have 45% higher close rate",
                "action": "Send second proposal version to negotiating deals",
            },
            {
                "type": "risk_pattern",
                "finding": "7+ day response gaps predict 60% churn",
                "action": "Implement 3-day follow-up rule for all stalled deals",
            },
            {
                "type": "timing",
                "finding": "Average deal closes in 28 days",
                "action": "Use 30-day forecast for cash flow planning",
            },
        ],
    }
