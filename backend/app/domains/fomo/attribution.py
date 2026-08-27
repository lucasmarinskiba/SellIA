"""Multi-touch Attribution Engine - Track FOMO impact"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Tuple
from uuid import UUID


class AttributionEngine:
    @staticmethod
    def first_touch(touchpoints: List[Dict], conversion_value: Decimal) -> Dict:
        """First touchpoint gets 100% credit"""
        if not touchpoints:
            return {}

        first = touchpoints[0]
        channel = first.get("channel", "web")

        return {
            "email": conversion_value if channel == "email" else Decimal("0"),
            "sms": conversion_value if channel == "sms" else Decimal("0"),
            "web": conversion_value if channel == "web" else Decimal("0"),
        }

    @staticmethod
    def last_touch(touchpoints: List[Dict], conversion_value: Decimal) -> Dict:
        """Last touchpoint gets 100% credit"""
        if not touchpoints:
            return {}

        last = touchpoints[-1]
        channel = last.get("channel", "web")

        return {
            "email": conversion_value if channel == "email" else Decimal("0"),
            "sms": conversion_value if channel == "sms" else Decimal("0"),
            "web": conversion_value if channel == "web" else Decimal("0"),
        }

    @staticmethod
    def linear(touchpoints: List[Dict], conversion_value: Decimal) -> Dict:
        """Equal credit to all touchpoints"""
        n = len(touchpoints)
        if n == 0:
            return {}

        share = conversion_value / n

        attribution = {
            "email": Decimal("0"),
            "sms": Decimal("0"),
            "web": Decimal("0"),
        }

        for tp in touchpoints:
            channel = tp.get("channel", "web")
            attribution[channel] += share

        return attribution

    @staticmethod
    def time_decay(touchpoints: List[Dict], conversion_value: Decimal) -> Dict:
        """Later touchpoints get more credit (exponential)"""
        n = len(touchpoints)
        if n == 0:
            return {}

        # Weights: 1, 2, 3, ..., n (exponential decay)
        weights = [1 + i for i in range(n)]
        total_weight = sum(weights)

        attribution = {
            "email": Decimal("0"),
            "sms": Decimal("0"),
            "web": Decimal("0"),
        }

        for idx, tp in enumerate(touchpoints):
            channel = tp.get("channel", "web")
            share = (Decimal(weights[idx]) / Decimal(total_weight)) * conversion_value
            attribution[channel] += share

        return attribution

    @staticmethod
    def custom_rule_based(touchpoints: List[Dict], conversion_value: Decimal) -> Dict:
        """Custom rules: Email 10%, SMS 30%, Web 60%"""
        attribution = {
            "email": conversion_value * Decimal("0.1"),
            "sms": conversion_value * Decimal("0.3"),
            "web": conversion_value * Decimal("0.6"),
        }

        return attribution

    @staticmethod
    async def calculate_channel_roi(
        channel: str,
        total_attributed_revenue: Decimal,
        channel_spend: Decimal,
    ) -> Dict:
        """Calculate ROI by channel"""
        if channel_spend <= 0:
            roi = Decimal("0")
        else:
            roi = (total_attributed_revenue - channel_spend) / channel_spend

        return {
            "channel": channel,
            "total_attributed_revenue": float(total_attributed_revenue),
            "spend": float(channel_spend),
            "roi": float(roi),
            "roi_multiple": f"{roi:.1f}x" if roi > 0 else "N/A",
        }

    @staticmethod
    async def get_channel_contribution(
        attributions: List[Dict],
    ) -> Dict:
        """Summary of each channel's contribution"""
        total = {}
        count = {}

        for attr in attributions:
            for channel in ["email", "sms", "web"]:
                total[channel] = total.get(channel, Decimal("0")) + attr.get(channel, Decimal("0"))
                count[channel] = count.get(channel, 0) + 1

        grand_total = sum(total.values())

        contribution = {}
        for channel in ["email", "sms", "web"]:
            channel_total = total.get(channel, Decimal("0"))
            pct = (channel_total / grand_total * 100) if grand_total > 0 else 0
            contribution[channel] = {
                "total_revenue": float(channel_total),
                "contribution_percent": float(pct),
                "attribution_count": count.get(channel, 0),
                "avg_per_attribution": float(channel_total / count.get(channel, 1)) if count.get(channel, 0) > 0 else 0,
            }

        return contribution
