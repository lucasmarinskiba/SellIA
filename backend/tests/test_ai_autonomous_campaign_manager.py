"""Fase E: AI Autonomous Campaign Manager Tests"""

from datetime import datetime, timedelta, timezone
import pytest

from app.domains.fomo.ai_autonomous_campaign_manager import (
    AIAutonomousCampaignManager,
    OpportunityDetector,
    CampaignAutoBuilder,
    PerformanceMonitor,
    AutoScaler,
    DailyReportGenerator,
    FOMO_CALENDAR,
)

# A date with no seasonal event in the 14-day lead window
QUIET_DATE = datetime(2026, 3, 15, tzinfo=timezone.utc)
# 5 days before Black Friday (Nov 29) — within lead time but past the
# <=3-day "high priority" cutoff, so this is the medium-priority case
NEAR_BLACK_FRIDAY = datetime(2026, 11, 24, tzinfo=timezone.utc)
# 2 days before Black Friday — inside the <=3-day high-priority cutoff
IMMINENT_BLACK_FRIDAY = datetime(2026, 11, 27, tzinfo=timezone.utc)


class TestOpportunityDetector:
    def test_stock_opportunity_critical(self):
        opp = OpportunityDetector.detect_stock_opportunity(3, "prod1")
        assert opp["type"] == "low_stock"
        assert opp["priority"] == "high"

    def test_stock_opportunity_none_when_plenty(self):
        opp = OpportunityDetector.detect_stock_opportunity(500, "prod1")
        assert opp is None

    def test_stock_opportunity_low_medium_priority(self):
        opp = OpportunityDetector.detect_stock_opportunity(15, "prod1")
        assert opp["priority"] == "medium"

    def test_seasonal_opportunity_none_on_quiet_date(self):
        opp = OpportunityDetector.detect_seasonal_opportunity(QUIET_DATE, lead_time_days=14)
        assert opp is None

    def test_seasonal_opportunity_detects_upcoming_event(self):
        opp = OpportunityDetector.detect_seasonal_opportunity(NEAR_BLACK_FRIDAY, lead_time_days=14)
        assert opp is not None
        assert opp["event_name"] == "Black Friday"
        assert opp["days_until"] == 5
        assert opp["priority"] == "medium"  # outside the <=3-day high-priority cutoff

    def test_seasonal_opportunity_high_priority_when_imminent(self):
        opp = OpportunityDetector.detect_seasonal_opportunity(IMMINENT_BLACK_FRIDAY, lead_time_days=14)
        assert opp is not None
        assert opp["days_until"] == 2
        assert opp["priority"] == "high"

    def test_seasonal_opportunity_year_wraps_correctly(self):
        # Jan 1 New Year Sale, checked from Dec 30 of the previous year
        late_dec = datetime(2026, 12, 30, tzinfo=timezone.utc)
        opp = OpportunityDetector.detect_seasonal_opportunity(late_dec, lead_time_days=14)
        assert opp is not None
        assert opp["event_name"] == "New Year Sale"
        assert opp["days_until"] == 2

    def test_competitor_opportunity_none_when_no_signal(self):
        assert OpportunityDetector.detect_competitor_opportunity(None) is None

    def test_competitor_opportunity_none_when_below_threshold(self):
        signal = {"competitor_name": "RivalCo", "discount_percent": 10}
        assert OpportunityDetector.detect_competitor_opportunity(signal) is None

    def test_competitor_opportunity_detected_above_threshold(self):
        signal = {"competitor_name": "RivalCo", "discount_percent": 35}
        opp = OpportunityDetector.detect_competitor_opportunity(signal)
        assert opp["type"] == "competitor_activity"
        assert opp["priority"] == "high"

    def test_detect_all_sorts_by_priority(self):
        opportunities = OpportunityDetector.detect_all(
            real_stock=15,  # medium priority
            reference_date=NEAR_BLACK_FRIDAY,  # high priority seasonal
            competitor_signal={"competitor_name": "X", "discount_percent": 35},  # high priority
        )
        assert len(opportunities) == 3
        priorities = [o["priority"] for o in opportunities]
        assert priorities[0] == "high"

    def test_detect_all_empty_when_nothing_found(self):
        opportunities = OpportunityDetector.detect_all(reference_date=QUIET_DATE)
        assert opportunities == []


