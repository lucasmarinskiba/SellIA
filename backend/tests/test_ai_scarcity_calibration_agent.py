"""Fase C: AI Scarcity Calibration Agent Tests"""

from datetime import datetime, timedelta, timezone
import pytest

from app.domains.fomo.ai_scarcity_calibration_agent import (
    AIScarcityCalibrationAgent,
    StockDisplayCalibrator,
    DiscountElasticityCalibrator,
    UrgencyFatigueDetector,
    IntensityABTestManager,
)

NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)


def days_ago(n: int) -> datetime:
    return NOW - timedelta(days=n)


class TestStockDisplayCalibrator:
    def test_out_of_stock(self):
        result = StockDisplayCalibrator.compute_display_tier(0)
        assert result["tier"] == "out_of_stock"
        assert result["show_scarcity_message"] is False

    def test_critical_tier(self):
        result = StockDisplayCalibrator.compute_display_tier(3)
        assert result["tier"] == "critical"
        assert result["show_scarcity_message"] is True
        assert "3" in result["message"]

    def test_low_tier(self):
        result = StockDisplayCalibrator.compute_display_tier(15)
        assert result["tier"] == "low"
        assert result["show_scarcity_message"] is True

    def test_plenty_tier_no_scarcity_message(self):
        result = StockDisplayCalibrator.compute_display_tier(500)
        assert result["tier"] == "plenty"
        assert result["show_scarcity_message"] is False
        assert result["message"] is None

    def test_custom_thresholds(self):
        result = StockDisplayCalibrator.compute_display_tier(50, low_threshold=100, critical_threshold=10)
        assert result["tier"] == "low"

    def test_validate_claim_truthful(self):
        result = StockDisplayCalibrator.validate_scarcity_claim("Solo 3 quedan", 3)
        assert result["compliant"] is True
        assert result["claimed_stock"] == 3

    def test_validate_claim_understated_stock_flagged(self):
        result = StockDisplayCalibrator.validate_scarcity_claim("Solo 2 quedan", 500)
        assert result["compliant"] is False
        assert any(i["type"] == "understated_stock" for i in result["issues"])

    def test_validate_claim_overstated_is_fine(self):
        # Claiming MORE than real stock isn't a scarcity-deception risk
        result = StockDisplayCalibrator.validate_scarcity_claim("Quedan 10", 3)
        assert result["compliant"] is True

    def test_validate_claim_unjustified_urgency_language(self):
        result = StockDisplayCalibrator.validate_scarcity_claim("¡Últimas unidades, date prisa!", 500)
        assert result["compliant"] is False
        assert any(i["type"] == "unjustified_urgency" for i in result["issues"])

    def test_validate_claim_no_numbers_low_stock_fine(self):
        result = StockDisplayCalibrator.validate_scarcity_claim("Stock disponible", 3)
        assert result["compliant"] is True


class TestDiscountElasticityCalibrator:
    def test_fit_curve_insufficient_data(self):
        curve = DiscountElasticityCalibrator.fit_elasticity_curve([{"discount_percent": 10, "conversion_rate": 0.1}])
        assert curve is None

    def test_fit_curve_identical_x_returns_none(self):
        data = [
            {"discount_percent": 10, "conversion_rate": 0.1},
            {"discount_percent": 10, "conversion_rate": 0.15},
        ]
        curve = DiscountElasticityCalibrator.fit_elasticity_curve(data)
        assert curve is None

    def test_fit_curve_positive_slope(self):
        data = [
            {"discount_percent": 10, "conversion_rate": 0.05},
            {"discount_percent": 20, "conversion_rate": 0.10},
            {"discount_percent": 30, "conversion_rate": 0.15},
        ]
        curve = DiscountElasticityCalibrator.fit_elasticity_curve(data)
        assert curve is not None
        slope, intercept = curve
        assert slope > 0

    def test_predict_conversion_rate_bounded(self):
        rate = DiscountElasticityCalibrator.predict_conversion_rate(1000, slope=0.01, intercept=0.05)
        assert 0.0 <= rate <= 1.0

    def test_recommend_optimal_discount_insufficient_data(self):
        result = DiscountElasticityCalibrator.recommend_optimal_discount([])
        assert result["confidence"] == "low"
        assert result["recommended_discount_percent"] == 20

    def test_recommend_optimal_discount_with_data(self):
        data = [
            {"discount_percent": 10, "conversion_rate": 0.05},
            {"discount_percent": 20, "conversion_rate": 0.08},
            {"discount_percent": 30, "conversion_rate": 0.10},
            {"discount_percent": 40, "conversion_rate": 0.11},
            {"discount_percent": 50, "conversion_rate": 0.115},
        ]
        result = DiscountElasticityCalibrator.recommend_optimal_discount(data)
        assert result["confidence"] == "high"
        assert 10 <= result["recommended_discount_percent"] <= 50
        assert len(result["all_candidates"]) > 0

    def test_recommend_discount_respects_bounds(self):
        data = [
            {"discount_percent": 10, "conversion_rate": 0.05},
            {"discount_percent": 20, "conversion_rate": 0.20},
        ]
        result = DiscountElasticityCalibrator.recommend_optimal_discount(data, min_discount=10, max_discount=25)
        assert 10 <= result["recommended_discount_percent"] <= 25


