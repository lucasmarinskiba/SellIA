"""Momentum Tracker — DAU/WAU/MAU, velocity, retention, churn."""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MomentumTracker:
    """Track growth momentum metrics."""

    @staticmethod
    def calculate_engagement_funnel(
        signups_day: int,
        active_day_1: int,
        active_day_7: int,
        active_day_30: int,
    ) -> Dict[str, Any]:
        """Calculate engagement funnel metrics."""

        dau = active_day_1
        wau = active_day_7
        mau = active_day_30

        return {
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "dau_to_mau_ratio": round(dau / mau, 2) if mau > 0 else 0,
            "day_1_retention": round(active_day_1 / signups_day * 100, 1),
            "day_7_retention": round(active_day_7 / signups_day * 100, 1),
            "day_30_retention": round(active_day_30 / signups_day * 100, 1),
            "health_score": "excellent" if active_day_30 / signups_day > 0.3 else "good" if active_day_30 / signups_day > 0.1 else "needs_improvement",
        }

    @staticmethod
    def track_cohort_retention(
        cohort_name: str,
        cohort_size: int,
        retention_by_week: List[int],
    ) -> Dict[str, Any]:
        """Track retention by cohort."""

        if not retention_by_week:
            return {}

        week_1_retention = retention_by_week[0] / cohort_size if len(retention_by_week) > 0 else 0
        week_4_retention = retention_by_week[-1] / cohort_size if retention_by_week else 0

        return {
            "cohort": cohort_name,
            "cohort_size": cohort_size,
            "week_1_retention": round(week_1_retention * 100, 1),
            "week_4_retention": round(week_4_retention * 100, 1),
            "retention_cliff": "Week 1" if week_1_retention < 0.3 else "Week 2+" if week_1_retention > 0.5 else "Gradual",
            "retention_by_week": retention_by_week,
        }

    @staticmethod
    def predict_churn(
        current_engagement_score: float,
        engagement_trend: str,  # "increasing", "stable", "decreasing"
    ) -> Dict[str, Any]:
        """Predict churn risk."""

        churn_risk = 0.1  # Base 10% churn

        if engagement_trend == "decreasing":
            churn_risk += 0.15
        elif engagement_trend == "increasing":
            churn_risk -= 0.05

        if current_engagement_score < 0.3:
            churn_risk += 0.2

        churn_risk = min(0.9, max(0.05, churn_risk))

        return {
            "churn_risk": round(churn_risk, 2),
            "risk_level": "critical" if churn_risk > 0.5 else "high" if churn_risk > 0.3 else "low",
            "engagement_score": current_engagement_score,
            "trend": engagement_trend,
            "intervention": "Win-back campaign" if churn_risk > 0.5 else "Re-engagement email" if churn_risk > 0.3 else "Monitor",
        }

    @staticmethod
    def calculate_growth_rate(
        metric_history: List[Dict[str, Any]],
        metric_name: str,
    ) -> Dict[str, Any]:
        """Calculate MoM growth rate."""

        if len(metric_history) < 2:
            return {"growth_rate": 0, "data_insufficient": True}

        recent = metric_history[-1].get(metric_name, 0)
        previous = metric_history[-2].get(metric_name, 1)

        growth_rate = ((recent - previous) / previous * 100) if previous > 0 else 0

        return {
            "metric": metric_name,
            "growth_rate_pct": round(growth_rate, 1),
            "growth_trend": "accelerating" if growth_rate > 15 else "healthy" if growth_rate > 5 else "slowing",
            "status": "on_track" if growth_rate >= 15 else "warning" if growth_rate >= 5 else "concerning",
        }

    @staticmethod
    def forecast_growth(
        current_users: int,
        monthly_growth_rate: float,  # e.g., 0.15 for 15%
        months: int = 12,
    ) -> List[Dict[str, Any]]:
        """Forecast user growth."""

        forecast = []
        current = current_users

        for month in range(months + 1):
            forecast.append({
                "month": month,
                "users": int(current),
                "monthly_new": int(current * monthly_growth_rate) if month > 0 else 0,
            })
            current *= (1 + monthly_growth_rate)

        return forecast

    @staticmethod
    def identify_growth_stage(
        dau: int,
        monthly_growth_rate: float,
    ) -> str:
        """Identify current growth stage."""

        if dau < 100:
            return "pre_launch"
        elif dau < 1000 and monthly_growth_rate > 0.3:
            return "hypergrowth"
        elif dau < 10000 and monthly_growth_rate > 0.15:
            return "growth"
        elif monthly_growth_rate > 0.05:
            return "mature"
        else:
            return "plateau"
