from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from app.domains.enterprise.performance_dashboard import (
    PerformanceDashboardEngine,
    TimeRange,
)

router = APIRouter(tags=["analytics"])
dashboard_engine = PerformanceDashboardEngine()


@router.get("/analytics/dashboard/{user_id}")
async def get_performance_dashboard(
    user_id: str,
    segment: str = Query("active", description="User segment"),
    time_range: str = Query("month", description="Time range: today, week, month, quarter, year"),
):
    """Get complete performance dashboard for user."""
    try:
        time_range_enum = TimeRange(time_range)
    except ValueError:
        time_range_enum = TimeRange.MONTH

    dashboard = dashboard_engine.get_dashboard(user_id, segment, time_range_enum)

    return {
        "user_id": user_id,
        "segment": segment,
        "time_range": time_range,
        "kpi_cards": [
            {
                "label": kpi.label,
                "metric_type": kpi.metric_type.value,
                "current_value": kpi.current_value,
                "unit": kpi.unit,
                "target": kpi.target,
                "trend": kpi.trend,
                "trend_direction": kpi.trend_direction,
                "last_updated": kpi.last_updated.isoformat(),
                "sparkline_data": kpi.sparkline_data,
            }
            for kpi in dashboard.kpi_cards
        ],
        "agent_performance": [
            {
                "agent_id": agent.agent_id,
                "agent_name": agent.agent_name,
                "status": agent.status,
                "tasks_completed": agent.tasks_completed,
                "success_rate": agent.success_rate,
                "avg_response_time": agent.avg_response_time,
                "leads_generated": agent.leads_generated,
                "conversions": agent.conversions,
                "revenue_attributed": agent.revenue_attributed,
                "efficiency_score": agent.efficiency_score,
            }
            for agent in dashboard.agent_performance
        ],
        "segment_benchmarks": {
            "segment_name": dashboard.segment_benchmarks.segment_name,
            "total_users": dashboard.segment_benchmarks.total_users,
            "active_users": dashboard.segment_benchmarks.active_users,
            "avg_leads_per_user": dashboard.segment_benchmarks.avg_leads_per_user,
            "avg_revenue_per_user": dashboard.segment_benchmarks.avg_revenue_per_user,
            "avg_conversion_rate": dashboard.segment_benchmarks.avg_conversion_rate,
            "churn_rate": dashboard.segment_benchmarks.churn_rate,
            "expansion_rate": dashboard.segment_benchmarks.expansion_rate,
        },
        "pipeline": {
            "total_pipeline_value": dashboard.pipeline.total_pipeline_value,
            "opportunities_in_stage": dashboard.pipeline.opportunities_in_stage,
            "avg_deal_size": dashboard.pipeline.avg_deal_size,
            "days_in_pipeline": dashboard.pipeline.days_in_pipeline,
            "forecast_confidence": dashboard.pipeline.forecast_confidence,
        },
        "generated_at": dashboard.generated_at.isoformat(),
    }


@router.get("/analytics/kpis/{user_id}")
async def get_kpis(
    user_id: str,
    segment: str = Query("active"),
    time_range: str = Query("month"),
):
    """Get only KPI cards for quick dashboard view."""
    try:
        time_range_enum = TimeRange(time_range)
    except ValueError:
        time_range_enum = TimeRange.MONTH

    dashboard = dashboard_engine.get_dashboard(user_id, segment, time_range_enum)

    return {
        "user_id": user_id,
        "time_range": time_range,
        "kpis": [
            {
                "label": kpi.label,
                "value": kpi.current_value,
                "unit": kpi.unit,
                "target": kpi.target,
                "trend": kpi.trend,
                "direction": kpi.trend_direction,
            }
            for kpi in dashboard.kpi_cards
        ],
    }


@router.get("/analytics/agents/{user_id}")
async def get_agent_metrics(user_id: str):
    """Get detailed agent performance metrics."""
    dashboard = dashboard_engine.get_dashboard(user_id, "active", TimeRange.MONTH)

    return {
        "user_id": user_id,
        "agents": [
            {
                "id": agent.agent_id,
                "name": agent.agent_name,
                "status": agent.status,
                "performance": {
                    "tasks_completed": agent.tasks_completed,
                    "success_rate": agent.success_rate,
                    "efficiency_score": agent.efficiency_score,
                    "avg_response_time": agent.avg_response_time,
                },
                "business_impact": {
                    "leads_generated": agent.leads_generated,
                    "conversions": agent.conversions,
                    "revenue_attributed": agent.revenue_attributed,
                },
            }
            for agent in dashboard.agent_performance
        ],
    }


@router.get("/analytics/pipeline/{user_id}")
async def get_pipeline_view(user_id: str):
    """Get pipeline analysis and forecasting."""
    dashboard = dashboard_engine.get_dashboard(user_id, "active", TimeRange.MONTH)

    return {
        "user_id": user_id,
        "pipeline": {
            "total_value": dashboard.pipeline.total_pipeline_value,
            "stages": dashboard.pipeline.opportunities_in_stage,
            "avg_deal_size": dashboard.pipeline.avg_deal_size,
            "avg_days_in_pipeline": dashboard.pipeline.days_in_pipeline,
            "forecast_confidence": dashboard.pipeline.forecast_confidence,
            "forecast": {
                "projected_revenue_30d": round(
                    dashboard.pipeline.total_pipeline_value
                    * (dashboard.pipeline.forecast_confidence / 100)
                    * 0.3,
                    2,
                ),
                "projected_conversions_30d": max(
                    1,
                    int(
                        sum(dashboard.pipeline.opportunities_in_stage.values())
                        * (dashboard.pipeline.forecast_confidence / 100)
                        * 0.15
                    ),
                ),
            },
        },
    }


@router.get("/analytics/benchmarks/{user_id}")
async def get_segment_benchmarks(
    user_id: str, segment: str = Query("active", description="User segment")
):
    """Get segment benchmarks and compare user vs segment."""
    dashboard = dashboard_engine.get_dashboard(user_id, segment, TimeRange.MONTH)
    benchmarks = dashboard.segment_benchmarks

    return {
        "segment": segment,
        "benchmarks": {
            "total_users": benchmarks.total_users,
            "active_users": benchmarks.active_users,
            "metrics": {
                "avg_leads_per_user": benchmarks.avg_leads_per_user,
                "avg_revenue_per_user": benchmarks.avg_revenue_per_user,
                "avg_conversion_rate": benchmarks.avg_conversion_rate,
            },
            "health": {
                "churn_rate": benchmarks.churn_rate,
                "expansion_rate": benchmarks.expansion_rate,
            },
        },
    }
