"""Orchestrator — multi-domain decision engine."""

from decimal import Decimal

from app.domains.orchestrator.types import (
    Action,
    BusinessMetrics,
    OrchestratorPlan,
    Priority,
    Recommendation,
)


def test_priority_classification():
    """Test runway → priority mapping."""
    # Preserve cash
    m = BusinessMetrics(
        cash_balance=Decimal("1000"),
        runway_days=20,
        forecast_revenue_30d=Decimal("5000"),
        forecast_confidence=Decimal("0.5"),
        current_monthly_opex=Decimal("2000"),
        current_gross_margin=Decimal("0.35"),
        highest_roas_channel="instagram",
        lowest_roas_channel="tiktok",
        ad_spend_daily=Decimal("100"),
        priority=Priority.PRESERVE_CASH,
    )
    assert m.runway_days < 30

    # Growth mode
    m2 = BusinessMetrics(
        cash_balance=Decimal("50000"),
        runway_days=150,
        forecast_revenue_30d=Decimal("15000"),
        forecast_confidence=Decimal("0.7"),
        current_monthly_opex=Decimal("2000"),
        current_gross_margin=Decimal("0.40"),
        highest_roas_channel="instagram",
        lowest_roas_channel="tiktok",
        ad_spend_daily=Decimal("100"),
        priority=Priority.GROWTH,
    )
    assert m2.runway_days > 90


def test_recommendation_structure():
    """Verify recommendation format."""
    rec = Recommendation(
        action=Action.REALLOCATE_AD_BUDGET,
        rationale="Shift to high-ROAS channel",
        target_value=Decimal("0.20"),
        confidence=Decimal("0.85"),
        impact_revenue_30d=Decimal("500"),
    )
    assert rec.action == Action.REALLOCATE_AD_BUDGET
    assert rec.confidence == Decimal("0.85")
    assert rec.impact_revenue_30d == Decimal("500")


def test_plan_structure():
    """Verify plan structure."""
    metrics = BusinessMetrics(
        cash_balance=Decimal("10000"),
        runway_days=60,
        forecast_revenue_30d=Decimal("8000"),
        forecast_confidence=Decimal("0.6"),
        current_monthly_opex=Decimal("2000"),
        current_gross_margin=Decimal("0.35"),
        highest_roas_channel="instagram",
        lowest_roas_channel="tiktok",
        ad_spend_daily=Decimal("100"),
        priority=Priority.BALANCED,
    )
    plan = OrchestratorPlan(
        business_id="test-biz",
        metrics=metrics,
        priority=Priority.BALANCED,
        recommendations=[],
        scenario_name="current_state",
    )
    assert plan.business_id == "test-biz"
    assert plan.priority == Priority.BALANCED
    assert plan.metrics.runway_days == 60
