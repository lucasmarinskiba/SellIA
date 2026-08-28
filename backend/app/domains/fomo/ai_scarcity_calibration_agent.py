"""
Fase C: AI Scarcity Calibration Agent

Calibrates scarcity/urgency messaging so it stays truthful AND effective:
- StockDisplayCalibrator: never shows a scarcity claim the real stock doesn't
  back up (FTC-style deceptive-scarcity compliance risk)
- DiscountElasticityCalibrator: fits a lightweight elasticity curve from
  historical discount->conversion data to recommend the discount level that
  maximizes revenue, not just conversion rate
- UrgencyFatigueDetector: campaign/segment-level version of fatigue — detects
  when urgency wording itself is losing effect across consecutive sends
  (distinct from Fase D's FOMOFatigueDetector, which is per-customer)
- IntensityABTestManager: two-proportion z-test to decide, with statistical
  confidence, whether a stronger urgency variant actually outperforms a
  softer one, or whether the test needs more data before acting
"""

import math
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from app.core.logger import get_logger

logger = get_logger(__name__)


class StockDisplayCalibrator:
    """Ensure displayed scarcity messaging is truthful relative to real stock —
    protects against deceptive-scarcity compliance risk (FTC Act Section 5 /
    equivalent consumer protection rules in most markets treat fabricated
    urgency/scarcity claims as an unfair or deceptive practice)."""

    DEFAULT_LOW_THRESHOLD = 20
    DEFAULT_CRITICAL_THRESHOLD = 5

    @staticmethod
    def compute_display_tier(
        real_stock: int,
        low_threshold: int = DEFAULT_LOW_THRESHOLD,
        critical_threshold: int = DEFAULT_CRITICAL_THRESHOLD,
    ) -> Dict[str, Any]:
        """Decide what tier of scarcity messaging is truthfully justified"""
        if real_stock <= 0:
            return {
                "tier": "out_of_stock",
                "show_scarcity_message": False,
                "message": "Agotado",
                "real_stock": real_stock,
            }
        if real_stock <= critical_threshold:
            return {
                "tier": "critical",
                "show_scarcity_message": True,
                "message": f"¡Solo {real_stock} quedan!",
                "real_stock": real_stock,
            }
        if real_stock <= low_threshold:
            return {
                "tier": "low",
                "show_scarcity_message": True,
                "message": f"Quedan {real_stock} unidades",
                "real_stock": real_stock,
            }
        return {
            "tier": "plenty",
            "show_scarcity_message": False,
            "message": None,
            "real_stock": real_stock,
            "note": "Stock abundante — no mostrar mensaje de escasez sería engañoso",
        }

    @staticmethod
    def validate_scarcity_claim(displayed_message: str, real_stock: int) -> Dict[str, Any]:
        """Check a displayed message's numeric claim against real stock.
        Flags BOTH directions of deception: claiming a lower number than
        reality (fake urgency) and using urgency language while stock is
        actually abundant."""
        numbers = re.findall(r"\d+", displayed_message)
        claimed_stock = int(numbers[0]) if numbers else None

        urgency_words = ["solo", "último", "última", "quedan", "agotándose", "only", "last", "limited"]
        uses_urgency_language = any(w in displayed_message.lower() for w in urgency_words)

        issues = []

        if claimed_stock is not None and claimed_stock < real_stock:
            issues.append({
                "type": "understated_stock",
                "detail": f"Mensaje dice '{claimed_stock}' pero el stock real es {real_stock} — riesgo de escasez falsa",
            })

        if uses_urgency_language and claimed_stock is None and real_stock > StockDisplayCalibrator.DEFAULT_LOW_THRESHOLD:
            issues.append({
                "type": "unjustified_urgency",
                "detail": f"Lenguaje de urgencia sin número, pero stock real ({real_stock}) es abundante",
            })

        return {
            "compliant": len(issues) == 0,
            "claimed_stock": claimed_stock,
            "real_stock": real_stock,
            "issues": issues,
        }


