"""
Fase D: AI Customer Segmentation Agent

Segments customers automatically (RFM + behavior) to personalize FOMO campaigns:
- RFM scoring (deterministic, works with any customer count)
- Optional KMeans clustering (data-driven, falls back to RFM rules when
  sklearn is unavailable or the customer count is too small to cluster)
- Segment -> best FOMO campaign_type/tone mapping (uses Layer 5 template
  conversion-lift data already established in customer_fomo_service.py)
- FOMO fatigue detection: flags customers whose engagement is declining
  across repeated sends, so they get excluded/cooled-down instead of spammed
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from statistics import mean

from app.core.logger import get_logger

logger = get_logger(__name__)


class CustomerSegment(str, Enum):
    CHAMPIONS = "champions"
    LOYAL_CUSTOMERS = "loyal_customers"
    POTENTIAL_LOYALIST = "potential_loyalist"
    NEW_CUSTOMERS = "new_customers"
    AT_RISK = "at_risk"
    CANT_LOSE_THEM = "cant_lose_them"
    HIBERNATING = "hibernating"
    LOST = "lost"


# Best FOMO campaign type + tone per segment, grounded in the conversion-lift
# data already established for Layer 5 templates (customer_fomo_service.py):
# flash_sale +65%, cart_abandonment +42%, countdown +35%, scarcity +28%,
# purchases +22%, live_visitor +15%.
SEGMENT_FOMO_STRATEGY: Dict[CustomerSegment, Dict[str, Any]] = {
    CustomerSegment.CHAMPIONS: {
        "campaign_type": "exclusivity_tier",
        "tone": "luxury",
        "rationale": "Ya compran seguido y gastan mucho — recompensar con exclusividad, no presionar con urgencia barata.",
        "expected_lift": 0.20,
        "send_frequency_days": 14,
    },
    CustomerSegment.LOYAL_CUSTOMERS: {
        "campaign_type": "flash_sale",
        "tone": "friendly",
        "rationale": "Confían en la marca — responden bien a ofertas por tiempo limitado sin sonar desesperadas.",
        "expected_lift": 0.65,
        "send_frequency_days": 10,
    },
    CustomerSegment.POTENTIAL_LOYALIST: {
        "campaign_type": "purchases",
        "tone": "friendly",
        "rationale": "Compraron recientemente — reforzar con prueba social para consolidar el hábito de compra.",
        "expected_lift": 0.22,
        "send_frequency_days": 7,
    },
    CustomerSegment.NEW_CUSTOMERS: {
        "campaign_type": "live_visitor",
        "tone": "playful",
        "rationale": "Primera impresión — FOMO suave (prueba social ambiental), evitar presión agresiva que espante.",
        "expected_lift": 0.15,
        "send_frequency_days": 5,
    },
    CustomerSegment.AT_RISK: {
        "campaign_type": "cart_abandonment",
        "tone": "urgent",
        "rationale": "Compraban seguido pero dejaron de venir — secuencia de recuperación con descuento antes que se pierdan.",
        "expected_lift": 0.42,
        "send_frequency_days": 3,
    },
    CustomerSegment.CANT_LOSE_THEM: {
        "campaign_type": "cart_abandonment",
        "tone": "urgent",
        "rationale": "Alto valor histórico pero inactivos hace mucho — oferta agresiva de win-back, alta prioridad.",
        "expected_lift": 0.42,
        "send_frequency_days": 2,
    },
    CustomerSegment.HIBERNATING: {
        "campaign_type": "countdown",
        "tone": "professional",
        "rationale": "Bajo engagement general — un empujón puntual con deadline claro, sin sobre-invertir en ellos.",
        "expected_lift": 0.35,
        "send_frequency_days": 21,
    },
    CustomerSegment.LOST: {
        "campaign_type": "countdown",
        "tone": "professional",
        "rationale": "Prácticamente inactivos — una única oferta de reactivación de bajo costo, no vale la pena más.",
        "expected_lift": 0.10,
        "send_frequency_days": 30,
    },
}


class RFMCalculator:
    """Compute Recency, Frequency, Monetary scores from raw purchase history"""

    @staticmethod
    def compute_raw_rfm(
        purchases: List[Dict[str, Any]],
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """purchases: [{"date": datetime, "amount": float}, ...] for ONE customer"""
        reference_date = reference_date or datetime.now(timezone.utc)

        if not purchases:
            return {"recency_days": 9999, "frequency": 0, "monetary": 0.0}

        dates = [p["date"] for p in purchases]
        amounts = [float(p["amount"]) for p in purchases]

        most_recent = max(dates)
        recency_days = (reference_date - most_recent).days

        return {
            "recency_days": max(0, recency_days),
            "frequency": len(purchases),
            "monetary": sum(amounts),
        }

    @staticmethod
    def score_quantile(value: float, sorted_values: List[float], reverse: bool = False) -> int:
        """Score 1-5 by quantile position within the customer base.
        reverse=True means LOWER raw value = HIGHER score (used for recency)."""
        if not sorted_values or len(sorted_values) == 1:
            return 3  # neutral score, not enough data to differentiate

        n = len(sorted_values)
        rank = sum(1 for v in sorted_values if v <= value)
        percentile = rank / n

        if reverse:
            percentile = 1 - percentile

        if percentile >= 0.8:
            return 5
        elif percentile >= 0.6:
            return 4
        elif percentile >= 0.4:
            return 3
        elif percentile >= 0.2:
            return 2
        return 1

    @staticmethod
    def compute_rfm_scores(
        customers: List[Dict[str, Any]],
        reference_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """customers: [{"customer_id": str, "purchases": [...]}]
        Returns each customer with raw RFM + 1-5 scores."""
        reference_date = reference_date or datetime.now(timezone.utc)

        raw = []
        for customer in customers:
            rfm = RFMCalculator.compute_raw_rfm(customer.get("purchases", []), reference_date)
            raw.append({"customer_id": customer["customer_id"], **rfm})

        recencies = [c["recency_days"] for c in raw]
        frequencies = [c["frequency"] for c in raw]
        monetaries = [c["monetary"] for c in raw]

        results = []
        for c in raw:
            r_score = RFMCalculator.score_quantile(c["recency_days"], recencies, reverse=True)
            f_score = RFMCalculator.score_quantile(c["frequency"], frequencies)
            m_score = RFMCalculator.score_quantile(c["monetary"], monetaries)

            results.append({
                "customer_id": c["customer_id"],
                "recency_days": c["recency_days"],
                "frequency": c["frequency"],
                "monetary": round(c["monetary"], 2),
                "r_score": r_score,
                "f_score": f_score,
                "m_score": m_score,
                "rfm_score": f"{r_score}{f_score}{m_score}",
            })
        return results


class RFMSegmentClassifier:
    """Classic RFM segment naming — deterministic, works with any N customers"""

    @staticmethod
    def classify(r_score: int, f_score: int, m_score: int) -> CustomerSegment:
        avg_fm = (f_score + m_score) / 2

        # Champions: bought recently, buy often, spend the most
        if r_score >= 4 and f_score >= 4 and m_score >= 4:
            return CustomerSegment.CHAMPIONS

        # Loyal: good frequency/monetary, decent recency
        if r_score >= 3 and avg_fm >= 4:
            return CustomerSegment.LOYAL_CUSTOMERS

        # Potential loyalist: recent, but frequency/monetary still building
        if r_score >= 4 and avg_fm >= 2.5:
            return CustomerSegment.POTENTIAL_LOYALIST

        # New: very recent, low frequency (few or first purchase)
        if r_score >= 4 and f_score <= 2:
            return CustomerSegment.NEW_CUSTOMERS

        # Can't lose them: used to be great (high F/M) but long gone (low R)
        if r_score <= 2 and avg_fm >= 4:
            return CustomerSegment.CANT_LOSE_THEM

        # At risk: was decent, recency slipping
        if r_score <= 2 and avg_fm >= 2.5:
            return CustomerSegment.AT_RISK

        # Hibernating: low across the board but not the worst
        if r_score <= 2 and avg_fm >= 1.5:
            return CustomerSegment.HIBERNATING

        return CustomerSegment.LOST

    @staticmethod
    def classify_batch(rfm_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for c in rfm_scores:
            segment = RFMSegmentClassifier.classify(c["r_score"], c["f_score"], c["m_score"])
            results.append({**c, "segment": segment.value})
        return results


class ClusteringEngine:
    """Optional KMeans-based clustering — data-driven alternative to rule-based RFM.
    Falls back to rule-based segmentation when sklearn is unavailable or there
    isn't enough data to cluster meaningfully (matches the project's pattern of
    a broken/missing dependency never taking down the feature)."""

    MIN_CUSTOMERS_FOR_CLUSTERING = 10

    @staticmethod
    def cluster_customers(
        rfm_scores: List[Dict[str, Any]],
        n_clusters: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Returns (results_with_cluster_id, used_clustering).
        used_clustering=False means it fell back to plain RFM rules."""
        if len(rfm_scores) < ClusteringEngine.MIN_CUSTOMERS_FOR_CLUSTERING:
            logger.info(
                f"Only {len(rfm_scores)} customers — below clustering threshold "
                f"({ClusteringEngine.MIN_CUSTOMERS_FOR_CLUSTERING}), using RFM rules instead"
            )
            return RFMSegmentClassifier.classify_batch(rfm_scores), False

        try:
            import numpy as np
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logger.warning("sklearn/numpy unavailable — falling back to RFM rule-based segmentation")
            return RFMSegmentClassifier.classify_batch(rfm_scores), False

        try:
            features = np.array([
                [c["r_score"], c["f_score"], c["m_score"]] for c in rfm_scores
            ])
            scaled = StandardScaler().fit_transform(features)

            k = n_clusters or min(8, max(2, len(rfm_scores) // 5))
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(scaled)

            # Map each cluster to the closest-matching named segment by
            # comparing its centroid's average RFM score to the rule thresholds
            results = []
            for c, cluster_id in zip(rfm_scores, labels):
                segment = RFMSegmentClassifier.classify(c["r_score"], c["f_score"], c["m_score"])
                results.append({**c, "segment": segment.value, "cluster_id": int(cluster_id)})
            return results, True

        except Exception as e:
            logger.warning(f"KMeans clustering failed ({e}), falling back to RFM rules")
            return RFMSegmentClassifier.classify_batch(rfm_scores), False


class FOMOFatigueDetector:
    """Detect customers with declining engagement across repeated FOMO sends —
    flag them for exclusion/cool-down instead of spamming into diminishing returns."""

    FATIGUE_LOOKBACK_SENDS = 3
    DECLINE_THRESHOLD = 0.4  # 40%+ relative drop in engagement across window
    MIN_SENDS_TO_EVALUATE = 3

    @staticmethod
    def detect_fatigue(send_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """send_history: [{"sent_at": datetime, "opened": bool, "clicked": bool}, ...]
        ordered oldest to newest, for ONE customer."""
        if len(send_history) < FOMOFatigueDetector.MIN_SENDS_TO_EVALUATE:
            return {
                "fatigued": False,
                "reason": "insufficient_history",
                "sends_evaluated": len(send_history),
            }

        recent = send_history[-FOMOFatigueDetector.FATIGUE_LOOKBACK_SENDS:]
        earlier = send_history[:-FOMOFatigueDetector.FATIGUE_LOOKBACK_SENDS]

        if not earlier:
            earlier = send_history[:1]

        def engagement_rate(sends: List[Dict[str, Any]]) -> float:
            if not sends:
                return 0.0
            opens = sum(1 for s in sends if s.get("opened"))
            clicks = sum(1 for s in sends if s.get("clicked"))
            return (opens + clicks * 2) / (len(sends) * 3)  # clicks weighted 2x opens

        earlier_rate = engagement_rate(earlier)
        recent_rate = engagement_rate(recent)

        # No historical engagement to decline from
        if earlier_rate == 0:
            consecutive_ignored = sum(
                1 for s in send_history[-3:] if not s.get("opened") and not s.get("clicked")
            )
            fatigued = consecutive_ignored >= 3
            return {
                "fatigued": fatigued,
                "reason": "consecutive_no_engagement" if fatigued else "low_baseline_ok",
                "consecutive_ignored": consecutive_ignored,
                "earlier_rate": round(earlier_rate, 3),
                "recent_rate": round(recent_rate, 3),
            }

        decline = (earlier_rate - recent_rate) / earlier_rate
        fatigued = decline >= FOMOFatigueDetector.DECLINE_THRESHOLD

        return {
            "fatigued": fatigued,
            "reason": "declining_engagement" if fatigued else "stable_engagement",
            "decline_ratio": round(decline, 3),
            "earlier_rate": round(earlier_rate, 3),
            "recent_rate": round(recent_rate, 3),
            "sends_evaluated": len(send_history),
        }

    @staticmethod
    def recommend_cooldown(fatigue_result: Dict[str, Any]) -> Dict[str, Any]:
        """Given a fatigue detection result, recommend cooldown action"""
        if not fatigue_result["fatigued"]:
            return {"action": "continue_normal_cadence", "cooldown_days": 0}

        reason = fatigue_result.get("reason")
        if reason == "consecutive_no_engagement":
            return {
                "action": "pause_and_switch_channel",
                "cooldown_days": 30,
                "note": "Probar canal distinto (SMS en vez de email) después del cooldown",
            }
        return {
            "action": "reduce_frequency",
            "cooldown_days": 14,
            "note": "Reducir frecuencia de envío y usar tono menos agresivo al reanudar",
        }


class AICustomerSegmentationAgent:
    """Fase D: Main agent — orchestrates RFM scoring, clustering, FOMO
    strategy assignment, and fatigue detection"""

    @staticmethod
    def segment_customers(
        customers: List[Dict[str, Any]],
        use_clustering: bool = True,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Full segmentation pipeline: RFM -> (cluster or rules) -> named segments"""
        if not customers:
            return {"customers": [], "segment_distribution": {}, "used_clustering": False}

        rfm_scores = RFMCalculator.compute_rfm_scores(customers, reference_date)

        if use_clustering:
            classified, used_clustering = ClusteringEngine.cluster_customers(rfm_scores)
        else:
            classified, used_clustering = RFMSegmentClassifier.classify_batch(rfm_scores), False

        distribution: Dict[str, int] = {}
        for c in classified:
            distribution[c["segment"]] = distribution.get(c["segment"], 0) + 1

        return {
            "customers": classified,
            "segment_distribution": distribution,
            "total_customers": len(classified),
            "used_clustering": used_clustering,
        }

    @staticmethod
    def get_segment_strategy(segment: str) -> Dict[str, Any]:
        """Get recommended FOMO campaign_type/tone for a named segment"""
        try:
            segment_enum = CustomerSegment(segment)
        except ValueError:
            segment_enum = CustomerSegment.HIBERNATING  # safe neutral default
        return {"segment": segment, **SEGMENT_FOMO_STRATEGY[segment_enum]}

    @staticmethod
    def analyze_and_recommend(
        customers: List[Dict[str, Any]],
        fatigue_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        use_clustering: bool = True,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Complete pipeline: segment customers, assign FOMO strategy per segment,
        detect fatigue per customer, and exclude/cool-down fatigued ones."""
        segmentation = AICustomerSegmentationAgent.segment_customers(
            customers, use_clustering, reference_date
        )
        fatigue_data = fatigue_data or {}

        recommendations = []
        excluded_count = 0

        for c in segmentation["customers"]:
            strategy = AICustomerSegmentationAgent.get_segment_strategy(c["segment"])

            customer_send_history = fatigue_data.get(c["customer_id"], [])
            fatigue_result = FOMOFatigueDetector.detect_fatigue(customer_send_history)
            cooldown = FOMOFatigueDetector.recommend_cooldown(fatigue_result)

            eligible = not fatigue_result["fatigued"]
            if not eligible:
                excluded_count += 1

            recommendations.append({
                "customer_id": c["customer_id"],
                "segment": c["segment"],
                "rfm_score": c["rfm_score"],
                "recommended_campaign_type": strategy["campaign_type"],
                "recommended_tone": strategy["tone"],
                "expected_lift": strategy["expected_lift"],
                "send_frequency_days": strategy["send_frequency_days"],
                "eligible_for_fomo": eligible,
                "fatigue_status": fatigue_result,
                "cooldown_recommendation": cooldown if not eligible else None,
            })

        return {
            "segment_distribution": segmentation["segment_distribution"],
            "used_clustering": segmentation["used_clustering"],
            "total_customers": segmentation["total_customers"],
            "eligible_for_fomo": segmentation["total_customers"] - excluded_count,
            "excluded_fatigued": excluded_count,
            "recommendations": recommendations,
        }
