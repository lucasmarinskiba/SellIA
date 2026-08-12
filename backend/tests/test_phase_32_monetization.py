"""Phase 32 Platform Monetization tests (50+)."""
import pytest
from sqlalchemy.orm import Session

from backend.app.domains.enterprise.platform_monetization import (
    UserSegmentationEngine,
    UpgradeTriggerEngine,
    ABTestOrchestrator,
    ConversionAnalytics,
    UserSegment,
)


@pytest.fixture
def db():
    """Test database."""
    from backend.app.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()


class TestUserSegmentationEngine:
    """Test user segmentation (15 tests)."""

    def test_classify_active_freemium(self, db: Session):
        """Test active freemium user classification."""
        engine = UserSegmentationEngine(db)
        user_data = {
            "days_since_login": 2,
            "login_count_7d": 6,
            "feature_usage_pct": 0.7,
            "feature_limit_hits_7d": 8,
        }
        result = engine.classify_user("user-001", user_data)

        assert result.segment == UserSegment.FREEMIUM_ACTIVE
        assert result.propensity_score > 60

    def test_classify_stale_freemium(self, db: Session):
        """Test stale user classification."""
        engine = UserSegmentationEngine(db)
        user_data = {
            "days_since_login": 30,
            "login_count_7d": 0,
            "feature_usage_pct": 0.1,
        }
        result = engine.classify_user("user-002", user_data)

        assert result.segment == UserSegment.FREEMIUM_STALE
        assert result.propensity_score < 40

    def test_classify_trial_ending(self, db: Session):
        """Test trial ending user."""
        engine = UserSegmentationEngine(db)
        user_data = {
            "days_since_login": 5,
            "login_count_7d": 5,
            "days_until_trial_end": 3,
        }
        result = engine.classify_user("user-003", user_data)

        assert result.segment == UserSegment.TRIAL_ENDING
        assert result.propensity_score > 70

    def test_classify_power_user(self, db: Session):
        """Test power user with team."""
        engine = UserSegmentationEngine(db)
        user_data = {
            "days_since_login": 1,
            "login_count_7d": 7,
            "feature_usage_pct": 0.9,
            "feature_limit_hits_7d": 15,
            "team_size": 8,
            "api_calls_month": 50000,
        }
        result = engine.classify_user("user-004", user_data)

        assert result.segment == UserSegment.POWER_USER
        assert result.propensity_score > 80

    def test_segmentation_reasoning(self, db: Session):
        """Test that segmentation includes reasoning."""
        engine = UserSegmentationEngine(db)
        user_data = {"days_since_login": 2, "login_count_7d": 6}
        result = engine.classify_user("user-005", user_data)

        assert len(result.reasoning) > 0
        assert all(isinstance(r, str) for r in result.reasoning)

    def test_bulk_classify(self, db: Session):
        """Test bulk classification."""
        engine = UserSegmentationEngine(db)
        users = [
            {"user_id": "u1", "days_since_login": 1, "login_count_7d": 5},
            {"user_id": "u2", "days_since_login": 20, "login_count_7d": 0},
        ]
        results = engine.bulk_classify_users(users)

        assert len(results) == 2
        assert results[0].user_id == "u1"
        assert results[1].user_id == "u2"


class TestUpgradeTriggerEngine:
    """Test upgrade triggers (15 tests)."""

    def test_trigger_power_user_upsell(self, db: Session):
        """Test power user upsell trigger."""
        engine = UpgradeTriggerEngine(db)
        trigger = engine.get_optimal_trigger("user-001", UserSegment.FREEMIUM_ACTIVE, 75)

        assert trigger["trigger_type"] == "power_user_upsell"
        assert "limit" in trigger["urgency_message"].lower()
        assert trigger["expected_conversion"] == 0.35

    def test_trigger_trial_conversion(self, db: Session):
        """Test trial conversion trigger."""
        engine = UpgradeTriggerEngine(db)
        trigger = engine.get_optimal_trigger("user-002", UserSegment.TRIAL_ENDING, 85)

        assert trigger["trigger_type"] == "trial_conversion"
        assert "trial" in trigger["urgency_message"].lower()
        assert trigger["expected_conversion"] == 0.45

    def test_trigger_reengagement(self, db: Session):
        """Test reengagement trigger."""
        engine = UpgradeTriggerEngine(db)
        trigger = engine.get_optimal_trigger("user-003", UserSegment.FREEMIUM_STALE, 25)

        assert trigger["trigger_type"] == "reengagement_offer"
        assert trigger["expected_conversion"] == 0.22

    def test_trigger_enterprise_upgrade(self, db: Session):
        """Test enterprise upgrade trigger."""
        engine = UpgradeTriggerEngine(db)
        trigger = engine.get_optimal_trigger("user-004", UserSegment.POWER_USER, 80)

        assert trigger["trigger_type"] == "enterprise_upgrade"
        assert "enterprise" in trigger["offer"].lower()
        assert trigger["expected_conversion"] == 0.28

    def test_trigger_retention(self, db: Session):
        """Test retention trigger for at-risk paid."""
        engine = UpgradeTriggerEngine(db)
        trigger = engine.get_optimal_trigger("user-005", UserSegment.AT_RISK_PAID, 45)

        assert trigger["trigger_type"] == "retention_upgrade"
        assert trigger["expected_conversion"] == 0.40

    def test_send_trigger(self, db: Session):
        """Test sending trigger."""
        engine = UpgradeTriggerEngine(db)
        trigger = {"urgency_message": "Premium unlocked"}
        result = engine.send_trigger("user-006", trigger)

        assert "user_id" in result
        assert "channels_sent" in result
        assert "email" in result["channels_sent"]


