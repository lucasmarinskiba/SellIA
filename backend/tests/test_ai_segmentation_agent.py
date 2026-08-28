"""Fase D: AI Customer Segmentation Agent Tests"""

from datetime import datetime, timedelta, timezone
import pytest

from app.domains.fomo.ai_segmentation_agent import (
    AICustomerSegmentationAgent,
    RFMCalculator,
    RFMSegmentClassifier,
    ClusteringEngine,
    FOMOFatigueDetector,
    CustomerSegment,
    SEGMENT_FOMO_STRATEGY,
)

NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)


def days_ago(n: int) -> datetime:
    return NOW - timedelta(days=n)


def make_customer(customer_id: str, purchases: list) -> dict:
    return {"customer_id": customer_id, "purchases": purchases}


class TestRFMCalculator:
    def test_compute_raw_rfm_no_purchases(self):
        rfm = RFMCalculator.compute_raw_rfm([], reference_date=NOW)
        assert rfm["recency_days"] == 9999
        assert rfm["frequency"] == 0
        assert rfm["monetary"] == 0.0

    def test_compute_raw_rfm_with_purchases(self):
        purchases = [
            {"date": days_ago(30), "amount": 100},
            {"date": days_ago(5), "amount": 50},
        ]
        rfm = RFMCalculator.compute_raw_rfm(purchases, reference_date=NOW)
        assert rfm["recency_days"] == 5
        assert rfm["frequency"] == 2
        assert rfm["monetary"] == 150.0

    def test_score_quantile_single_value_neutral(self):
        assert RFMCalculator.score_quantile(100, [100]) == 3

    def test_score_quantile_reverse_for_recency(self):
        # lower recency (more recent) should score higher when reverse=True
        values = [1, 10, 20, 30, 100]
        low_recency_score = RFMCalculator.score_quantile(1, values, reverse=True)
        high_recency_score = RFMCalculator.score_quantile(100, values, reverse=True)
        assert low_recency_score > high_recency_score

    def test_compute_rfm_scores_batch(self):
        customers = [
            make_customer("c1", [{"date": days_ago(1), "amount": 500}] * 10),
            make_customer("c2", [{"date": days_ago(200), "amount": 10}]),
        ]
        scores = RFMCalculator.compute_rfm_scores(customers, reference_date=NOW)
        assert len(scores) == 2
        c1 = next(c for c in scores if c["customer_id"] == "c1")
        c2 = next(c for c in scores if c["customer_id"] == "c2")
        # c1: recent + frequent + high spend should outscore c2 on all fronts
        assert c1["r_score"] >= c2["r_score"]
        assert c1["f_score"] >= c2["f_score"]
        assert c1["m_score"] >= c2["m_score"]

    def test_rfm_score_string_format(self):
        customers = [make_customer("c1", [{"date": days_ago(1), "amount": 100}])]
        scores = RFMCalculator.compute_rfm_scores(customers, reference_date=NOW)
        assert len(scores[0]["rfm_score"]) == 3
        assert scores[0]["rfm_score"].isdigit()


class TestRFMSegmentClassifier:
    def test_champions(self):
        assert RFMSegmentClassifier.classify(5, 5, 5) == CustomerSegment.CHAMPIONS
        assert RFMSegmentClassifier.classify(4, 4, 4) == CustomerSegment.CHAMPIONS

    def test_new_customers(self):
        assert RFMSegmentClassifier.classify(5, 1, 1) == CustomerSegment.NEW_CUSTOMERS

    def test_cant_lose_them(self):
        assert RFMSegmentClassifier.classify(1, 5, 5) == CustomerSegment.CANT_LOSE_THEM

    def test_lost(self):
        assert RFMSegmentClassifier.classify(1, 1, 1) == CustomerSegment.LOST

    def test_at_risk(self):
        result = RFMSegmentClassifier.classify(2, 3, 3)
        assert result == CustomerSegment.AT_RISK

    def test_classify_batch(self):
        rfm_scores = [
            {"customer_id": "c1", "r_score": 5, "f_score": 5, "m_score": 5, "rfm_score": "555"},
            {"customer_id": "c2", "r_score": 1, "f_score": 1, "m_score": 1, "rfm_score": "111"},
        ]
        results = RFMSegmentClassifier.classify_batch(rfm_scores)
        assert results[0]["segment"] == CustomerSegment.CHAMPIONS.value
        assert results[1]["segment"] == CustomerSegment.LOST.value

    def test_every_segment_has_a_strategy(self):
        for segment in CustomerSegment:
            assert segment in SEGMENT_FOMO_STRATEGY
            strategy = SEGMENT_FOMO_STRATEGY[segment]
            assert "campaign_type" in strategy
            assert "tone" in strategy
            assert 0 < strategy["expected_lift"] <= 1.0


