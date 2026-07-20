"""Pricing Agent — Dynamic pricing based on ML + market conditions."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PricingRecommendation:
    """Pricing recommendation with strategy."""

    property_id: str
    asking_price: float
    recommended_price: float
    confidence: float
    strategy: str  # aggressive, balanced, conservative
    market_conditions: Dict[str, Any]
    factors: Dict[str, float]  # Individual factor impacts
    reasoning: List[str]


class PricingAgent:
    """Dynamic pricing using ML predictions + market analysis."""

    def __init__(self, ml_engine: Optional[Any] = None):
        self.ml_engine = ml_engine
        self.recommendations: Dict[str, PricingRecommendation] = {}

    def calculate_pricing_recommendation(
        self, property_data: Dict[str, Any], market_data: Dict[str, Any], strategy: str = "balanced"
    ) -> PricingRecommendation:
        """Calculate optimal price for property."""
        property_id = property_data.get("property_id", "unknown")
        asking_price = property_data.get("asking_price", 0)

        # Get base valuation
        base_price = self._calculate_base_valuation(property_data, market_data)

        # Calculate adjustments
        factors = self._calculate_price_factors(property_data, market_data)

        # Apply strategy multiplier
        strategy_multiplier = self._get_strategy_multiplier(strategy)

        # Calculate recommended price
        recommended_price = base_price * strategy_multiplier

        # Calculate confidence
        confidence = self._calculate_price_confidence(property_data, market_data)

        # Generate reasoning
        reasoning = self._generate_pricing_reasoning(property_data, market_data, strategy, factors)

        recommendation = PricingRecommendation(
            property_id=property_id,
            asking_price=asking_price,
            recommended_price=recommended_price,
            confidence=confidence,
            strategy=strategy,
            market_conditions=self._summarize_market_conditions(market_data),
            factors=factors,
            reasoning=reasoning,
        )

        self.recommendations[property_id] = recommendation
        logger.info(f"Pricing recommendation for {property_id}: ${recommended_price:,.0f} ({strategy})")

        return recommendation

    def _calculate_base_valuation(self, property_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Calculate base property valuation."""
        # Start with comparable sales data
        comparable_prices = market_data.get("comparable_prices", [])

        if comparable_prices:
            import statistics

            # Use median of comps for stability
            base_price = statistics.median(comparable_prices)
        else:
            # Fallback to asking price or estimate
            base_price = property_data.get("asking_price", 0)
            if base_price == 0:
                base_price = property_data.get("size_sqft", 0) * 150

        return base_price

    def _calculate_price_factors(self, property_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate impact of individual factors on price."""
        factors = {}

        # Property condition factor
        condition = property_data.get("condition", "average").lower()
        condition_factors = {"excellent": 1.10, "good": 1.05, "average": 1.0, "fair": 0.95, "poor": 0.85}
        factors["condition"] = condition_factors.get(condition, 1.0)

        # Market trend factor
        market_trend = market_data.get("market_trend", "stable")
        trend_factors = {"uptrend": 1.08, "stable": 1.0, "downtrend": 0.92}
        factors["market_trend"] = trend_factors.get(market_trend, 1.0)

        # Inventory factor (supply/demand)
        active_listings = market_data.get("active_listings_count", 100)
        avg_listings = market_data.get("average_listings", 100)
        if active_listings < avg_listings * 0.5:
            factors["inventory_scarcity"] = 1.12  # Seller's market
        elif active_listings > avg_listings * 1.5:
            factors["inventory_scarcity"] = 0.90  # Buyer's market
        else:
            factors["inventory_scarcity"] = 1.0

        # Days on market factor
        days_on_market = property_data.get("days_on_market", 0)
        if days_on_market > 180:
            factors["days_on_market"] = 0.92
        elif days_on_market > 90:
            factors["days_on_market"] = 0.96
        elif days_on_market < 7:
            factors["days_on_market"] = 1.05
        else:
            factors["days_on_market"] = 1.0

        # Location desirability
        location_score = property_data.get("location_score", 50)
        factors["location"] = 1.0 + (location_score - 50) / 500

        # Age/modernization
        year_built = property_data.get("year_built", 0)
        current_year = datetime.utcnow().year
        property_age = current_year - year_built

        if property_age < 5:
            factors["age"] = 1.10
        elif property_age < 15:
            factors["age"] = 1.05
        elif property_age < 30:
            factors["age"] = 1.0
        elif property_age < 50:
            factors["age"] = 0.95
        else:
            factors["age"] = 0.85

        # Financing appeal
        if property_data.get("can_mortgage"):
            factors["mortgage_appeal"] = 1.05
        else:
            factors["mortgage_appeal"] = 0.90

        return factors

    def _get_strategy_multiplier(self, strategy: str) -> float:
        """Get price multiplier based on strategy."""
        multipliers = {
            "aggressive": 1.08,  # Ask high, expect negotiations
            "balanced": 1.0,  # At market rate
            "conservative": 0.95,  # Undercut to sell quick
        }
        return multipliers.get(strategy, 1.0)

    def _calculate_price_confidence(self, property_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Calculate confidence level of pricing recommendation."""
        confidence = 0.5

        # More comparables = higher confidence
        comparable_count = len(market_data.get("comparable_prices", []))
        if comparable_count >= 10:
            confidence += 0.3
        elif comparable_count >= 5:
            confidence += 0.2
        elif comparable_count >= 2:
            confidence += 0.1

        # Recent market data = higher confidence
        if market_data.get("data_freshness_days", 999) <= 30:
            confidence += 0.1
        elif market_data.get("data_freshness_days", 999) <= 90:
            confidence += 0.05

        # Standard property characteristics = higher confidence
        if not property_data.get("unique_features"):
            confidence += 0.05

        return min(confidence, 1.0)

    def _summarize_market_conditions(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize key market conditions."""
        return {
            "trend": market_data.get("market_trend", "unknown"),
            "avg_time_to_sale_days": market_data.get("avg_time_to_sale_days", 0),
            "inventory_level": market_data.get("inventory_level", "unknown"),
            "buyer_activity": market_data.get("buyer_activity_level", "moderate"),
            "price_momentum": market_data.get("price_momentum", 0),
        }

    def _generate_pricing_reasoning(
        self, property_data: Dict[str, Any], market_data: Dict[str, Any], strategy: str, factors: Dict[str, float]
    ) -> List[str]:
        """Generate reasoning for pricing recommendation."""
        reasoning = []

        # Market conditions
        trend = market_data.get("market_trend", "stable")
        if trend == "uptrend":
            reasoning.append("Strong market conditions allow premium pricing")
        elif trend == "downtrend":
            reasoning.append("Soft market requires competitive pricing")

        # Inventory
        active_listings = market_data.get("active_listings_count", 100)
        avg_listings = market_data.get("average_listings", 100)
        if active_listings < avg_listings * 0.5:
            reasoning.append("Low inventory supports higher pricing")
        elif active_listings > avg_listings * 1.5:
            reasoning.append("High inventory requires aggressive pricing")

        # Days on market
        days_on_market = property_data.get("days_on_market", 0)
        if days_on_market > 90:
            reasoning.append(f"Property on market {days_on_market} days - consider price reduction")
        elif days_on_market < 7:
            reasoning.append("Strong buyer interest - can maintain or increase price")

        # Condition
        condition = property_data.get("condition", "average")
        if condition == "excellent":
            reasoning.append("Excellent condition supports premium pricing")
        elif condition == "poor":
            reasoning.append("Repairs needed - price reflects as-is condition")

        # Strategy
        if strategy == "aggressive":
            reasoning.append("Aggressive strategy: List high, expect negotiations to market rate")
        elif strategy == "conservative":
            reasoning.append("Conservative strategy: Undercut market to attract quick sale")

        return reasoning

    def suggest_negotiation_targets(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Suggest negotiation targets based on pricing."""
        if property_id not in self.recommendations:
            return None

        rec = self.recommendations[property_id]

        return {
            "property_id": property_id,
            "asking_price": rec.asking_price,
            "recommended_price": rec.recommended_price,
            "negotiation_targets": {
                "first_offer_target": rec.recommended_price * 0.92,
                "walk_away_price": rec.recommended_price * 0.85,
                "accept_price": rec.recommended_price * 0.97,
                "best_price": rec.recommended_price,
            },
            "rationale": {
                "first_offer_target": "Open negotiations ~8% below market",
                "walk_away_price": "Absolute minimum - don't go below this",
                "accept_price": "Acceptable compromise close to market rate",
                "best_price": "Optimal price based on market analysis",
            },
        }

    def compare_pricing_strategies(self, property_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare all three pricing strategies."""
        strategies = {}

        for strategy in ["aggressive", "balanced", "conservative"]:
            rec = self.calculate_pricing_recommendation(property_data, market_data, strategy)
            strategies[strategy] = {
                "recommended_price": rec.recommended_price,
                "time_to_sale_days": self._estimate_time_to_sale(rec.recommended_price, market_data),
                "expected_negotiations": self._estimate_negotiation_rounds(strategy),
                "probability_of_sale": self._estimate_sale_probability(strategy),
            }

        return strategies

    def _estimate_time_to_sale(self, price: float, market_data: Dict[str, Any]) -> float:
        """Estimate time to sale based on price."""
        avg_time = market_data.get("avg_time_to_sale_days", 30)
        market_price = market_data.get("average_listing_price", 300000)

        # Underpriced = faster sale
        if price < market_price * 0.95:
            return avg_time * 0.7
        elif price < market_price:
            return avg_time * 0.85
        elif price < market_price * 1.05:
            return avg_time
        else:
            return avg_time * 1.5

    def _estimate_negotiation_rounds(self, strategy: str) -> int:
        """Estimate negotiation rounds."""
        return {"aggressive": 3, "balanced": 2, "conservative": 1}.get(strategy, 2)

    def _estimate_sale_probability(self, strategy: str) -> float:
        """Estimate probability of sale."""
        return {"aggressive": 0.70, "balanced": 0.85, "conservative": 0.95}.get(strategy, 0.80)
