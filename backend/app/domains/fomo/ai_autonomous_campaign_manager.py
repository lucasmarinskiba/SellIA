"""
Fase E: AI Autonomous Campaign Manager

Runs the FOMO campaign lifecycle end-to-end with minimal human input:
- OpportunityDetector: spots reasons to launch a campaign (low stock,
  upcoming seasonal event, competitor activity signal)
- CampaignAutoBuilder: turns an opportunity into a concrete campaign plan
  (template, tone, discount, send window) — reuses Fase C's stock/discount
  calibration and Fase B's cold-start send-time prediction rather than
  re-deriving them
- PerformanceMonitor + AutoScaler: watches live metrics, decides whether to
  pause (negative ROI), scale up (strong ROI), or hold steady
- DailyReportGenerator: plain-language daily summary of what happened and
  what the agent did about it

This agent does NOT re-implement scarcity math, timing, or copywriting — it
orchestrates the agents from Fases A/B/C. It does not do competitor scraping
(that's Fase F's job); it only accepts a competitor signal as input.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from app.core.logger import get_logger
from app.domains.fomo.ai_scarcity_calibration_agent import (
    StockDisplayCalibrator,
    DiscountElasticityCalibrator,
)
from app.domains.fomo.ai_timing_optimizer_agent import SendTimePredictor, COLD_START_WINDOWS

logger = get_logger(__name__)


# Approximate FOMO-relevant calendar dates (month, day). Some (Black Friday,
# Mother's Day) technically float year to year — fixed here as a reasonable
# heuristic anchor, not a precise holiday calculator.
FOMO_CALENDAR = [
    {"name": "New Year Sale", "month": 1, "day": 1, "template_type": "flash_sale"},
    {"name": "Valentine's Day", "month": 2, "day": 14, "template_type": "countdown"},
    {"name": "Mother's Day", "month": 5, "day": 11, "template_type": "countdown"},
    {"name": "Summer Sale Kickoff", "month": 7, "day": 1, "template_type": "flash_sale"},
    {"name": "Back to School", "month": 8, "day": 15, "template_type": "scarcity"},
    {"name": "Black Friday", "month": 11, "day": 29, "template_type": "flash_sale"},
    {"name": "Cyber Monday", "month": 12, "day": 2, "template_type": "flash_sale"},
    {"name": "Christmas Countdown", "month": 12, "day": 25, "template_type": "countdown"},
]


class OpportunityDetector:
    """Detect reasons to launch a FOMO campaign"""

    @staticmethod
    def detect_stock_opportunity(
        real_stock: int,
        product_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        tier = StockDisplayCalibrator.compute_display_tier(real_stock)
        if tier["tier"] not in ("low", "critical"):
            return None

        return {
            "type": "low_stock",
            "priority": "high" if tier["tier"] == "critical" else "medium",
            "product_id": product_id,
            "real_stock": real_stock,
            "suggested_template_type": "scarcity",
            "detail": tier,
        }

    @staticmethod
    def detect_seasonal_opportunity(
        reference_date: Optional[datetime] = None,
        lead_time_days: int = 14,
    ) -> Optional[Dict[str, Any]]:
        reference_date = reference_date or datetime.now(timezone.utc)

        closest = None
        closest_days = None

        for event in FOMO_CALENDAR:
            try:
                candidate = reference_date.replace(
                    month=event["month"], day=event["day"],
                    hour=0, minute=0, second=0, microsecond=0,
                )
            except ValueError:
                continue  # e.g. Feb 29 on a non-leap reference year

            if candidate.date() < reference_date.date():
                candidate = candidate.replace(year=candidate.year + 1)

            days_until = (candidate.date() - reference_date.date()).days

            if 0 <= days_until <= lead_time_days:
                if closest_days is None or days_until < closest_days:
                    closest = event
                    closest_days = days_until

        if closest is None:
            return None

        return {
            "type": "seasonal_event",
            "priority": "high" if closest_days <= 3 else "medium",
            "event_name": closest["name"],
            "days_until": closest_days,
            "suggested_template_type": closest["template_type"],
        }

    @staticmethod
    def detect_competitor_opportunity(
        competitor_signal: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """competitor_signal (produced elsewhere, e.g. Fase F when built):
        {"competitor_name": str, "discount_percent": float, "detected_at": datetime}"""
        if not competitor_signal:
            return None

        discount = competitor_signal.get("discount_percent", 0)
        if discount < 15:
            return None  # not significant enough to react to

        return {
            "type": "competitor_activity",
            "priority": "high" if discount >= 30 else "medium",
            "competitor_name": competitor_signal.get("competitor_name", "unknown"),
            "competitor_discount_percent": discount,
            "suggested_template_type": "flash_sale",
        }

    @staticmethod
    def detect_all(
        real_stock: Optional[int] = None,
        product_id: Optional[str] = None,
        reference_date: Optional[datetime] = None,
        competitor_signal: Optional[Dict[str, Any]] = None,
        seasonal_lead_time_days: int = 14,
    ) -> List[Dict[str, Any]]:
        opportunities = []

        if real_stock is not None:
            stock_opp = OpportunityDetector.detect_stock_opportunity(real_stock, product_id)
            if stock_opp:
                opportunities.append(stock_opp)

        seasonal_opp = OpportunityDetector.detect_seasonal_opportunity(
            reference_date, seasonal_lead_time_days
        )
        if seasonal_opp:
            opportunities.append(seasonal_opp)

        competitor_opp = OpportunityDetector.detect_competitor_opportunity(competitor_signal)
        if competitor_opp:
            opportunities.append(competitor_opp)

        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(key=lambda o: priority_order.get(o["priority"], 3))
        return opportunities


class CampaignAutoBuilder:
    """Turn a detected opportunity into a concrete campaign plan"""

    @staticmethod
    def build_campaign_plan(
        opportunity: Dict[str, Any],
        discount_historical_data: Optional[List[Dict[str, float]]] = None,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        template_type = opportunity["suggested_template_type"]

        discount = DiscountElasticityCalibrator.recommend_optimal_discount(
            discount_historical_data or []
        )

        # Population-level cold-start send window (this plan targets a broad
        # audience, not one individual customer — per-customer personalization
        # happens later via Fase B when the campaign actually sends)
        best_cold_start = max(COLD_START_WINDOWS, key=lambda w: w["weight"])

        tone = "urgent" if opportunity["priority"] == "high" else "friendly"

        return {
            "opportunity_source": opportunity["type"],
            "opportunity_priority": opportunity["priority"],
            "template_type": template_type,
            "tone": tone,
            "recommended_discount_percent": discount["recommended_discount_percent"],
            "discount_confidence": discount["confidence"],
            "send_window": best_cold_start,
            "created_at": (reference_date or datetime.now(timezone.utc)).isoformat(),
            "status": "planned",
        }


class PerformanceMonitor:
    """Watch live campaign metrics and classify health"""

    NEGATIVE_ROI_THRESHOLD = -0.1  # -10% or worse
    STRONG_ROI_THRESHOLD = 2.0     # 200%+ ROI

    @staticmethod
    def compute_roi(revenue: float, cost: float) -> float:
        if cost <= 0:
            return 0.0
        return (revenue - cost) / cost

    @staticmethod
    def evaluate_campaign_health(metrics: Dict[str, float]) -> Dict[str, Any]:
        """metrics: {"impressions", "conversions", "revenue", "cost"}"""
        revenue = metrics.get("revenue", 0.0)
        cost = metrics.get("cost", 0.0)
        impressions = metrics.get("impressions", 0)
        conversions = metrics.get("conversions", 0)

        roi = PerformanceMonitor.compute_roi(revenue, cost)
        conversion_rate = conversions / impressions if impressions > 0 else 0.0

        if roi <= PerformanceMonitor.NEGATIVE_ROI_THRESHOLD:
            status = "negative_roi"
        elif roi >= PerformanceMonitor.STRONG_ROI_THRESHOLD:
            status = "strong_performance"
        else:
            status = "healthy"

        return {
            "status": status,
            "roi": round(roi, 4),
            "conversion_rate": round(conversion_rate, 4),
            "revenue": revenue,
            "cost": cost,
        }

    @staticmethod
    def detect_roi_trend(metrics_history: List[Dict[str, float]]) -> Dict[str, Any]:
        """metrics_history: daily [{"revenue", "cost"}, ...] ordered oldest to newest"""
        if len(metrics_history) < 2:
            return {"trend": "insufficient_data", "days_evaluated": len(metrics_history)}

        rois = [PerformanceMonitor.compute_roi(m.get("revenue", 0), m.get("cost", 0)) for m in metrics_history]

        declines = sum(1 for i in range(1, len(rois)) if rois[i] < rois[i - 1])
        decline_ratio = declines / (len(rois) - 1)

        if decline_ratio >= 0.66:
            trend = "declining"
        elif decline_ratio <= 0.33:
            trend = "improving"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "days_evaluated": len(metrics_history),
            "latest_roi": round(rois[-1], 4),
            "decline_ratio": round(decline_ratio, 3),
        }


class AutoScaler:
    """Decide + size the pause/scale action from a health evaluation"""

    MAX_SCALE_INCREASE = 0.5  # never more than +50% at once

    @staticmethod
    def decide_action(
        health: Dict[str, Any],
        trend: Optional[Dict[str, Any]] = None,
        current_budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        if health["status"] == "negative_roi":
            return {
                "action": "auto_pause",
                "reason": f"ROI at {health['roi']:.1%} is below the pause threshold",
            }

        if trend and trend.get("trend") == "declining" and health["status"] != "strong_performance":
            return {
                "action": "auto_pause",
                "reason": "ROI trending down across recent days even though not yet negative",
            }

        if health["status"] == "strong_performance":
            new_budget = None
            if current_budget is not None:
                new_budget = round(current_budget * (1 + AutoScaler.MAX_SCALE_INCREASE), 2)
            return {
                "action": "auto_scale",
                "reason": f"ROI at {health['roi']:.1%} exceeds the scale-up threshold",
                "scale_increase_percent": AutoScaler.MAX_SCALE_INCREASE * 100,
                "current_budget": current_budget,
                "recommended_budget": new_budget,
            }

        return {"action": "continue", "reason": "Performance within normal healthy range"}


class DailyReportGenerator:
    """Plain-language daily campaign summary"""

    @staticmethod
    def generate_daily_report(
        campaign_id: str,
        today_metrics: Dict[str, float],
        health: Dict[str, Any],
        action: Dict[str, Any],
        report_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        report_date = report_date or datetime.now(timezone.utc)

        return {
            "campaign_id": campaign_id,
            "date": report_date.date().isoformat(),
            "summary": {
                "revenue": today_metrics.get("revenue", 0.0),
                "cost": today_metrics.get("cost", 0.0),
                "roi": health["roi"],
                "conversion_rate": health["conversion_rate"],
                "status": health["status"],
            },
            "action_taken": action["action"],
            "action_reason": action["reason"],
            "headline": DailyReportGenerator._headline(health, action),
        }

    @staticmethod
    def _headline(health: Dict[str, Any], action: Dict[str, Any]) -> str:
        if action["action"] == "auto_pause":
            return f"⏸️ Campaña pausada automáticamente — ROI {health['roi']:.1%}"
        if action["action"] == "auto_scale":
            return f"📈 Campaña escalada automáticamente — ROI {health['roi']:.1%}"
        return f"✅ Campaña saludable — ROI {health['roi']:.1%}, conversión {health['conversion_rate']:.1%}"


class AIAutonomousCampaignManager:
    """Fase E: Main agent — scan for opportunities, build campaigns, monitor,
    decide pause/scale, report daily"""

    @staticmethod
    def scan_for_opportunities(
        real_stock: Optional[int] = None,
        product_id: Optional[str] = None,
        reference_date: Optional[datetime] = None,
        competitor_signal: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        opportunities = OpportunityDetector.detect_all(
            real_stock, product_id, reference_date, competitor_signal
        )
        return {"opportunities_found": len(opportunities), "opportunities": opportunities}

    @staticmethod
    def create_campaign_from_opportunity(
        opportunity: Dict[str, Any],
        discount_historical_data: Optional[List[Dict[str, float]]] = None,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        return CampaignAutoBuilder.build_campaign_plan(
            opportunity, discount_historical_data, reference_date
        )

    @staticmethod
    def monitor_and_decide(
        today_metrics: Dict[str, float],
        metrics_history: Optional[List[Dict[str, float]]] = None,
        current_budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        health = PerformanceMonitor.evaluate_campaign_health(today_metrics)
        trend = PerformanceMonitor.detect_roi_trend(metrics_history or [])
        action = AutoScaler.decide_action(health, trend, current_budget)

        return {"health": health, "trend": trend, "action": action}

    @staticmethod
    def run_daily_cycle(
        campaign_id: str,
        today_metrics: Dict[str, float],
        metrics_history: Optional[List[Dict[str, float]]] = None,
        current_budget: Optional[float] = None,
        report_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Full daily cycle for an ALREADY-RUNNING campaign: monitor -> decide -> report"""
        decision = AIAutonomousCampaignManager.monitor_and_decide(
            today_metrics, metrics_history, current_budget
        )
        report = DailyReportGenerator.generate_daily_report(
            campaign_id, today_metrics, decision["health"], decision["action"], report_date
        )
        return {**decision, "daily_report": report}

    @staticmethod
    def full_autonomous_cycle(
        real_stock: Optional[int] = None,
        product_id: Optional[str] = None,
        reference_date: Optional[datetime] = None,
        competitor_signal: Optional[Dict[str, Any]] = None,
        discount_historical_data: Optional[List[Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """Scan -> plan for the single highest-priority opportunity (a NEW
        campaign, no metrics history yet — monitoring starts once it sends)"""
        scan = AIAutonomousCampaignManager.scan_for_opportunities(
            real_stock, product_id, reference_date, competitor_signal
        )

        if scan["opportunities_found"] == 0:
            return {**scan, "campaign_plan": None}

        top_opportunity = scan["opportunities"][0]
        plan = AIAutonomousCampaignManager.create_campaign_from_opportunity(
            top_opportunity, discount_historical_data, reference_date
        )

        return {**scan, "campaign_plan": plan}
