from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DealScoreFactors:
    stage: str
    days_in_stage: int
    engagement_velocity: float
    proposal_status: str
    comment_count: int
    last_activity_days: int
    deal_value: float
    historical_close_rate: float


@dataclass
class DealScore:
    deal_id: str
    user_id: str
    win_probability: float
    confidence_level: float
    risk_level: RiskLevel
    engagement_velocity: float
    ai_score_factors: dict
    timestamp: datetime


class DealScorer:
    STAGE_WEIGHTS = {
        "discovery": 0.1,
        "qualified": 0.2,
        "proposal": 0.4,
        "negotiation": 0.6,
        "closed": 1.0,
    }

    ENGAGEMENT_MULTIPLIER = 1.5
    ACTIVITY_DECAY_DAYS = 14
    CRITICAL_THRESHOLD_DAYS = 30

    def score_deal(self, factors: DealScoreFactors) -> DealScore:
        """Calculate win probability and risk level for a deal."""
        stage_score = self.STAGE_WEIGHTS.get(factors.stage, 0.1)
        engagement_score = self._calculate_engagement_score(factors)
        activity_score = self._calculate_activity_score(factors.last_activity_days)
        proposal_score = self._calculate_proposal_score(factors.proposal_status)

        win_probability = self._blend_scores(
            stage_score,
            engagement_score,
            activity_score,
            proposal_score,
            factors.historical_close_rate,
        )

        confidence_level = self._calculate_confidence(factors)
        risk_level = self._assess_risk(factors, win_probability)

        return DealScore(
            deal_id=factors.deal_id if hasattr(factors, "deal_id") else "unknown",
            user_id=factors.user_id if hasattr(factors, "user_id") else "unknown",
            win_probability=max(0, min(1, win_probability)),
            confidence_level=max(0, min(1, confidence_level)),
            risk_level=risk_level,
            engagement_velocity=engagement_score,
            ai_score_factors={
                "stage_score": stage_score,
                "engagement_score": engagement_score,
                "activity_score": activity_score,
                "proposal_score": proposal_score,
                "historical_close_rate": factors.historical_close_rate,
            },
            timestamp=datetime.utcnow(),
        )

    def _calculate_engagement_score(self, factors: DealScoreFactors) -> float:
        """Score based on engagement velocity and comment activity."""
        comment_score = min(1.0, factors.comment_count / 10)
        velocity = min(1.0, factors.engagement_velocity)
        return (comment_score * 0.4 + velocity * 0.6) * self.ENGAGEMENT_MULTIPLIER

    def _calculate_activity_score(self, last_activity_days: int) -> float:
        """Score based on recency of activity."""
        if last_activity_days == 0:
            return 1.0
        if last_activity_days > self.CRITICAL_THRESHOLD_DAYS:
            return 0.1
        decay = 1.0 - (last_activity_days / self.ACTIVITY_DECAY_DAYS)
        return max(0.1, decay)

    def _calculate_proposal_score(self, proposal_status: str) -> float:
        """Score based on proposal status."""
        status_scores = {
            "not_sent": 0.0,
            "sent": 0.5,
            "reviewed": 0.7,
            "accepted": 0.9,
            "contract_signed": 1.0,
        }
        return status_scores.get(proposal_status, 0.0)

    def _blend_scores(
        self,
        stage: float,
        engagement: float,
        activity: float,
        proposal: float,
        historical: float,
    ) -> float:
        """Blend component scores into final win probability."""
        weights = {
            "stage": 0.25,
            "engagement": 0.3,
            "activity": 0.15,
            "proposal": 0.2,
            "historical": 0.1,
        }

        return (
            stage * weights["stage"]
            + engagement * weights["engagement"]
            + activity * weights["activity"]
            + proposal * weights["proposal"]
            + historical * weights["historical"]
        )

    def _calculate_confidence(self, factors: DealScoreFactors) -> float:
        """Calculate confidence in the score prediction."""
        data_points = [
            factors.comment_count > 0,
            factors.proposal_status != "not_sent",
            factors.days_in_stage < 60,
            factors.last_activity_days < 7,
        ]
        data_confidence = sum(data_points) / len(data_points)

        stage_confidence = {
            "discovery": 0.3,
            "qualified": 0.5,
            "proposal": 0.7,
            "negotiation": 0.85,
            "closed": 1.0,
        }.get(factors.stage, 0.3)

        return (data_confidence * 0.6 + stage_confidence * 0.4) * 0.9

    def _assess_risk(self, factors: DealScoreFactors, win_probability: float) -> RiskLevel:
        """Assess risk level based on multiple factors."""
        if factors.last_activity_days > self.CRITICAL_THRESHOLD_DAYS:
            return RiskLevel.CRITICAL

        risk_score = 0
        if factors.last_activity_days > 14:
            risk_score += 2
        if factors.proposal_status == "not_sent":
            risk_score += 2
        if factors.days_in_stage > 45:
            risk_score += 1
        if win_probability < 0.3:
            risk_score += 2

        if risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


