from fastapi import APIRouter, Depends, Query
from app.domains.enterprise.forecasting import ForecastingManager, DealOutcomeAnalyzer
from app.domains.enterprise.collaboration import CollaborationManager

router = APIRouter()

forecasting = ForecastingManager()
outcome_analyzer = DealOutcomeAnalyzer()
collaboration = CollaborationManager()


@router.post("/intelligence/analyze-deals/{user_id}")
async def analyze_deals(user_id: str, deals: list[dict] = []):
    """Analyze deals for win probability and risk assessment."""
    result = forecasting.analyze_deals(user_id, deals)
    return {
        "status": "ok",
        "user_id": user_id,
        "analysis": result,
    }


@router.get("/intelligence/deal-score/{deal_id}")
async def get_deal_score(deal_id: str):
    """Get current deal score and risk assessment."""
    score = forecasting.deal_scores.get(deal_id)
    if not score:
        return {
            "status": "not_found",
            "deal_id": deal_id,
            "message": "Deal not yet scored. Run analyze-deals first.",
        }

    return {
        "status": "ok",
        "deal_id": deal_id,
        "score": {
            "win_probability": score.win_probability,
            "confidence": score.confidence_level,
            "risk_level": score.risk_level,
            "engagement_velocity": score.engagement_velocity,
            "factors": score.ai_score_factors,
        },
    }


@router.post("/intelligence/forecast-revenue/{user_id}")
async def forecast_revenue(user_id: str, deals: list[dict] = [], periods: list[int] = Query([30, 60, 90])):
    """Generate revenue forecast for multiple periods."""
    forecast = forecasting.forecast_revenue(user_id, deals, periods)

    return {
        "status": "ok",
        "user_id": user_id,
        "forecast": forecast,
    }


@router.get("/intelligence/at-risk-deals")
async def get_at_risk_deals():
    """Get summary of all at-risk deals."""
    summary = forecasting.get_at_risk_summary()

    return {
        "status": "ok",
        "at_risk_summary": summary,
    }


@router.get("/intelligence/at-risk-deals/{user_id}")
async def get_user_at_risk_deals(user_id: str):
    """Get at-risk deals for specific user."""
    at_risk = [d for d in forecasting.at_risk_deals if d.get("user_id") == user_id or user_id == "all"]

    return {
        "status": "ok",
        "user_id": user_id,
        "at_risk_deals": at_risk,
        "count": len(at_risk),
    }


@router.post("/intelligence/record-outcome/{deal_id}")
async def record_deal_outcome(
    deal_id: str,
    user_id: str,
    outcome: str,
    final_value: float = None,
    days_to_close: int = 0,
    forecasted_probability: float = 0.5,
    win_loss_reason: str = None,
):
    """Record deal outcome (won/lost) for accuracy tracking."""
    result = outcome_analyzer.record_outcome(
        deal_id,
        user_id,
        outcome,
        final_value,
        days_to_close,
        forecasted_probability,
        win_loss_reason,
    )

    return {
        "status": "ok",
        "outcome": result,
    }


@router.get("/intelligence/accuracy-metrics/{user_id}")
async def get_accuracy_metrics(user_id: str):
    """Get forecast accuracy metrics for user."""
    metrics = outcome_analyzer.get_accuracy_metrics(user_id)

    return {
        "status": "ok",
        "user_id": user_id,
        "metrics": metrics,
    }


@router.get("/intelligence/win-loss-summary/{user_id}")
async def get_win_loss_summary(user_id: str):
    """Get win/loss analysis and patterns."""
    summary = outcome_analyzer.get_win_loss_summary(user_id)

    return {
        "status": "ok",
        "user_id": user_id,
        "summary": summary,
    }


@router.get("/intelligence/dashboard/{user_id}")
async def get_intelligence_dashboard(user_id: str):
    """Get comprehensive intelligence dashboard."""
    at_risk = forecasting.get_at_risk_summary()
    accuracy = outcome_analyzer.get_accuracy_metrics(user_id)
    win_loss = outcome_analyzer.get_win_loss_summary(user_id)

    return {
        "status": "ok",
        "user_id": user_id,
        "dashboard": {
            "at_risk": at_risk,
            "accuracy": accuracy,
            "win_loss_patterns": win_loss,
            "total_deals_analyzed": len(forecasting.deal_scores),
        },
    }
