"""
Advanced Sales Intelligence Engine — ML scoring, predictive models, adaptive strategies.

Predicts: conversion, churn, LTV, optimal pricing, best channel, timing.
"""

import logging
from typing import Dict, List, Any
import math

logger = logging.getLogger(__name__)


class PredictiveLeadScoring:
    """ML-based lead scoring (predicts conversion before contact)."""

    FEATURE_WEIGHTS = {
        "company_size": 0.15,  # Larger = higher conversion
        "industry_fit": 0.20,  # Perfect fit = highest
        "job_title": 0.10,  # Decision-makers convert more
        "website_engagement": 0.20,  # Pages visited, time on site
        "pricing_page_views": 0.15,  # Viewed pricing = buying signal
        "competitor_mention": 0.10,  # Researching alternatives
        "email_engagement": 0.10,  # Opens, clicks = intent
    }

    @staticmethod
    def score_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula lead score 0-100 (predicts conversion).

        Integra múltiples signals → modelo predictivo.
        """

        score = 0.0

        # Company size (0-15 points)
        company_size = lead.get("company_size", 0)
        if company_size > 1000:
            score += 15
        elif company_size > 100:
            score += 10
        elif company_size > 10:
            score += 5

        # Industry fit (0-20 points)
        product_category = lead.get("product_category", "")
        lead_industry = lead.get("industry", "")
        if product_category == lead_industry or lead_industry in ["tech", "saas"]:
            score += 20

        # Job title (0-10 points)
        title = lead.get("title", "").lower()
        if any(keyword in title for keyword in ["ceo", "cto", "vp", "director", "manager"]):
            score += 10

        # Website engagement (0-20 points)
        page_views = lead.get("page_views", 0)
        time_on_site = lead.get("time_on_site_seconds", 0)
        score += min(page_views * 2, 10)  # Max 10 points
        score += min(time_on_site / 60, 10)  # Max 10 points (10min = 10 points)

        # Pricing page views (0-15 points)
        if lead.get("viewed_pricing_page"):
            score += 15

        # Competitor mention (0-10 points)
        if lead.get("researching_competitors"):
            score += 10

        # Email engagement (0-10 points)
        email_open_rate = lead.get("email_open_rate", 0)
        email_click_rate = lead.get("email_click_rate", 0)
        score += min(email_open_rate * 5, 5)
        score += min(email_click_rate * 5, 5)

        # Determine segment
        if score > 80:
            segment = "HOT"
        elif score > 60:
            segment = "WARM"
        elif score > 40:
            segment = "COOL"
        else:
            segment = "COLD"

        return {
            "lead_id": lead.get("id"),
            "score": min(score, 100),
            "segment": segment,
            "prediction": {
                "conversion_probability": score / 100,
                "expected_deal_size": 5000 if score > 70 else 2500,
                "sales_cycle_days": 7 if score > 80 else (15 if score > 60 else 30),
            },
        }


class ChurnPredictionModel:
    """Predice churn 30-60 días en avance."""

    @staticmethod
    def predict_churn(customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predice probabilidad churn (0-1).

        Señales: usage decline, support issues, engagement down, payment delays.
        """

        churn_risk = 0.0

        # Usage decline (weight: 0.3)
        usage_trend = customer.get("usage_trend", 0)  # -1 to +1
        if usage_trend < -0.5:
            churn_risk += 0.3
        elif usage_trend < 0:
            churn_risk += 0.15

        # Support tickets (weight: 0.2)
        support_tickets_30d = customer.get("support_tickets_30d", 0)
        if support_tickets_30d > 5:
            churn_risk += 0.2
        elif support_tickets_30d > 2:
            churn_risk += 0.1

        # Email engagement (weight: 0.2)
        email_open_rate = customer.get("email_open_rate", 0)
        if email_open_rate < 0.1:
            churn_risk += 0.2
        elif email_open_rate < 0.3:
            churn_risk += 0.1

        # Payment delays (weight: 0.15)
        if customer.get("payment_overdue"):
            churn_risk += 0.15

        # NPS (weight: 0.15)
        nps = customer.get("nps_score", 0)
        if nps < 30:
            churn_risk += 0.15
        elif nps < 50:
            churn_risk += 0.08

        # Determine action
        if churn_risk > 0.7:
            action = "immediate_intervention"
            intervention = "executive call + special offer + concession"
        elif churn_risk > 0.5:
            action = "win_back_campaign"
            intervention = "email series + discount + re-engagement content"
        elif churn_risk > 0.3:
            action = "engagement_boost"
            intervention = "educational content + tips + success stories"
        else:
            action = "maintain_relationship"
            intervention = "regular updates + exclusive access"

        return {
            "customer_id": customer.get("id"),
            "churn_probability": min(churn_risk, 1.0),
            "risk_level": "HIGH" if churn_risk > 0.7 else ("MEDIUM" if churn_risk > 0.5 else "LOW"),
            "recommended_action": action,
            "intervention": intervention,
            "expected_recovery_rate": 0.3 if churn_risk > 0.7 else (0.6 if churn_risk > 0.5 else 0.8),
        }


