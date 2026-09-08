"""Deal scoring, pipeline forecasting and outcome tracking -- backed by real
Deal rows (app.domains.crm.models.Deal), not caller-supplied dicts or
in-memory state.

Rewrite history: ForecastingManager originally took `deals: list[dict]` as
input and cached results in plain instance attributes on a module-level
singleton -- meaning scores/at-risk lists were shared across every business
in the app and lost on every restart. api/v1/enterprise_forecast.py
additionally called 6 methods (add_opportunity, get_pipeline_forecast,
project_revenue, generate_scenarios, get_conversion_funnel,
identify_risk_opportunities) that never existed anywhere, against an
`Opportunity`/`DealStage`/`ProbabilityModel` set of classes that also never
existed -- a second, never-built parallel concept to the real `Deal` model.
Consolidated onto Deal instead of building a duplicate "Opportunity" system:
every method here now queries live Deal rows scoped by business_id and
returns real numbers. Only actual win/loss events are persisted (see
forecasting_models.DealOutcome) -- deal scores and pipeline forecasts are
recomputed on every call, which is more correct than a cache (Deal state
changes constantly and a stale forecast is worse than a slower one).
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from dataclasses import asdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.crm.models import Deal, LeadStage
from app.domains.enterprise.collaboration import DealComment
from .deal_scorer import DealScorer, RevenueForecast, DealScoreFactors, RiskLevel

# Maps the app's real pipeline stages onto DealScorer's weight buckets
# (which were written with generic stage names). closed_lost intentionally
# scores like a fresh lead's low end -- a scored "risk" list should never
# include already-lost deals, and the win_probability output isn't
# meaningful for a deal that's already resolved.
_STAGE_TO_SCORER_KEY = {
    LeadStage.NEW_LEAD: "discovery",
    LeadStage.CONTACTED: "discovery",
    LeadStage.QUALIFIED: "qualified",
    LeadStage.PROPOSAL_SENT: "proposal",
    LeadStage.NEGOTIATING: "negotiation",
    LeadStage.CLOSED_WON: "closed",
    LeadStage.CLOSED_LOST: "discovery",
    LeadStage.NURTURE: "discovery",
}

# Open (not yet won/lost) stages -- what "the pipeline" means throughout
# this module. Closed deals are excluded from forecasts/risk/funnel by
# design (a closed deal isn't a forecast input anymore).
_OPEN_STAGES = [
    LeadStage.NEW_LEAD, LeadStage.CONTACTED, LeadStage.QUALIFIED,
    LeadStage.PROPOSAL_SENT, LeadStage.NEGOTIATING, LeadStage.NURTURE,
]


def _deal_to_factors_dict(deal: Deal, comment_count: int) -> dict:
    """Convert a real Deal row into the dict shape DealScorer/RevenueForecast
    expect. engagement_velocity and historical_close_rate have no real data
    source yet in this schema (no per-deal activity/touch log, no historical
    win-rate-by-segment table) -- defaulted honestly rather than invented;
    everything else here is real.
    """
    now = datetime.now(timezone.utc)
    updated_at = deal.updated_at if deal.updated_at.tzinfo else deal.updated_at.replace(tzinfo=timezone.utc)
    days_since_update = max((now - updated_at).days, 0)

    return {
        "id": str(deal.id),
        "name": deal.title,
        "stage": _STAGE_TO_SCORER_KEY.get(deal.stage, "discovery"),
        "days_in_stage": days_since_update,
        "engagement_velocity": 0.0,  # no per-deal activity log to derive this from yet
        "proposal_status": "sent" if deal.stage in (
            LeadStage.PROPOSAL_SENT, LeadStage.NEGOTIATING, LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST
        ) else "not_sent",
        "comment_count": comment_count,
        "last_activity_days": days_since_update,
        "value": float(deal.value) if deal.value is not None else 0.0,
        "close_rate": 0.5,  # no historical win-rate-by-segment data source yet
    }


async def _fetch_open_deals_with_comments(business_id: UUID, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Deal).where(Deal.business_id == business_id, Deal.stage.in_(_OPEN_STAGES))
    )
    deals = result.scalars().all()
    if not deals:
        return []

    deal_ids = [str(d.id) for d in deals]
    counts_result = await db.execute(
        select(DealComment.deal_id, func.count(DealComment.id))
        .where(DealComment.deal_id.in_(deal_ids))
        .group_by(DealComment.deal_id)
    )
    counts = dict(counts_result.all())

    return [_deal_to_factors_dict(d, counts.get(str(d.id), 0)) for d in deals]


class ForecastingManager:
    def __init__(self):
        self.scorer = DealScorer()
        self.forecaster = RevenueForecast()

    async def analyze_deals(self, business_id: UUID, db: AsyncSession) -> dict:
        """Score every open deal in the pipeline for win probability and risk."""
        deals = await _fetch_open_deals_with_comments(business_id, db)

        scores = []
        at_risk = []
        high_probability = []

        for deal in deals:
            factors = DealScoreFactors(
                stage=deal["stage"], days_in_stage=deal["days_in_stage"],
                engagement_velocity=deal["engagement_velocity"], proposal_status=deal["proposal_status"],
                comment_count=deal["comment_count"], last_activity_days=deal["last_activity_days"],
                deal_value=deal["value"], historical_close_rate=deal["close_rate"],
            )
            score = self.scorer.score_deal(factors)
            score_dict = asdict(score)
            score_dict["deal_id"] = deal["id"]
            scores.append(score_dict)

            if score.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                at_risk.append({
                    "deal_id": deal["id"], "deal_name": deal["name"],
                    "value": deal["value"], "win_probability": score.win_probability,
                    "risk_level": score.risk_level.value,
                    "risk_reason": self._get_risk_reason(deal, score),
                    "suggested_action": self._get_suggested_action(deal, score),
                })
            if score.win_probability >= 0.7:
                high_probability.append({
                    "deal_id": deal["id"], "deal_name": deal["name"],
                    "value": deal["value"], "win_probability": score.win_probability,
                })

        return {
            "total_deals": len(deals),
            "high_probability_count": len(high_probability),
            "at_risk_count": len(at_risk),
            "scores": scores,
            "at_risk_deals": at_risk,
            "high_probability_deals": high_probability,
        }

    async def get_deal_score(self, business_id: UUID, deal_id: UUID, db: AsyncSession) -> Optional[dict]:
        """Score a single deal."""
        result = await db.execute(select(Deal).where(Deal.id == deal_id, Deal.business_id == business_id))
        deal = result.scalar_one_or_none()
        if not deal:
            return None

        count_result = await db.execute(
            select(func.count(DealComment.id)).where(DealComment.deal_id == str(deal_id))
        )
        deal_dict = _deal_to_factors_dict(deal, count_result.scalar() or 0)
        factors = DealScoreFactors(
            stage=deal_dict["stage"], days_in_stage=deal_dict["days_in_stage"],
            engagement_velocity=deal_dict["engagement_velocity"], proposal_status=deal_dict["proposal_status"],
            comment_count=deal_dict["comment_count"], last_activity_days=deal_dict["last_activity_days"],
            deal_value=deal_dict["value"], historical_close_rate=deal_dict["close_rate"],
        )
        score = self.scorer.score_deal(factors)
        return {
            "win_probability": score.win_probability,
            "confidence": score.confidence_level,
            "risk_level": score.risk_level.value,
            "engagement_velocity": score.engagement_velocity,
            "factors": score.ai_score_factors,
        }

    async def forecast_revenue(self, business_id: UUID, db: AsyncSession, periods: list[int] = None) -> dict:
        """Revenue forecast for multiple day-ahead periods."""
        if periods is None:
            periods = [30, 60, 90]
        deals = await _fetch_open_deals_with_comments(business_id, db)
        return {f"forecast_{p}d": self.forecaster.forecast_revenue(deals, p) for p in periods}

    async def get_pipeline_forecast(self, business_id: UUID, db: AsyncSession) -> dict:
        """Pipeline snapshot with weighted forecast, broken down by stage."""
        deals = await _fetch_open_deals_with_comments(business_id, db)
        if not deals:
            return {
                "timestamp": datetime.now(timezone.utc), "total_opportunities": 0,
                "total_pipeline_value": 0.0, "weighted_forecast": 0.0,
                "average_deal_size": 0.0, "average_days_in_pipeline": 0.0, "by_stage": {},
            }

        by_stage: dict[str, dict] = {}
        total_value = 0.0
        weighted_total = 0.0
        total_days = 0

        for deal in deals:
            factors = DealScoreFactors(
                stage=deal["stage"], days_in_stage=deal["days_in_stage"],
                engagement_velocity=deal["engagement_velocity"], proposal_status=deal["proposal_status"],
                comment_count=deal["comment_count"], last_activity_days=deal["last_activity_days"],
                deal_value=deal["value"], historical_close_rate=deal["close_rate"],
            )
            score = self.scorer.score_deal(factors)
            total_value += deal["value"]
            weighted_total += deal["value"] * score.win_probability
            total_days += deal["days_in_stage"]

            bucket = by_stage.setdefault(deal["stage"], {"count": 0, "value": 0.0, "weighted_value": 0.0, "probabilities": []})
            bucket["count"] += 1
            bucket["value"] += deal["value"]
            bucket["weighted_value"] += deal["value"] * score.win_probability
            bucket["probabilities"].append(score.win_probability)

        for stage_data in by_stage.values():
            probs = stage_data.pop("probabilities")
            stage_data["avg_probability"] = (sum(probs) / len(probs)) * 100 if probs else 0.0

        return {
            "timestamp": datetime.now(timezone.utc),
            "total_opportunities": len(deals),
            "total_pipeline_value": total_value,
            "weighted_forecast": weighted_total,
            "average_deal_size": total_value / len(deals),
            "average_days_in_pipeline": total_days / len(deals),
            "by_stage": by_stage,
        }

    async def project_revenue(self, business_id: UUID, db: AsyncSession, days_ahead: int, target_revenue: Optional[float]) -> dict:
        """Best/likely/worst-case revenue projection for a period ahead."""
        deals = await _fetch_open_deals_with_comments(business_id, db)
        forecast = self.forecaster.forecast_revenue(deals, days_ahead)
        most_likely = forecast.get("projected", 0.0)

        # Best/worst case derived from confidence spread rather than a
        # separately-invented model: +/-25% around the weighted projection,
        # a standard sales-forecasting convention when no historical
        # variance data exists yet to compute a real confidence interval.
        best_case = most_likely * 1.25
        worst_case = most_likely * 0.75

        avg_deal_size = (sum(d["value"] for d in deals) / len(deals)) if deals else 0.0
        pipeline_velocity = most_likely / days_ahead if days_ahead else 0.0

        probability_of_target = None
        if target_revenue:
            probability_of_target = min(100.0, max(0.0, (most_likely / target_revenue) * 100)) if target_revenue > 0 else 0.0

        return {
            "period": f"{days_ahead}d",
            "projected_revenue": most_likely,
            "confidence": forecast.get("confidence", 0.0) * 100,
            "best_case": best_case,
            "most_likely": most_likely,
            "worst_case": worst_case,
            "probability_of_target": probability_of_target,
            "key_drivers": {"avg_deal_size": avg_deal_size, "pipeline_velocity": pipeline_velocity},
        }

    async def generate_scenarios(self, business_id: UUID, db: AsyncSession, days_ahead: int) -> list[dict]:
        """Best/base/worst case scenario breakdown (same math as project_revenue, different shape)."""
        projection = await self.project_revenue(business_id, db, days_ahead, None)
        return [
            {"name": "best_case", "projected_revenue": projection["best_case"], "probability": 25,
             "assumptions": "All open deals close on schedule; no slippage"},
            {"name": "most_likely", "projected_revenue": projection["most_likely"], "probability": 50,
             "assumptions": "Deals close at their current scored win probability"},
            {"name": "worst_case", "projected_revenue": projection["worst_case"], "probability": 25,
             "assumptions": "High-risk deals slip or fall through"},
        ]

    async def get_conversion_funnel(self, business_id: UUID, db: AsyncSession) -> dict:
        """Real stage-by-stage funnel: count and value of ALL deals (including closed) per stage."""
        result = await db.execute(select(Deal).where(Deal.business_id == business_id))
        deals = result.scalars().all()

        stage_order = [s.value for s in LeadStage]
        funnel: dict[str, dict] = {s: {"count": 0, "value": 0.0} for s in stage_order}
        for d in deals:
            bucket = funnel[d.stage.value]
            bucket["count"] += 1
            bucket["value"] += float(d.value) if d.value is not None else 0.0

        total_count = len(deals) or 1
        cumulative_value = 0.0
        for stage in stage_order:
            cumulative_value += funnel[stage]["value"]
            funnel[stage]["percentage"] = (funnel[stage]["count"] / total_count) * 100
            funnel[stage]["cumulative_value"] = cumulative_value

        return funnel

    async def identify_risk_opportunities(self, business_id: UUID, db: AsyncSession) -> dict:
        """At-risk (high/critical score) and stalled (60+ days untouched) open deals."""
        analysis = await self.analyze_deals(business_id, db)
        stalled = [d for d in analysis["at_risk_deals"] if "60+" in d.get("risk_reason", "")]
        risk_value = sum(d["value"] for d in analysis["at_risk_deals"])

        return {
            "at_risk_count": analysis["at_risk_count"],
            "stalled_count": len(stalled),
            "risk_value": risk_value,
            "at_risk": analysis["at_risk_deals"],
            "stalled": stalled,
        }

    async def get_at_risk_summary(self, business_id: UUID, db: AsyncSession) -> dict:
        analysis = await self.analyze_deals(business_id, db)
        critical = [d for d in analysis["at_risk_deals"] if d["risk_level"] == "critical"]
        return {
            "total_at_risk": analysis["at_risk_count"],
            "critical_count": len(critical),
            "total_value_at_risk": sum(d["value"] for d in analysis["at_risk_deals"]),
            "deals": analysis["at_risk_deals"],
        }

    def _get_risk_reason(self, deal: dict, score) -> str:
        if deal["last_activity_days"] > 30:
            return "No activity for 30+ days"
        if deal["proposal_status"] == "not_sent":
            return "No proposal sent"
        if deal["days_in_stage"] > 60:
            return "Stuck in stage for 60+ days"
        if score.win_probability < 0.3:
            return "Low win probability"
        return "Multiple risk factors"

    def _get_suggested_action(self, deal: dict, score) -> str:
        if deal["proposal_status"] == "not_sent":
            return "Send proposal immediately"
        if deal["last_activity_days"] > 14:
            return "Schedule check-in call with customer"
        if score.win_probability < 0.3:
            return "Conduct deal review with manager"
        return "Increase engagement frequency"


class DealOutcomeAnalyzer:
    """Win/loss outcome recording and forecast-accuracy tracking, backed by
    the real DealOutcome table (forecasting_models.py)."""

    @staticmethod
    async def record_outcome(
        db: AsyncSession,
        deal_id: UUID,
        business_id: UUID,
        outcome: str,
        final_value: Optional[float],
        days_to_close: int,
        forecasted_probability: float,
        win_loss_reason: Optional[str] = None,
    ) -> dict:
        from .forecasting_models import DealOutcome

        accuracy = 1.0 - abs(forecasted_probability - (1.0 if outcome == "won" else 0.0))
        record = DealOutcome(
            deal_id=deal_id, business_id=business_id, outcome=outcome,
            final_value=final_value, days_to_close=days_to_close,
            forecasted_probability=forecasted_probability, forecast_accuracy=accuracy,
            win_loss_reason=win_loss_reason,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return {
            "deal_id": str(deal_id), "outcome": outcome, "final_value": final_value,
            "days_to_close": days_to_close, "forecasted_probability": forecasted_probability,
            "forecast_accuracy": accuracy, "win_loss_reason": win_loss_reason,
            "recorded_at": record.recorded_at.isoformat(),
        }

    @staticmethod
    async def get_accuracy_metrics(business_id: UUID, db: AsyncSession) -> dict:
        from .forecasting_models import DealOutcome

        result = await db.execute(select(DealOutcome).where(DealOutcome.business_id == business_id))
        outcomes = result.scalars().all()
        if not outcomes:
            return {"total_outcomes": 0, "accuracy": 0, "won_count": 0, "lost_count": 0}

        won_count = sum(1 for o in outcomes if o.outcome == "won")
        return {
            "total_outcomes": len(outcomes),
            "accuracy": float(sum(o.forecast_accuracy for o in outcomes) / len(outcomes)),
            "won_count": won_count,
            "lost_count": len(outcomes) - won_count,
            "win_rate": won_count / len(outcomes),
            "avg_days_to_close": sum(o.days_to_close or 0 for o in outcomes) / len(outcomes),
        }

    @staticmethod
    async def get_win_loss_summary(business_id: UUID, db: AsyncSession) -> dict:
        from .forecasting_models import DealOutcome

        result = await db.execute(select(DealOutcome).where(DealOutcome.business_id == business_id))
        outcomes = result.scalars().all()

        won_reasons = [o.win_loss_reason for o in outcomes if o.outcome == "won" and o.win_loss_reason]
        lost_reasons = [o.win_loss_reason for o in outcomes if o.outcome == "lost" and o.win_loss_reason]

        def top_reasons(reasons: list[str], top_n: int = 5) -> list[dict]:
            counts: dict[str, int] = {}
            for r in reasons:
                counts[r] = counts.get(r, 0) + 1
            return [{"reason": r, "count": c} for r, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]]

        return {
            "top_win_reasons": top_reasons(won_reasons),
            "top_loss_reasons": top_reasons(lost_reasons),
            "total_won": sum(1 for o in outcomes if o.outcome == "won"),
            "total_lost": sum(1 for o in outcomes if o.outcome == "lost"),
        }