class TestClusteringEngine:
    def test_falls_back_below_threshold(self):
        rfm_scores = [
            {"customer_id": f"c{i}", "r_score": 3, "f_score": 3, "m_score": 3, "rfm_score": "333"}
            for i in range(3)
        ]
        results, used_clustering = ClusteringEngine.cluster_customers(rfm_scores)
        assert used_clustering is False
        assert all("segment" in r for r in results)

    def test_clusters_with_enough_data(self):
        rfm_scores = []
        for i in range(15):
            score = 5 if i % 2 == 0 else 1
            rfm_scores.append({
                "customer_id": f"c{i}", "r_score": score, "f_score": score, "m_score": score,
                "rfm_score": f"{score}{score}{score}",
            })
        results, used_clustering = ClusteringEngine.cluster_customers(rfm_scores)
        assert len(results) == 15
        assert all("segment" in r for r in results)
        # used_clustering may be True (sklearn present) or False (fallback) —
        # either way results must be well-formed
        if used_clustering:
            assert all("cluster_id" in r for r in results)


class TestFOMOFatigueDetector:
    def test_insufficient_history(self):
        result = FOMOFatigueDetector.detect_fatigue([{"opened": True, "clicked": False}])
        assert result["fatigued"] is False
        assert result["reason"] == "insufficient_history"

    def test_declining_engagement_flagged(self):
        history = [
            {"sent_at": days_ago(30), "opened": True, "clicked": True},
            {"sent_at": days_ago(20), "opened": True, "clicked": True},
            {"sent_at": days_ago(10), "opened": False, "clicked": False},
            {"sent_at": days_ago(5), "opened": False, "clicked": False},
            {"sent_at": days_ago(1), "opened": False, "clicked": False},
        ]
        result = FOMOFatigueDetector.detect_fatigue(history)
        assert result["fatigued"] is True
        assert result["reason"] == "declining_engagement"

    def test_stable_engagement_not_flagged(self):
        # 6 sends so both the "earlier" and "recent" 3-send windows are
        # equally sized and equally engaged — a thin 1-item earlier window
        # (e.g. only 4 total sends) is inherently noisy and not representative.
        history = [
            {"sent_at": days_ago(60), "opened": True, "clicked": True},
            {"sent_at": days_ago(50), "opened": True, "clicked": False},
            {"sent_at": days_ago(40), "opened": True, "clicked": True},
            {"sent_at": days_ago(30), "opened": True, "clicked": True},
            {"sent_at": days_ago(20), "opened": True, "clicked": False},
            {"sent_at": days_ago(10), "opened": True, "clicked": True},
        ]
        result = FOMOFatigueDetector.detect_fatigue(history)
        assert result["fatigued"] is False

    def test_zero_baseline_consecutive_ignored(self):
        history = [
            {"sent_at": days_ago(30), "opened": False, "clicked": False},
            {"sent_at": days_ago(20), "opened": False, "clicked": False},
            {"sent_at": days_ago(10), "opened": False, "clicked": False},
        ]
        result = FOMOFatigueDetector.detect_fatigue(history)
        assert result["fatigued"] is True
        assert result["reason"] == "consecutive_no_engagement"

    def test_recommend_cooldown_not_fatigued(self):
        cooldown = FOMOFatigueDetector.recommend_cooldown({"fatigued": False})
        assert cooldown["action"] == "continue_normal_cadence"
        assert cooldown["cooldown_days"] == 0

    def test_recommend_cooldown_declining(self):
        cooldown = FOMOFatigueDetector.recommend_cooldown(
            {"fatigued": True, "reason": "declining_engagement"}
        )
        assert cooldown["action"] == "reduce_frequency"
        assert cooldown["cooldown_days"] == 14

    def test_recommend_cooldown_no_engagement(self):
        cooldown = FOMOFatigueDetector.recommend_cooldown(
            {"fatigued": True, "reason": "consecutive_no_engagement"}
        )
        assert cooldown["action"] == "pause_and_switch_channel"
        assert cooldown["cooldown_days"] == 30


