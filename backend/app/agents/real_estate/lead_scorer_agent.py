"""Lead Scorer Agent — 6-factor buyer profile evaluation."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
import json

logger = logging.getLogger(__name__)


@dataclass
class LeadScoreBreakdown:
    """Detailed lead scoring breakdown."""

    budget_score: float
    motivation_score: float
    timeline_score: float
    credit_score_metric: float
    location_preference_score: float
    property_type_alignment: float
    overall_score: float
    recommendation: str


class LeadScorerAgent:
    """Score buyer profiles on 6 critical factors."""

    SCORE_WEIGHTS = {
        "budget": 0.25,
        "motivation": 0.20,
        "timeline": 0.20,
        "credit": 0.15,
        "location": 0.10,
        "property_type": 0.10,
    }

    def __init__(self):
        self.scores_history: Dict[str, Any] = {}

    def score_lead(self, lead_data: Dict[str, Any]) -> LeadScoreBreakdown:
        """Evaluate buyer profile on 6 factors."""

        budget_score = self._evaluate_budget(lead_data)
        motivation_score = self._evaluate_motivation(lead_data)
        timeline_score = self._evaluate_timeline(lead_data)
        credit_score_metric = self._evaluate_credit(lead_data)
        location_score = self._evaluate_location_preference(lead_data)
        property_type_score = self._evaluate_property_type_alignment(lead_data)

        overall_score = (
            budget_score * self.SCORE_WEIGHTS["budget"]
            + motivation_score * self.SCORE_WEIGHTS["motivation"]
            + timeline_score * self.SCORE_WEIGHTS["timeline"]
            + credit_score_metric * self.SCORE_WEIGHTS["credit"]
            + location_score * self.SCORE_WEIGHTS["location"]
            + property_type_score * self.SCORE_WEIGHTS["property_type"]
        )

        recommendation = self._generate_recommendation(overall_score, lead_data)

        breakdown = LeadScoreBreakdown(
            budget_score=budget_score,
            motivation_score=motivation_score,
            timeline_score=timeline_score,
            credit_score_metric=credit_score_metric,
            location_preference_score=location_score,
            property_type_alignment=property_type_score,
            overall_score=overall_score,
            recommendation=recommendation,
        )

        # Store in history
        lead_id = lead_data.get("lead_id", "unknown")
        self.scores_history[lead_id] = breakdown

        logger.info(f"Lead {lead_id} scored: {overall_score:.1f}/100 - {recommendation}")
        return breakdown

    def _evaluate_budget(self, lead_data: Dict[str, Any]) -> float:
        """Factor 1: Budget capacity & qualification."""
        budget_min = lead_data.get("budget_min", 0)
        budget_max = lead_data.get("budget_max", 0)
        monthly_income = lead_data.get("monthly_income", 0)

        score = 0.0

        # Budget range clarity
        if budget_max - budget_min > 0:
            score += 20

        # Budget size
        if budget_max > 500000:
            score += 30
        elif budget_max > 250000:
            score += 20
        elif budget_max > 100000:
            score += 10

        # Income-to-budget ratio
        if monthly_income > 0:
            ratio = budget_max / (monthly_income * 12)
            if 2 <= ratio <= 5:  # Healthy range
                score += 30
            elif 1 <= ratio < 2 or 5 < ratio <= 7:
                score += 15
            else:
                score += 5

        # Down payment availability
        if lead_data.get("down_payment_ready"):
            score += 20

        return min(score, 100.0)

    def _evaluate_motivation(self, lead_data: Dict[str, Any]) -> float:
        """Factor 2: Buyer motivation & intent."""
        motivation = lead_data.get("motivation", "").lower()
        intent_signals = lead_data.get("intent_signals", [])

        score = 0.0

        # Primary motivation
        if "investment" in motivation:
            score += 35  # Investors are serious
        elif "primary_residence" in motivation:
            score += 30
        elif "second_home" in motivation:
            score += 20
        elif "rental" in motivation:
            score += 25

        # Intent signals (viewed multiple properties, attended showings, etc)
        signals_weight = {
            "property_views": 5,
            "showings_attended": 15,
            "prequalified": 30,
            "made_offer_previously": 20,
            "contacted_agent_multiple": 10,
        }

        for signal, weight in signals_weight.items():
            if signal in intent_signals:
                score += weight

        return min(score, 100.0)

    def _evaluate_timeline(self, lead_data: Dict[str, Any]) -> float:
        """Factor 3: Purchase timeline & urgency."""
        timeline = lead_data.get("timeline", "").lower()

        score_map = {
            "immediate": 100,
            "within_1_month": 90,
            "within_3_months": 75,
            "within_6_months": 50,
            "within_1_year": 30,
            "exploring": 20,
            "no_timeline": 0,
        }

        # Find matching timeline
        for key, value in score_map.items():
            if key in timeline:
                return float(value)

        return 30.0  # Default for unclear timelines

    def _evaluate_credit(self, lead_data: Dict[str, Any]) -> float:
        """Factor 4: Credit worthiness."""
        credit_score = lead_data.get("credit_score")
        bankruptcy_history = lead_data.get("bankruptcy_history", False)
        foreclosure_history = lead_data.get("foreclosure_history", False)
        late_payments = lead_data.get("late_payments", 0)

        score = 0.0

        # Credit score
        if credit_score:
            if credit_score >= 750:
                score += 50
            elif credit_score >= 700:
                score += 40
            elif credit_score >= 650:
                score += 25
            elif credit_score >= 600:
                score += 10
            else:
                score += 0

        # Negative history
        if bankruptcy_history:
            score -= 40
        if foreclosure_history:
            score -= 30
        if late_payments > 5:
            score -= 20
        elif late_payments > 2:
            score -= 10
        elif late_payments > 0:
            score -= 5

        # Pre-approved helps
        if lead_data.get("prequalified"):
            score += 20

        return max(0.0, min(score, 100.0))

    def _evaluate_location_preference(self, lead_data: Dict[str, Any]) -> float:
        """Factor 5: Location preference clarity."""
        preferred_locations = lead_data.get("preferred_locations", [])
        school_district_important = lead_data.get("school_district_important", False)
        commute_distance_preference = lead_data.get("commute_distance_max_miles")

        score = 0.0

        # Location specificity
        if preferred_locations:
            if len(preferred_locations) == 1:
                score += 40  # Very specific
            elif len(preferred_locations) <= 3:
                score += 30
            elif len(preferred_locations) <= 5:
                score += 20
            else:
                score += 10

        # Specific preferences
        if school_district_important:
            score += 20

        if commute_distance_preference:
            if commute_distance_preference < 30:
                score += 20
            elif commute_distance_preference < 60:
                score += 15
            else:
                score += 5

        # Flexibility
        if lead_data.get("location_flexibility"):
            score += 10

        return min(score, 100.0)

    def _evaluate_property_type_alignment(self, lead_data: Dict[str, Any]) -> float:
        """Factor 6: Property type preferences."""
        preferred_types = lead_data.get("preferred_property_types", [])
        min_bedrooms = lead_data.get("min_bedrooms")
        max_bedrooms = lead_data.get("max_bedrooms")
        lot_size_preference = lead_data.get("lot_size_preference")

        score = 0.0

        # Clear property type preference
        if preferred_types:
            score += 30

        # Bedroom requirements
        if min_bedrooms and max_bedrooms:
            score += 25
        elif min_bedrooms or max_bedrooms:
            score += 15

        # Lot size consideration
        if lot_size_preference:
            score += 20

        # House features
        if lead_data.get("required_features"):
            score += 15

        # Flexibility
        if lead_data.get("property_type_flexibility"):
            score += 10

        return min(score, 100.0)

    def _generate_recommendation(self, overall_score: float, lead_data: Dict[str, Any]) -> str:
        """Generate recommendation based on score."""
        if overall_score >= 80:
            return "HIGHLY QUALIFIED - Priority lead, ready to show properties"
        elif overall_score >= 65:
            return "QUALIFIED - Good fit, verify financing status"
        elif overall_score >= 50:
            return "PARTIALLY QUALIFIED - Needs improvement in 1-2 areas"
        elif overall_score >= 35:
            return "NEEDS NURTURING - Follow-up needed, may qualify later"
        else:
            return "NOT QUALIFIED - Requires significant improvement or circumstances change"

    def get_lead_quality_report(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed scoring report for lead."""
        if lead_id not in self.scores_history:
            return None

        breakdown = self.scores_history[lead_id]
        return {
            "lead_id": lead_id,
            "overall_score": breakdown.overall_score,
            "factors": {
                "budget": breakdown.budget_score,
                "motivation": breakdown.motivation_score,
                "timeline": breakdown.timeline_score,
                "credit": breakdown.credit_score_metric,
                "location_preference": breakdown.location_preference_score,
                "property_type_alignment": breakdown.property_type_alignment,
            },
            "weights": self.SCORE_WEIGHTS,
            "recommendation": breakdown.recommendation,
        }

    def batch_score_leads(self, leads: list) -> Dict[str, LeadScoreBreakdown]:
        """Score multiple leads."""
        results = {}
        for lead in leads:
            lead_id = lead.get("lead_id")
            results[lead_id] = self.score_lead(lead)
        return results
