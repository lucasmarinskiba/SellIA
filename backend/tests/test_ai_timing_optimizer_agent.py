"""Fase B: AI Timing Optimizer Agent Tests"""

from datetime import datetime, timedelta, timezone
import pytest

from app.domains.fomo.ai_timing_optimizer_agent import (
    AITimingOptimizerAgent,
    EngagementTimeAnalyzer,
    SendTimePredictor,
    DynamicDelayAdjuster,
    COLD_START_WINDOWS,
    MIN_SAMPLES_FOR_PERSONALIZATION,
)

NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)  # Friday


def at_hour(day_offset: int, hour: int) -> datetime:
    base = NOW - timedelta(days=day_offset)
    return base.replace(hour=hour, minute=0, second=0, microsecond=0)


class TestEngagementTimeAnalyzer:
    def test_empty_history(self):
        heatmap = EngagementTimeAnalyzer.build_heatmap([])
        assert heatmap["sample_count"] == 0
        assert heatmap["sufficient_data"] is False
        assert all(v == 0.0 for v in heatmap["hour_engagement"].values())

    def test_sufficient_data_flag(self):
        history = [{"sent_at": at_hour(i, 10), "opened": True, "clicked": False} for i in range(6)]
        heatmap = EngagementTimeAnalyzer.build_heatmap(history)
        assert heatmap["sample_count"] == 6
        assert heatmap["sufficient_data"] is True

    def test_hour_engagement_weighting(self):
        history = [
            {"sent_at": at_hour(0, 10), "opened": True, "clicked": True},   # hour 10: full engagement
            {"sent_at": at_hour(1, 3), "opened": False, "clicked": False},  # hour 3: no engagement
        ]
        heatmap = EngagementTimeAnalyzer.build_heatmap(history)
        assert heatmap["hour_engagement"][10] > heatmap["hour_engagement"][3]
        assert heatmap["hour_engagement"][10] == 1.0  # (1 open + 2 click)/3 = 1.0

    def test_day_of_week_engagement(self):
        # NOW is a Friday (weekday()==4)
        history = [{"sent_at": NOW, "opened": True, "clicked": True}]
        heatmap = EngagementTimeAnalyzer.build_heatmap(history)
        assert heatmap["day_of_week_engagement"][4] == 1.0

    def test_ignores_entries_without_sent_at(self):
        history = [{"opened": True, "clicked": True}]  # missing sent_at
        heatmap = EngagementTimeAnalyzer.build_heatmap(history)
        assert all(v == 0.0 for v in heatmap["hour_engagement"].values())


class TestSendTimePredictor:
    def test_cold_start_below_threshold(self):
        history = [{"sent_at": at_hour(0, 10), "opened": True, "clicked": False}]
        heatmap = EngagementTimeAnalyzer.build_heatmap(history)
        prediction = SendTimePredictor.predict_best_window(heatmap)
        assert prediction["personalized"] is False
        assert prediction["reason"] == "insufficient_history"
        assert prediction["confidence"] == "low"

    def test_cold_start_zero_engagement(self):
        history = [
            {"sent_at": at_hour(i, 10), "opened": False, "clicked": False}
            for i in range(6)
        ]
        heatmap = EngagementTimeAnalyzer.build_heatmap(history)
        prediction = SendTimePredictor.predict_best_window(heatmap)
        assert prediction["personalized"] is False
        assert prediction["reason"] == "no_engagement_recorded"

    def test_personalized_prediction(self):
        history = []
        for i in range(10):
            history.append({"sent_at": at_hour(i, 19), "opened": True, "clicked": True})
        for i in range(10):
            history.append({"sent_at": at_hour(i, 4), "opened": False, "clicked": False})
        heatmap = EngagementTimeAnalyzer.build_heatmap(history)
        prediction = SendTimePredictor.predict_best_window(heatmap)
        assert prediction["personalized"] is True
        assert prediction["recommended_hour"] == 19
        assert prediction["confidence"] == "high"

    def test_next_send_datetime_future(self):
        prediction = {"recommended_hour": 15, "recommended_hour_range": (14, 16)}
        result = SendTimePredictor.next_send_datetime(prediction, reference_date=NOW)
        assert result > NOW
        assert result.hour == 15

    def test_next_send_datetime_cold_start_uses_range_start(self):
        prediction = {"recommended_hour_range": (9, 11)}
        result = SendTimePredictor.next_send_datetime(prediction, reference_date=NOW)
        assert result.hour == 9