class TestAICustomerSegmentationAgent:
    def test_segment_customers_empty(self):
        result = AICustomerSegmentationAgent.segment_customers([])
        assert result["customers"] == []
        assert result["segment_distribution"] == {}

    def test_segment_customers_basic(self):
        # RFM quantile scoring is population-relative — needs enough customers
        # in the batch for the best one to actually land in the top band.
        customers = [
            make_customer("champion", [{"date": days_ago(1), "amount": 1000}] * 10),
            make_customer("mid1", [{"date": days_ago(60), "amount": 200}] * 3),
            make_customer("mid2", [{"date": days_ago(90), "amount": 150}] * 2),
            make_customer("mid3", [{"date": days_ago(120), "amount": 100}] * 2),
            make_customer("lost", [{"date": days_ago(500), "amount": 5}]),
        ]
        result = AICustomerSegmentationAgent.segment_customers(customers, use_clustering=False)
        assert result["total_customers"] == 5
        assert result["used_clustering"] is False
        segments = {c["customer_id"]: c["segment"] for c in result["customers"]}
        assert segments["champion"] == CustomerSegment.CHAMPIONS.value
        # Worst-of-batch lands in one of the two lowest tiers — exact boundary
        # depends on quantile scoring relative to the rest of the batch.
        assert segments["lost"] in (CustomerSegment.LOST.value, CustomerSegment.HIBERNATING.value)

    def test_get_segment_strategy_valid(self):
        strategy = AICustomerSegmentationAgent.get_segment_strategy("champions")
        assert strategy["campaign_type"] == "exclusivity_tier"
        assert strategy["tone"] == "luxury"

    def test_get_segment_strategy_invalid_defaults_safely(self):
        strategy = AICustomerSegmentationAgent.get_segment_strategy("not_a_real_segment")
        assert "campaign_type" in strategy  # doesn't crash, safe fallback

    def test_analyze_and_recommend_full_pipeline(self):
        customers = [
            make_customer("c1", [{"date": days_ago(1), "amount": 200}] * 5),
            make_customer("c2", [{"date": days_ago(300), "amount": 5}]),
        ]
        result = AICustomerSegmentationAgent.analyze_and_recommend(
            customers, use_clustering=False, reference_date=NOW
        )
        assert result["total_customers"] == 2
        assert len(result["recommendations"]) == 2
        for rec in result["recommendations"]:
            assert "recommended_campaign_type" in rec
            assert "recommended_tone" in rec
            assert "eligible_for_fomo" in rec

    def test_analyze_and_recommend_excludes_fatigued(self):
        customers = [make_customer("c1", [{"date": days_ago(1), "amount": 100}] * 5)]
        fatigue_data = {
            "c1": [
                {"sent_at": days_ago(30), "opened": False, "clicked": False},
                {"sent_at": days_ago(20), "opened": False, "clicked": False},
                {"sent_at": days_ago(10), "opened": False, "clicked": False},
            ]
        }
        result = AICustomerSegmentationAgent.analyze_and_recommend(
            customers, fatigue_data=fatigue_data, use_clustering=False, reference_date=NOW
        )
        assert result["excluded_fatigued"] == 1
        assert result["eligible_for_fomo"] == 0
        assert result["recommendations"][0]["eligible_for_fomo"] is False
        assert result["recommendations"][0]["cooldown_recommendation"] is not None

    def test_analyze_and_recommend_no_fatigue_data_all_eligible(self):
        customers = [
            make_customer("c1", [{"date": days_ago(1), "amount": 100}]),
            make_customer("c2", [{"date": days_ago(2), "amount": 200}]),
        ]
        result = AICustomerSegmentationAgent.analyze_and_recommend(
            customers, use_clustering=False, reference_date=NOW
        )
        assert result["eligible_for_fomo"] == 2
        assert result["excluded_fatigued"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
