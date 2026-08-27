"""OrchestratorService — multi-domain decision engine."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.cashflow.service import CashFlowService
from app.domains.orchestrator.types import (
    Action,
    BusinessMetrics,
    OrchestratorPlan,
    Priority,
    Recommendation,
    Scenario,
)

logger = get_logger(__name__)


class OrchestratorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(self, business_id: uuid.UUID) -> OrchestratorPlan:
        """Analyze current state across all domains → produce recommendation plan."""
        metrics = await self._gather_metrics(business_id)
        priority = self._classify_priority(metrics)
        recommendations = self._make_recommendations(metrics, priority)

        return OrchestratorPlan(
            business_id=str(business_id),
            metrics=metrics,
            priority=priority,
            recommendations=recommendations,
            reasoning=self._explain_reasoning(metrics, priority, recommendations),
        )

    async def _gather_metrics(self, business_id: uuid.UUID) -> BusinessMetrics:
        """Fetch real-time snapshots from ledger, forecasting, ad_budget domains."""
        # Cash + runway from cashflow
        cf_svc = CashFlowService(self.db)
        try:
            cf = await cf_svc.forecast(business_id, horizon_days=30)
            cash = cf.end_balance
            runway = cf.runway_days
            revenue_30d = sum(p.revenue_forecast for p in cf.points)
        except Exception:  # noqa: BLE001
            cash = Decimal("0")
            runway = None
            revenue_30d = Decimal("0")

        # Forecast confidence from forecasting domain
        from app.domains.forecasting.service import ForecastingService

        fc_svc = ForecastingService(self.db)
        forecast_data = await fc_svc.get_forecast(business_id, "total:revenue:daily:*", horizon=30)
        confidence = Decimal("0.5")
        if forecast_data and forecast_data.get("points"):
            points = forecast_data["points"]
            q10_sum = sum(p.get("q10", 0) for p in points)
            q90_sum = sum(p.get("q90", 0) for p in points)
            q50_sum = sum(p.get("yhat", 0) for p in points)
            if q50_sum > 0:
                confidence = Decimal(str((q90_sum - q10_sum) / (2 * q50_sum)))
                confidence = Decimal("1") - confidence.min(Decimal("1"))

        # OpEx and margins from ledger
        from app.domains.ledger.service import LedgerService

        ledger_svc = LedgerService(self.db)
        try:
            pnl = await ledger_svc.profit_and_loss(business_id, period_months=1)
            monthly_opex = pnl.get("total_opex", Decimal("0"))
            gross_margin = pnl.get("gross_margin_pct", Decimal("0.3"))
        except Exception:  # noqa: BLE001
            monthly_opex = Decimal("0")
            gross_margin = Decimal("0.3")

        # Ad budget metrics from ad_budget domain
        from app.domains.ad_budget.service import AdBudgetService

        ab_svc = AdBudgetService(self.db)
        try:
            channels = await ab_svc.list_channels(business_id)
            high_roas = max(channels, key=lambda c: c.last_roas or Decimal("0")).name if channels else "unknown"
            low_roas = min(channels, key=lambda c: c.last_roas or Decimal("99")).name if channels else "unknown"
            daily_spend = sum(c.daily_budget or Decimal("0") for c in channels)
        except Exception:  # noqa: BLE001
            high_roas = "unknown"
            low_roas = "unknown"
            daily_spend = Decimal("0")

        return BusinessMetrics(
            cash_balance=cash,
            runway_days=runway,
            forecast_revenue_30d=revenue_30d,
            forecast_confidence=confidence,
            current_monthly_opex=monthly_opex,
            current_gross_margin=gross_margin,
            highest_roas_channel=high_roas,
            lowest_roas_channel=low_roas,
            ad_spend_daily=daily_spend,
            priority=Priority.BALANCED,  # updated below
        )

    def _classify_priority(self, metrics: BusinessMetrics) -> Priority:
        """Map runway to priority level."""
        runway = metrics.runway_days or 180
        if runway < 30:
            return Priority.PRESERVE_CASH
        elif runway < 60:
            return Priority.STABILIZE
        elif runway < 90:
            return Priority.BALANCED
        else:
            return Priority.GROWTH

    def _make_recommendations(
        self, metrics: BusinessMetrics, priority: Priority
    ) -> list[Recommendation]:
        """Generate action recommendations based on priority + metrics."""
        recs = []

        if priority == Priority.PRESERVE_CASH:
            # Cash emergency: cut spend, preserve cash
            recs.append(
                Recommendation(
                    action=Action.REDUCE_AD_SPEND,
                    rationale=f"Runway critical ({metrics.runway_days} days). Reduce ad spend 30% to preserve cash.",
                    target_value=Decimal("0.70"),  # reduce to 70% of current
                    confidence=Decimal("0.95"),
                    impact_cash_30d=metrics.ad_spend_daily * 30 * Decimal("0.30"),
                    impact_revenue_30d=metrics.forecast_revenue_30d * Decimal("-0.10"),
                )
            )
            recs.append(
                Recommendation(
                    action=Action.CUT_OPEX,
                    rationale="In cash preservation mode. Negotiate vendor payments, defer non-critical costs.",
                    target_value=Decimal("0.85"),  # reduce to 85% of current
                    confidence=Decimal("0.70"),
                    impact_cash_30d=metrics.current_monthly_opex * Decimal("0.15"),
                )
            )

        elif priority == Priority.STABILIZE:
            # Tight runway: be selective with spend
            if metrics.forecast_confidence < Decimal("0.3"):
                recs.append(
                    Recommendation(
                        action=Action.REDUCE_AD_SPEND,
                        rationale=f"Forecast confidence low ({metrics.forecast_confidence:.1%}). Reduce spend 15% until forecast clears.",
                        target_value=Decimal("0.85"),
                        confidence=Decimal("0.80"),
                        impact_cash_30d=metrics.ad_spend_daily * 30 * Decimal("0.15"),
                    )
                )
            else:
                recs.append(
                    Recommendation(
                        action=Action.REALLOCATE_AD_BUDGET,
                        rationale=f"Shift budget toward {metrics.highest_roas_channel} (high ROAS) from {metrics.lowest_roas_channel}.",
                        target_value=Decimal("0.15"),  # 15% shift
                        confidence=Decimal("0.85"),
                        impact_revenue_30d=metrics.forecast_revenue_30d * Decimal("0.05"),
                    )
                )

        elif priority == Priority.BALANCED:
            # Normal operations: optimize for ROAS
            recs.append(
                Recommendation(
                    action=Action.REALLOCATE_AD_BUDGET,
                    rationale=f"Rebalance toward {metrics.highest_roas_channel}. Expected revenue lift 8%.",
                    target_value=Decimal("0.20"),
                    confidence=Decimal("0.80"),
                    impact_revenue_30d=metrics.forecast_revenue_30d * Decimal("0.08"),
                )
            )

        else:  # GROWTH
            # Strong cash position: invest in growth
            recs.append(
                Recommendation(
                    action=Action.REALLOCATE_AD_BUDGET,
                    rationale=f"Strong runway ({metrics.runway_days} days). Increase spend on {metrics.highest_roas_channel} by 20%.",
                    target_value=Decimal("1.20"),
                    confidence=Decimal("0.85"),
                    impact_revenue_30d=metrics.forecast_revenue_30d * Decimal("0.12"),
                    impact_cash_30d=-(metrics.ad_spend_daily * 30 * Decimal("0.20")),
                )
            )

        return recs

    def _explain_reasoning(
        self, metrics: BusinessMetrics, priority: Priority, recommendations: list[Recommendation]
    ) -> str:
        """Narrative explanation of the decision."""
        lines = [
            f"Priority: {priority.value}",
            f"Cash runway: {metrics.runway_days} days",
            f"Forecast confidence: {metrics.forecast_confidence:.0%}",
            f"30-day revenue forecast: ${metrics.forecast_revenue_30d:,.0f}",
            f"Daily ad spend: ${metrics.ad_spend_daily:,.0f}",
            f"Highest ROAS: {metrics.highest_roas_channel}",
            f"Recommendations: {len(recommendations)} action(s)",
        ]
        return "; ".join(lines)

    async def scenarios(
        self, business_id: uuid.UUID, base_plan: OrchestratorPlan
    ) -> list[Scenario]:
        """Generate what-if scenarios for planning."""
        scenarios_list = []

        # Scenario 1: increase ad spend 25%
        metrics = base_plan.metrics
        scenarios_list.append(
            Scenario(
                name="ad_spend_+25%",
                description="Increase daily ad spend by 25%",
                changes={"ad_spend_daily": 0.25},
                projected_cash_30d=metrics.cash_balance - (metrics.ad_spend_daily * 30 * Decimal("0.25")),
                projected_revenue_30d=metrics.forecast_revenue_30d * Decimal("1.10"),
                projected_runway_days=(
                    int((metrics.cash_balance - (metrics.ad_spend_daily * 30 * Decimal("0.25"))) / (metrics.current_monthly_opex / 30))
                    if metrics.current_monthly_opex > 0
                    else None
                ),
                feasibility="easy",
                risks=["erosion of ROAS if scaling beyond sweet spot", "cash burn accelerates"],
            )
        )

        # Scenario 2: reduce opex 15%
        scenarios_list.append(
            Scenario(
                name="opex_-15%",
                description="Reduce operating expenses by 15%",
                changes={"opex_pct": -0.15},
                projected_cash_30d=metrics.cash_balance + (metrics.current_monthly_opex * Decimal("0.15")),
                projected_revenue_30d=metrics.forecast_revenue_30d * Decimal("0.98"),  # slight impact
                projected_runway_days=(
                    int((metrics.cash_balance + (metrics.current_monthly_opex * Decimal("0.15"))) / ((metrics.current_monthly_opex * Decimal("0.85")) / 30))
                    if metrics.current_monthly_opex > 0
                    else None
                ),
                feasibility="moderate",
                risks=["reduced capacity/service quality", "may impact retention"],
            )
        )

        # Scenario 3: do nothing (baseline)
        scenarios_list.append(
            Scenario(
                name="baseline",
                description="Continue current operations",
                changes={},
                projected_cash_30d=metrics.cash_balance - (metrics.ad_spend_daily * 30),
                projected_revenue_30d=metrics.forecast_revenue_30d,
                projected_runway_days=metrics.runway_days,
                feasibility="easy",
                risks=[],
            )
        )

        return scenarios_list
