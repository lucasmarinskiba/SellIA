"""Dynamic Pricing Engine: ROAS-driven pricing"""

from decimal import Decimal
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class DynamicPricingEngine:
    @staticmethod
    async def calculate_seat_price(
        current_seats: int,
        total_seats: int = 100,
        base_price: Decimal = Decimal("99"),
    ) -> Decimal:
        """Scarcity-based pricing based on occupancy"""
        occupancy = current_seats / total_seats

        if occupancy < 0.2:
            return base_price
        elif occupancy < 0.5:
            return base_price * Decimal("1.2")
        elif occupancy < 0.8:
            return base_price * Decimal("1.5")
        elif occupancy < 0.95:
            return base_price * Decimal("2.0")
        else:
            return base_price * Decimal("3.0")

    @staticmethod
    async def calculate_feature_cost(
        feature_name: str,
        monthly_usage: int,
    ) -> Decimal:
        """Variable pricing for feature add-ons"""
        pricing = {
            "sms_sending": [
                {"max": 100, "cost": Decimal("0")},
                {"max": 500, "cost": Decimal("10")},
                {"max": 2000, "cost": Decimal("30")},
            ],
            "email_sending": [
                {"max": 1000, "cost": Decimal("0")},
                {"max": 5000, "cost": Decimal("15")},
                {"max": 20000, "cost": Decimal("50")},
            ],
            "api_calls": [
                {"max": 10000, "cost": Decimal("0")},
                {"max": 50000, "cost": Decimal("25")},
                {"max": 200000, "cost": Decimal("100")},
            ],
        }

        tiers = pricing.get(feature_name, [])
        for tier in tiers:
            if monthly_usage <= tier["max"]:
                return tier["cost"]

        return tiers[-1]["cost"] if tiers else Decimal("0")

    @staticmethod
    async def optimize_by_roas(
        current_roas: float,
        current_price: Decimal,
        target_roas: float = 3.0,
    ) -> Decimal:
        """Adjust price based on ROAS performance"""
        roas_ratio = current_roas / target_roas

        if roas_ratio < 0.8:
            return current_price * Decimal("0.85")
        elif roas_ratio < 0.9:
            return current_price * Decimal("0.95")
        elif roas_ratio > 1.2:
            return current_price * Decimal("1.15")
        elif roas_ratio > 1.1:
            return current_price * Decimal("1.08")
        else:
            return current_price

    @staticmethod
    def calculate_early_bird_discount(
        base_price: Decimal,
        discount_percent: int = 30,
    ) -> Decimal:
        """Calculate early bird pricing"""
        return base_price * (1 - Decimal(discount_percent) / 100)

    @staticmethod
    def calculate_volume_discount(
        quantity: int,
        unit_price: Decimal,
    ) -> Dict:
        """Calculate bulk discounts"""
        discounts = {
            (1, 10): 0,
            (11, 50): 5,
            (51, 100): 10,
            (101, 500): 15,
            (501, float("inf")): 20,
        }

        discount_pct = 0
        for (min_qty, max_qty), disc in discounts.items():
            if min_qty <= quantity <= max_qty:
                discount_pct = disc
                break

        discounted_price = unit_price * (1 - Decimal(discount_pct) / 100)
        total = discounted_price * quantity

        return {
            "unit_price": float(unit_price),
            "quantity": quantity,
            "discount_percent": discount_pct,
            "discounted_unit_price": float(discounted_price),
            "total": float(total),
        }
