from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from app.domains.enterprise.forecasting import ForecastingManager

router = APIRouter(tags=["forecasting"])
forecasting_engine = ForecastingManager()


@router.post("/forecast/opportunities/add")
async def add_opportunity(
    user_id: str = Query(...),
    title: str = Query(...),
    amount: float = Query(...),
    stage: str = Query("prospecting"),
    contact_name: str = Query(...),
    source: str = Query("direct"),
):
    """Add sales opportunity to pipeline."""
    try:
        stage_enum = DealStage(stage)
        opportunity = Opportunity(
            id=f"opp_{datetime.now().timestamp()}",
            title=title,
            amount=amount,
            stage=stage_enum,
            probability=50.0,
            days_in_stage=0,
            close_date_estimated=datetime.now() + timedelta(days=30),
            contact_name=contact_name,
            source=source,
        )

        forecasting_engine.add_opportunity(user_id, opportunity)

        return {
            "status": "added",
            "opportunity_id": opportunity.id,
            "title": title,
            "amount": amount,
            "stage": stage,
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid stage: {stage}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/forecast/pipeline/{user_id}")
async def get_pipeline_forecast(
    user_id: str,
    model: str = Query("standard", description="conservative, standard, optimistic"),
):
    """Get pipeline snapshot with weighted forecast."""
    try:
        model_enum = ProbabilityModel(model)
        pipeline = forecasting_engine.get_pipeline_forecast(user_id, model_enum)

        return {
            "timestamp": pipeline.timestamp.isoformat(),
            "total_opportunities": pipeline.total_opportunities,
            "total_pipeline_value": f"${pipeline.total_pipeline_value:,.2f}",
            "weighted_forecast": f"${pipeline.weighted_forecast:,.2f}",
            "average_deal_size": f"${pipeline.average_deal_size:,.2f}",
            "average_days_in_pipeline": round(pipeline.average_days_in_pipeline, 1),
            "by_stage": {
                stage: {
                    "count": data["count"],
                    "value": f"${data['value']:,.2f}",
                    "weighted_value": f"${data['weighted_value']:,.2f}",
                    "avg_probability": f"{data['avg_probability']:.1f}%",
                }
                for stage, data in pipeline.by_stage.items()
            },
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid model: {model}"}


@router.get("/forecast/revenue/{user_id}")
async def project_revenue(
    user_id: str,
    days_ahead: int = Query(30, ge=1, le=365),
    target_revenue: float = Query(None),
):
    """Project revenue for period ahead."""
    try:
        projection = forecasting_engine.project_revenue(
            user_id, days_ahead, target_revenue
        )

        return {
            "period": projection.period,
            "projected_revenue": f"${projection.projected_revenue:,.2f}",
            "confidence": f"{projection.confidence_level:.1f}%",
            "scenarios": {
                "best_case": f"${projection.best_case:,.2f}",
                "most_likely": f"${projection.most_likely:,.2f}",
                "worst_case": f"${projection.worst_case:,.2f}",
            },
            "probability_of_target": (
                f"{projection.probability_of_target:.1f}%" if target_revenue else "N/A"
            ),
            "key_drivers": {
                "avg_deal_size": f"${projection.key_drivers['avg_deal_size']:,.2f}",
                "pipeline_velocity": f"${projection.key_drivers['pipeline_velocity']:,.2f}/day",
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/forecast/scenarios/{user_id}")
async def get_forecast_scenarios(
    user_id: str,
    days_ahead: int = Query(30, ge=1, le=365),
):
    """Get best/base/worst case scenarios."""
    try:
        scenarios = forecasting_engine.generate_scenarios(user_id, days_ahead)

        return {
            "period": f"{days_ahead}d",
            "scenarios": [
                {
                    "name": s.name,
                    "projected_revenue": f"${s.projected_revenue:,.2f}",
                    "probability": f"{s.probability}%",
                    "assumptions": s.assumptions,
                }
                for s in scenarios
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/forecast/funnel/{user_id}")
async def get_conversion_funnel(user_id: str):
    """Get conversion funnel analysis."""
    try:
        funnel = forecasting_engine.get_conversion_funnel(user_id)

        return {
            "user_id": user_id,
            "funnel": {
                stage: {
                    "count": data["count"],
                    "percentage": f"{data['percentage']:.1f}%",
                    "value": f"${data['value']:,.2f}",
                    "cumulative_value": f"${data['cumulative_value']:,.2f}",
                }
                for stage, data in funnel.items()
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/forecast/risks/{user_id}")
async def identify_risks(user_id: str):
    """Identify at-risk and stalled opportunities."""
    try:
        risks = forecasting_engine.identify_risk_opportunities(user_id)

        return {
            "user_id": user_id,
            "summary": {
                "at_risk_count": risks["at_risk_count"],
                "stalled_count": risks["stalled_count"],
                "risk_value": f"${risks['risk_value']:,.2f}",
            },
            "at_risk_opportunities": risks["at_risk"],
            "stalled_opportunities": risks["stalled"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
