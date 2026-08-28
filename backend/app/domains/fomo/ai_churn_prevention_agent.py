"""
Fase G: AI Predictive Churn-to-FOMO Agent

Predicts churn risk per customer and auto-triggers a win-back FOMO sequence
when risk crosses a threshold, with the offer sized to the customer's
historical value:
- ChurnRiskScorer: heuristic risk score from purchase-interval deviation +
  engagement decline (reuses RFMCalculator/FOMOFatigueDetector from Fase D
  rather than re-deriving RFM/engagement math); optional logistic-regression
  path when labeled historical churn outcomes are available, falling back to
  the heuristic on missing sklearn, too few labeled samples, or a failed fit
- WinBackTriggerEngine: threshold-gated decision to fire the win-back sequence
- PersonalizedOfferCalibrator: sizes the win-back discount to the customer's
  monetary value relative to the batch — don't over-invest retaining a
  low-value customer, don't under-invest losing a high-value one
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from statistics import mean, median

from app.core.logger import get_logger
from app.domains.fomo.ai_segmentation_agent import RFMCalculator, FOMOFatigueDetector

logger = get_logger(__name__)


class ChurnRiskTier:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChurnRiskScorer:
    """Score churn risk 0.0-1.0 per customer"""

    MIN_LABELED_SAMPLES_FOR_ML = 20

    @staticmethod
    def compute_purchase_interval_stats(purchases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Average days between consecutive purchases — the customer's own
        'normal' buying rhythm, used to judge whether their current silence
        is actually unusual for THEM specifically."""
        if len(purchases) < 2:
            return {"avg_interval_days": None, "has_data": False}

        dates = sorted(p["date"] for p in purchases)
        intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        intervals = [i for i in intervals if i >= 0]

        if not intervals:
            return {"avg_interval_days": None, "has_data": False}

        return {
            "avg_interval_days": round(mean(intervals), 1),
            "median_interval_days": round(median(intervals), 1),
            "has_data": True,
        }

    @staticmethod
    def heuristic_risk_score(
        purchases: List[Dict[str, Any]],
        send_history: Optional[List[Dict[str, Any]]] = None,
        reference_date: Optional[datetime] = None,
        population_avg_interval_days: float = 30.0,
    ) -> Dict[str, Any]:
        """Blend recency-vs-own-rhythm deviation with engagement decline into
        a single risk score. No labeled churn outcomes required."""
        reference_date = reference_date or datetime.now(timezone.utc)
        rfm = RFMCalculator.compute_raw_rfm(purchases, reference_date)
        interval_stats = ChurnRiskScorer.compute_purchase_interval_stats(purchases)

        if rfm["frequency"] == 0:
            # Never purchased — not a churn case, it's an acquisition case
            return {
                "risk_score": 0.0,
                "tier": ChurnRiskTier.LOW,
                "reason": "no_purchase_history",
                "recency_days": rfm["recency_days"],
            }

        expected_interval = interval_stats["avg_interval_days"] or population_avg_interval_days
        recency_ratio = rfm["recency_days"] / expected_interval if expected_interval > 0 else 1.0

        # Sigmoid-shaped mapping: ratio of 1.0 (right on schedule) -> low risk,
        # ratio of 3.0+ (3x their normal gap) -> high risk
        recency_risk = min(1.0, max(0.0, (recency_ratio - 1.0) / 3.0))

        engagement_risk = 0.0
        if send_history:
            fatigue = FOMOFatigueDetector.detect_fatigue(send_history)
            if fatigue["reason"] == "declining_engagement":
                engagement_risk = min(1.0, fatigue.get("decline_ratio", 0.0))
            elif fatigue["reason"] == "consecutive_no_engagement":
                engagement_risk = 0.8

        # Recency deviation is the primary signal; engagement decline
        # corroborates/adjusts it rather than dominating (weighted blend)
        risk_score = (recency_risk * 0.7) + (engagement_risk * 0.3)
        risk_score = round(min(1.0, max(0.0, risk_score)), 4)

        return {
            "risk_score": risk_score,
            "tier": ChurnRiskScorer._tier_from_score(risk_score),
            "recency_days": rfm["recency_days"],
            "expected_interval_days": expected_interval,
            "recency_ratio": round(recency_ratio, 2),
            "engagement_risk": round(engagement_risk, 3),
            "method": "heuristic",
        }

    @staticmethod
    def _tier_from_score(score: float) -> str:
        if score >= 0.75:
            return ChurnRiskTier.CRITICAL
        if score >= 0.5:
            return ChurnRiskTier.HIGH
        if score >= 0.25:
            return ChurnRiskTier.MEDIUM
        return ChurnRiskTier.LOW

    @staticmethod
    def fit_ml_model(labeled_customers: List[Dict[str, Any]]):
        """labeled_customers: [{"features": {...}, "churned": bool}, ...]
        Returns a fitted sklearn LogisticRegression + feature order, or None
        if sklearn is unavailable or there isn't enough labeled data."""
        if len(labeled_customers) < ChurnRiskScorer.MIN_LABELED_SAMPLES_FOR_ML:
            return None

        try:
            from sklearn.linear_model import LogisticRegression
            import numpy as np
        except ImportError:
            logger.warning("sklearn/numpy unavailable — churn scoring stays heuristic-only")
            return None

        feature_keys = ["recency_days", "frequency", "monetary", "recency_ratio"]

        try:
            X = np.array([[c["features"].get(k, 0.0) for k in feature_keys] for c in labeled_customers])
            y = np.array([1 if c["churned"] else 0 for c in labeled_customers])

            if len(set(y.tolist())) < 2:
                logger.warning("Labeled churn data has only one class — can't fit logistic regression")
                return None

            model = LogisticRegression(max_iter=1000)
            model.fit(X, y)
            return {"model": model, "feature_keys": feature_keys}
        except Exception as e:
            logger.warning(f"Churn model fit failed ({e}), falling back to heuristic")
            return None

    @staticmethod
    def ml_risk_score(fitted: Dict[str, Any], features: Dict[str, float]) -> float:
        try:
            import numpy as np
            X = np.array([[features.get(k, 0.0) for k in fitted["feature_keys"]]])
            proba = fitted["model"].predict_proba(X)[0]
            # predict_proba columns follow model.classes_ order (sklearn sorts
            # classes ascending, so for binary {0,1} labels index 1 is churn=1)
            churn_class_index = list(fitted["model"].classes_).index(1)
            return float(proba[churn_class_index])
        except Exception as e:
            logger.warning(f"ML risk scoring failed ({e}), returning neutral score")
            return 0.5


