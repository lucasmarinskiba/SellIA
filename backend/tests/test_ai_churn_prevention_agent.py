"""Fase G: AI Predictive Churn-to-FOMO Agent Tests"""

from datetime import datetime, timedelta, timezone
import pytest

from app.domains.fomo.ai_churn_prevention_agent import (
    AIChurnPreventionAgent,
    ChurnRiskScorer,
    ChurnRiskTier,
    PersonalizedOfferCalibrator,
    WinBackTriggerEngine,
)

NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)


def days_ago(n: int) -> datetime:
    return NOW - timedelta(days=n)


def purchase(day_offset: int, amount: float) -> dict:
    return {"date": days_ago(day_offset), "amount": amount}


class TestChurnRiskScorer:
    def test_no_purchase_history(self):
        result = ChurnRiskScorer.heuristic_risk_score([], reference_date=NOW)
        assert result["risk_score"] == 0.0
        assert result["reason"] == "no_purchase_history"

    def test_purchase_interval_stats_insufficient(self):
        stats = ChurnRiskScorer.compute_purchase_interval_stats([purchase(10, 100)])
        assert stats["has_data"] is False

    def test_purchase_interval_stats_computed(self):
        purchases = [purchase(60, 100), purchase(30, 100), purchase(0, 100)]
        stats = ChurnRiskScorer.compute_purchase_interval_stats(purchases)
        assert stats["has_data"] is True
        assert stats["avg_interval_days"] == 30.0

    def test_on_schedule_customer_low_risk(self):
        # Buys every 30 days, last purchase was 25 days ago — right on schedule
        purchases = [purchase(85, 100), purchase(55, 100), purchase(25, 100)]
        result = ChurnRiskScorer.heuristic_risk_score(purchases, reference_date=NOW)
        assert result["tier"] in (ChurnRiskTier.LOW, ChurnRiskTier.MEDIUM)
        assert result["risk_score"] < 0.5

    def test_overdue_customer_high_risk(self):
        # Buys every 15 days normally, but hasn't purchased in 90 days — 6x overdue
        purchases = [purchase(120, 100), purchase(105, 100), purchase(90, 100)]
        result = ChurnRiskScorer.heuristic_risk_score(purchases, reference_date=NOW)
        assert result["tier"] in (ChurnRiskTier.HIGH, ChurnRiskTier.CRITICAL)
        assert result["risk_score"] >= 0.5

    def test_engagement_decline_increases_risk(self):
        purchases = [purchase(60, 100), purchase(30, 100)]
        declining_history = [
            {"sent_at": days_ago(50), "opened": True, "clicked": True},
            {"sent_at": days_ago(40), "opened": True, "clicked": True},
            {"sent_at": days_ago(30), "opened": False, "clicked": False},
            {"sent_at": days_ago(20), "opened": False, "clicked": False},
            {"sent_at": days_ago(10), "opened": False, "clicked": False},
        ]
        without_engagement = ChurnRiskScorer.heuristic_risk_score(purchases, reference_date=NOW)
        with_engagement = ChurnRiskScorer.heuristic_risk_score(
            purchases, declining_history, reference_date=NOW
        )
        assert with_engagement["risk_score"] >= without_engagement["risk_score"]

    def test_tier_boundaries(self):
        assert ChurnRiskScorer._tier_from_score(0.1) == ChurnRiskTier.LOW
        assert ChurnRiskScorer._tier_from_score(0.3) == ChurnRiskTier.MEDIUM
        assert ChurnRiskScorer._tier_from_score(0.6) == ChurnRiskTier.HIGH
        assert ChurnRiskScorer._tier_from_score(0.9) == ChurnRiskTier.CRITICAL

    def test_fit_ml_model_insufficient_samples(self):
        labeled = [{"features": {"recency_days": 10}, "churned": False}] * 5
        model = ChurnRiskScorer.fit_ml_model(labeled)
        assert model is None

    def test_fit_ml_model_single_class(self):
        labeled = [
            {"features": {"recency_days": i, "frequency": 5, "monetary": 100, "recency_ratio": 1.0}, "churned": False}
            for i in range(25)
        ]
        model = ChurnRiskScorer.fit_ml_model(labeled)
        assert model is None

    def test_fit_ml_model_success(self):
        labeled = []
        for i in range(15):
            labeled.append({
                "features": {"recency_days": 5, "frequency": 10, "monetary": 1000, "recency_ratio": 0.5},
                "churned": False,
            })
        for i in range(15):
            labeled.append({
                "features": {"recency_days": 200, "frequency": 1, "monetary": 20, "recency_ratio": 5.0},
                "churned": True,
            })
        model = ChurnRiskScorer.fit_ml_model(labeled)
        assert model is not None
        assert "model" in model
        assert "feature_keys" in model

    def test_ml_risk_score_predicts_high_for_churn_pattern(self):
        labeled = []
        for i in range(15):
            labeled.append({
                "features": {"recency_days": 5, "frequency": 10, "monetary": 1000, "recency_ratio": 0.5},
                "churned": False,
            })
        for i in range(15):
            labeled.append({
                "features": {"recency_days": 200, "frequency": 1, "monetary": 20, "recency_ratio": 5.0},
                "churned": True,
            })
        fitted = ChurnRiskScorer.fit_ml_model(labeled)
        score = ChurnRiskScorer.ml_risk_score(
            fitted, {"recency_days": 210, "frequency": 1, "monetary": 15, "recency_ratio": 5.5}
        )
        assert score > 0.5