class OptimalChannelSelector:
    """Selecciona mejor canal por buyer profile + historical performance."""

    CHANNEL_PERFORMANCE = {
        "email": {"conversion_rate": 0.03, "cost_per_click": 0.05, "volume": "high"},
        "phone": {"conversion_rate": 0.15, "cost_per_click": 5.0, "volume": "low"},
        "whatsapp": {"conversion_rate": 0.08, "cost_per_click": 0.10, "volume": "high"},
        "linkedin": {"conversion_rate": 0.05, "cost_per_click": 0.50, "volume": "medium"},
        "ads": {"conversion_rate": 0.02, "cost_per_click": 1.0, "volume": "high"},
        "sms": {"conversion_rate": 0.06, "cost_per_click": 0.02, "volume": "high"},
    }

    @staticmethod
    def select_best_channel(
        buyer: Dict[str, Any],
        budget: float,
        target_conversions: int,
    ) -> Dict[str, Any]:
        """
        Selecciona canal optimal por ROI.

        budget = presupuesto total
        target_conversions = cuántas conversiones necesitamos
        """

        best_channel = None
        best_roi = 0

        for channel, perf in OptimalChannelSelector.CHANNEL_PERFORMANCE.items():
            # Estimar cost para target conversions
            conv_rate = perf["conversion_rate"]
            cost_per_click = perf["cost_per_click"]

            clicks_needed = target_conversions / conv_rate
            total_cost = clicks_needed * cost_per_click

            if total_cost <= budget:
                # ROI = conversions / cost
                roi = target_conversions / total_cost if total_cost > 0 else 0

                if roi > best_roi:
                    best_roi = roi
                    best_channel = channel

        return {
            "recommended_channel": best_channel or "email",  # Default
            "expected_roi": best_roi,
            "estimated_cost": (target_conversions / OptimalChannelSelector.CHANNEL_PERFORMANCE[best_channel or "email"]["conversion_rate"]) * OptimalChannelSelector.CHANNEL_PERFORMANCE[best_channel or "email"]["cost_per_click"],
            "alternative_channels": sorted(
                [(ch, (p["conversion_rate"])) for ch, p in OptimalChannelSelector.CHANNEL_PERFORMANCE.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:3],
        }


class AdaptiveSalesStrategy:
    """Adapta estrategia basada en histórico de éxito/fallo."""

    @staticmethod
    def recommend_approach(
        buyer: Dict[str, Any],
        product: Dict[str, Any],
        historical_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Recomienda approach (price, guarantee, channel, offer) basado en aprendizaje.

        Si similar buyer + similar product = qué funcionó antes?
        """

        similar_past_deals = historical_data.get("similar_deals", [])

        if not similar_past_deals:
            return {"approach": "standard", "recommendation": "Use default strategy"}

        # Analiza qué funcionó
        winning_approaches = [d for d in similar_past_deals if d.get("won")]
        winning_rate = len(winning_approaches) / len(similar_past_deals)

        if winning_rate == 0:
            return {"approach": "pivot", "recommendation": "Try different approach, past ones failed"}

        # Extract pattern
        avg_closing_price = sum(d.get("closed_price", 0) for d in winning_approaches) / len(winning_approaches) if winning_approaches else 0
        most_used_guarantee = max(
            set(d.get("guarantee_type") for d in winning_approaches),
            key=lambda x: sum(1 for d in winning_approaches if d.get("guarantee_type") == x),
            default="money_back",
        )
        best_channel = max(
            set(d.get("channel") for d in winning_approaches),
            key=lambda x: sum(1 for d in winning_approaches if d.get("channel") == x),
            default="email",
        )

        return {
            "win_rate": f"{winning_rate*100:.0f}%",
            "recommended_price": avg_closing_price,
            "recommended_guarantee": most_used_guarantee,
            "recommended_channel": best_channel,
            "confidence": "high" if len(winning_approaches) > 5 else "medium",
        }
