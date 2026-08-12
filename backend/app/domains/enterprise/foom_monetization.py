"""Advanced FOOM Monetization Engine for SellIA.

Double Revenue Layer:
1. Platform FOOM (SellIA → Paying Users): Convert free users to paid subscriptions
2. User FOOM Tools (Users → Their Customers): Enable users to sell with FOOM

Revenue Model: Freemium → usage-triggered upgrade → network effects → viral growth
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
from anthropic import Anthropic

client_anthropic = Anthropic()


class UserSegment(Enum):
    """User segments for targeted FOOM."""
    FREEMIUM_ACTIVE = "freemium_active"  # Using daily, high engagement
    FREEMIUM_STALE = "freemium_stale"  # Inactive 7+ days
    TRIAL_ENDING = "trial_ending"  # Trial expires in <7 days
    POWER_USER = "power_user"  # Heavy feature usage, perfect upsell
    AT_RISK_PAID = "at_risk_paid"  # Paid user, might churn


@dataclass
class PlatformFOOMTrigger:
    """FOOM trigger for acquiring paying users."""
    user_segment: UserSegment
    trigger_type: str
    urgency_message: str
    offer: str  # discount, feature unlock, extended trial
    psychology: str
    expected_conversion: float  # historical conversion %


class PlatformMonetizationFOOM:
    """Generate FOOM to convert free → paid users."""

    def __init__(self, db):
        self.db = db

    def get_upgrade_trigger(self, user_id: str, user_data: Dict[str, Any]) -> Optional[PlatformFOOMTrigger]:
        """Identify optimal upgrade trigger for user."""
        segment = self._classify_user_segment(user_data)

        if segment == UserSegment.FREEMIUM_ACTIVE:
            return self._trigger_power_user_upsell(user_data)
        elif segment == UserSegment.FREEMIUM_STALE:
            return self._trigger_reengagement_with_offer(user_data)
        elif segment == UserSegment.TRIAL_ENDING:
            return self._trigger_trial_conversion(user_data)
        elif segment == UserSegment.POWER_USER:
            return self._trigger_premium_tier_upgrade(user_data)
        elif segment == UserSegment.AT_RISK_PAID:
            return self._trigger_retention_upgrade(user_data)

        return None

    def _classify_user_segment(self, user_data: Dict[str, Any]) -> UserSegment:
        """Classify user into segment."""
        days_since_login = user_data.get("days_since_login", 0)
        login_count_7d = user_data.get("login_count_7d", 0)
        feature_usage_pct = user_data.get("feature_usage_pct", 0)
        days_until_trial_end = user_data.get("days_until_trial_end", 999)
        is_paid = user_data.get("is_paid", False)

        if is_paid and days_since_login > 14:
            return UserSegment.AT_RISK_PAID

        if days_until_trial_end < 7:
            return UserSegment.TRIAL_ENDING

        if login_count_7d >= 5 and feature_usage_pct > 0.6:
            return UserSegment.POWER_USER

        if login_count_7d >= 4:
            return UserSegment.FREEMIUM_ACTIVE

        if days_since_login > 7:
            return UserSegment.FREEMIUM_STALE

        return UserSegment.FREEMIUM_ACTIVE

    def _trigger_power_user_upsell(self, user_data: Dict[str, Any]) -> PlatformFOOMTrigger:
        """Upsell power users to premium tier."""
        features_used = user_data.get("features_used", [])
        feature_limit_hits = user_data.get("feature_limit_hits_7d", 0)

        return PlatformFOOMTrigger(
            user_segment=UserSegment.FREEMIUM_ACTIVE,
            trigger_type="power_user_upsell",
            urgency_message=f"You've hit your limit {feature_limit_hits}x this week. Premium users get unlimited.",
            offer="40% off first month of Premium ($29/mo → $17/mo)",
            psychology="Loss aversion: they're losing productivity hitting limits. Concrete solution.",
            expected_conversion=0.35,
        )

    def _trigger_reengagement_with_offer(self, user_data: Dict[str, Any]) -> PlatformFOOMTrigger:
        """Re-engage stale users with time-limited offer."""
        days_inactive = user_data.get("days_since_login", 0)

        return PlatformFOOMTrigger(
            user_segment=UserSegment.FREEMIUM_STALE,
            trigger_type="reengagement_offer",
            urgency_message=f"We miss you! It's been {days_inactive} days. Come back with 50% off.",
            offer="50% off Premium for 3 months (trial offer ending soon)",
            psychology="Reciprocity: show value first, then ask. Time-limited makes it scarce.",
            expected_conversion=0.22,
        )

    def _trigger_trial_conversion(self, user_data: Dict[str, Any]) -> PlatformFOOMTrigger:
        """Convert ending trials to paid."""
        days_left = user_data.get("days_until_trial_end", 0)
        features_used = len(user_data.get("features_used", []))

        return PlatformFOOMTrigger(
            user_segment=UserSegment.TRIAL_ENDING,
            trigger_type="trial_conversion",
            urgency_message=f"Your trial ends in {days_left} days. You've used {features_used} features—don't lose access.",
            offer=f"Lock in 40% discount if you subscribe today (expires in {days_left} days)",
            psychology="Loss aversion + scarcity + urgency. They've invested time in trial.",
            expected_conversion=0.45,
        )

    def _trigger_premium_tier_upgrade(self, user_data: Dict[str, Any]) -> PlatformFOOMTrigger:
        """Upgrade premium to enterprise tier."""
        team_size = user_data.get("team_size", 1)
        calls_used = user_data.get("api_calls_month", 0)

        return PlatformFOOMTrigger(
            user_segment=UserSegment.POWER_USER,
            trigger_type="enterprise_upgrade",
            urgency_message=f"Your team of {team_size} is using {calls_used} calls/mo. Enterprise tier unlocks {calls_used * 5}+.",
            offer="Enterprise tier: $299/mo (vs Premium $29/mo) → unlimited seats + API + support",
            psychology="Authority + social proof: other teams at this size use Enterprise.",
            expected_conversion=0.28,
        )

    def _trigger_retention_upgrade(self, user_data: Dict[str, Any]) -> PlatformFOOMTrigger:
        """Prevent churn by upgrading at-risk paid users."""
        churn_risk = user_data.get("churn_risk", 0)

        return PlatformFOOMTrigger(
            user_segment=UserSegment.AT_RISK_PAID,
            trigger_type="retention_upgrade",
            urgency_message="Your engagement is declining. Upgrade to unlock features that'll re-engage your team.",
            offer="Free upgrade to next tier for 3 months (normally $X/mo)",
            psychology="Prevention: stop churn with value add, not discount.",
            expected_conversion=0.40,
        )


class UserFOOMEnablement:
    """Enable SellIA users to generate FOOM for their products."""

    def __init__(self, db):
        self.db = db

    def generate_user_foom_strategy(self, user_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete FOOM selling strategy for user's product."""
        strategy = {
            "product_name": product_data.get("product_name"),
            "industry": product_data.get("industry"),
            "avg_deal_size": product_data.get("avg_deal_size", 5000),

            # 1. Scarcity levers
            "scarcity": self._generate_scarcity_levers(product_data),

            # 2. Social proof generators
            "social_proof": self._generate_social_proof_template(product_data),

            # 3. Urgency messaging
            "urgency_templates": self._generate_urgency_messages(product_data),

            # 4. FOOM content calendar
            "content_calendar": self._generate_foom_content_calendar(product_data),

            # 5. Landing page FOOM elements
            "landing_page_foom": self._generate_landing_page_foom(product_data),

            # 6. Email sequence with FOOM
            "email_sequence": self._generate_foom_email_sequence(product_data),

            # 7. Social media FOOM posts
            "social_posts": self._generate_social_foom_posts(product_data),
        }
        return strategy

    def _generate_scarcity_levers(self, product_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate real scarcity mechanisms."""
        return [
            {
                "lever": "Limited capacity",
                "implementation": "We can only onboard X customers/month due to service quality",
                "psychology": "Real scarcity = valuable access",
                "messaging": "Only 3 onboarding slots left this month",
            },
            {
                "lever": "Pricing increase",
                "implementation": "Schedule price increase for next month (real or perceived)",
                "psychology": "Loss aversion: current price is temporary benefit",
                "messaging": "Price increases on 2027-02-01. Lock in current rate today.",
            },
            {
                "lever": "Feature rollback",
                "implementation": "Free features becoming premium (real timeline)",
                "psychology": "Scarcity + loss aversion combined",
                "messaging": "50% discount on premium features ending soon",
            },
            {
                "lever": "Cohort-based",
                "implementation": "Next cohort starts 2027-02-15. Only X seats available.",
                "psychology": "Social proof + scarcity + FOMO",
                "messaging": "Next cohort starts in 14 days. 7/10 seats filled.",
            },
        ]

    def _generate_social_proof_template(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate social proof data structure."""
        return {
            "customer_count": f"Join {product_data.get('customer_count', 500)}+ customers",
            "daily_signups": "X people signed up today",
            "customer_testimonials": [
                {
                    "quote": "This saved us $X/year",
                    "customer": "Company Name, Industry",
                    "metric": "+40% revenue increase",
                },
            ],
            "case_study": f"How {product_data.get('top_customer', 'Customer')} achieved $X results",
            "social_proof_messaging": [
                "Join 500+ companies using this solution",
                "47 people joined this week",
                "Used by Fortune 500 companies",
                "Recommended by industry experts",
            ],
        }

    def _generate_urgency_messages(self, product_data: Dict[str, Any]) -> List[str]:
        """Generate urgency messaging templates."""
        return [
            "Price increases next week—lock in current rate",
            "Only 3 cohort spots left",
            "Your competitors are already using this",
            "Every day you wait costs $X in lost opportunity",
            "Trial ends in 7 days",
            "Limited-time bonus if you decide this week",
            "Next cohort starts {date}—don't miss it",
        ]

    def _generate_foom_content_calendar(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate 4-week FOOM content calendar."""
        return {
            "week_1": {
                "theme": "Awareness + Problem",
                "posts": [
                    {"day": "Monday", "content": "Problem statement post (education)"},
                    {"day": "Wednesday", "content": "Customer success story"},
                    {"day": "Friday", "content": "Industry trend + competitive threat"},
                ],
            },
            "week_2": {
                "theme": "Solution + FOOM",
                "posts": [
                    {"day": "Monday", "content": "Solution overview (no pitch yet)"},
                    {"day": "Wednesday", "content": "X people joined this week (social proof)"},
                    {"day": "Friday", "content": "Price increase announcement (urgency)"},
                ],
            },
            "week_3": {
                "theme": "Scarcity + Urgency",
                "posts": [
                    {"day": "Monday", "content": "Limited spots remaining (scarcity)"},
                    {"day": "Wednesday", "content": "FOMO post: competitors winning (loss aversion)"},
                    {"day": "Friday", "content": "Last chance post (urgency)"},
                ],
            },
            "week_4": {
                "theme": "Conversion + Close",
                "posts": [
                    {"day": "Monday", "content": "CTA: Join today (close)"},
                    {"day": "Wednesday", "content": "Objection handling post"},
                    {"day": "Friday", "content": "Last day messaging (final urgency)"},
                ],
            },
        }

    def _generate_landing_page_foom(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate landing page FOOM elements."""
        return {
            "hero_headline": f"Join 500+ companies using {product_data.get('product_name')}—before pricing increases",
            "subheadline": "Limited spots available. Next cohort starts 2027-02-15.",
            "hero_cta": "Reserve Your Spot (Only 3 Left)",
            "social_proof_counter": "523 people signed up this month",
            "urgency_banner": "⏰ Price increases on 2027-02-01. Lock in current rate today.",
            "scarcity_indicator": "✓ 7 of 10 spots filled. 3 remaining.",
            "objection_section": "Common concerns answered",
            "fomo_section": "What you'll be able to do after joining",
        }

    def _generate_foom_email_sequence(self, product_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate 5-email FOOM sequence."""
        return [
            {
                "day": 0,
                "subject": "You have $X at stake if you don't act",
                "hook": "Problem quantification + cost of delay",
                "foom_element": "Financial impact math",
            },
            {
                "day": 1,
                "subject": "500+ companies already doing this",
                "hook": "Social proof + competitive threat",
                "foom_element": "What competitors are winning",
            },
            {
                "day": 3,
                "subject": "Price increases in 3 days",
                "hook": "Urgency + scarcity",
                "foom_element": "Time-bound offer (expires X date)",
            },
            {
                "day": 5,
                "subject": "Only 2 spots left (47 people in last 48 hours)",
                "hook": "Extreme scarcity + momentum",
                "foom_element": "Live counter of spots remaining",
            },
            {
                "day": 7,
                "subject": "Last chance: expires tonight",
                "hook": "Final urgency",
                "foom_element": "Countdown timer + last CTA",
            },
        ]

    def _generate_social_foom_posts(self, product_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate 10 viral-ready social media posts."""
        return [
            {
                "platform": "LinkedIn",
                "post": "523 people joined this week. Next cohort starts 2027-02-15. 3 spots left.",
                "engagement_lever": "FOMO + scarcity",
            },
            {
                "platform": "Twitter",
                "post": "Price going up next week. Lock in the rate today if you're serious about this.",
                "engagement_lever": "Urgency",
            },
            {
                "platform": "LinkedIn",
                "post": "While you're thinking about it, your competitor just joined.",
                "engagement_lever": "Loss aversion",
            },
            {
                "platform": "Twitter",
                "post": "Most people wait until the price increases, then regret it. Don't be that person.",
                "engagement_lever": "Regret aversion",
            },
            {
                "platform": "LinkedIn",
                "post": "Every day you wait costs $500 in lost opportunity. Math doesn't lie.",
                "engagement_lever": "Quantified FOMO",
            },
        ]


class FOMOPerformanceOptimizer:
    """ML-based optimization of FOOM strategies."""

    def __init__(self, db):
        self.db = db

    def optimize_foom_strategy(self, user_id: str, ab_test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend optimized FOOM strategy based on A/B tests."""
        best_performers = self._identify_top_performers(ab_test_results)
        optimization_recommendations = self._generate_recommendations(best_performers)

        return {
            "current_conversion_rate": ab_test_results.get("current_conversion_rate", 0.15),
            "optimized_conversion_rate": self._estimate_optimized_rate(best_performers),
            "top_performing_elements": best_performers,
            "recommendations": optimization_recommendations,
            "expected_revenue_lift": self._calculate_revenue_lift(ab_test_results, best_performers),
        }

    def _identify_top_performers(self, ab_test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify highest-converting FOOM elements."""
        all_variants = ab_test_results.get("variants", [])
        sorted_variants = sorted(
            all_variants,
            key=lambda v: v.get("conversion_rate", 0),
            reverse=True
        )
        return sorted_variants[:5]  # Top 5

    def _generate_recommendations(self, best_performers: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        for i, performer in enumerate(best_performers, 1):
            element_type = performer.get("element_type")
            conversion = performer.get("conversion_rate", 0)

            if element_type == "urgency_message":
                recommendations.append(f"Use '{performer.get('variant')}' in all urgency messaging (+{(conversion - 0.15)*100:.0f}% lift)")
            elif element_type == "social_proof":
                recommendations.append(f"Amplify {performer.get('variant')} across landing page (+{(conversion - 0.15)*100:.0f}% lift)")
            elif element_type == "offer":
                recommendations.append(f"Lead with '{performer.get('variant')}' offer in email sequence (+{(conversion - 0.15)*100:.0f}% lift)")

        return recommendations

    def _estimate_optimized_rate(self, best_performers: List[Dict[str, Any]]) -> float:
        """Estimate conversion rate after optimization."""
        if not best_performers:
            return 0.15
        avg_top_5_rate = sum(v.get("conversion_rate", 0) for v in best_performers) / len(best_performers)
        return min(0.45, avg_top_5_rate)  # Cap at 45%

    def _calculate_revenue_lift(self, ab_test_results: Dict[str, Any], best_performers: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate revenue impact of optimizations."""
        current_rate = ab_test_results.get("current_conversion_rate", 0.15)
        optimized_rate = self._estimate_optimized_rate(best_performers)
        monthly_visitors = ab_test_results.get("monthly_visitors", 10000)
        avg_deal_size = ab_test_results.get("avg_deal_size", 5000)

        current_monthly_revenue = monthly_visitors * current_rate * avg_deal_size
        optimized_monthly_revenue = monthly_visitors * optimized_rate * avg_deal_size
        monthly_lift = optimized_monthly_revenue - current_monthly_revenue

        return {
            "current_monthly_revenue": current_monthly_revenue,
            "optimized_monthly_revenue": optimized_monthly_revenue,
            "monthly_lift": monthly_lift,
            "annual_lift": monthly_lift * 12,
        }


class NetworkEffectFOOM:
    """FOOM through network effects (viral growth)."""

    def __init__(self, db):
        self.db = db

    def generate_referral_foom(self, user_id: str, user_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate FOOM-based referral program mechanics."""
        return {
            "referral_incentive": "Refer a friend → both get 1 month free Premium",
            "social_proof_lever": "Show how many people the user has already convinced",
            "viral_loop": {
                "step_1": "User sees their 'influencer score' (how many they've referred)",
                "step_2": "FOOM: 'Most users at your level have referred 5+ people'",
                "step_3": "Referral reward + leaderboard (social proof)",
            },
            "expected_viral_coefficient": 1.4,  # 1 user brings 1.4 new users
            "network_effect_message": "Join 500+ growing companies. Your network is using this.",
        }

    def calculate_lifetime_value_with_network(self, user_metrics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate LTV including network effects."""
        base_ltv = user_metrics.get("base_ltv", 1000)
        referral_rate = user_metrics.get("referral_rate", 0.15)
        viral_coefficient = 1.4

        network_expansion_value = base_ltv * referral_rate * viral_coefficient
        total_ltv = base_ltv + network_expansion_value

        return {
            "base_ltv": base_ltv,
            "network_expansion_value": network_expansion_value,
            "total_ltv_with_network": total_ltv,
            "expansion_multiple": total_ltv / base_ltv,
        }