class TestDynamicDelayAdjuster:
    def test_no_latency_data(self):
        stats = DynamicDelayAdjuster.compute_response_latency([])
        assert stats["has_data"] is False

        adjustment = DynamicDelayAdjuster.adjust_delay(120, stats, "short_followup")
        assert adjustment["personalized"] is False
        assert adjustment["adjusted_delay_minutes"] == 120

    def test_fast_responder_shortens_delay(self):
        history = [
            {"sent_at": at_hour(i, 10), "opened_at": at_hour(i, 10) + timedelta(minutes=5)}
            for i in range(5)
        ]
        stats = DynamicDelayAdjuster.compute_response_latency(history)
        assert stats["has_data"] is True
        assert stats["median_minutes"] == 5.0

        adjustment = DynamicDelayAdjuster.adjust_delay(120, stats, "short_followup")
        assert adjustment["adjusted_delay_minutes"] < 120
        assert adjustment["personalized"] is True

    def test_slow_responder_lengthens_delay(self):
        history = [
            {"sent_at": at_hour(i, 10), "opened_at": at_hour(i, 10) + timedelta(minutes=600)}
            for i in range(5)
        ]
        stats = DynamicDelayAdjuster.compute_response_latency(history)
        adjustment = DynamicDelayAdjuster.adjust_delay(120, stats, "short_followup")
        assert adjustment["adjusted_delay_minutes"] > 120

    def test_delay_respects_bounds(self):
        # Extremely fast responder shouldn't push delay below the category floor
        history = [
            {"sent_at": at_hour(i, 10), "opened_at": at_hour(i, 10) + timedelta(seconds=10)}
            for i in range(5)
        ]
        stats = DynamicDelayAdjuster.compute_response_latency(history)
        adjustment = DynamicDelayAdjuster.adjust_delay(5, stats, "immediate")
        assert adjustment["adjusted_delay_minutes"] >= 2  # immediate category floor

    def test_optimize_sequence_all_steps(self):
        base_delays = [
            {"step": 1, "delay_minutes": 5, "category": "immediate"},
            {"step": 2, "delay_minutes": 120, "category": "short_followup"},
            {"step": 3, "delay_minutes": 1440, "category": "long_followup"},
        ]
        history = [
            {"sent_at": at_hour(i, 10), "opened_at": at_hour(i, 10) + timedelta(minutes=3)}
            for i in range(5)
        ]
        optimized = DynamicDelayAdjuster.optimize_sequence(base_delays, history)
        assert len(optimized) == 3
        for step in optimized:
            assert "original_delay_minutes" in step
            assert "delay_minutes" in step


class TestAITimingOptimizerAgent:
    def test_analyze_engagement_patterns(self):
        history = [{"sent_at": at_hour(0, 10), "opened": True, "clicked": False}]
        result = AITimingOptimizerAgent.analyze_engagement_patterns(history)
        assert "hour_engagement" in result

    def test_predict_optimal_send_time_returns_iso_datetime(self):
        history = [{"sent_at": at_hour(0, 10), "opened": True, "clicked": False}]
        result = AITimingOptimizerAgent.predict_optimal_send_time(history, reference_date=NOW)
        assert "next_send_datetime" in result
        parsed = datetime.fromisoformat(result["next_send_datetime"])
        assert parsed > NOW

    def test_optimize_automation_schedule_unknown_type(self):
        result = AITimingOptimizerAgent.optimize_automation_schedule("not_a_real_type", [])
        assert result["error"] == "unknown_automation_type"

    def test_optimize_automation_schedule_cart_abandonment(self):
        history = [
            {"sent_at": at_hour(i, 10), "opened_at": at_hour(i, 10) + timedelta(minutes=10)}
            for i in range(5)
        ]
        result = AITimingOptimizerAgent.optimize_automation_schedule("cart_abandonment", history)
        assert result["automation_type"] == "cart_abandonment"
        assert len(result["steps"]) == 3

    def test_get_send_recommendation_cleared(self):
        history = [
            {"sent_at": at_hour(i, 19), "opened": True, "clicked": True}
            for i in range(5)
        ]
        result = AITimingOptimizerAgent.get_send_recommendation(
            "cust_1", "cart_abandonment", history, reference_date=NOW
        )
        assert result["customer_id"] == "cust_1"
        assert result["cleared_to_send"] is True
        assert result["cooldown_recommendation"] is None

    def test_get_send_recommendation_fatigued_blocks_send(self):
        history = [
            {"sent_at": at_hour(i, 10), "opened": False, "clicked": False}
            for i in range(3)
        ]
        result = AITimingOptimizerAgent.get_send_recommendation(
            "cust_2", "cart_abandonment", history, reference_date=NOW
        )
        assert result["cleared_to_send"] is False
        assert result["cooldown_recommendation"] is not None

    def test_batch_optimize(self):
        customers_history = {
            "engaged_customer": [
                {"sent_at": at_hour(i, 19), "opened": True, "clicked": True} for i in range(5)
            ],
            "fatigued_customer": [
                {"sent_at": at_hour(i, 10), "opened": False, "clicked": False} for i in range(3)
            ],
        }
        result = AITimingOptimizerAgent.batch_optimize(
            customers_history, "cart_abandonment", reference_date=NOW
        )
        assert result["total_customers"] == 2
        assert result["cleared_to_send"] == 1
        assert result["on_cooldown"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