class TestUrgencyFatigueDetector:
    def test_insufficient_history(self):
        result = UrgencyFatigueDetector.detect_intensity_fatigue([
            {"sent_at": days_ago(1), "urgency_intensity": "high", "conversion_rate": 0.1}
        ])
        assert result["fatigued"] is False
        assert result["reason"] == "insufficient_campaign_history"

    def test_declining_returns_flagged(self):
        history = [
            {"sent_at": days_ago(60), "urgency_intensity": "high", "conversion_rate": 0.20},
            {"sent_at": days_ago(50), "urgency_intensity": "high", "conversion_rate": 0.18},
            {"sent_at": days_ago(40), "urgency_intensity": "high", "conversion_rate": 0.10},
            {"sent_at": days_ago(30), "urgency_intensity": "high", "conversion_rate": 0.08},
            {"sent_at": days_ago(20), "urgency_intensity": "high", "conversion_rate": 0.06},
            {"sent_at": days_ago(10), "urgency_intensity": "high", "conversion_rate": 0.05},
        ]
        result = UrgencyFatigueDetector.detect_intensity_fatigue(history)
        assert result["fatigued"] is True
        assert result["reason"] == "declining_intensity_returns"

    def test_stable_effectiveness_not_flagged(self):
        history = [
            {"sent_at": days_ago(60), "urgency_intensity": "high", "conversion_rate": 0.10},
            {"sent_at": days_ago(50), "urgency_intensity": "high", "conversion_rate": 0.11},
            {"sent_at": days_ago(40), "urgency_intensity": "high", "conversion_rate": 0.10},
            {"sent_at": days_ago(30), "urgency_intensity": "high", "conversion_rate": 0.12},
            {"sent_at": days_ago(20), "urgency_intensity": "high", "conversion_rate": 0.10},
            {"sent_at": days_ago(10), "urgency_intensity": "high", "conversion_rate": 0.11},
        ]
        result = UrgencyFatigueDetector.detect_intensity_fatigue(history)
        assert result["fatigued"] is False

    def test_recommend_adjustment_not_fatigued(self):
        rec = UrgencyFatigueDetector.recommend_intensity_adjustment({"fatigued": False})
        assert rec["action"] == "maintain_current_intensity"

    def test_recommend_adjustment_fatigued(self):
        rec = UrgencyFatigueDetector.recommend_intensity_adjustment({"fatigued": True})
        assert rec["action"] == "reduce_urgency_intensity"


class TestIntensityABTestManager:
    def test_z_test_insufficient_sample(self):
        result = IntensityABTestManager.z_test_two_proportions(0, 0, 5, 10)
        assert result["error"] == "insufficient_sample"

    def test_z_test_significant_difference(self):
        # Large, clearly different samples
        result = IntensityABTestManager.z_test_two_proportions(100, 1000, 180, 1000)
        assert result["significant"] is True
        assert result["lift"] > 0

    def test_z_test_no_significant_difference(self):
        result = IntensityABTestManager.z_test_two_proportions(100, 1000, 102, 1000)
        assert result["significant"] is False

    def test_analyze_intensity_test_underpowered(self):
        result = IntensityABTestManager.analyze_intensity_test(
            {"conversions": 5, "visitors": 20}, {"conversions": 8, "visitors": 20}, min_sample_size=100
        )
        assert result["under_powered"] is True
        assert result["recommendation"] == "continue_test"

    def test_analyze_intensity_test_adopt_high(self):
        result = IntensityABTestManager.analyze_intensity_test(
            {"conversions": 100, "visitors": 1000}, {"conversions": 180, "visitors": 1000}, min_sample_size=100
        )
        assert result["recommendation"] == "adopt_high_intensity"

    def test_analyze_intensity_test_adopt_low(self):
        result = IntensityABTestManager.analyze_intensity_test(
            {"conversions": 180, "visitors": 1000}, {"conversions": 100, "visitors": 1000}, min_sample_size=100
        )
        assert result["recommendation"] == "adopt_low_intensity"

    def test_analyze_intensity_test_tie_defaults_to_low(self):
        result = IntensityABTestManager.analyze_intensity_test(
            {"conversions": 100, "visitors": 1000}, {"conversions": 101, "visitors": 1000}, min_sample_size=100
        )
        assert result["recommendation"] == "no_significant_difference_use_low_intensity"