class PersonalizedOfferCalibrator:
    """Size the win-back offer to the customer's value relative to the batch —
    retention spend should scale with what's actually at stake."""

    OFFER_TIERS = [
        {"min_percentile": 0.8, "discount_percent": 30, "label": "high_value"},
        {"min_percentile": 0.5, "discount_percent": 20, "label": "mid_value"},
        {"min_percentile": 0.2, "discount_percent": 15, "label": "standard_value"},
        {"min_percentile": 0.0, "discount_percent": 10, "label": "low_value"},
    ]

    @staticmethod
    def calibrate_offer(monetary_value: float, batch_monetary_values: List[float]) -> Dict[str, Any]:
        if not batch_monetary_values or len(batch_monetary_values) < 2:
            # Not enough of a batch to rank against — use the standard tier
            tier = PersonalizedOfferCalibrator.OFFER_TIERS[2]
            return {
                "discount_percent": tier["discount_percent"],
                "tier": tier["label"],
                "percentile": None,
                "reason": "insufficient_batch_context",
            }

        sorted_values = sorted(batch_monetary_values)
        n = len(sorted_values)
        rank = sum(1 for v in sorted_values if v <= monetary_value)
        percentile = rank / n

        for tier in PersonalizedOfferCalibrator.OFFER_TIERS:
            if percentile >= tier["min_percentile"]:
                return {
                    "discount_percent": tier["discount_percent"],
                    "tier": tier["label"],
                    "percentile": round(percentile, 3),
                }

        # unreachable given OFFER_TIERS' last entry has min_percentile 0.0,
        # kept only as a defensive fallback
        return {"discount_percent": 10, "tier": "low_value", "percentile": round(percentile, 3)}


class WinBackTriggerEngine:
    """Threshold-gated decision to fire the win-back FOMO sequence"""

    DEFAULT_THRESHOLD = 0.5

    @staticmethod
    def should_trigger(risk_result: Dict[str, Any], threshold: float = DEFAULT_THRESHOLD) -> bool:
        return risk_result["risk_score"] >= threshold

    @staticmethod
    def build_win_back_sequence(offer: Dict[str, Any], risk_tier: str) -> Dict[str, Any]:
        """Sequence intensity scales with risk tier — critical risk gets a
        faster, more direct sequence than medium risk."""
        if risk_tier == ChurnRiskTier.CRITICAL:
            steps = [
                {"step": 1, "delay_minutes": 0, "channel": "email", "template": "win_back_urgent"},
                {"step": 2, "delay_minutes": 1440, "channel": "sms", "template": "win_back_offer_reminder"},
                {"step": 3, "delay_minutes": 4320, "channel": "email", "template": "win_back_final"},
            ]
        else:
            steps = [
                {"step": 1, "delay_minutes": 0, "channel": "email", "template": "win_back_offer"},
                {"step": 2, "delay_minutes": 4320, "channel": "email", "template": "win_back_reminder"},
            ]

        return {
            "sequence": steps,
            "offer_discount_percent": offer["discount_percent"],
            "offer_tier": offer["tier"],
            "risk_tier": risk_tier,
        }


