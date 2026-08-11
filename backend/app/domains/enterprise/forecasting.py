from datetime import datetime
from typing import Optional
from dataclasses import asdict
from .deal_scorer import DealScorer, RevenueForecast, DealScore, RiskLevel


class ForecastingManager:
    def __init__(self):
        self.scorer = DealScorer()
        self.forecaster = RevenueForecast()
        self.deal_scores: dict[str, DealScore] = {}
        self.at_risk_deals: list[dict] = []
        self.forecast_history: list[dict] = []

    def analyze_deals(self, user_id: str, deals: list[dict]) -> dict:
        """Analyze all deals for user and return comprehensive report."""
        scores = []
        at_risk = []
        high_probability = []

        for deal in deals:
            deal_id = deal.get("id")
            score = self.scorer.score_deal(
                {
                    "deal_id": deal_id,
                    "user_id": user_id,
                    "stage": deal.get("stage", "discovery"),
                    "days_in_stage": deal.get("days_in_stage", 0),
                    "engagement_velocity": deal.get("engagement_velocity", 0),
                    "proposal_status": deal.get("proposal_status", "not_sent"),
                    "comment_count": deal.get("comment_count", 0),
                    "last_activity_days": deal.get("last_activity_days", 0),
                    "deal_value": deal.get("value", 0),
                    "historical_close_rate": deal.get("close_rate", 0.5),
                }
            )

            self.deal_scores[deal_id] = score
            scores.append(asdict(score))

            if score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                at_risk.append(
                    {
                        "deal_id": deal_id,
                        "deal_name": deal.get("name"),
                        "win_probability": score.win_probability,
                        "risk_level": score.risk_level,
                        "risk_reason": self._get_risk_reason(deal, score),
                        "suggested_action": self._get_suggested_action(deal, score),
                    }
                )
                self.at_risk_deals.append(at_risk[-1])

            if score.win_probability >= 0.7:
                high_probability.append(
                    {
                        "deal_id": deal_id,
                        "deal_name": deal.get("name"),
                        "value": deal.get("value", 0),
                        "win_probability": score.win_probability,
                    }
                )

        return {
            "total_deals": len(deals),
            "high_probability_count": len(high_probability),
            "at_risk_count": len(at_risk),
            "scores": scores,
            "at_risk_deals": at_risk,
            "high_probability_deals": high_probability,
        }

    def forecast_revenue(
        self, user_id: str, deals: list[dict], periods: list[int] = None
    ) -> dict:
        """Generate revenue forecast for multiple periods."""
        if periods is None:
            periods = [30, 60, 90]

        forecasts = {}
        for period in periods:
            forecasts[f"forecast_{period}d"] = self.forecaster.forecast_revenue(
                deals, period
            )

        self.forecast_history.append(
            {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "forecasts": forecasts,
            }
        )

        return {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "forecasts": forecasts,
        }

    def get_at_risk_summary(self) -> dict:
        """Get summary of all at-risk deals."""
        if not self.at_risk_deals:
            return {"total_at_risk": 0, "critical_count": 0, "deals": []}

        critical_count = sum(
            1 for d in self.at_risk_deals if d.get("risk_level") == "critical"
        )

        return {
            "total_at_risk": len(self.at_risk_deals),
            "critical_count": critical_count,
            "total_value_at_risk": sum(
                d.get("value", 0) for d in self.at_risk_deals
            ),
            "deals": self.at_risk_deals,
        }

    def _get_risk_reason(self, deal: dict, score: DealScore) -> str:
        """Determine why deal is at risk."""
        last_activity = deal.get("last_activity_days", 0)
        if last_activity > 30:
            return "No activity for 30+ days"
        if deal.get("proposal_status") == "not_sent":
            return "No proposal sent"
        if deal.get("days_in_stage", 0) > 60:
            return "Stuck in stage for 60+ days"
        if score.win_probability < 0.3:
            return "Low win probability"
        return "Multiple risk factors"

    def _get_suggested_action(self, deal: dict, score: DealScore) -> str:
        """Get suggested action for at-risk deal."""
        proposal_status = deal.get("proposal_status")
        if proposal_status == "not_sent":
            return "Send proposal immediately"
        if proposal_status == "sent":
            return "Follow up on proposal review"
        if deal.get("last_activity_days", 0) > 14:
            return "Schedule check-in call with customer"
        if score.win_probability < 0.3:
            return "Conduct deal review with manager"
        return "Increase engagement frequency"

    def clear_cache(self):
        """Clear in-memory cache."""
        self.deal_scores.clear()
        self.at_risk_deals.clear()