class DiscountElasticityCalibrator:
    """Fit a lightweight elasticity curve from historical discount/conversion
    data to recommend the revenue-maximizing discount within bounds — deeper
    discounts raise conversion but eat margin, so conversion rate alone is
    the wrong optimization target."""

    @staticmethod
    def fit_elasticity_curve(
        historical_data: List[Dict[str, float]],
    ) -> Optional[Tuple[float, float]]:
        """historical_data: [{"discount_percent": float, "conversion_rate": float}, ...]
        Returns (slope, intercept) of a simple least-squares linear fit, or
        None if there isn't enough distinct data to fit a line."""
        points = [(d["discount_percent"], d["conversion_rate"]) for d in historical_data]
        distinct_x = set(p[0] for p in points)
        if len(points) < 2 or len(distinct_x) < 2:
            return None

        n = len(points)
        sum_x = sum(p[0] for p in points)
        sum_y = sum(p[1] for p in points)
        sum_xy = sum(p[0] * p[1] for p in points)
        sum_xx = sum(p[0] * p[0] for p in points)

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return None

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept

    @staticmethod
    def predict_conversion_rate(discount_percent: float, slope: float, intercept: float) -> float:
        predicted = slope * discount_percent + intercept
        return max(0.0, min(1.0, predicted))

    @staticmethod
    def recommend_optimal_discount(
        historical_data: List[Dict[str, float]],
        min_discount: int = 10,
        max_discount: int = 50,
        step: int = 5,
    ) -> Dict[str, Any]:
        """Sweep candidate discounts within bounds, predicting conversion rate
        via the fitted curve, and pick the one maximizing a margin-adjusted
        revenue proxy: conversion_rate * (1 - discount/100)."""
        curve = DiscountElasticityCalibrator.fit_elasticity_curve(historical_data)

        if curve is None:
            return {
                "recommended_discount_percent": 20,
                "confidence": "low",
                "reason": "insufficient_historical_data",
                "data_points": len(historical_data),
            }

        slope, intercept = curve
        candidates = []
        for discount in range(min_discount, max_discount + 1, step):
            predicted_cr = DiscountElasticityCalibrator.predict_conversion_rate(discount, slope, intercept)
            revenue_score = predicted_cr * (1 - discount / 100)
            candidates.append({
                "discount_percent": discount,
                "predicted_conversion_rate": round(predicted_cr, 4),
                "revenue_score": round(revenue_score, 4),
            })

        best = max(candidates, key=lambda c: c["revenue_score"])

        return {
            "recommended_discount_percent": best["discount_percent"],
            "predicted_conversion_rate": best["predicted_conversion_rate"],
            "confidence": "high" if len(historical_data) >= 5 else "medium",
            "data_points": len(historical_data),
            "elasticity_slope": round(slope, 5),
            "all_candidates": candidates,
        }


