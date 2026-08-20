"""Unified analytics dashboard service — aggregate all location metrics."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.analytics.unified_dashboard_models import (
    UnifiedLocationMetric, BusinessDashboardSummary, LocationComparison, FunnelStageMetric
)

logger = logging.getLogger(__name__)


class UnifiedDashboardService:
    """Calculate and aggregate metrics across locations."""

    @staticmethod
    def aggregate_location_day(
        location_id: UUID,
        business_id: UUID,
        date: str,
        db: Session = None
    ) -> dict:
        """Aggregate all metrics for location on given date."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.locations.checkin_models import LocationCheckin, LocationFeedback
        from app.domains.staff.task_models import StaffTask, TaskStatus
        from app.domains.inventory.inventory_models import LocationInventory
        from app.domains.pricing.pricing_models import PricingTransaction

        date_start = datetime.fromisoformat(f"{date}T00:00:00+00:00")
        date_end = date_start + timedelta(days=1)

        # Foot traffic
        checkins = db.query(LocationCheckin).filter(
            LocationCheckin.location_id == location_id,
            LocationCheckin.created_at >= date_start,
            LocationCheckin.created_at < date_end
        ).all()

        total_visitors = len(checkins)
        avg_dwell = sum(c.dwell_seconds for c in checkins if c.dwell_seconds) // max(len([c for c in checkins if c.dwell_seconds]), 1)
        peak_hour = None
        if checkins:
            hours = [c.checkin_time.hour for c in checkins]
            peak_hour = max(set(hours), key=hours.count) if hours else None

        # Staff
        tasks = db.query(StaffTask).filter(
            StaffTask.location_id == location_id,
            StaffTask.assigned_at >= date_start,
            StaffTask.assigned_at < date_end
        ).all()

        tasks_completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        tasks_assigned = len(tasks)
        task_completion_rate = (tasks_completed / max(tasks_assigned, 1)) * 100

        # Feedback
        feedback_list = db.query(LocationFeedback).filter(
            LocationFeedback.location_id == location_id,
            LocationFeedback.created_at >= date_start,
            LocationFeedback.created_at < date_end,
            LocationFeedback.nps_score.isnot(None)
        ).all()

        nps_scores = [f.nps_score for f in feedback_list]
        nps_avg = sum(nps_scores) / len(nps_scores) if nps_scores else 0
        nps_detractors = len([s for s in nps_scores if s < 7])

        sentiments = [f.sentiment for f in feedback_list]
        positive_count = len([s for s in sentiments if s == "positive"])
        negative_count = len([s for s in sentiments if s == "negative"])
        sentiment_positive_pct = (positive_count / max(len(sentiments), 1)) * 100
        sentiment_negative_pct = (negative_count / max(len(sentiments), 1)) * 100

        # Revenue
        transactions = db.query(PricingTransaction).filter(
            PricingTransaction.location_id == location_id,
            PricingTransaction.created_at >= date_start,
            PricingTransaction.created_at < date_end
        ).all()

        base_revenue = sum(float(t.base_price) for t in transactions)
        final_revenue = sum(float(t.final_price) for t in transactions)
        total_discounts = sum(float(t.discount_amount) for t in transactions)
        revenue_per_visitor = final_revenue / max(total_visitors, 1)

        # Check or create metric
        existing = db.query(UnifiedLocationMetric).filter(
            UnifiedLocationMetric.location_id == location_id,
            UnifiedLocationMetric.date == date
        ).first()

        if existing:
            existing.total_visitors = total_visitors
            existing.avg_dwell_minutes = avg_dwell // 60
            existing.peak_hour = peak_hour
            existing.tasks_assigned = tasks_assigned
            existing.tasks_completed = tasks_completed
            existing.task_completion_rate = Decimal(str(task_completion_rate))
            existing.nps_avg = Decimal(str(round(nps_avg, 1)))
            existing.nps_detractors = nps_detractors
            existing.sentiment_positive_pct = Decimal(str(round(sentiment_positive_pct, 2)))
            existing.sentiment_negative_pct = Decimal(str(round(sentiment_negative_pct, 2)))
            existing.base_revenue = Decimal(str(base_revenue))
            existing.final_revenue = Decimal(str(final_revenue))
            existing.total_discounts = Decimal(str(total_discounts))
            existing.revenue_per_visitor = Decimal(str(round(revenue_per_visitor, 2)))
        else:
            existing = UnifiedLocationMetric(
                location_id=location_id,
                business_id=business_id,
                date=date,
                total_visitors=total_visitors,
                avg_dwell_minutes=avg_dwell // 60,
                peak_hour=peak_hour,
                tasks_assigned=tasks_assigned,
                tasks_completed=tasks_completed,
                task_completion_rate=Decimal(str(task_completion_rate)),
                nps_avg=Decimal(str(round(nps_avg, 1))),
                nps_detractors=nps_detractors,
                sentiment_positive_pct=Decimal(str(round(sentiment_positive_pct, 2))),
                sentiment_negative_pct=Decimal(str(round(sentiment_negative_pct, 2))),
                base_revenue=Decimal(str(base_revenue)),
                final_revenue=Decimal(str(final_revenue)),
                total_discounts=Decimal(str(total_discounts)),
                revenue_per_visitor=Decimal(str(round(revenue_per_visitor, 2)))
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        logger.info(f"Unified metrics aggregated: {location_id} on {date}")

        return {
            "location_id": str(location_id),
            "date": date,
            "visitors": total_visitors,
            "revenue": float(final_revenue),
            "nps_avg": float(nps_avg),
            "task_completion": int(task_completion_rate)
        }

    @staticmethod
    def generate_business_summary(
        business_id: UUID,
        date: str = None,
        db: Session = None
    ) -> dict:
        """Generate high-level business summary."""
        if not db:
            raise ValueError("Database session required")

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        from app.domains.locations.models import Location

        locations = db.query(Location).filter(Location.business_id == business_id).all()
        active_locations = len([l for l in locations if l.is_active])

        # Get metrics for past 30 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        metrics = db.query(UnifiedLocationMetric).filter(
            UnifiedLocationMetric.business_id == business_id,
            UnifiedLocationMetric.date >= cutoff_str
        ).all()

        if not metrics:
            return {"summary_generated": False, "reason": "No metrics available"}

        total_visitors = sum(m.total_visitors for m in metrics)
        total_revenue = sum(float(m.final_revenue) for m in metrics)
        avg_nps = sum(float(m.nps_avg) for m in metrics) / len(metrics) if metrics else 0
        avg_task_completion = sum(float(m.task_completion_rate) for m in metrics) / len(metrics)

        # Check or create summary
        existing = db.query(BusinessDashboardSummary).filter(
            BusinessDashboardSummary.business_id == business_id
        ).first()

        if existing:
            existing.date = date
            existing.total_locations = len(locations)
            existing.active_locations = active_locations
            existing.total_visitors_month = total_visitors
            existing.avg_visitors_per_location = Decimal(str(total_visitors / max(active_locations, 1)))
            existing.avg_nps_by_location = Decimal(str(round(avg_nps, 1)))
            existing.total_revenue_month = Decimal(str(total_revenue))
            existing.revenue_per_location = Decimal(str(total_revenue / max(active_locations, 1)))
            existing.overall_health_score = int(min(100, (avg_task_completion + (avg_nps * 10)) / 2))
        else:
            existing = BusinessDashboardSummary(
                business_id=business_id,
                date=date,
                total_locations=len(locations),
                active_locations=active_locations,
                total_visitors_month=total_visitors,
                avg_visitors_per_location=Decimal(str(total_visitors / max(active_locations, 1))),
                avg_nps_by_location=Decimal(str(round(avg_nps, 1))),
                total_revenue_month=Decimal(str(total_revenue)),
                revenue_per_location=Decimal(str(total_revenue / max(active_locations, 1))),
                overall_health_score=int(min(100, (avg_task_completion + (avg_nps * 10)) / 2))
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        logger.info(f"Business summary generated: {business_id}")

        return {
            "business_id": str(business_id),
            "locations": active_locations,
            "visitors_month": total_visitors,
            "revenue_month": float(total_revenue),
            "avg_nps": float(avg_nps),
            "health_score": existing.overall_health_score
        }

    @staticmethod
    def compare_locations(
        business_id: UUID,
        date: str,
        db: Session = None
    ) -> dict:
        """Compare metrics across locations to identify top/bottom performers."""
        if not db:
            raise ValueError("Database session required")

        metrics = db.query(UnifiedLocationMetric).filter(
            UnifiedLocationMetric.business_id == business_id,
            UnifiedLocationMetric.date == date
        ).all()

        if not metrics:
            return {"comparison_generated": False}

        # Find best/worst
        by_visitors = sorted(metrics, key=lambda m: m.total_visitors, reverse=True)
        by_revenue = sorted(metrics, key=lambda m: m.final_revenue, reverse=True)
        by_nps = sorted(metrics, key=lambda m: m.nps_avg, reverse=True)

        # Variance
        visitor_values = [m.total_visitors for m in metrics]
        revenue_values = [float(m.final_revenue) for m in metrics]
        nps_values = [float(m.nps_avg) for m in metrics]

        visitor_variance = (max(visitor_values) - min(visitor_values)) / max(sum(visitor_values) / len(visitor_values), 1) * 100 if visitor_values else 0
        revenue_variance = (max(revenue_values) - min(revenue_values)) / max(sum(revenue_values) / len(revenue_values), 1) * 100 if revenue_values else 0
        nps_variance = max(nps_values) - min(nps_values) if nps_values else 0

        comparison = LocationComparison(
            business_id=business_id,
            date=date,
            location_id_best_visitors=by_visitors[0].location_id if by_visitors else None,
            location_id_best_revenue=by_revenue[0].location_id if by_revenue else None,
            location_id_best_nps=by_nps[0].location_id if by_nps else None,
            location_id_lowest_visitors=by_visitors[-1].location_id if by_visitors else None,
            location_id_lowest_revenue=by_revenue[-1].location_id if by_revenue else None,
            location_id_lowest_nps=by_nps[-1].location_id if by_nps else None,
            visitor_variance_pct=Decimal(str(round(visitor_variance, 2))),
            revenue_variance_pct=Decimal(str(round(revenue_variance, 2))),
            nps_variance=Decimal(str(round(nps_variance, 1)))
        )

        db.add(comparison)
        db.commit()

        logger.info(f"Location comparison generated: {business_id} on {date}")

        return {
            "comparison_generated": True,
            "best_visitors": str(by_visitors[0].location_id) if by_visitors else None,
            "best_revenue": str(by_revenue[0].location_id) if by_revenue else None,
            "best_nps": str(by_nps[0].location_id) if by_nps else None,
            "visitor_variance_pct": float(visitor_variance),
            "revenue_variance_pct": float(revenue_variance)
        }
