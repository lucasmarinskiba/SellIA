"""Customer Retention — Fidelización, contención churn, upsell."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ChurnRiskLevel(str, Enum):
    """Customer churn risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChurnScore:
    """Customer churn risk score."""
    customer_id: str
    customer_name: str
    risk_level: ChurnRiskLevel
    score: float  # 0-1, higher = more risk
    risk_factors: List[str]
    confidence: float  # 0-1
    recommended_actions: List[str]
    expected_ltv_if_retained: float
    intervention_urgency: str  # low, medium, high, critical


@dataclass
class HappinessTactic:
    """Specific tactic to increase customer happiness."""
    tactic_id: str
    name: str
    description: str
    implementation_steps: List[str]
    cost: float
    expected_nps_lift: int  # Points
    timeline_days: int
    success_metrics: List[str]


@dataclass
class ReactivationOffer:
    """Offer to reactivate churned customer."""
    customer_id: str
    discount_percent: float
    new_features: List[str]
    special_treatment: str
    offer_duration_days: int
    expected_reactivation_rate: float
    reasoning: str


class RetentionEngine:
    """Engine for fidelización, churn prevention, and upsell."""

    def __init__(self):
        """Initialize retention engine."""
        pass

    def calculate_churn_risk(
        self,
        customer_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
    ) -> ChurnScore:
        """
        Identify customers at churn risk.

        Signals:
        - Feature usage drop (usage churn)
        - Payment issues (billing churn)
        - Inactivity (dormant)
        - Competitor activity
        - Industry trends (e.g., recession)

        Args:
            customer_data: Current customer data
            historical_data: Historical customer data

        Returns:
            Churn risk score and recommended actions
        """
        logger.info(f"Calculating churn risk for customer: {customer_data.get('customer_id')}")

        # Calculate individual risk factors
        usage_risk = self._analyze_usage_churn(customer_data, historical_data)
        billing_risk = self._analyze_billing_churn(customer_data)
        inactivity_risk = self._analyze_inactivity(customer_data, historical_data)
        competitive_risk = customer_data.get("competitor_activity", 0)
        industry_risk = customer_data.get("industry_churn_rate", 0.05)

        # Weighted average
        risk_factors = {
            "usage_decline": usage_risk,
            "billing_issues": billing_risk,
            "inactivity": inactivity_risk,
            "competitive_threat": competitive_risk,
            "industry_trend": industry_risk,
        }

        overall_score = sum(risk_factors.values()) / len(risk_factors)

        # Determine risk level
        if overall_score > 0.75:
            risk_level = ChurnRiskLevel.CRITICAL
        elif overall_score > 0.50:
            risk_level = ChurnRiskLevel.HIGH
        elif overall_score > 0.25:
            risk_level = ChurnRiskLevel.MEDIUM
        else:
            risk_level = ChurnRiskLevel.LOW

        # Generate recommended actions
        recommended_actions = self._generate_retention_actions(risk_level, risk_factors)

        # Calculate LTV if retained
        ltv = customer_data.get("lifetime_value", 0.0)
        mrr = customer_data.get("monthly_revenue", 0.0)
        expected_ltv = (mrr * 36) if risk_level != ChurnRiskLevel.CRITICAL else (mrr * 12)

        return ChurnScore(
            customer_id=customer_data.get("customer_id", "unknown"),
            customer_name=customer_data.get("customer_name", "Unknown"),
            risk_level=risk_level,
            score=overall_score,
            risk_factors=[f"{k}: {v:.1f}" for k, v in risk_factors.items() if v > 0.1],
            confidence=0.75,
            recommended_actions=recommended_actions,
            expected_ltv_if_retained=expected_ltv,
            intervention_urgency=self._determine_urgency(risk_level),
        )

    def happiness_strategy(
        self,
        customer_data: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> List[HappinessTactic]:
        """
        Convert satisfied → promoter (NPS 9-10).

        Tactics:
        - Proactive support (reach out before problem)
        - Exclusive perks (early access, discounts)
        - Community (users connect with users)
        - Education (training, resources)

        Args:
            customer_data: Customer data
            business_profile: Business profile

        Returns:
            Ranked list of happiness tactics
        """
        logger.info(f"Generating happiness strategy for {customer_data.get('customer_id')}")

        nps_score = customer_data.get("nps_score", 0)
        tactics = []

        # For promoters (9-10), delight them
        if nps_score >= 9:
            tactics.extend(self._delighter_tactics(customer_data))

        # For passives (7-8), convert to promoters
        if 7 <= nps_score < 9:
            tactics.extend(self._passive_conversion_tactics(customer_data))

        # For detractors (0-6), turn around
        if nps_score < 7:
            tactics.extend(self._detractor_recovery_tactics(customer_data))

        # Always add community tactics
        tactics.append(self._community_building_tactic())

        # Always add education tactics
        tactics.append(self._education_tactic(business_profile))

        return tactics

    def win_back_campaign(
        self,
        churned_customer_data: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> ReactivationOffer:
        """
        Bring back churned customers.

        Offer strategy:
        - Offer: better price, new features, special treatment
        - Timing: too soon (irrelevant), too late (moved on)
        - Channel: email, SMS, retargeting ads

        Args:
            churned_customer_data: Churned customer data
            business_profile: Business profile

        Returns:
            Win-back offer strategy
        """
        logger.info(f"Creating win-back campaign for: {churned_customer_data.get('customer_id')}")

        # Determine churn reason
        churn_reason = churned_customer_data.get("churn_reason", "unknown")

        # Calculate discount
        customer_ltv = churned_customer_data.get("lifetime_value", 0.0)
        discount_percent = self._calculate_winback_discount(customer_ltv, churn_reason)

        # Determine new features to highlight
        new_features = self._identify_new_features(business_profile, churn_reason)

        # Determine special treatment
        special_treatment = self._create_special_treatment(customer_ltv, business_profile)

        # Determine offer duration
        days_since_churn = churned_customer_data.get("days_since_churn", 90)
        offer_duration = self._optimize_offer_timing(days_since_churn)

        # Estimate reactivation rate
        reactivation_rate = self._estimate_reactivation_rate(
            discount_percent,
            new_features,
            churn_reason,
        )

        return ReactivationOffer(
            customer_id=churned_customer_data.get("customer_id", "unknown"),
            discount_percent=discount_percent,
            new_features=new_features,
            special_treatment=special_treatment,
            offer_duration_days=offer_duration,
            expected_reactivation_rate=reactivation_rate,
            reasoning=f"Customer churned due to: {churn_reason}. "
            f"Offer {discount_percent:.0%} discount + {len(new_features)} new features. "
            f"Expected reactivation: {reactivation_rate:.0%}",
        )

    def upsell_opportunity(
        self,
        customer_data: Dict[str, Any],
        available_products: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Identify upsell/cross-sell opportunities.

        Args:
            customer_data: Customer data
            available_products: Available products/services

        Returns:
            Recommended upsell or None
        """
        current_products = customer_data.get("current_products", [])
        revenue = customer_data.get("monthly_revenue", 0.0)

        # Find complementary products not yet purchased
        upsell_candidates = [
            p for p in available_products
            if p["id"] not in current_products and p.get("tier", "basic") != "basic"
        ]

        if not upsell_candidates:
            return None

        # Score each by fit and price
        best_fit = max(
            upsell_candidates,
            key=lambda x: self._upsell_fit_score(customer_data, x),
        )

        return {
            "product_id": best_fit["id"],
            "product_name": best_fit["name"],
            "expected_revenue_increase": best_fit.get("price", revenue * 0.25),
            "pitch": f"Based on your usage, you'd benefit from {best_fit['name']}",
        }

    # Private helper methods

    def _analyze_usage_churn(
        self,
        customer_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
    ) -> float:
        """Analyze usage decline."""
        if not historical_data or len(historical_data) < 2:
            return 0.0

        current_usage = customer_data.get("monthly_usage", 0)
        previous_usage = historical_data[-1].get("monthly_usage", current_usage)

        if previous_usage == 0:
            return 0.0

        decline_percent = (previous_usage - current_usage) / previous_usage
        return max(min(decline_percent, 1.0), 0.0)

    def _analyze_billing_churn(self, customer_data: Dict[str, Any]) -> float:
        """Analyze billing issues."""
        recent_failures = customer_data.get("payment_failures_last_90_days", 0)
        failed_cards = customer_data.get("failed_cards", 0)

        if recent_failures > 2 or failed_cards > 0:
            return 0.5 + (recent_failures * 0.1)
        return 0.0

    def _analyze_inactivity(
        self,
        customer_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
    ) -> float:
        """Analyze customer inactivity."""
        last_activity = customer_data.get("last_activity_days_ago", 365)

        if last_activity > 90:
            return 0.8
        elif last_activity > 30:
            return 0.4
        elif last_activity > 7:
            return 0.1
        return 0.0

    def _generate_retention_actions(
        self,
        risk_level: ChurnRiskLevel,
        risk_factors: Dict[str, float],
    ) -> List[str]:
        """Generate recommended retention actions."""
        actions = []

        if risk_level == ChurnRiskLevel.CRITICAL:
            actions.append("Call customer today (executive call)")
            actions.append("Offer dedicated support for 30 days")

        if risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]:
            actions.append("Identify and fix main issue")
            actions.append("Offer temporary discount (20-30%)")

        if risk_factors.get("usage_decline", 0) > 0.5:
            actions.append("Send usage training/webinar invite")

        if risk_factors.get("billing_issues", 0) > 0:
            actions.append("Troubleshoot payment method")

        if not actions:
            actions.append("Send personalized success email")

        return actions

    def _determine_urgency(self, risk_level: ChurnRiskLevel) -> str:
        """Determine intervention urgency."""
        return str(risk_level.value)

    def _delighter_tactics(self, customer_data: Dict[str, Any]) -> List[HappinessTactic]:
        """Generate tactics to delight promoters."""
        return [
            HappinessTactic(
                tactic_id="delight_exclusive_access",
                name="Exclusive Early Access to New Features",
                description="Invite promoters to beta test new features",
                implementation_steps=[
                    "Identify next feature launch",
                    "Invite top promoters to beta program",
                    "Gather feedback and testimonials",
                ],
                cost=100,
                expected_nps_lift=2,
                timeline_days=14,
                success_metrics=["Beta participation rate", "Feedback quality"],
            ),
            HappinessTactic(
                tactic_id="delight_vip_tier",
                name="VIP Treatment / Priority Support",
                description="Highest quality support with dedicated contact",
                implementation_steps=[
                    "Assign dedicated success manager",
                    "Quarterly business reviews",
                    "Priority support queue",
                ],
                cost=200,
                expected_nps_lift=3,
                timeline_days=7,
                success_metrics=["Support satisfaction", "Response time"],
            ),
        ]

    def _passive_conversion_tactics(self, customer_data: Dict[str, Any]) -> List[HappinessTactic]:
        """Generate tactics to convert passives to promoters."""
        return [
            HappinessTactic(
                tactic_id="passive_personalization",
                name="Personalized Success Optimization",
                description="Identify unrealized value and help customer unlock it",
                implementation_steps=[
                    "Schedule 30-min call to understand goals",
                    "Identify top 3 quick wins",
                    "Implement quick wins together",
                ],
                cost=150,
                expected_nps_lift=5,
                timeline_days=14,
                success_metrics=["Customer satisfaction increase", "Usage increase %"],
            ),
        ]

    def _detractor_recovery_tactics(self, customer_data: Dict[str, Any]) -> List[HappinessTactic]:
        """Generate tactics to recover detractors."""
        return [
            HappinessTactic(
                tactic_id="recover_listening_call",
                name="Executive Listening Call",
                description="CEO/founder calls to listen and resolve",
                implementation_steps=[
                    "Schedule call with executive",
                    "Listen to frustrations",
                    "Develop resolution plan",
                    "Follow up weekly",
                ],
                cost=0,
                expected_nps_lift=10,
                timeline_days=3,
                success_metrics=["Issue resolved", "NPS improvement"],
            ),
        ]

    def _community_building_tactic(self) -> HappinessTactic:
        """Tactic to build community."""
        return HappinessTactic(
            tactic_id="community_user_group",
            name="User Community & Events",
            description="Create space for customers to connect and learn from each other",
            implementation_steps=[
                "Create private Slack/Discord for customers",
                "Host monthly virtual user meetups",
                "Share customer wins and use cases",
            ],
            cost=300,
            expected_nps_lift=4,
            timeline_days=30,
            success_metrics=["Community size", "Monthly active participation"],
        )

    def _education_tactic(self, business_profile: "BusinessProfile") -> HappinessTactic:
        """Tactic for customer education."""
        return HappinessTactic(
            tactic_id="education_training",
            name="Structured Training & Certification",
            description="Help customers become power users through education",
            implementation_steps=[
                "Create 5-module training course",
                "Offer certification program",
                "Recognize certified users publicly",
            ],
            cost=500,
            expected_nps_lift=6,
            timeline_days=60,
            success_metrics=["Completion rate", "Usage increase %"],
        )

    def _calculate_winback_discount(self, ltv: float, churn_reason: str) -> float:
        """Calculate appropriate win-back discount."""
        base_discount = 0.20  # 20%

        if "price" in churn_reason.lower():
            return 0.30
        elif "competitor" in churn_reason.lower():
            return 0.25
        elif "features" in churn_reason.lower():
            return 0.10

        return base_discount

    def _identify_new_features(
        self,
        business_profile: "BusinessProfile",
        churn_reason: str,
    ) -> List[str]:
        """Identify new features to highlight."""
        if "features" in churn_reason.lower():
            return ["New advanced analytics", "API access", "Custom integrations"]
        return ["Improved performance", "New dashboard", "Enhanced reporting"]

    def _create_special_treatment(self, ltv: float, business_profile: "BusinessProfile") -> str:
        """Create special treatment offer."""
        if ltv > 50_000:
            return "Dedicated customer success manager for 6 months"
        elif ltv > 10_000:
            return "Priority support + quarterly business reviews"
        else:
            return "30 days of premium support included"

    def _optimize_offer_timing(self, days_since_churn: int) -> int:
        """Optimize offer validity period."""
        if days_since_churn < 30:
            return 14  # 2 weeks to decide
        elif days_since_churn < 90:
            return 21  # 3 weeks
        else:
            return 7  # 1 week (almost moved on)

    def _estimate_reactivation_rate(
        self,
        discount_percent: float,
        new_features: List[str],
        churn_reason: str,
    ) -> float:
        """Estimate probability of reactivation."""
        rate = 0.10

        if discount_percent >= 0.25:
            rate += 0.15
        elif discount_percent >= 0.15:
            rate += 0.10

        if len(new_features) >= 3:
            rate += 0.10

        if "price" in churn_reason.lower():
            rate += 0.15

        return min(rate, 0.60)

    def _upsell_fit_score(self, customer_data: Dict[str, Any], product: Dict[str, Any]) -> float:
        """Calculate fit score for upsell."""
        score = 0.0

        # Product tier progression
        current_tier = customer_data.get("current_tier", "basic")
        if product.get("tier") == "pro" and current_tier == "basic":
            score += 0.5

        # Usage-based fit
        usage = customer_data.get("monthly_usage", 0)
        if usage > 1000:
            score += 0.3

        # Price sensitivity
        revenue = customer_data.get("monthly_revenue", 0)
        if revenue > product.get("price", 0) * 2:
            score += 0.2

        return score