class AIChurnPreventionAgent:
    """Fase G: Main agent — score risk, decide trigger, personalize offer"""

    @staticmethod
    def score_customer(
        purchases: List[Dict[str, Any]],
        send_history: Optional[List[Dict[str, Any]]] = None,
        reference_date: Optional[datetime] = None,
        fitted_model: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Score one customer's churn risk — ML if a fitted model is supplied
        and heuristic features can be computed, heuristic-only otherwise."""
        heuristic = ChurnRiskScorer.heuristic_risk_score(purchases, send_history, reference_date)

        if fitted_model is not None and heuristic.get("recency_ratio") is not None:
            rfm = RFMCalculator.compute_raw_rfm(purchases, reference_date or datetime.now(timezone.utc))
            features = {
                "recency_days": rfm["recency_days"],
                "frequency": rfm["frequency"],
                "monetary": rfm["monetary"],
                "recency_ratio": heuristic["recency_ratio"],
            }
            ml_score = ChurnRiskScorer.ml_risk_score(fitted_model, features)
            return {
                **heuristic,
                "risk_score": round(ml_score, 4),
                "tier": ChurnRiskScorer._tier_from_score(ml_score),
                "method": "ml",
                "heuristic_risk_score": heuristic["risk_score"],
            }

        return heuristic

    @staticmethod
    def evaluate_and_trigger(
        customer_id: str,
        purchases: List[Dict[str, Any]],
        batch_monetary_values: List[float],
        send_history: Optional[List[Dict[str, Any]]] = None,
        threshold: float = WinBackTriggerEngine.DEFAULT_THRESHOLD,
        reference_date: Optional[datetime] = None,
        fitted_model: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Full pipeline for one customer: score -> trigger decision ->
        personalized win-back sequence if triggered"""
        risk = AIChurnPreventionAgent.score_customer(purchases, send_history, reference_date, fitted_model)
        triggered = WinBackTriggerEngine.should_trigger(risk, threshold)

        result = {
            "customer_id": customer_id,
            "risk_score": risk["risk_score"],
            "risk_tier": risk["tier"],
            "triggered": triggered,
            "win_back_sequence": None,
        }

        if triggered:
            monetary_value = sum(float(p.get("amount", 0)) for p in purchases)
            offer = PersonalizedOfferCalibrator.calibrate_offer(monetary_value, batch_monetary_values)
            result["win_back_sequence"] = WinBackTriggerEngine.build_win_back_sequence(offer, risk["tier"])
            result["customer_monetary_value"] = round(monetary_value, 2)

        return result

    @staticmethod
    def batch_evaluate(
        customers: List[Dict[str, Any]],
        threshold: float = WinBackTriggerEngine.DEFAULT_THRESHOLD,
        fatigue_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        reference_date: Optional[datetime] = None,
        labeled_training_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """customers: [{"customer_id": str, "purchases": [...]}]
        Runs the full pipeline across a batch, sharing the batch's monetary
        distribution for offer calibration and an optional fitted ML model."""
        fatigue_data = fatigue_data or {}

        batch_monetary_values = [
            sum(float(p.get("amount", 0)) for p in c.get("purchases", []))
            for c in customers
        ]

        fitted_model = None
        if labeled_training_data:
            fitted_model = ChurnRiskScorer.fit_ml_model(labeled_training_data)

        results = []
        triggered_count = 0
        for customer in customers:
            result = AIChurnPreventionAgent.evaluate_and_trigger(
                customer_id=customer["customer_id"],
                purchases=customer.get("purchases", []),
                batch_monetary_values=batch_monetary_values,
                send_history=fatigue_data.get(customer["customer_id"]),
                threshold=threshold,
                reference_date=reference_date,
                fitted_model=fitted_model,
            )
            results.append(result)
            if result["triggered"]:
                triggered_count += 1

        return {
            "total_customers": len(customers),
            "triggered_win_back": triggered_count,
            "used_ml_model": fitted_model is not None,
            "results": results,
        }