class DealOutcomeAnalyzer:
    """Analyze win/loss patterns and forecast accuracy."""

    def __init__(self):
        self.outcomes: list[dict] = []

    def record_outcome(
        self,
        deal_id: str,
        user_id: str,
        outcome: str,
        final_value: Optional[float],
        days_to_close: int,
        forecasted_probability: float,
        win_loss_reason: Optional[str] = None,
    ) -> dict:
        """Record a deal outcome (won/lost)."""
        accuracy = abs(
            forecasted_probability - (1.0 if outcome == "won" else 0.0)
        )

        record = {
            "deal_id": deal_id,
            "user_id": user_id,
            "outcome": outcome,
            "final_value": final_value,
            "days_to_close": days_to_close,
            "forecasted_probability": forecasted_probability,
            "forecast_accuracy": 1.0 - accuracy,
            "win_loss_reason": win_loss_reason,
            "recorded_at": datetime.utcnow().isoformat(),
        }

        self.outcomes.append(record)
        return record

    def get_accuracy_metrics(self, user_id: str) -> dict:
        """Get forecast accuracy metrics for user."""
        user_outcomes = [o for o in self.outcomes if o.get("user_id") == user_id]

        if not user_outcomes:
            return {
                "total_outcomes": 0,
                "accuracy": 0,
                "won_count": 0,
                "lost_count": 0,
            }

        won_count = sum(1 for o in user_outcomes if o.get("outcome") == "won")
        lost_count = len(user_outcomes) - won_count

        avg_accuracy = (
            sum(o.get("forecast_accuracy", 0) for o in user_outcomes)
            / len(user_outcomes)
        )

        return {
            "total_outcomes": len(user_outcomes),
            "accuracy": avg_accuracy,
            "won_count": won_count,
            "lost_count": lost_count,
            "win_rate": won_count / len(user_outcomes),
            "avg_days_to_close": (
                sum(o.get("days_to_close", 0) for o in user_outcomes)
                / len(user_outcomes)
            ),
        }

    def get_win_loss_summary(self, user_id: str) -> dict:
        """Get summary of why deals were won/lost."""
        user_outcomes = [o for o in self.outcomes if o.get("user_id") == user_id]

        won_reasons = [
            o.get("win_loss_reason")
            for o in user_outcomes
            if o.get("outcome") == "won" and o.get("win_loss_reason")
        ]
        lost_reasons = [
            o.get("win_loss_reason")
            for o in user_outcomes
            if o.get("outcome") == "lost" and o.get("win_loss_reason")
        ]

        return {
            "top_win_reasons": self._get_top_reasons(won_reasons),
            "top_loss_reasons": self._get_top_reasons(lost_reasons),
            "total_won": sum(1 for o in user_outcomes if o.get("outcome") == "won"),
            "total_lost": sum(1 for o in user_outcomes if o.get("outcome") == "lost"),
        }

    def _get_top_reasons(self, reasons: list[str], top_n: int = 5) -> list[dict]:
        """Get most common reasons."""
        if not reasons:
            return []

        reason_counts = {}
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        sorted_reasons = sorted(
            reason_counts.items(), key=lambda x: x[1], reverse=True
        )
        return [{"reason": r, "count": c} for r, c in sorted_reasons[:top_n]]
