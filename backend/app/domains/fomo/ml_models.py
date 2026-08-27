"""ML Models: Conversion, churn, LTV prediction"""

import numpy as np
from typing import Dict, Tuple, List
from datetime import datetime


class FOOMMLModels:
    def __init__(self):
        self.conversion_model = None
        self.churn_model = None
        self.ltv_model = None

    async def predict_conversion(self, user_history: Dict, campaign_type: str) -> float:
        """Predict: 0.0-1.0 probability user converts"""
        features = self._extract_conversion_features(user_history, campaign_type)
        if not features:
            return 0.5

        # Mock prediction (would be trained model)
        score = (
            features[0] / 1000 * 0.3 +  # AOV impact
            (1 - features[2]) * 0.2 +  # Cart abandon rate
            features[5] * 0.2 +  # Has purchased
            features[10] * 0.3  # Campaign type effectiveness
        )
        return min(1.0, max(0.0, score))

    async def predict_churn(self, user_metrics: Dict) -> float:
        """Predict: 0.0-1.0 churn risk score"""
        features = self._extract_churn_features(user_metrics)
        if not features:
            return 0.2

        # High inactivity + low adoption = high churn
        inactivity_score = min(features[0] / 30, 1.0)  # Days inactive
        adoption_score = 1 - features[3]  # Feature adoption

        churn_score = (inactivity_score * 0.5 + adoption_score * 0.5)
        return min(1.0, max(0.0, churn_score))

    async def predict_ltv(self, user_history: Dict) -> float:
        """Predict: Lifetime value in USD for 12 months"""
        features = self._extract_ltv_features(user_history)
        if not features:
            return 100.0

        # Simple model: monthly revenue * months active * growth factor
        monthly_revenue = features[0]
        months_active = features[1]
        growth_rate = 1 + (features[2] / 100)  # Convert % to factor

        ltv = monthly_revenue * 12 * growth_rate
        return max(0, ltv)

    def _extract_conversion_features(self, user_history: Dict, campaign_type: str) -> list:
        """15 features for conversion prediction"""
        return [
            user_history.get("avg_order_value", 50),
            max(0, 30 - user_history.get("days_since_last_visit", 99)),
            user_history.get("cart_abandonment_rate", 0.3),
            1 if user_history.get("last_device", "").lower() == "mobile" else 0,
            datetime.now().hour / 24,
            1 if user_history.get("has_purchased", False) else 0,
            user_history.get("avg_session_duration", 180) / 600,
            len(user_history.get("purchases", [])),
            user_history.get("days_since_signup", 999) / 365,
            user_history.get("email_open_rate", 0.25),
            {"scarcity": 1, "countdown": 0.8, "social_proof": 0.9, "exclusivity": 0.7}.get(campaign_type, 0.5),
            user_history.get("sms_click_rate", 0.1),
            user_history.get("support_tickets", 0) / 10,
            {"free": 0, "pro": 1, "enterprise": 2}.get(user_history.get("plan", "free"), 0) / 2,
            user_history.get("referral_source_quality", 0.5),
        ]

    def _extract_churn_features(self, user_metrics: Dict) -> list:
        """12 features for churn prediction"""
        return [
            user_metrics.get("days_inactive", 14),
            user_metrics.get("revenue_trend", 0),
            user_metrics.get("support_tickets", 0),
            user_metrics.get("feature_adoption", 0.5),
            max(0, (datetime.now() - user_metrics.get("created_at", datetime.now())).days),
            user_metrics.get("conversions_last_30d", 5),
            {"free": 0, "pro": 1, "enterprise": 2}.get(user_metrics.get("plan", "free"), 0) / 2,
            user_metrics.get("login_frequency_7d", 3),
            user_metrics.get("feature_usage_score", 0.6),
            (user_metrics.get("nps_score", 0) + 100) / 200,
            user_metrics.get("payment_failures", 0),
            user_metrics.get("months_active", 6),
        ]

    def _extract_ltv_features(self, user_history: Dict) -> list:
        """10 features for LTV prediction"""
        return [
            user_history.get("avg_monthly_revenue", 500),
            user_history.get("months_active", 6),
            user_history.get("revenue_growth_rate", 5),
            {"free": 0, "pro": 1, "enterprise": 2}.get(user_history.get("plan", "free"), 0) / 2,
            len(user_history.get("products", [])) / 100,
            user_history.get("support_ticket_ratio", 0.1),
            user_history.get("email_engagement", 0.4),
            0.2,  # Placeholder for churn probability
            user_history.get("referral_count", 0),
            user_history.get("feature_upgrade_count", 0),
        ]

    async def segment_by_fomo_sensitivity(self, users_data: List[Dict]) -> Dict:
        """Segment users into 4 FOMO sensitivity tiers"""
        segments = {"high": [], "medium": [], "low": [], "unresponsive": []}

        for user in users_data:
            conversion_prob = await self.predict_conversion(user.get("history", {}), "scarcity")
            churn_prob = await self.predict_churn(user.get("metrics", {}))

            fomo_score = conversion_prob * (1 - churn_prob)

            if fomo_score > 0.6:
                segments["high"].append(user["id"])
            elif foom_score > 0.4:
                segments["medium"].append(user["id"])
            elif fomo_score > 0.2:
                segments["low"].append(user["id"])
            else:
                segments["unresponsive"].append(user["id"])

        return segments
