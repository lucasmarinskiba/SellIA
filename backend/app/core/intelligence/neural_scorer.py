"""Neural scoring engine — ML-based lead scoring, pricing, recommendation."""

import logging
from typing import Dict, List, Any
import math

logger = logging.getLogger(__name__)


class NeuralScorer:
    """Neural net (heuristics-based) scoring."""

    @staticmethod
    def score_lead(lead: Dict[str, Any]) -> float:
        """
        Score lead 0-100 based on signals.

        Signals: email domain, source, engagement, firmographic.
        """
        score = 0.0

        # Email domain quality (0-20 points)
        email = lead.get("email", "").lower()
        if email.endswith((".com", ".io", ".co")):
            score += 10
        if "@company.com" in email:
            score += 10

        # Source quality (0-20 points)
        source = lead.get("source", "")
        source_weights = {
            "organic_search": 20,
            "referral": 18,
            "paid_ads": 12,
            "social": 8,
            "direct": 15,
            "cold_email": 5,
        }
        score += source_weights.get(source, 0)

        # Engagement signals (0-30 points)
        page_views = lead.get("page_views", 0)
        time_on_site = lead.get("time_on_site_seconds", 0)
        
        score += min(page_views * 2, 15)  # Max 15 points
        score += min(time_on_site / 60, 15)  # Max 15 points (15 min+ = 15 points)

        # Company size (0-15 points)
        company_size = lead.get("company_size", 0)
        if company_size > 1000:
            score += 15
        elif company_size > 100:
            score += 10
        elif company_size > 10:
            score += 5

        # Industry fit (0-15 points)
        industry = lead.get("industry", "")
        fit_industries = ["saas", "ecommerce", "consulting", "agency"]
        if industry.lower() in fit_industries:
            score += 15

        return min(score, 100)

    @staticmethod
    def calculate_dynamic_price(base_price: float, factors: Dict[str, Any]) -> float:
        """
        Calcula precio dinámico basado en múltiples factores.

        Factors: demand, competition, inventory, urgency.
        """
        price = base_price
        multiplier = 1.0

        # Demand factor (0.8x - 1.3x)
        traffic_last_hour = factors.get("traffic_last_hour", 0)
        conversion_rate = factors.get("conversion_rate", 0.02)
        demand_signal = traffic_last_hour * conversion_rate
        demand_multiplier = 1.0 + (demand_signal / 100)  # +1-3% per 100 signals
        demand_multiplier = min(demand_multiplier, 1.3)
        multiplier *= demand_multiplier

        # Competitor factor (0.95x - 1.05x)
        comp_price = factors.get("competitor_price", base_price)
        our_quality = factors.get("our_quality_score", 5)  # 1-10
        comp_quality = factors.get("competitor_quality", 5)
        if comp_quality > 0:
            quality_ratio = our_quality / comp_quality
            comp_multiplier = 1.0 + ((quality_ratio - 1) * 0.05)  # ±5% based on quality gap
            multiplier *= comp_multiplier

        # Inventory depletion (0.9x - 1.3x)
        stock = factors.get("stock_level", 100)
        inventory_multiplier = 1.0
        if stock < 5:
            inventory_multiplier = 1.3  # +30% scarcity
        elif stock < 20:
            inventory_multiplier = 1.15  # +15%
        multiplier *= inventory_multiplier

        # Time urgency (days to expiry / season end)
        days_left = factors.get("days_to_expiry", 365)
        if days_left < 7:
            urgency_multiplier = 0.9  # -10% discount to move inventory
        elif days_left < 30:
            urgency_multiplier = 0.95
        else:
            urgency_multiplier = 1.0
        multiplier *= urgency_multiplier

        final_price = base_price * multiplier
        return round(final_price, 2)

    @staticmethod
    def score_content_viral_potential(content: Dict[str, Any]) -> float:
        """Score contenido por viral potential 0-100."""
        score = 0.0

        # Emotional hooks (0-30)
        emotions = ["surprise", "anger", "joy", "fear", "sadness"]
        if any(e in content.get("sentiment", "").lower() for e in emotions):
            score += 30

        # Length heuristic (0-20)
        word_count = len(content.get("text", "").split())
        if 100 < word_count < 500:
            score += 20  # Goldilocks zone

        # Has CTA (0-15)
        cta_keywords = ["click", "share", "subscribe", "like", "comment", "join"]
        if any(cta in content.get("text", "").lower() for cta in cta_keywords):
            score += 15

        # Visual elements (0-20)
        if content.get("has_image"):
            score += 10
        if content.get("has_video"):
            score += 10

        # Timing (0-15)
        # Best times: Tue-Thu, 9am-5pm
        day = content.get("day_of_week", "")
        hour = content.get("hour", 0)
        if day in ["Tuesday", "Wednesday", "Thursday"] and 9 <= hour <= 17:
            score += 15

        return min(score, 100)

    @staticmethod
    def rank_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank actions by expected ROI."""
        for action in actions:
            roi_score = 0.0

            # Effort vs impact
            effort = action.get("effort_hours", 1)
            expected_conversion = action.get("expected_conversion_lift", 0)
            roi_score = (expected_conversion / effort) * 100

            action["roi_score"] = roi_score

        return sorted(actions, key=lambda a: a["roi_score"], reverse=True)