class RevenueForecast:
    def __init__(self):
        self.scorer = DealScorer()

    def forecast_revenue(
        self, deals: list[dict], days_ahead: int = 30
    ) -> dict:
        """Forecast revenue based on deal scores."""
        if not deals:
            return {
                "total_pipeline": 0,
                "projected": 0,
                "confidence": 0,
                "deal_breakdown": [],
            }

        deal_forecasts = []
        total_pipeline = 0
        weighted_revenue = 0
        total_confidence = 0

        for deal in deals:
            total_pipeline += deal.get("value", 0)

            factors = DealScoreFactors(
                stage=deal.get("stage", "discovery"),
                days_in_stage=deal.get("days_in_stage", 0),
                engagement_velocity=deal.get("engagement_velocity", 0),
                proposal_status=deal.get("proposal_status", "not_sent"),
                comment_count=deal.get("comment_count", 0),
                last_activity_days=deal.get("last_activity_days", 0),
                deal_value=deal.get("value", 0),
                historical_close_rate=deal.get("close_rate", 0.5),
            )

            score = self.scorer.score_deal(factors)
            prob_in_period = self._calculate_close_probability(
                score, deal.get("days_in_stage", 0), days_ahead
            )

            deal_value = deal.get("value", 0)
            expected_value = deal_value * prob_in_period

            deal_forecasts.append(
                {
                    "deal_id": deal.get("id"),
                    "name": deal.get("name"),
                    "value": deal_value,
                    "win_probability": score.win_probability,
                    "expected_value": expected_value,
                    "days_ahead": days_ahead,
                    "risk_level": score.risk_level,
                }
            )

            weighted_revenue += expected_value
            total_confidence += score.confidence_level

        avg_confidence = total_confidence / len(deals) if deals else 0

        return {
            "total_pipeline": total_pipeline,
            "projected": weighted_revenue,
            "confidence": avg_confidence,
            "days_ahead": days_ahead,
            "deal_breakdown": deal_forecasts,
        }

    def _calculate_close_probability(
        self, score: DealScore, days_in_stage: int, days_ahead: int
    ) -> float:
        """Estimate probability of closing within days_ahead."""
        stage_close_times = {
            "discovery": 45,
            "qualified": 30,
            "proposal": 20,
            "negotiation": 10,
            "closed": 0,
        }

        days_to_close = stage_close_times.get("proposal", 30)
        if days_in_stage > days_to_close:
            return max(0.5, score.win_probability * 0.7)

        days_remaining = days_to_close - days_in_stage
        if days_remaining <= 0:
            return score.win_probability
        if days_remaining > days_ahead:
            return score.win_probability * 0.3

        return score.win_probability * (1.0 - (days_remaining / days_ahead) * 0.4)
