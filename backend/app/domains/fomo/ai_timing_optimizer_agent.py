"""
Fase B: AI Timing Optimizer Agent

Decides WHEN to send each FOMO message, per individual customer:
- Analyzes each customer's historical open/click pattern by hour-of-day
  and day-of-week to predict their optimal send window
- Adjusts automation delays dynamically based on typical response latency
  (fast responders get shorter follow-up delays, slow responders get longer
  windows) instead of the fixed 5min/2h/24h steps used elsewhere
- Reuses FOMOFatigueDetector (Fase D) rather than re-implementing fatigue
  detection — timing optimization must respect the same cooldown signal
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from statistics import median, mean

from app.core.logger import get_logger
from app.domains.fomo.ai_segmentation_agent import FOMOFatigueDetector

logger = get_logger(__name__)


# Population-level cold-start defaults (industry email/SMS benchmarks) —
# used when a customer has no engagement history to personalize from.
COLD_START_WINDOWS = [
    {"hour_range": (9, 11), "label": "morning", "weight": 0.35},
    {"hour_range": (13, 15), "label": "early_afternoon", "weight": 0.25},
    {"hour_range": (18, 21), "label": "evening", "weight": 0.40},
]

MIN_SAMPLES_FOR_PERSONALIZATION = 5

# Bounds so latency-based delay adjustment never produces something absurd.
DELAY_BOUNDS_MINUTES = {
    "immediate": (2, 30),        # e.g. cart_abandoned step 1 (base 5m)
    "short_followup": (30, 360),  # e.g. cart_abandoned step 2 (base 120m)
    "long_followup": (360, 4320),  # e.g. cart_abandoned step 3 (base 1440m/24h), capped at 3 days
}


class EngagementTimeAnalyzer:
    """Build an hour-of-day / day-of-week engagement heatmap from send history"""

    @staticmethod
    def build_heatmap(send_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """send_history: [{"sent_at": datetime, "opened": bool, "clicked": bool}, ...]
        Returns engagement score (0-1) per hour-of-day and per day-of-week,
        weighted by opens (1x) and clicks (2x)."""
        hour_scores: Dict[int, float] = {h: 0.0 for h in range(24)}
        hour_counts: Dict[int, int] = {h: 0 for h in range(24)}
        dow_scores: Dict[int, float] = {d: 0.0 for d in range(7)}
        dow_counts: Dict[int, int] = {d: 0 for d in range(7)}

        for send in send_history:
            sent_at = send.get("sent_at")
            if sent_at is None:
                continue
            hour = sent_at.hour
            dow = sent_at.weekday()

            engagement = (1 if send.get("opened") else 0) + (2 if send.get("clicked") else 0)

            hour_scores[hour] += engagement
            hour_counts[hour] += 1
            dow_scores[dow] += engagement
            dow_counts[dow] += 1

        hour_avg = {
            h: (hour_scores[h] / hour_counts[h] / 3.0) if hour_counts[h] > 0 else 0.0
            for h in range(24)
        }
        dow_avg = {
            d: (dow_scores[d] / dow_counts[d] / 3.0) if dow_counts[d] > 0 else 0.0
            for d in range(7)
        }

        return {
            "hour_engagement": hour_avg,
            "day_of_week_engagement": dow_avg,
            "sample_count": len(send_history),
            "sufficient_data": len(send_history) >= MIN_SAMPLES_FOR_PERSONALIZATION,
        }


class SendTimePredictor:
    """Predict the best send window for a customer — personalized when enough
    history exists, cold-start industry-default otherwise."""

    @staticmethod
    def predict_best_window(heatmap: Dict[str, Any]) -> Dict[str, Any]:
        if not heatmap["sufficient_data"]:
            best_cold_start = max(COLD_START_WINDOWS, key=lambda w: w["weight"])
            return {
                "personalized": False,
                "reason": "insufficient_history",
                "sample_count": heatmap["sample_count"],
                "recommended_hour_range": best_cold_start["hour_range"],
                "label": best_cold_start["label"],
                "confidence": "low",
            }

        hour_engagement = heatmap["hour_engagement"]
        best_hour = max(hour_engagement, key=hour_engagement.get)
        best_score = hour_engagement[best_hour]

        if best_score == 0.0:
            # Had history but zero engagement anywhere — fall back to cold-start
            best_cold_start = max(COLD_START_WINDOWS, key=lambda w: w["weight"])
            return {
                "personalized": False,
                "reason": "no_engagement_recorded",
                "sample_count": heatmap["sample_count"],
                "recommended_hour_range": best_cold_start["hour_range"],
                "label": best_cold_start["label"],
                "confidence": "low",
            }

        dow_engagement = heatmap["day_of_week_engagement"]
        best_dow = max(dow_engagement, key=dow_engagement.get)

        confidence = "high" if heatmap["sample_count"] >= 15 else "medium"

        return {
            "personalized": True,
            "sample_count": heatmap["sample_count"],
            "recommended_hour": best_hour,
            "recommended_hour_range": (max(0, best_hour - 1), min(23, best_hour + 1)),
            "recommended_day_of_week": best_dow,
            "confidence": confidence,
            "engagement_score": round(best_score, 3),
        }

    @staticmethod
    def next_send_datetime(
        prediction: Dict[str, Any],
        reference_date: Optional[datetime] = None,
    ) -> datetime:
        """Compute the next concrete datetime matching the predicted window"""
        reference_date = reference_date or datetime.now(timezone.utc)
        target_hour = prediction.get("recommended_hour")
        if target_hour is None:
            target_hour = prediction["recommended_hour_range"][0]

        candidate = reference_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if candidate <= reference_date:
            candidate += timedelta(days=1)

        target_dow = prediction.get("recommended_day_of_week")
        if target_dow is not None:
            days_ahead = (target_dow - candidate.weekday()) % 7
            candidate += timedelta(days=days_ahead)

        return candidate


class DynamicDelayAdjuster:
    """Adjust fixed automation delays based on a customer's typical response
    latency — replaces the static 5min/2h/24h steps with per-customer timing."""

    @staticmethod
    def compute_response_latency(send_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """send_history entries need 'sent_at' and optional 'opened_at' for
        messages that were opened. Returns latency stats in minutes."""
        latencies = []
        for send in send_history:
            sent_at = send.get("sent_at")
            opened_at = send.get("opened_at")
            if sent_at and opened_at and opened_at > sent_at:
                latencies.append((opened_at - sent_at).total_seconds() / 60)

        if not latencies:
            return {"has_data": False, "median_minutes": None, "mean_minutes": None}

        return {
            "has_data": True,
            "median_minutes": round(median(latencies), 1),
            "mean_minutes": round(mean(latencies), 1),
            "fastest_minutes": round(min(latencies), 1),
            "slowest_minutes": round(max(latencies), 1),
            "sample_count": len(latencies),
        }

    @staticmethod
    def adjust_delay(
        base_delay_minutes: int,
        latency_stats: Dict[str, Any],
        delay_category: str,
    ) -> Dict[str, Any]:
        """Scale a fixed base delay toward the customer's typical response
        latency, clipped to sane per-category bounds."""
        bounds = DELAY_BOUNDS_MINUTES.get(delay_category, (base_delay_minutes // 2, base_delay_minutes * 3))

        if not latency_stats.get("has_data"):
            return {
                "adjusted_delay_minutes": base_delay_minutes,
                "personalized": False,
                "reason": "no_latency_data",
            }

        median_latency = latency_stats["median_minutes"]

        # Fast responder: they typically open within minutes — shorten the
        # wait so the follow-up lands while intent is still warm.
        # Slow responder: give more room before following up, avoid nagging.
        if median_latency <= base_delay_minutes * 0.3:
            adjusted = base_delay_minutes * 0.6
        elif median_latency >= base_delay_minutes * 1.5:
            adjusted = base_delay_minutes * 1.4
        else:
            adjusted = base_delay_minutes

        adjusted = max(bounds[0], min(bounds[1], adjusted))

        return {
            "adjusted_delay_minutes": round(adjusted),
            "base_delay_minutes": base_delay_minutes,
            "personalized": True,
            "customer_median_latency_minutes": median_latency,
        }

    @staticmethod
    def optimize_sequence(
        base_delays: List[Dict[str, Any]],
        send_history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """base_delays: [{"step": 1, "delay_minutes": 5, "category": "immediate"}, ...]
        Returns the same steps with delay_minutes adjusted per customer."""
        latency_stats = DynamicDelayAdjuster.compute_response_latency(send_history)

        optimized = []
        for step in base_delays:
            result = DynamicDelayAdjuster.adjust_delay(
                step["delay_minutes"],
                latency_stats,
                step.get("category", "short_followup"),
            )
            optimized.append({
                **step,
                "delay_minutes": result["adjusted_delay_minutes"],
                "original_delay_minutes": step["delay_minutes"],
                "personalized": result["personalized"],
            })
        return optimized


class AITimingOptimizerAgent:
    """Fase B: Main agent — orchestrates engagement analysis, send-time
    prediction, dynamic delay adjustment, and fatigue-aware scheduling"""

    # Standard automation delay templates (mirrors workflow_integration.py's
    # cart_abandonment/flash_sale sequences) — the optimizer personalizes
    # these rather than hardcoding fixed minutes everywhere.
    AUTOMATION_BASE_DELAYS = {
        "cart_abandonment": [
            {"step": 1, "delay_minutes": 5, "category": "immediate", "channel": "email"},
            {"step": 2, "delay_minutes": 120, "category": "short_followup", "channel": "email"},
            {"step": 3, "delay_minutes": 1440, "category": "long_followup", "channel": "sms"},
        ],
        "flash_sale": [
            {"step": 1, "delay_minutes": 0, "category": "immediate", "channel": "email"},
            {"step": 2, "delay_minutes": 240, "category": "short_followup", "channel": "email"},
            {"step": 3, "delay_minutes": 1380, "category": "long_followup", "channel": "sms"},
            {"step": 4, "delay_minutes": 1410, "category": "long_followup", "channel": "sms"},
        ],
    }

    @staticmethod
    def analyze_engagement_patterns(send_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build the raw heatmap for a customer"""
        return EngagementTimeAnalyzer.build_heatmap(send_history)

    @staticmethod
    def predict_optimal_send_time(
        send_history: List[Dict[str, Any]],
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Predict when to send this customer's NEXT message"""
        heatmap = EngagementTimeAnalyzer.build_heatmap(send_history)
        prediction = SendTimePredictor.predict_best_window(heatmap)
        next_send = SendTimePredictor.next_send_datetime(prediction, reference_date)

        return {
            **prediction,
            "next_send_datetime": next_send.isoformat(),
        }

    @staticmethod
    def optimize_automation_schedule(
        automation_type: str,
        send_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Adjust a fixed automation sequence's delays for one customer"""
        base_delays = AITimingOptimizerAgent.AUTOMATION_BASE_DELAYS.get(automation_type)
        if base_delays is None:
            return {"error": "unknown_automation_type", "automation_type": automation_type}

        optimized_steps = DynamicDelayAdjuster.optimize_sequence(base_delays, send_history)
        latency_stats = DynamicDelayAdjuster.compute_response_latency(send_history)

        return {
            "automation_type": automation_type,
            "latency_profile": latency_stats,
            "steps": optimized_steps,
        }

    @staticmethod
    def get_send_recommendation(
        customer_id: str,
        automation_type: str,
        send_history: List[Dict[str, Any]],
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Full recommendation for one customer: best send window + adjusted
        delays + fatigue check (reusing Fase D's detector — timing must never
        override a cooldown recommendation)."""
        timing = AITimingOptimizerAgent.predict_optimal_send_time(send_history, reference_date)
        schedule = AITimingOptimizerAgent.optimize_automation_schedule(automation_type, send_history)

        fatigue_result = FOMOFatigueDetector.detect_fatigue(send_history)
        cooldown = FOMOFatigueDetector.recommend_cooldown(fatigue_result)

        return {
            "customer_id": customer_id,
            "automation_type": automation_type,
            "send_time_prediction": timing,
            "optimized_schedule": schedule,
            "fatigue_status": fatigue_result,
            "cleared_to_send": not fatigue_result["fatigued"],
            "cooldown_recommendation": cooldown if fatigue_result["fatigued"] else None,
        }

    @staticmethod
    def batch_optimize(
        customers_history: Dict[str, List[Dict[str, Any]]],
        automation_type: str,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Run get_send_recommendation for a batch of customers"""
        recommendations = []
        cleared_count = 0

        for customer_id, history in customers_history.items():
            rec = AITimingOptimizerAgent.get_send_recommendation(
                customer_id, automation_type, history, reference_date
            )
            recommendations.append(rec)
            if rec["cleared_to_send"]:
                cleared_count += 1

        return {
            "automation_type": automation_type,
            "total_customers": len(recommendations),
            "cleared_to_send": cleared_count,
            "on_cooldown": len(recommendations) - cleared_count,
            "recommendations": recommendations,
        }
