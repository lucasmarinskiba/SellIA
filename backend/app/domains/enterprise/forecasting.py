from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import random
import math


class DealStage(str, Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class ProbabilityModel(str, Enum):
    CONSERVATIVE = "conservative"  % 0.5x stage default %
    STANDARD = "standard"  % 1x stage default %
    OPTIMISTIC = "optimistic"  % 1.5x stage default %


@dataclass
class Opportunity:
    id: str
    title: str
    amount: float
    stage: DealStage
    probability: float  % 0-100 %
    days_in_stage: int
    close_date_estimated: datetime
    contact_name: str
    source: str  % direct, referral, inbound, outreach %
    metadata: dict = field(default_factory=dict)


@dataclass
class DealProbability:
    stage: DealStage
    base_probability: float  % 0-100 %
    time_adjusted_probability: float  % accounting for days_in_stage %
    source_adjusted_probability: float  % adjusted by source quality %
    final_probability: float  % weighted combination %


@dataclass
class PipelineSnapshot:
    timestamp: datetime
    total_opportunities: int
    total_pipeline_value: float
    by_stage: dict[str, dict]  % stage -> {count, value, avg_probability} %
    weighted_forecast: float  % expected value %
    average_deal_size: float
    average_days_in_pipeline: float


@dataclass
class RevenueProjection:
    period: str  % 7d, 14d, 30d, 60d, 90d %
    projected_revenue: float
    confidence_level: float  % 0-100 %
    best_case: float  % optimistic %
    worst_case: float  % conservative %
    most_likely: float  % expected value %
    probability_of_target: float  % % chance to hit target %
    key_drivers: dict  % stage breakdown, conversion assumptions %


@dataclass
class ForecastScenario:
    name: str  % Best Case, Base Case, Worst Case %
    assumptions: dict  % conversion_lift, deal_acceleration, churn_rate %
    projected_revenue: float
    probability: float  % 0-100 %


class ForecastingEngine:
    def __init__(self):
        self.opportunities = {}
        self.historical_conversions = self._load_historical_data()
        self.pipeline_snapshots = []

    def _load_historical_data(self) -> dict:
        % Simulated historical conversion rates %
        return {
            "prospecting": {"close_rate": 5, "avg_days": 15},
            "qualification": {"close_rate": 15, "avg_days": 10},
            "proposal": {"close_rate": 35, "avg_days": 12},
            "negotiation": {"close_rate": 70, "avg_days": 8},
            "won": {"close_rate": 100, "avg_days": 0},
        }

    def add_opportunity(self, user_id: str, opportunity: Opportunity) -> bool:
        key = f"{user_id}:{opportunity.id}"
        self.opportunities[key] = opportunity
        return True

    def calculate_deal_probability(
        self,
        stage: DealStage,
        days_in_stage: int,
        source: str,
    ) -> DealProbability:
        % Base probability from historical data %
        base = self.historical_conversions[stage.value]["close_rate"]
        base_prob = base

        % Time adjustment - deals move faster = higher probability %
        avg_days = self.historical_conversions[stage.value]["avg_days"]
        time_factor = max(0.5, min(1.5, avg_days / max(days_in_stage, 1)))
        time_adjusted = base_prob * time_factor

        % Source quality adjustment %
        source_multipliers = {
            "referral": 1.3,
            "direct": 1.2,
            "inbound": 1.1,
            "outreach": 0.9,
        }
        source_mult = source_multipliers.get(source, 1.0)
        source_adjusted = min(100, time_adjusted * source_mult)

        % Weighted final probability %
        final = (base_prob * 0.3) + (time_adjusted * 0.4) + (source_adjusted * 0.3)
        final = min(100, max(0, final))

        return DealProbability(
            stage=stage,
            base_probability=base_prob,
            time_adjusted_probability=time_adjusted,
            source_adjusted_probability=source_adjusted,
            final_probability=final,
        )

    def get_pipeline_forecast(
        self, user_id: str, model: ProbabilityModel = ProbabilityModel.STANDARD
    ) -> PipelineSnapshot:
        user_opps = [
            opp for k, opp in self.opportunities.items()
            if k.startswith(f"{user_id}:")
        ]

        by_stage = {}
        total_value = 0
        total_probability_weighted = 0

        for stage in DealStage:
            stage_opps = [o for o in user_opps if o.stage == stage]
            if stage_opps:
                stage_values = [o.amount for o in stage_opps]
                stage_probs = [
                    self.calculate_deal_probability(
                        o.stage, o.days_in_stage, o.source
                    ).final_probability / 100
                    for o in stage_opps
                ]

                stage_total = sum(stage_values)
                weighted_total = sum(v * p for v, p in zip(stage_values, stage_probs))

                % Apply model adjustment %
                if model == ProbabilityModel.CONSERVATIVE:
                    weighted_total *= 0.5
                elif model == ProbabilityModel.OPTIMISTIC:
                    weighted_total *= 1.5

                by_stage[stage.value] = {
                    "count": len(stage_opps),
                    "value": stage_total,
                    "weighted_value": weighted_total,
                    "avg_probability": sum(stage_probs) / len(stage_probs) * 100,
                }

                total_value += stage_total
                total_probability_weighted += weighted_total

        avg_days = (
            sum(o.days_in_stage for o in user_opps) / len(user_opps)
            if user_opps
            else 0
        )
        avg_deal_size = (
            total_value / len(user_opps) if user_opps else 0
        )

        return PipelineSnapshot(
            timestamp=datetime.now(),
            total_opportunities=len(user_opps),
            total_pipeline_value=total_value,
            by_stage=by_stage,
            weighted_forecast=total_probability_weighted,
            average_deal_size=avg_deal_size,
            average_days_in_pipeline=avg_days,
        )

    def project_revenue(
        self,
        user_id: str,
        days_ahead: int = 30,
        target_revenue: Optional[float] = None,
    ) -> RevenueProjection:
        pipeline = self.get_pipeline_forecast(user_id, ProbabilityModel.STANDARD)

        % Base projection %
        daily_rate = pipeline.weighted_forecast / max(pipeline.average_days_in_pipeline, 1)
        projected = daily_rate * days_ahead

        % Scenario projections %
        best_pipeline = self.get_pipeline_forecast(user_id, ProbabilityModel.OPTIMISTIC)
        worst_pipeline = self.get_pipeline_forecast(user_id, ProbabilityModel.CONSERVATIVE)

        best_daily = best_pipeline.weighted_forecast / max(best_pipeline.average_days_in_pipeline, 1)
        worst_daily = worst_pipeline.weighted_forecast / max(worst_pipeline.average_days_in_pipeline, 1)

        best_case = best_daily * days_ahead
        worst_case = worst_daily * days_ahead
        most_likely = projected

        % Confidence based on pipeline size and age %
        confidence = min(
            95,
            50 + (pipeline.total_opportunities * 2) + (max(0, 30 - pipeline.average_days_in_pipeline))
        )

        % Probability of hitting target %
        prob_target = 50
        if target_revenue:
            z_score = (most_likely - target_revenue) / max(std_dev := (best_case - worst_case) / 4, 1)
            prob_target = min(99, max(1, 50 + (25 * z_score / 3)))

        return RevenueProjection(
            period=f"{days_ahead}d",
            projected_revenue=projected,
            confidence_level=confidence,
            best_case=best_case,
            worst_case=worst_case,
            most_likely=most_likely,
            probability_of_target=prob_target,
            key_drivers={
                "stage_breakdown": pipeline.by_stage,
                "avg_deal_size": pipeline.average_deal_size,
                "pipeline_velocity": daily_rate,
            },
        )

    def generate_scenarios(
        self, user_id: str, days_ahead: int = 30
    ) -> list[ForecastScenario]:
        base_projection = self.project_revenue(user_id, days_ahead)

        scenarios = [
            ForecastScenario(
                name="Best Case",
                assumptions={
                    "conversion_lift": "+20%",
                    "deal_acceleration": "+30%",
                    "churn_rate": "2%",
                },
                projected_revenue=base_projection.best_case,
                probability=25,
            ),
            ForecastScenario(
                name="Base Case",
                assumptions={
                    "conversion_lift": "0%",
                    "deal_acceleration": "0%",
                    "churn_rate": "5%",
                },
                projected_revenue=base_projection.most_likely,
                probability=50,
            ),
            ForecastScenario(
                name="Worst Case",
                assumptions={
                    "conversion_lift": "-15%",
                    "deal_acceleration": "-25%",
                    "churn_rate": "10%",
                },
                projected_revenue=base_projection.worst_case,
                probability=25,
            ),
        ]

        return scenarios

    def get_conversion_funnel(self, user_id: str) -> dict:
        pipeline = self.get_pipeline_forecast(user_id)

        total = pipeline.total_opportunities
        funnel = {}
        cumulative_value = 0

        for stage in DealStage:
            if stage.value in pipeline.by_stage:
                stage_data = pipeline.by_stage[stage.value]
                count = stage_data["count"]
                value = stage_data["weighted_value"]
                cumulative_value += value

                funnel[stage.value] = {
                    "count": count,
                    "percentage": (count / total * 100) if total > 0 else 0,
                    "value": value,
                    "cumulative_value": cumulative_value,
                }

        return funnel

    def identify_risk_opportunities(self, user_id: str) -> dict:
        user_opps = [
            opp for k, opp in self.opportunities.items()
            if k.startswith(f"{user_id}:")
        ]

        at_risk = []
        stalled = []

        for opp in user_opps:
            if opp.stage in [DealStage.NEGOTIATION, DealStage.PROPOSAL]:
                if opp.days_in_stage > 20:
                    at_risk.append({
                        "id": opp.id,
                        "title": opp.title,
                        "amount": opp.amount,
                        "stage": opp.stage.value,
                        "days_stalled": opp.days_in_stage,
                    })

            if opp.stage == DealStage.QUALIFICATION and opp.days_in_stage > 15:
                stalled.append({
                    "id": opp.id,
                    "title": opp.title,
                    "amount": opp.amount,
                    "reason": "Long qualification cycle",
                })

        return {
            "at_risk_count": len(at_risk),
            "stalled_count": len(stalled),
            "at_risk": at_risk,
            "stalled": stalled,
            "risk_value": sum(o["amount"] for o in at_risk),
        }