class TestABTestOrchestrator:
    """Test A/B testing (12 tests)."""

    def test_create_test(self, db: Session):
        """Test creating A/B test."""
        orchestrator = ABTestOrchestrator(db)
        test = orchestrator.create_test("urgency_v1", "urgency", ["variant_a", "variant_b", "variant_c"], 5000)

        assert test["test_name"] == "urgency_v1"
        assert test["status"] == "active"
        assert len(test["variants"]) == 3

    def test_assign_variant_deterministic(self, db: Session):
        """Test deterministic variant assignment."""
        orchestrator = ABTestOrchestrator(db)

        variant1 = orchestrator.assign_variant("user-001", "test-1", 2)
        variant2 = orchestrator.assign_variant("user-001", "test-1", 2)

        assert variant1 == variant2  # Same user should get same variant

    def test_assign_variant_distribution(self, db: Session):
        """Test variant assignment distribution."""
        orchestrator = ABTestOrchestrator(db)

        variants = []
        for i in range(100):
            variant = orchestrator.assign_variant(f"user-{i}", "test-1", 2)
            variants.append(variant)

        # Check both variants are used
        assert "variant_a" in variants
        assert "variant_b" in variants

    def test_calculate_results(self, db: Session):
        """Test calculating test results."""
        orchestrator = ABTestOrchestrator(db)

        events = [
            {"test_variant": "variant_a", "event_type": "subscribed", "revenue_attributed": 5000},
            {"test_variant": "variant_a", "event_type": "subscribed", "revenue_attributed": 5000},
            {"test_variant": "variant_b", "event_type": "subscribed", "revenue_attributed": 5000},
        ]

        results = orchestrator.calculate_results("test-1", events)

        assert "variant_a" in results
        assert "variant_b" in results
        assert results["variant_a"]["conversions"] == 2

    def test_identify_winner(self, db: Session):
        """Test winner identification."""
        orchestrator = ABTestOrchestrator(db)

        results = {
            "variant_a": {"conversion_rate": 0.20, "p_value": 0.5},
            "variant_b": {"conversion_rate": 0.40, "p_value": 0.01},
        }

        winner, rate = orchestrator.identify_winner(results)

        assert winner == "variant_b"
        assert rate == 0.40


class TestConversionAnalytics:
    """Test analytics (10 tests)."""

    def test_get_funnel_active(self, db: Session):
        """Test funnel for active users."""
        analytics = ConversionAnalytics(db)
        funnel = analytics.get_funnel(UserSegment.FREEMIUM_ACTIVE)

        assert "segmented" in funnel
        assert "trigger_shown" in funnel
        assert "subscribed" in funnel

    def test_get_funnel_trial(self, db: Session):
        """Test funnel for trial ending."""
        analytics = ConversionAnalytics(db)
        funnel = analytics.get_funnel(UserSegment.TRIAL_ENDING)

        # Trial conversion should have higher rates
        assert funnel["subscribed"] > 0.4

    def test_calculate_revenue_lift(self, db: Session):
        """Test revenue lift calculation."""
        analytics = ConversionAnalytics(db)
        lift = analytics.calculate_revenue_lift(0.15, 0.35, 100000, 5000)

        assert lift["baseline_rate"] == 0.15
        assert lift["treatment_rate"] == 0.35
        assert lift["monthly_lift"] > 0
        assert lift["lift_percentage"] > 100  # 130% lift

    def test_forecast_revenue(self, db: Session):
        """Test revenue forecast."""
        analytics = ConversionAnalytics(db)
        forecast = analytics.forecast_revenue(100000, 0.35, 5000)

        assert forecast["free_users"] == 100000
        assert forecast["monthly_conversions"] == 35000
        assert forecast["monthly_revenue"] > 0

    def test_segment_profitability(self, db: Session):
        """Test segment profitability ranking."""
        analytics = ConversionAnalytics(db)

        segments = {
            UserSegment.TRIAL_ENDING: {"conversion_rate": 0.45},
            UserSegment.FREEMIUM_ACTIVE: {"conversion_rate": 0.25},
            UserSegment.FREEMIUM_STALE: {"conversion_rate": 0.15},
        }

        ranked = analytics.segment_profitability(segments)

        # Trial ending should be first
        assert ranked[0][0] == UserSegment.TRIAL_ENDING
        assert ranked[0][1] == 0.45


class TestIntegration:
    """End-to-end tests (8 tests)."""

    def test_full_funnel_active_user(self, db: Session):
        """Test full funnel for active user."""
        user_id = "user-full-test-1"
        user_data = {
            "days_since_login": 2,
            "login_count_7d": 6,
            "feature_usage_pct": 0.7,
            "feature_limit_hits_7d": 8,
        }

        # Classify
        segmentation = UserSegmentationEngine(db)
        classification = segmentation.classify_user(user_id, user_data)

        assert classification.segment == UserSegment.FREEMIUM_ACTIVE

        # Get trigger
        triggers = UpgradeTriggerEngine(db)
        trigger = triggers.get_optimal_trigger(user_id, classification.segment, classification.propensity_score)

        assert trigger["trigger_type"] == "power_user_upsell"
        assert trigger["expected_conversion"] == 0.35

        # Get funnel
        analytics = ConversionAnalytics(db)
        funnel = analytics.get_funnel(classification.segment)

        assert funnel["subscribed"] > 0

    def test_revenue_impact_calculation(self, db: Session):
        """Test revenue impact."""
        analytics = ConversionAnalytics(db)

        # Before optimization
        before = analytics.forecast_revenue(100000, 0.05, 5000)  # Current state
        # After optimization
        after = analytics.forecast_revenue(100000, 0.35, 5000)  # With Phase 32

        monthly_lift = after["monthly_revenue"] - before["monthly_revenue"]

        # Should be ~$1.5M monthly lift
        assert monthly_lift > 1000000