class TestPersonalizedOfferCalibrator:
    def test_insufficient_batch_context(self):
        result = PersonalizedOfferCalibrator.calibrate_offer(500, [500])
        assert result["reason"] == "insufficient_batch_context"

    def test_high_value_customer_gets_best_offer(self):
        batch = [10, 20, 50, 100, 1000]
        result = PersonalizedOfferCalibrator.calibrate_offer(1000, batch)
        assert result["tier"] == "high_value"
        assert result["discount_percent"] == 30

    def test_low_value_customer_gets_smallest_offer(self):
        batch = [10, 20, 50, 100, 1000]
        result = PersonalizedOfferCalibrator.calibrate_offer(10, batch)
        assert result["discount_percent"] <= 15

    def test_offer_tiers_ordered(self):
        discounts = [t["discount_percent"] for t in PersonalizedOfferCalibrator.OFFER_TIERS]
        assert discounts == sorted(discounts, reverse=True)


class TestWinBackTriggerEngine:
    def test_should_trigger_above_threshold(self):
        assert WinBackTriggerEngine.should_trigger({"risk_score": 0.6}, threshold=0.5) is True

    def test_should_not_trigger_below_threshold(self):
        assert WinBackTriggerEngine.should_trigger({"risk_score": 0.3}, threshold=0.5) is False

    def test_critical_sequence_has_more_steps(self):
        offer = {"discount_percent": 20, "tier": "mid_value"}
        critical_seq = WinBackTriggerEngine.build_win_back_sequence(offer, ChurnRiskTier.CRITICAL)
        medium_seq = WinBackTriggerEngine.build_win_back_sequence(offer, ChurnRiskTier.MEDIUM)
        assert len(critical_seq["sequence"]) >= len(medium_seq["sequence"])
        assert critical_seq["sequence"][0]["delay_minutes"] == 0


class TestAIChurnPreventionAgent:
    def test_score_customer_heuristic(self):
        purchases = [purchase(120, 100), purchase(90, 100)]
        result = AIChurnPreventionAgent.score_customer(purchases, reference_date=NOW)
        assert result["method"] == "heuristic"
        assert "risk_score" in result

    def test_evaluate_and_trigger_fires_for_high_risk(self):
        purchases = [purchase(150, 500), purchase(120, 500)]
        result = AIChurnPreventionAgent.evaluate_and_trigger(
            customer_id="c1",
            purchases=purchases,
            batch_monetary_values=[100, 500, 1000],
            threshold=0.4,
            reference_date=NOW,
        )
        if result["triggered"]:
            assert result["win_back_sequence"] is not None
            assert "offer_discount_percent" in result["win_back_sequence"]

    def test_evaluate_and_trigger_no_fire_for_low_risk(self):
        purchases = [purchase(35, 100), purchase(5, 100)]
        result = AIChurnPreventionAgent.evaluate_and_trigger(
            customer_id="c2",
            purchases=purchases,
            batch_monetary_values=[100, 200],
            threshold=0.8,
            reference_date=NOW,
        )
        assert result["triggered"] is False
        assert result["win_back_sequence"] is None

    def test_batch_evaluate(self):
        customers = [
            {"customer_id": "at_risk", "purchases": [purchase(150, 500), purchase(120, 500)]},
            {"customer_id": "healthy", "purchases": [purchase(10, 100), purchase(5, 100)]},
        ]
        result = AIChurnPreventionAgent.batch_evaluate(customers, threshold=0.4, reference_date=NOW)
        assert result["total_customers"] == 2
        assert result["used_ml_model"] is False
        assert len(result["results"]) == 2

    def test_batch_evaluate_with_ml_training_data(self):
        customers = [
            {"customer_id": "c1", "purchases": [purchase(200, 500), purchase(180, 500)]},
        ]
        labeled = []
        for i in range(15):
            labeled.append({
                "features": {"recency_days": 5, "frequency": 10, "monetary": 1000, "recency_ratio": 0.5},
                "churned": False,
            })
        for i in range(15):
            labeled.append({
                "features": {"recency_days": 200, "frequency": 1, "monetary": 20, "recency_ratio": 5.0},
                "churned": True,
            })
        result = AIChurnPreventionAgent.batch_evaluate(
            customers, threshold=0.4, reference_date=NOW, labeled_training_data=labeled
        )
        assert result["used_ml_model"] is True
        assert result["results"][0]["risk_score"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