class TestAIScarcityCalibrationAgent:
    def test_calibrate_stock_display(self):
        result = AIScarcityCalibrationAgent.calibrate_stock_display(3)
        assert result["tier"] == "critical"

    def test_audit_scarcity_message(self):
        result = AIScarcityCalibrationAgent.audit_scarcity_message("Solo 2 quedan", 500)
        assert result["compliant"] is False

    def test_calibrate_discount(self):
        data = [
            {"discount_percent": 10, "conversion_rate": 0.05},
            {"discount_percent": 30, "conversion_rate": 0.12},
        ]
        result = AIScarcityCalibrationAgent.calibrate_discount(data)
        assert "recommended_discount_percent" in result

    def test_check_urgency_fatigue_includes_recommendation(self):
        history = [
            {"sent_at": days_ago(i * 10), "urgency_intensity": "high", "conversion_rate": 0.1}
            for i in range(4)
        ]
        result = AIScarcityCalibrationAgent.check_urgency_fatigue(history)
        assert "recommendation" in result

    def test_run_ab_test_analysis(self):
        result = AIScarcityCalibrationAgent.run_ab_test_analysis(
            {"conversions": 100, "visitors": 1000}, {"conversions": 180, "visitors": 1000}
        )
        assert "recommendation" in result

    def test_full_calibration_fatigue_overrides_ab_test(self):
        # Fatigued campaign history, but AB test strongly favors high intensity —
        # fatigue must still win and force low intensity
        campaign_history = [
            {"sent_at": days_ago(60), "urgency_intensity": "high", "conversion_rate": 0.20},
            {"sent_at": days_ago(50), "urgency_intensity": "high", "conversion_rate": 0.18},
            {"sent_at": days_ago(40), "urgency_intensity": "high", "conversion_rate": 0.10},
            {"sent_at": days_ago(30), "urgency_intensity": "high", "conversion_rate": 0.08},
            {"sent_at": days_ago(20), "urgency_intensity": "high", "conversion_rate": 0.06},
            {"sent_at": days_ago(10), "urgency_intensity": "high", "conversion_rate": 0.05},
        ]
        ab_variants = {
            "low": {"conversions": 100, "visitors": 1000},
            "high": {"conversions": 180, "visitors": 1000},
        }
        result = AIScarcityCalibrationAgent.full_calibration(
            real_stock=15,
            discount_historical_data=[
                {"discount_percent": 10, "conversion_rate": 0.05},
                {"discount_percent": 30, "conversion_rate": 0.12},
            ],
            campaign_history=campaign_history,
            ab_test_variants=ab_variants,
        )
        assert result["urgency_fatigue"]["fatigued"] is True
        assert result["final_intensity_recommendation"] == "low"

    def test_full_calibration_no_fatigue_adopts_ab_winner(self):
        campaign_history = [
            {"sent_at": days_ago(i * 10), "urgency_intensity": "high", "conversion_rate": 0.10}
            for i in range(4)
        ]
        ab_variants = {
            "low": {"conversions": 100, "visitors": 1000},
            "high": {"conversions": 180, "visitors": 1000},
        }
        result = AIScarcityCalibrationAgent.full_calibration(
            real_stock=15,
            discount_historical_data=[
                {"discount_percent": 10, "conversion_rate": 0.05},
                {"discount_percent": 30, "conversion_rate": 0.12},
            ],
            campaign_history=campaign_history,
            ab_test_variants=ab_variants,
        )
        assert result["urgency_fatigue"]["fatigued"] is False
        assert result["final_intensity_recommendation"] == "high"

    def test_full_calibration_without_ab_test(self):
        result = AIScarcityCalibrationAgent.full_calibration(
            real_stock=15,
            discount_historical_data=[],
            campaign_history=[],
        )
        assert result["ab_test"] is None
        assert result["final_intensity_recommendation"] == "low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
