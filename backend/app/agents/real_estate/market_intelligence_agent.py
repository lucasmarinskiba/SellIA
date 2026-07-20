"""Market Intelligence Agent — Local market knowledge, trends, competitors."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MarketReport:
    """Comprehensive market analysis report."""

    market_area: str
    report_date: datetime
    median_price: float
    average_price_per_sqft: float
    active_listings: int
    sold_last_30_days: int
    average_days_on_market: int
    price_trend: str  # uptrend, stable, downtrend
    price_momentum: float  # YoY % change
    market_temperature: str  # hot, warm, cool, cold
    buyer_demand_level: str  # high, moderate, low
    supply_demand_ratio: float
    recommended_pricing_strategy: str
    top_selling_features: List[str] = field(default_factory=list)
    market_headwinds: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)


class MarketIntelligenceAgent:
    """Provide market insights and competitive analysis."""

    def __init__(self):
        self.market_reports: Dict[str, MarketReport] = {}
        self.competitor_tracking: Dict[str, List[Dict[str, Any]]] = {}

    def generate_market_report(self, location: str, market_data: Dict[str, Any]) -> MarketReport:
        """Generate comprehensive market analysis report."""
        # Extract key metrics
        median_price = market_data.get("median_price", 300000)
        avg_price_sqft = market_data.get("avg_price_per_sqft", 250)
        active_listings = market_data.get("active_listings", 100)
        sold_30_days = market_data.get("sold_last_30_days", 20)
        avg_dom = market_data.get("avg_days_on_market", 30)
        price_momentum = market_data.get("yoy_price_change", 0)

        # Determine market conditions
        market_temperature = self._determine_market_temperature(active_listings, sold_30_days, avg_dom)
        price_trend = self._determine_price_trend(price_momentum)
        buyer_demand = self._assess_buyer_demand(sold_30_days, active_listings)
        supply_demand = self._calculate_supply_demand_ratio(active_listings, sold_30_days)

        # Get market insights
        top_features = self._identify_top_selling_features(market_data)
        headwinds = self._identify_market_headwinds(market_data)
        opportunities = self._identify_opportunities(market_data)
        pricing_strategy = self._recommend_pricing_strategy(market_temperature, price_trend)

        report = MarketReport(
            market_area=location,
            report_date=datetime.utcnow(),
            median_price=median_price,
            average_price_per_sqft=avg_price_sqft,
            active_listings=active_listings,
            sold_last_30_days=sold_30_days,
            average_days_on_market=avg_dom,
            price_trend=price_trend,
            price_momentum=price_momentum,
            market_temperature=market_temperature,
            buyer_demand_level=buyer_demand,
            supply_demand_ratio=supply_demand,
            recommended_pricing_strategy=pricing_strategy,
            top_selling_features=top_features,
            market_headwinds=headwinds,
            opportunities=opportunities,
        )

        self.market_reports[location] = report
        logger.info(f"Generated market report for {location}: {market_temperature} market")

        return report

    def _determine_market_temperature(self, active_listings: int, sold_30_days: int, avg_dom: int) -> str:
        """Determine market temperature (hot/warm/cool/cold)."""
        if sold_30_days > 25 and avg_dom < 15 and active_listings < 80:
            return "hot"
        elif sold_30_days > 15 and avg_dom < 30 and active_listings < 120:
            return "warm"
        elif sold_30_days > 10 and avg_dom < 45:
            return "cool"
        else:
            return "cold"

    def _determine_price_trend(self, yoy_change: float) -> str:
        """Determine price trend from YoY change."""
        if yoy_change > 5:
            return "uptrend"
        elif yoy_change > -2:
            return "stable"
        else:
            return "downtrend"

    def _assess_buyer_demand(self, sold_30_days: int, active_listings: int) -> str:
        """Assess buyer demand level."""
        if sold_30_days > 25:
            return "high"
        elif sold_30_days > 15:
            return "moderate"
        else:
            return "low"

    def _calculate_supply_demand_ratio(self, active_listings: int, sold_30_days: int) -> float:
        """Calculate months of supply (inventory/sales rate)."""
        if sold_30_days == 0:
            return 999.0
        monthly_sales_rate = sold_30_days / 1
        return active_listings / monthly_sales_rate

    def _identify_top_selling_features(self, market_data: Dict[str, Any]) -> List[str]:
        """Identify top-selling property features in market."""
        features = []
        if market_data.get("high_demand_features"):
            features.extend(market_data["high_demand_features"][:3])
        else:
            features = [
                "Updated kitchen",
                "Large backyard",
                "Recently renovated",
                "Master suite",
                "Open floor plan",
            ]
        return features

    def _identify_market_headwinds(self, market_data: Dict[str, Any]) -> List[str]:
        """Identify market challenges/headwinds."""
        headwinds = []
        if market_data.get("high_inventory"):
            headwinds.append("High inventory - buyer's market")
        if market_data.get("rising_interest_rates"):
            headwinds.append("Rising interest rates reducing affordability")
        if market_data.get("economic_concerns"):
            headwinds.append("Economic uncertainty impacting demand")
        return headwinds

    def _identify_opportunities(self, market_data: Dict[str, Any]) -> List[str]:
        """Identify market opportunities."""
        opportunities = []
        if market_data.get("low_inventory"):
            opportunities.append("Low inventory - strong seller's market")
        if market_data.get("population_growth"):
            opportunities.append("Growing population increasing demand")
        if market_data.get("development_planned"):
            opportunities.append("Planned development increasing area value")
        return opportunities

    def _recommend_pricing_strategy(self, market_temp: str, price_trend: str) -> str:
        """Recommend pricing strategy based on market conditions."""
        if market_temp in ["hot", "warm"] and price_trend == "uptrend":
            return "aggressive - strong market supports premium pricing"
        elif market_temp == "cool" and price_trend == "stable":
            return "balanced - competitive pricing at market rate"
        elif market_temp in ["cool", "cold"] and price_trend == "downtrend":
            return "conservative - competitive pricing needed"
        else:
            return "balanced"

    def analyze_neighborhood(self, address: str, neighborhood_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze neighborhood characteristics."""
        return {
            "address": address,
            "walkability_score": neighborhood_data.get("walkability_score", 50),
            "schools_nearby": neighborhood_data.get("schools_count", 0),
            "crime_rate": neighborhood_data.get("crime_rate", "moderate"),
            "median_income": neighborhood_data.get("median_income", 60000),
            "population_trend": neighborhood_data.get("population_trend", "stable"),
            "amenities": neighborhood_data.get("amenities", []),
            "desirability_score": self._calculate_desirability(neighborhood_data),
        }

    def _calculate_desirability(self, neighborhood_data: Dict[str, Any]) -> float:
        """Calculate neighborhood desirability (0-100)."""
        score = 50.0
        if neighborhood_data.get("walkability_score", 0) > 70:
            score += 15
        if neighborhood_data.get("schools_count", 0) > 3:
            score += 15
        if neighborhood_data.get("crime_rate") == "low":
            score += 20
        if neighborhood_data.get("population_trend") == "growing":
            score += 10
        return min(score, 100.0)

    def track_competitor(self, competitor_id: str, property_data: Dict[str, Any]) -> None:
        """Track competitor property listings."""
        if competitor_id not in self.competitor_tracking:
            self.competitor_tracking[competitor_id] = []

        self.competitor_tracking[competitor_id].append({
            "timestamp": datetime.utcnow(),
            "property_data": property_data,
        })

    def analyze_competition(self, market_area: str, property_type: str) -> Dict[str, Any]:
        """Analyze competitive landscape."""
        return {
            "market_area": market_area,
            "property_type": property_type,
            "competitive_analysis": {
                "estimated_competitors": 10,
                "average_list_price": 350000,
                "price_range": [250000, 450000],
                "average_list_to_sold_ratio": 0.97,
            },
            "market_positioning": "You are positioned at median price point",
        }

    def get_market_report(self, location: str) -> Optional[MarketReport]:
        """Retrieve market report for location."""
        return self.market_reports.get(location)