class TestCampaignAutoBuilder:
    def test_build_plan_from_stock_opportunity(self):
        opp = {"type": "low_stock", "priority": "high", "suggested_template_type": "scarcity"}
        plan = CampaignAutoBuilder.build_campaign_plan(opp)
        assert plan["template_type"] == "scarcity"
        assert plan["tone"] == "urgent"
        assert plan["opportunity_source"] == "low_stock"
        assert plan["status"] == "planned"

    def test_build_plan_medium_priority_friendly_tone(self):
        opp = {"type": "seasonal_event", "priority": "medium", "suggested_template_type": "flash_sale"}
        plan = CampaignAutoBuilder.build_campaign_plan(opp)
        assert plan["tone"] == "friendly"

    def test_build_plan_uses_discount_calibration(self):
        opp = {"type": "low_stock", "priority": "high", "suggested_template_type": "scarcity"}
        historical = [
            {"discount_percent": 10, "conversion_rate": 0.05},
            {"discount_percent": 30, "conversion_rate": 0.12},
        ]
        plan = CampaignAutoBuilder.build_campaign_plan(opp, discount_historical_data=historical)
        assert "recommended_discount_percent" in plan
        assert plan["discount_confidence"] in ("low", "medium", "high")

    def test_build_plan_includes_send_window(self):
        opp = {"type": "low_stock", "priority": "high", "suggested_template_type": "scarcity"}
        plan = CampaignAutoBuilder.build_campaign_plan(opp)
        assert "send_window" in plan
        assert "hour_range" in plan["send_window"]


class TestPerformanceMonitor:
    def test_compute_roi_zero_cost(self):
        assert PerformanceMonitor.compute_roi(1000, 0) == 0.0

    def test_compute_roi_positive(self):
        roi = PerformanceMonitor.compute_roi(2000, 1000)
        assert roi == 1.0

    def test_evaluate_health_negative_roi(self):
        health = PerformanceMonitor.evaluate_campaign_health(
            {"impressions": 1000, "conversions": 10, "revenue": 100, "cost": 500}
        )
        assert health["status"] == "negative_roi"

    def test_evaluate_health_strong_performance(self):
        health = PerformanceMonitor.evaluate_campaign_health(
            {"impressions": 1000, "conversions": 100, "revenue": 5000, "cost": 500}
        )
        assert health["status"] == "strong_performance"

    def test_evaluate_health_healthy(self):
        health = PerformanceMonitor.evaluate_campaign_health(
            {"impressions": 1000, "conversions": 50, "revenue": 1000, "cost": 800}
        )
        assert health["status"] == "healthy"

    def test_detect_trend_insufficient_data(self):
        trend = PerformanceMonitor.detect_roi_trend([{"revenue": 100, "cost": 50}])
        assert trend["trend"] == "insufficient_data"

    def test_detect_trend_declining(self):
        history = [
            {"revenue": 1000, "cost": 500},
            {"revenue": 800, "cost": 500},
            {"revenue": 600, "cost": 500},
            {"revenue": 400, "cost": 500},
        ]
        trend = PerformanceMonitor.detect_roi_trend(history)
        assert trend["trend"] == "declining"

    def test_detect_trend_improving(self):
        history = [
            {"revenue": 400, "cost": 500},
            {"revenue": 600, "cost": 500},
            {"revenue": 800, "cost": 500},
            {"revenue": 1000, "cost": 500},
        ]
        trend = PerformanceMonitor.detect_roi_trend(history)
        assert trend["trend"] == "improving"


