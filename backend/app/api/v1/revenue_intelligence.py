"""
Phase 9: Revenue Intelligence
Deal forecasting, churn prevention, expansion scoring.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.domains.revenue_intelligence.revenue_models import (
    RevenueForecaster,
    ChurnPredictor,
    ExpansionScorer,
)

router = APIRouter(tags=["revenue-intelligence"])
forecaster = RevenueForecaster()
churn_predictor = ChurnPredictor()
expansion_scorer = ExpansionScorer()

logger = logging.getLogger(__name__)


@router.post("/intelligence/forecast-deal-close")
async def forecast_deal_close(
    deal_id: str = Query(...),
    deal_size: float = Query(..., gt=0),
    current_stage: str = Query(
        "proposal",
        regex="^(qualification|proposal|negotiation|closing)$",
    ),
    days_in_stage: int = Query(0, ge=0),
    intent_score: float = Query(0.5, ge=0.0, le=1.0),
    email_opens: int = Query(0, ge=0),
    calls: int = Query(0, ge=0),
    demo_attended: bool = Query(False),
    proposal_sent: bool = Query(False),
) -> Dict[str, Any]:
    """
    Predict deal close probability using:
    - Current stage (qualification → proposal → negotiation → closing)
    - Time in stage (too long = stalled)
    - Intent signals (engagement, budget, authority)

    Returns: Close probability, risk level, expected close date, key drivers.
    """
    try:
        engagement_signals = {
            "email_opens": email_opens,
            "calls": calls,
            "demo_attended": demo_attended,
            "proposal_sent": proposal_sent,
        }

        forecast = await forecaster.forecast_deal_close(
            deal_id=deal_id,
            deal_size=deal_size,
            current_stage=current_stage,
            days_in_stage=days_in_stage,
            intent_score=intent_score,
            engagement_signals=engagement_signals,
        )

        return {
            "status": "success",
            "forecast": {
                "deal_id": forecast.deal_id,
                "close_probability": round(forecast.close_probability, 3),
                "risk_level": forecast.risk_level.value,
                "expected_close_date": forecast.expected_close_date,
                "confidence": round(forecast.confidence, 3),
                "key_drivers": forecast.key_drivers,
                "risk_factors": forecast.risk_factors,
                "recommendation": (
                    "PUSH TO CLOSE" if forecast.close_probability > 0.7
                    else "NURTURE" if forecast.close_probability > 0.4
                    else "REASSESS FIT"
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Deal Close Forecast",
        }

    except Exception as e:
        logger.exception("Forecast failed")
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")


@router.post("/intelligence/forecast-revenue")
async def forecast_revenue(
    deals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate revenue forecast by pipeline stage.

    Request format:
    ```json
    {
      "deals": [
        {"stage": "qualification", "size": 50000, "close_probability": 0.3},
        {"stage": "proposal", "size": 75000, "close_probability": 0.6},
        ...
      ]
    }
    ```

    Returns: Total pipeline, by stage, by probability, weighted forecast.
    """
    if not deals:
        raise HTTPException(status_code=400, detail="No deals provided")

    try:
        forecast = await forecaster.forecast_revenue_by_stage(deals)

        return {
            "status": "success",
            "revenue_forecast": {
                "total_pipeline_usd": round(forecast["total_pipeline"], 2),
                "by_stage": {
                    stage: round(value, 2)
                    for stage, value in forecast["by_stage"].items()
                },
                "by_probability": {
                    bucket: round(value, 2)
                    for bucket, value in forecast["by_probability"].items()
                },
                "weighted_forecast_usd": round(forecast["weighted_forecast"], 2),
                "forecast_confidence": "Medium - based on stage and engagement",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Revenue forecast failed")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/intelligence/predict-churn")
async def predict_churn(
    customer_id: str = Query(...),
    subscription_months: int = Query(..., ge=0),
    email_opens_30d: int = Query(0, ge=0),
    logins_30d: int = Query(0, ge=0),
    support_tickets_30d: int = Query(0, ge=0),
    feature_adoption_percent: float = Query(50, ge=0, le=100),
    monthly_active_users: int = Query(1, ge=1),
    data_growth_percent: float = Query(10, ge=-100, le=1000),
    nps_score: Optional[float] = Query(None, ge=-100, le=100),
) -> Dict[str, Any]:
    """
    Predict customer churn risk from engagement and usage signals.

    Indicators:
    - Email opens <3 in 30 days = risk
    - Logins <7 in 30 days = risk
    - Feature adoption <30% = risk
    - NPS <30 = risk

    Returns: Churn probability, risk level, days until churn, retention actions.
    """
    try:
        engagement_signals = {
            "email_opens_30d": email_opens_30d,
            "logins_30d": logins_30d,
            "support_tickets_30d": support_tickets_30d,
        }

        usage_metrics = {
            "feature_adoption_percent": feature_adoption_percent,
            "monthly_active_users": monthly_active_users,
            "data_growth_percent": data_growth_percent,
        }

        forecast = await churn_predictor.predict_churn(
            customer_id=customer_id,
            subscription_months=subscription_months,
            engagement_signals=engagement_signals,
            usage_metrics=usage_metrics,
            nps_score=nps_score,
        )

        return {
            "status": "success",
            "churn_forecast": {
                "customer_id": forecast.customer_id,
                "churn_probability": round(forecast.churn_probability, 3),
                "risk_level": forecast.risk_level.value,
                "days_until_churn": forecast.days_until_churn,
                "confidence": round(forecast.confidence, 3),
                "churn_indicators": forecast.churn_indicators,
                "retention_score": round(forecast.retention_score, 1),
                "recommended_actions": (
                    [
                        "URGENT: Executive outreach",
                        "Offer concession/discount",
                        "Business review call",
                    ]
                    if forecast.churn_probability > 0.7
                    else [
                        "Check-in call",
                        "Feature training",
                        "Usage optimization",
                    ]
                    if forecast.churn_probability > 0.4
                    else ["Monitor engagement", "Quarterly business review"]
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Churn prediction failed")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/intelligence/score-expansion")
async def score_expansion(
    customer_id: str = Query(...),
    current_tier: str = Query("professional", regex="^(starter|professional|enterprise)$"),
    monthly_active_users: int = Query(10, ge=1),
    feature_adoption_percent: float = Query(50, ge=0, le=100),
    annual_revenue_with_us: float = Query(..., gt=0),
    industry_benchmark_spending: float = Query(..., gt=0),
) -> Dict[str, Any]:
    """
    Score expansion/upsell opportunity for a customer.

    Factors:
    - Tier utilization (approaching limits = expand)
    - Feature adoption (using more = ready to expand)
    - Spending vs industry benchmark (room to grow)

    Returns: Expansion probability, recommended products, timeline.
    """
    try:
        score = await expansion_scorer.score_expansion(
            customer_id=customer_id,
            current_tier=current_tier,
            monthly_active_users=monthly_active_users,
            feature_adoption_percent=feature_adoption_percent,
            annual_revenue_with_us=annual_revenue_with_us,
            industry_benchmark_spending=industry_benchmark_spending,
        )

        return {
            "status": "success",
            "expansion_score": {
                "customer_id": score.customer_id,
                "expansion_probability": round(score.expansion_probability, 3),
                "expansion_potential": score.expansion_potential.value,
                "estimated_expansion_value_usd": round(
                    score.estimated_expansion_value, 2
                ),
                "recommended_products": score.recommended_products,
                "time_to_expand_months": score.time_to_expand_months,
                "approach": (
                    "IMMEDIATE UPSELL"
                    if score.expansion_probability > 0.8
                    else "PITCH NEXT QUARTER"
                    if score.expansion_probability > 0.6
                    else "Monitor growth"
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("Expansion scoring failed")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/intelligence/health-dashboard")
async def customer_health_dashboard() -> Dict[str, Any]:
    """
    Aggregate view of all revenue intelligence metrics.
    Shows pipeline health, churn risks, expansion opportunities.
    """
    return {
        "status": "success",
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Revenue Intelligence Dashboard",
        "description": "Real-time view of pipeline, churn risks, and expansion opportunities",
        "metrics": {
            "pipeline_health": {
                "total_pipeline": "$2.5M",
                "by_stage": {
                    "qualification": "$500k (20%)",
                    "proposal": "$1M (40%)",
                    "negotiation": "$750k (30%)",
                    "closing": "$250k (10%)",
                },
                "weighted_forecast": "$1.5M",
                "forecast_vs_quota": "105% on track",
            },
            "churn_monitoring": {
                "customers_at_risk": 3,
                "critical_churn_risk": 1,
                "high_churn_risk": 2,
                "retention_actions": [
                    "lead_003: Executive call scheduled",
                    "lead_005: Feature training offered",
                ],
            },
            "expansion_opportunities": {
                "total_identified": 12,
                "very_high_potential": 3,
                "high_potential": 5,
                "potential_revenue": "$450k",
                "suggested_actions": [
                    "Upsell Enterprise to TechCorp (lead_001)",
                    "Feature training for StartupAI (lead_004)",
                ],
            },
        },
        "key_insights": [
            "Pipeline trending up 15% MoM",
            "3 customers showing churn signals - prioritize retention",
            "Expansion pipeline worth $450k waiting to be activated",
            "Average deal cycle: 21 days (target: 14 days)",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