class UrgencyFatigueDetector:
    """Campaign/segment-level fatigue — detects when urgency WORDING itself
    is losing effect across consecutive campaigns using the same intensity,
    independent of any single customer's individual engagement (Fase D)."""

    MIN_CAMPAIGNS_TO_EVALUATE = 3

    @staticmethod
    def detect_intensity_fatigue(
        campaign_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """campaign_history: [{"sent_at": datetime, "urgency_intensity": str,
        "conversion_rate": float}, ...] ordered oldest to newest, all using
        the SAME intensity level."""
        if len(campaign_history) < UrgencyFatigueDetector.MIN_CAMPAIGNS_TO_EVALUATE:
            return {
                "fatigued": False,
                "reason": "insufficient_campaign_history",
                "campaigns_evaluated": len(campaign_history),
            }

        rates = [c["conversion_rate"] for c in campaign_history]

        # Consecutive-decline check: how many of the last N steps dropped
        # from the one before it
        declines = sum(1 for i in range(1, len(rates)) if rates[i] < rates[i - 1])
        decline_ratio = declines / (len(rates) - 1)

        # Trend check: compare average of the first half vs second half
        midpoint = len(rates) // 2
        first_half_avg = sum(rates[:midpoint]) / midpoint if midpoint > 0 else rates[0]
        second_half_avg = sum(rates[midpoint:]) / (len(rates) - midpoint)

        relative_drop = (
            (first_half_avg - second_half_avg) / first_half_avg
            if first_half_avg > 0 else 0
        )

        fatigued = decline_ratio >= 0.66 and relative_drop >= 0.15

        return {
            "fatigued": fatigued,
            "reason": "declining_intensity_returns" if fatigued else "stable_effectiveness",
            "campaigns_evaluated": len(campaign_history),
            "decline_ratio": round(decline_ratio, 3),
            "relative_drop": round(relative_drop, 3),
            "first_half_avg_conversion": round(first_half_avg, 4),
            "second_half_avg_conversion": round(second_half_avg, 4),
        }

    @staticmethod
    def recommend_intensity_adjustment(fatigue_result: Dict[str, Any]) -> Dict[str, Any]:
        if not fatigue_result["fatigued"]:
            return {"action": "maintain_current_intensity"}
        return {
            "action": "reduce_urgency_intensity",
            "note": "Bajar intensidad del wording o rotar mensajes — la audiencia se está habituando a la urgencia actual",
            "suggested_cooldown_campaigns": 2,
        }


class IntensityABTestManager:
    """Two-proportion z-test to determine, with statistical confidence,
    whether one urgency intensity variant beats another."""

    @staticmethod
    def z_test_two_proportions(
        conversions_a: int,
        visitors_a: int,
        conversions_b: int,
        visitors_b: int,
    ) -> Dict[str, Any]:
        if visitors_a == 0 or visitors_b == 0:
            return {"error": "insufficient_sample", "significant": False}

        p_a = conversions_a / visitors_a
        p_b = conversions_b / visitors_b
        p_pool = (conversions_a + conversions_b) / (visitors_a + visitors_b)

        se = math.sqrt(p_pool * (1 - p_pool) * (1 / visitors_a + 1 / visitors_b))
        if se == 0:
            return {
                "conversion_rate_a": p_a, "conversion_rate_b": p_b,
                "z_score": 0.0, "p_value": 1.0, "significant": False,
            }

        z = (p_b - p_a) / se
        # two-tailed p-value from the standard normal CDF
        p_value = 2 * (1 - IntensityABTestManager._normal_cdf(abs(z)))

        return {
            "conversion_rate_a": round(p_a, 4),
            "conversion_rate_b": round(p_b, 4),
            "z_score": round(z, 4),
            "p_value": round(p_value, 4),
            "significant": p_value < 0.05,
            "lift": round((p_b - p_a) / p_a, 4) if p_a > 0 else None,
        }

    @staticmethod
    def _normal_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def analyze_intensity_test(
        variant_low: Dict[str, int],
        variant_high: Dict[str, int],
        min_sample_size: int = 100,
    ) -> Dict[str, Any]:
        """variant_low/high: {"conversions": int, "visitors": int}"""
        result = IntensityABTestManager.z_test_two_proportions(
            variant_low["conversions"], variant_low["visitors"],
            variant_high["conversions"], variant_high["visitors"],
        )

        if "error" in result:
            return {**result, "recommendation": "insufficient_data"}

        under_powered = (
            variant_low["visitors"] < min_sample_size
            or variant_high["visitors"] < min_sample_size
        )

        if under_powered:
            recommendation = "continue_test"
        elif result["significant"] and result["lift"] and result["lift"] > 0:
            recommendation = "adopt_high_intensity"
        elif result["significant"] and result["lift"] and result["lift"] < 0:
            recommendation = "adopt_low_intensity"
        else:
            recommendation = "no_significant_difference_use_low_intensity"
            # ties go to the softer variant — less urgency-fatigue risk long-term

        return {
            **result,
            "under_powered": under_powered,
            "recommendation": recommendation,
        }


class AIScarcityCalibrationAgent:
    """Fase C: Main agent — orchestrates stock-claim compliance, discount
    elasticity, urgency-intensity fatigue, and A/B test analysis"""

    @staticmethod
    def calibrate_stock_display(
        real_stock: int,
        low_threshold: int = StockDisplayCalibrator.DEFAULT_LOW_THRESHOLD,
        critical_threshold: int = StockDisplayCalibrator.DEFAULT_CRITICAL_THRESHOLD,
    ) -> Dict[str, Any]:
        return StockDisplayCalibrator.compute_display_tier(real_stock, low_threshold, critical_threshold)

    @staticmethod
    def audit_scarcity_message(displayed_message: str, real_stock: int) -> Dict[str, Any]:
        return StockDisplayCalibrator.validate_scarcity_claim(displayed_message, real_stock)

    @staticmethod
    def calibrate_discount(
        historical_data: List[Dict[str, float]],
        min_discount: int = 10,
        max_discount: int = 50,
    ) -> Dict[str, Any]:
        return DiscountElasticityCalibrator.recommend_optimal_discount(
            historical_data, min_discount, max_discount
        )

    @staticmethod
    def check_urgency_fatigue(campaign_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        fatigue = UrgencyFatigueDetector.detect_intensity_fatigue(campaign_history)
        adjustment = UrgencyFatigueDetector.recommend_intensity_adjustment(fatigue)
        return {**fatigue, "recommendation": adjustment}

    @staticmethod
    def run_ab_test_analysis(
        variant_low: Dict[str, int],
        variant_high: Dict[str, int],
        min_sample_size: int = 100,
    ) -> Dict[str, Any]:
        return IntensityABTestManager.analyze_intensity_test(variant_low, variant_high, min_sample_size)

    @staticmethod
    def full_calibration(
        real_stock: int,
        discount_historical_data: List[Dict[str, float]],
        campaign_history: List[Dict[str, Any]],
        ab_test_variants: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> Dict[str, Any]:
        """Run all four calibrations together for one campaign decision"""
        stock_display = AIScarcityCalibrationAgent.calibrate_stock_display(real_stock)
        discount = AIScarcityCalibrationAgent.calibrate_discount(discount_historical_data)
        fatigue = AIScarcityCalibrationAgent.check_urgency_fatigue(campaign_history)

        ab_test = None
        if ab_test_variants and "low" in ab_test_variants and "high" in ab_test_variants:
            ab_test = AIScarcityCalibrationAgent.run_ab_test_analysis(
                ab_test_variants["low"], ab_test_variants["high"]
            )

        # Resolve final intensity recommendation: fatigue detection overrides
        # A/B test result — no test result justifies pushing a fatigued audience harder
        if fatigue["fatigued"]:
            final_intensity = "low"
        elif ab_test and ab_test.get("recommendation") == "adopt_high_intensity":
            final_intensity = "high"
        else:
            final_intensity = "low"

        return {
            "stock_display": stock_display,
            "discount_recommendation": discount,
            "urgency_fatigue": fatigue,
            "ab_test": ab_test,
            "final_intensity_recommendation": final_intensity,
        }
