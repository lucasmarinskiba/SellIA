"""Unified analytics dashboard API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import timezone, timedelta, datetime

from app.core.database import get_db
from app.domains.analytics.unified_dashboard_service import UnifiedDashboardService

router = APIRouter(prefix="/api/v1", tags=["unified-dashboard"])


@router.post("/locations/{location_id}/metrics/aggregate")
async def aggregate_location_metrics(
    location_id: UUID,
    date: str = Query(...),  # YYYY-MM-DD
    db: Session = Depends(get_db),
) -> dict:
    """Aggregate all metrics for location on given date."""
    try:
        result = UnifiedDashboardService.aggregate_location_day(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: from location
            date=date,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/businesses/{business_id}/summary")
async def generate_business_summary(
    business_id: UUID,
    date: Optional[str] = Query(None),  # YYYY-MM-DD, default today
    db: Session = Depends(get_db),
) -> dict:
    """Generate high-level business summary."""
    try:
        result = UnifiedDashboardService.generate_business_summary(
            business_id=business_id,
            date=date,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/businesses/{business_id}/location-comparison")
async def compare_locations(
    business_id: UUID,
    date: str = Query(...),  # YYYY-MM-DD
    db: Session = Depends(get_db),
) -> dict:
    """Compare metrics across locations."""
    try:
        result = UnifiedDashboardService.compare_locations(
            business_id=business_id,
            date=date,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/unified-metrics")
async def get_location_unified_metrics(
    location_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """Get unified metrics for location over time period."""
    try:
        from app.domains.analytics.unified_dashboard_models import UnifiedLocationMetric

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        metrics = db.query(UnifiedLocationMetric).filter(
            UnifiedLocationMetric.location_id == location_id,
            UnifiedLocationMetric.date >= cutoff_str
        ).order_by(UnifiedLocationMetric.date.desc()).all()

        metric_data = [
            {
                "date": m.date,
                "visitors": m.total_visitors,
                "avg_dwell_min": m.avg_dwell_minutes,
                "peak_hour": m.peak_hour,
                "nps_avg": float(m.nps_avg),
                "revenue": float(m.final_revenue),
                "task_completion_rate": float(m.task_completion_rate),
                "revenue_per_visitor": float(m.revenue_per_visitor),
            }
            for m in metrics
        ]

        return {
            "location_id": str(location_id),
            "period_days": days,
            "data_points": metric_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/businesses/{business_id}/unified-dashboard")
async def get_business_dashboard(
    business_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Get unified dashboard for entire business."""
    try:
        from app.domains.analytics.unified_dashboard_models import BusinessDashboardSummary

        summary = db.query(BusinessDashboardSummary).filter(
            BusinessDashboardSummary.business_id == business_id
        ).first()

        if not summary:
            return {"dashboard_available": False}

        return {
            "dashboard_available": True,
            "business_id": str(business_id),
            "locations": summary.active_locations,
            "total_locations": summary.total_locations,
            "metrics": {
                "visitors_month": summary.total_visitors_month,
                "unique_visitors": summary.unique_visitors_month,
                "avg_visitors_per_location": float(summary.avg_visitors_per_location),
                "revenue_month": float(summary.total_revenue_month),
                "attributed_revenue": float(summary.attributed_revenue_month),
                "attribution_rate": float(summary.attribution_rate),
                "avg_nps": float(summary.avg_nps_by_location),
                "avg_discount_rate": float(summary.avg_discount_rate),
                "inventory_turnover": float(summary.avg_inventory_turnover),
                "stock_outs": summary.total_stock_outs,
            },
            "health_score": summary.overall_health_score,
            "last_updated": summary.timestamp.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
