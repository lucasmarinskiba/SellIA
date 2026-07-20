"""Property Analyzer Agent — Valuation, comps, investment potential."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PropertyAnalysis:
    """Comprehensive property analysis."""

    property_id: str
    estimated_value: float
    value_confidence: float  # 0-1
    price_per_sqft: float
    estimated_annual_rent: Optional[float] = None
    cap_rate: Optional[float] = None  # For investment
    cash_on_cash_return: Optional[float] = None
    appreciation_potential: str = "moderate"
    investment_score: float = 0.0
    condition_assessment: str = "average"
    major_repairs_needed: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Comparable:
    """Market comparable property."""

    comp_id: str
    address: str
    sale_price: float
    sale_date: datetime
    size_sqft: float
    bedrooms: int
    bathrooms: int
    price_per_sqft: float
    age_of_comp_months: int
    similarity_score: float  # 0-100


class PropertyAnalyzerAgent:
    """Analyze properties for valuation and investment potential."""

    def __init__(self):
        self.comparables_database: List[Comparable] = []
        self.analysis_history: Dict[str, PropertyAnalysis] = {}

    def analyze_property(self, property_data: Dict[str, Any], comps: Optional[List[Comparable]] = None) -> PropertyAnalysis:
        """Perform comprehensive property analysis."""
        property_id = property_data.get("property_id", "unknown")

        # Valuation
        estimated_value = self._estimate_value(property_data, comps or [])
        value_confidence = self._calculate_confidence(property_data, comps or [])

        # Price metrics
        size_sqft = property_data.get("size_sqft", 0)
        price_per_sqft = estimated_value / size_sqft if size_sqft > 0 else 0

        # Investment analysis (if applicable)
        annual_rent = property_data.get("estimated_annual_rent")
        cap_rate = None
        cash_on_cash = None
        if annual_rent:
            cap_rate = (annual_rent / estimated_value) * 100 if estimated_value > 0 else 0
            down_payment = property_data.get("down_payment_amount", estimated_value * 0.2)
            cash_on_cash = (annual_rent / down_payment) * 100 if down_payment > 0 else 0

        # Condition assessment
        condition = self._assess_condition(property_data)

        # Repairs needed
        repairs = self._identify_needed_repairs(property_data)

        # Appreciation potential
        appreciation = self._estimate_appreciation_potential(property_data, comps or [])

        # Investment score
        investment_score = self._calculate_investment_score(
            property_data, estimated_value, cap_rate, condition
        )

        # Recommendations
        recommendations = self._generate_recommendations(property_data, estimated_value, condition, repairs)

        analysis = PropertyAnalysis(
            property_id=property_id,
            estimated_value=estimated_value,
            value_confidence=value_confidence,
            price_per_sqft=price_per_sqft,
            estimated_annual_rent=annual_rent,
            cap_rate=cap_rate,
            cash_on_cash_return=cash_on_cash,
            appreciation_potential=appreciation,
            investment_score=investment_score,
            condition_assessment=condition,
            major_repairs_needed=repairs,
            recommendations=recommendations,
        )

        self.analysis_history[property_id] = analysis
        logger.info(f"Analyzed property {property_id}: ${estimated_value:,.0f} (confidence: {value_confidence:.0%})")

        return analysis

    def _estimate_value(self, property_data: Dict[str, Any], comps: List[Comparable]) -> float:
        """Estimate property value using comparable sales."""
        if not comps:
            # Fallback: use asking price or estimate from sqft
            asking_price = property_data.get("asking_price", 0)
            if asking_price > 0:
                return asking_price
            return property_data.get("size_sqft", 0) * 150  # $150/sqft baseline

        # Sort comps by similarity
        sorted_comps = sorted(comps, key=lambda c: c.similarity_score, reverse=True)
        top_comps = sorted_comps[:3]  # Use top 3 most similar

        if not top_comps:
            return property_data.get("asking_price", 0)

        # Calculate weighted average price per sqft
        total_weight = sum(c.similarity_score for c in top_comps)
        weighted_price_per_sqft = sum(
            (c.price_per_sqft * c.similarity_score) for c in top_comps
        ) / total_weight

        # Adjust for time (appreciation/depreciation)
        months_since_sale = [(datetime.utcnow() - c.sale_date).days // 30 for c in top_comps]
        avg_months = statistics.mean(months_since_sale)

        # Assume 3% annual appreciation
        appreciation_factor = 1.0 + (0.03 * (avg_months / 12))

        size_sqft = property_data.get("size_sqft", 0)
        estimated_value = weighted_price_per_sqft * size_sqft * appreciation_factor

        return estimated_value

    def _calculate_confidence(self, property_data: Dict[str, Any], comps: List[Comparable]) -> float:
        """Calculate confidence level of valuation (0-1)."""
        confidence = 0.5

        # More comps = higher confidence
        if len(comps) >= 5:
            confidence += 0.25
        elif len(comps) >= 3:
            confidence += 0.15
        elif len(comps) >= 1:
            confidence += 0.05

        # Recent sales = higher confidence
        recent_comps = [c for c in comps if (datetime.utcnow() - c.sale_date).days <= 90]
        if len(recent_comps) >= 3:
            confidence += 0.15
        elif len(recent_comps) >= 1:
            confidence += 0.05

        # Property in good condition = higher confidence
        if property_data.get("condition", "").lower() in ["excellent", "good"]:
            confidence += 0.05

        return min(confidence, 1.0)

    def _assess_condition(self, property_data: Dict[str, Any]) -> str:
        """Assess overall property condition."""
        reported_condition = property_data.get("condition", "average").lower()

        if reported_condition in ["excellent", "like new"]:
            return "excellent"
        elif reported_condition in ["good", "well maintained"]:
            return "good"
        elif reported_condition == "fair":
            return "fair"
        else:
            return "poor"

    def _identify_needed_repairs(self, property_data: Dict[str, Any]) -> List[str]:
        """Identify major repairs from property data."""
        repairs = []
        year_built = property_data.get("year_built", 0)
        current_year = datetime.utcnow().year
        property_age = current_year - year_built

        # Age-based assessment
        if property_age > 50:
            repairs.append("Roof inspection recommended (age related)")
            repairs.append("Foundation inspection recommended")

        if property_age > 30:
            repairs.append("Electrical system upgrade may be needed")
            repairs.append("Plumbing inspection recommended")

        # Reported issues
        reported_issues = property_data.get("reported_issues", [])
        repairs.extend(reported_issues)

        # Condition-based
        if property_data.get("condition", "").lower() in ["poor", "fair"]:
            repairs.append("Comprehensive inspection highly recommended")

        return repairs

    def _estimate_appreciation_potential(self, property_data: Dict[str, Any], comps: List[Comparable]) -> str:
        """Estimate future appreciation potential."""
        # Check market trend
        if comps:
            recent_comps = [c for c in comps if (datetime.utcnow() - c.sale_date).days <= 180]
            old_comps = [c for c in comps if (datetime.utcnow() - c.sale_date).days > 180]

            if recent_comps and old_comps:
                recent_price = statistics.mean([c.price_per_sqft for c in recent_comps])
                old_price = statistics.mean([c.price_per_sqft for c in old_comps])

                price_change = (recent_price - old_price) / old_price if old_price > 0 else 0

                if price_change > 0.05:
                    return "high"
                elif price_change > 0.02:
                    return "moderate"
                elif price_change > -0.02:
                    return "stable"
                else:
                    return "declining"

        # Default based on location quality
        location_score = property_data.get("location_score", 0)
        if location_score > 80:
            return "high"
        elif location_score > 60:
            return "moderate"
        else:
            return "low"

    def _calculate_investment_score(
        self, property_data: Dict[str, Any], value: float, cap_rate: Optional[float], condition: str
    ) -> float:
        """Calculate investment score (0-100)."""
        score = 50.0

        # Cap rate (if applicable)
        if cap_rate:
            if cap_rate > 8:
                score += 25
            elif cap_rate > 6:
                score += 15
            elif cap_rate > 4:
                score += 5
            else:
                score -= 10

        # Condition
        if condition == "excellent":
            score += 15
        elif condition == "good":
            score += 10
        elif condition == "poor":
            score -= 20

        # Location
        location_score = property_data.get("location_score", 50)
        score += (location_score - 50) * 0.2

        return min(max(score, 0.0), 100.0)

    def _generate_recommendations(
        self, property_data: Dict[str, Any], value: float, condition: str, repairs: List[str]
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        asking_price = property_data.get("asking_price", 0)

        # Price recommendation
        if asking_price > value * 1.1:
            recommendations.append(f"Price appears high - consider offer around ${value * 0.95:,.0f}")
        elif asking_price < value * 0.9:
            recommendations.append(f"Price looks favorable - good value at asking price")

        # Condition-based
        if condition in ["fair", "poor"]:
            recommendations.append("Consider professional inspection before purchase")
            recommendations.append("Budget for repairs/updates")

        # Market timing
        days_on_market = property_data.get("days_on_market", 0)
        if days_on_market > 90:
            recommendations.append("Property on market >90 days - negotiate aggressively")
        elif days_on_market < 7:
            recommendations.append("Hot property - be prepared for multiple offers")

        # Investment-specific
        if property_data.get("is_investment_property"):
            if property_data.get("estimated_annual_rent", 0) > 0:
                recommendations.append("Strong rental potential - consider as investment")

        return recommendations

    def compare_properties(self, property_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple properties."""
        analyses = [self.analysis_history.get(pid) for pid in property_ids if pid in self.analysis_history]

        if not analyses:
            return {"error": "No analyses found"}

        return {
            "properties": [
                {
                    "property_id": a.property_id,
                    "estimated_value": a.estimated_value,
                    "price_per_sqft": a.price_per_sqft,
                    "cap_rate": a.cap_rate,
                    "investment_score": a.investment_score,
                }
                for a in analyses
            ],
            "best_value": min(analyses, key=lambda a: a.price_per_sqft).property_id,
            "best_investment": max(analyses, key=lambda a: a.investment_score).property_id if any(
                a.investment_score for a in analyses
            ) else None,
        }