class TestAutoScaler:
    def test_decide_pause_on_negative_roi(self):
        health = {"status": "negative_roi", "roi": -0.3}
        action = AutoScaler.decide_action(health)
        assert action["action"] == "auto_pause"

    def test_decide_scale_on_strong_performance(self):
        health = {"status": "strong_performance", "roi": 3.0}
        action = AutoScaler.decide_action(health, current_budget=1000)
        assert action["action"] == "auto_scale"
        assert action["recommended_budget"] == 1500.0

    def test_decide_continue_on_healthy(self):
        health = {"status": "healthy", "roi": 0.5}
        action = AutoScaler.decide_action(health)
        assert action["action"] == "continue"

    def test_decide_pause_on_declining_trend_even_if_not_yet_negative(self):
        health = {"status": "healthy", "roi": 0.1}
        trend = {"trend": "declining"}
        action = AutoScaler.decide_action(health, trend)
        assert action["action"] == "auto_pause"

    def test_scale_without_budget_returns_none_budget(self):
        health = {"status": "strong_performance", "roi": 3.0}
        action = AutoScaler.decide_action(health)
        assert action["action"] == "auto_scale"
        assert action["recommended_budget"] is None


class TestDailyReportGenerator:
    def test_generate_report_structure(self):
        health = {"roi": 0.5, "conversion_rate": 0.1, "status": "healthy"}
        action = {"action": "continue", "reason": "fine"}
        report = DailyReportGenerator.generate_daily_report(
            "camp1", {"revenue": 1000, "cost": 500}, health, action
        )
        assert report["campaign_id"] == "camp1"
        assert "headline" in report
        assert report["action_taken"] == "continue"

    def test_headline_reflects_pause(self):
        health = {"roi": -0.3, "conversion_rate": 0.01, "status": "negative_roi"}
        action = {"action": "auto_pause", "reason": "bad roi"}
        report = DailyReportGenerator.generate_daily_report("camp1", {}, health, action)
        assert "pausada" in report["headline"].lower()


class TestAIAutonomousCampaignManager:
    def test_scan_for_opportunities(self):
        result = AIAutonomousCampaignManager.scan_for_opportunities(
            real_stock=3, reference_date=QUIET_DATE
        )
        assert result["opportunities_found"] == 1

    def test_create_campaign_from_opportunity(self):
        opp = {"type": "low_stock", "priority": "high", "suggested_template_type": "scarcity"}
        plan = AIAutonomousCampaignManager.create_campaign_from_opportunity(opp)
        assert plan["template_type"] == "scarcity"

    def test_monitor_and_decide(self):
        result = AIAutonomousCampaignManager.monitor_and_decide(
            {"impressions": 1000, "conversions": 10, "revenue": 100, "cost": 500}
        )
        assert result["action"]["action"] == "auto_pause"

    def test_run_daily_cycle(self):
        result = AIAutonomousCampaignManager.run_daily_cycle(
            "camp1", {"impressions": 1000, "conversions": 50, "revenue": 2000, "cost": 500}
        )
        assert "daily_report" in result
        assert result["daily_report"]["campaign_id"] == "camp1"

    def test_full_autonomous_cycle_with_opportunity(self):
        result = AIAutonomousCampaignManager.full_autonomous_cycle(
            real_stock=3, product_id="prod1", reference_date=QUIET_DATE
        )
        assert result["opportunities_found"] == 1
        assert result["campaign_plan"] is not None
        assert result["campaign_plan"]["template_type"] == "scarcity"

    def test_full_autonomous_cycle_no_opportunity(self):
        result = AIAutonomousCampaignManager.full_autonomous_cycle(reference_date=QUIET_DATE)
        assert result["opportunities_found"] == 0
        assert result["campaign_plan"] is None

    def test_full_autonomous_cycle_picks_highest_priority(self):
        result = AIAutonomousCampaignManager.full_autonomous_cycle(
            real_stock=15,  # medium
            reference_date=IMMINENT_BLACK_FRIDAY,  # high (seasonal, 2 days out)
        )
        assert result["campaign_plan"]["opportunity_source"] == "seasonal_event"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
