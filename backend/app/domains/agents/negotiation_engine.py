"""Advanced Negotiation Engine - Dynamic pricing & contract optimization."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CompanySize(str, Enum):
    """Company size segments."""
    STARTUP = "startup"  # <50 employees
    SMB = "smb"  # 50-500
    MID_MARKET = "mid_market"  # 500-5000
    ENTERPRISE = "enterprise"  # 5000+


class NegotiationStrategy(str, Enum):
    """Negotiation strategy selection."""
    AGGRESSIVE = "aggressive"  # Max discount authority, aggressive closing
    BALANCED = "balanced"  # Standard playbook
    CONSERVATIVE = "conservative"  # Preserve margin, long-term value
    STRATEGIC = "strategic"  # Play for expansion potential


@dataclass
class PricingTier:
    """Pricing option presented to prospect."""
    name: str
    annual_price: float
    monthly_price: float
    features: List[str]
    discount_percent: float = 0.0
    payment_terms: str = "net_30"
    implementation_days: int = 30
    support_level: str = "standard"


@dataclass
class ContractTerms:
    """Contract negotiation parameters."""
    annual_price: float
    payment_schedule: str  # "monthly", "quarterly", "annual", "custom"
    contract_duration_months: int
    auto_renewal: bool
    support_level: str  # "standard", "premium", "enterprise"
    sla_uptime_percent: float  # 99.5, 99.9, etc
    implementation_included: bool
    training_hours_included: int
    legal_review_needed: bool


@dataclass
class DiscountAuthority:
    """Permission matrix for discounts by company size & deal stage."""
    company_size: CompanySize
    base_discount_max: float  # e.g., 0.20 = 20% max
    volume_bonus_threshold: float  # spending threshold for volume discount
    volume_bonus_max: float
    expansion_potential_multiplier: float  # if high expansion potential, allow more discount
    legal_review_threshold: float  # if discount > this, escalate to legal


class NegotiationEngine:
    """
    AI-driven negotiation logic:
    - Dynamic pricing based on intent, budget, company size
    - Contract term optimization
    - Discount authority enforcement
    - Strategy selection (aggressive/balanced/conservative)
    """

    def __init__(self):
        self.base_price = 75000  # Default annual price
        self.discount_authority_matrix = self._build_authority_matrix()

    def _build_authority_matrix(self) -> Dict[CompanySize, DiscountAuthority]:
        """Build discount authority rules by company size."""
        return {
            CompanySize.STARTUP: DiscountAuthority(
                company_size=CompanySize.STARTUP,
                base_discount_max=0.35,  # Up to 35% for startups
                volume_bonus_threshold=50000,
                volume_bonus_max=0.15,
                expansion_potential_multiplier=1.5,  # More flexibility if high expansion
                legal_review_threshold=0.30,
            ),
            CompanySize.SMB: DiscountAuthority(
                company_size=CompanySize.SMB,
                base_discount_max=0.20,
                volume_bonus_threshold=200000,
                volume_bonus_max=0.10,
                expansion_potential_multiplier=1.2,
                legal_review_threshold=0.25,
            ),
            CompanySize.MID_MARKET: DiscountAuthority(
                company_size=CompanySize.MID_MARKET,
                base_discount_max=0.15,
                volume_bonus_threshold=500000,
                volume_bonus_max=0.08,
                expansion_potential_multiplier=1.1,
                legal_review_threshold=0.15,
            ),
            CompanySize.ENTERPRISE: DiscountAuthority(
                company_size=CompanySize.ENTERPRISE,
                base_discount_max=0.10,
                volume_bonus_threshold=1000000,
                volume_bonus_max=0.05,
                expansion_potential_multiplier=1.05,
                legal_review_threshold=0.10,
            ),
        }

    async def estimate_company_size(
        self, employee_count: Optional[int] = None, company_name: Optional[str] = None
    ) -> CompanySize:
        """Estimate company size from employee count or name."""
        if employee_count:
            if employee_count < 50:
                return CompanySize.STARTUP
            elif employee_count < 500:
                return CompanySize.SMB
            elif employee_count < 5000:
                return CompanySize.MID_MARKET
            else:
                return CompanySize.ENTERPRISE

        # Default estimation (in production, call LinkedIn/Clearbit API)
        return CompanySize.SMB

    async def calculate_dynamic_pricing(
        self,
        intent_score: float,
        company_size: CompanySize,
        prospect_budget: Optional[float] = None,
        expansion_potential: float = 0.0,
        competitor_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate optimal pricing based on:
        - Intent score (0-1): higher intent = more flexibility
        - Company size: affects discount authority
        - Budget: respect prospect's budget range
        - Expansion potential: long-term value consideration
        - Competitor pricing: market positioning
        """
        authority = self.discount_authority_matrix[company_size]

        # Base discount from intent score
        intent_discount = 0.05 * intent_score  # 0-5% based on intent

        # Expansion bonus
        expansion_bonus = (
            authority.expansion_potential_multiplier - 1.0
        ) * expansion_potential  # up to 50% more flexibility

        # Calculate max allowed discount
        max_discount = min(
            authority.base_discount_max,
            (intent_discount + expansion_bonus),
        )

        # Adjust for prospect budget
        if prospect_budget and prospect_budget < self.base_price:
            # Prospect has lower budget, calculate achievable price
            max_price = prospect_budget
            actual_discount = max(0, 1.0 - (max_price / self.base_price))
            actual_discount = min(actual_discount, max_discount)
        else:
            actual_discount = max_discount

        # Calculate final price
        final_price = self.base_price * (1.0 - actual_discount)

        # Determine if legal review needed
        needs_legal = (
            actual_discount >= authority.legal_review_threshold
        )

        return {
            "base_price": self.base_price,
            "discount_percent": actual_discount * 100,
            "final_price": final_price,
            "intent_discount_contribution": intent_discount * 100,
            "expansion_bonus_contribution": expansion_bonus * 100,
            "max_allowed_discount": max_discount * 100,
            "needs_legal_review": needs_legal,
            "competitor_advantage": (
                f"{((competitor_price - final_price) / competitor_price * 100):.1f}%"
                if competitor_price
                else None
            ),
        }

    async def generate_pricing_tiers(
        self,
        final_price: float,
        company_size: CompanySize,
    ) -> List[PricingTier]:
        """Generate 3-tier pricing options (standard, professional, enterprise)."""
        discount = 1.0 - (final_price / self.base_price)

        tiers = [
            PricingTier(
                name="Standard",
                annual_price=final_price * 0.75,
                monthly_price=final_price * 0.75 / 12,
                features=["Core automation", "5 users", "Email support"],
                discount_percent=discount,
                payment_terms="monthly",
                support_level="standard",
                implementation_days=14,
            ),
            PricingTier(
                name="Professional",
                annual_price=final_price,
                monthly_price=final_price / 12,
                features=[
                    "Full automation",
                    "Unlimited users",
                    "Priority support",
                    "Custom workflows",
                ],
                discount_percent=discount,
                payment_terms="net_30",
                support_level="premium",
                implementation_days=30,
            ),
            PricingTier(
                name="Enterprise",
                annual_price=final_price * 1.5,
                monthly_price=final_price * 1.5 / 12,
                features=[
                    "Everything in Professional",
                    "Dedicated account manager",
                    "Custom integrations",
                    "SLA guarantee",
                    "Training included",
                ],
                discount_percent=discount * 0.8,  # Less discount for top tier
                payment_terms="net_60",
                support_level="enterprise",
                implementation_days=60,
            ),
        ]

        return tiers

    async def optimize_contract_terms(
        self,
        prospect_industry: str,
        company_size: CompanySize,
        annual_price: float,
        prospect_preferences: Optional[Dict[str, Any]] = None,
    ) -> ContractTerms:
        """
        Optimize contract terms based on industry, size, and price point.
        Returns recommended terms that maximize close probability + margin.
        """
        # Industry-based defaults
        default_duration = {
            "saas": 12,
            "software": 12,
            "enterprise": 36,
            "finance": 24,
            "healthcare": 24,
        }.get(prospect_industry.lower(), 12)

        # Company size defaults
        if company_size == CompanySize.ENTERPRISE:
            default_duration = max(default_duration, 36)
            support_level = "enterprise"
            sla_uptime = 99.99
            training_hours = 40
        elif company_size == CompanySize.MID_MARKET:
            support_level = "premium"
            sla_uptime = 99.9
            training_hours = 16
        else:
            support_level = "standard"
            sla_uptime = 99.5
            training_hours = 4

        # Determine payment schedule (longer contract → annual payment incentive)
        if default_duration >= 24:
            payment_schedule = "annual"
            price_adjustment = 1.0  # No discount for annual payment
        else:
            payment_schedule = "net_30"
            price_adjustment = 1.0

        # Override with prospect preferences if provided
        if prospect_preferences:
            default_duration = prospect_preferences.get(
                "preferred_duration_months", default_duration
            )
            support_level = prospect_preferences.get("support_level", support_level)

        return ContractTerms(
            annual_price=annual_price * price_adjustment,
            payment_schedule=payment_schedule,
            contract_duration_months=default_duration,
            auto_renewal=True,
            support_level=support_level,
            sla_uptime_percent=sla_uptime,
            implementation_included=company_size
            in [CompanySize.MID_MARKET, CompanySize.ENTERPRISE],
            training_hours_included=training_hours,
            legal_review_needed=company_size == CompanySize.ENTERPRISE,
        )

    async def select_negotiation_strategy(
        self,
        intent_score: float,
        company_size: CompanySize,
        expansion_potential: float,
        previous_objections_count: int = 0,
    ) -> NegotiationStrategy:
        """
        Select negotiation strategy based on deal characteristics:
        - High intent + high expansion = STRATEGIC (play for long-term value)
        - High intent + no expansion = AGGRESSIVE (close fast)
        - Low intent = CONSERVATIVE (preserve margin, low-touch)
        - Mid = BALANCED
        """
        # Scoring system
        score = 0.0

        # Intent contribution (0-3)
        score += intent_score * 3.0

        # Expansion contribution (0-3)
        score += expansion_potential * 3.0

        # Company size contribution (0-2)
        if company_size == CompanySize.ENTERPRISE:
            score += 2.0  # High priority
        elif company_size == CompanySize.MID_MARKET:
            score += 1.5
        elif company_size == CompanySize.SMB:
            score += 1.0

        # Objection count (negatively impacts)
        score -= previous_objections_count * 0.5

        # Strategy selection based on score
        if score >= 7.0 and expansion_potential > 0.7:
            return NegotiationStrategy.STRATEGIC
        elif score >= 6.0:
            return NegotiationStrategy.AGGRESSIVE
        elif score >= 4.0:
            return NegotiationStrategy.BALANCED
        else:
            return NegotiationStrategy.CONSERVATIVE

    async def get_strategy_playbook(
        self, strategy: NegotiationStrategy
    ) -> Dict[str, Any]:
        """Get negotiation tactics for selected strategy."""
        playbooks = {
            NegotiationStrategy.AGGRESSIVE: {
                "name": "Aggressive Close",
                "goal": "Fast close, maximize short-term revenue",
                "tactics": [
                    "Limited-time offer (48hr deadline)",
                    "Highlight competitors adopting solution",
                    "Emphasize ROI payback in 6 months",
                    "Fast implementation (2-week go-live)",
                ],
                "discount_authority": 0.20,
                "follow_up_cadence_hours": 4,
                "escalation_triggers": ["no response in 24h", "price objection"],
            },
            NegotiationStrategy.BALANCED: {
                "name": "Balanced Approach",
                "goal": "Fair deal structure, sustainable relationship",
                "tactics": [
                    "Multi-tier options (let prospect choose)",
                    "Flexible payment terms (quarterly option)",
                    "Standard 30-day implementation",
                    "Reference customer calls",
                ],
                "discount_authority": 0.15,
                "follow_up_cadence_hours": 24,
                "escalation_triggers": ["no response in 3 days", "budget concern"],
            },
            NegotiationStrategy.STRATEGIC: {
                "name": "Strategic Partnership",
                "goal": "Long-term expansion, account penetration",
                "tactics": [
                    "Pilot program (lower initial commit)",
                    "Expansion roadmap (multi-year value)",
                    "Executive sponsor engagement",
                    "Joint success metrics",
                    "Annual reviews with growth targets",
                ],
                "discount_authority": 0.25,
                "follow_up_cadence_hours": 48,
                "escalation_triggers": ["no executive engagement", "scope creep"],
            },
            NegotiationStrategy.CONSERVATIVE: {
                "name": "Margin Preservation",
                "goal": "Maintain price integrity, filter for fit",
                "tactics": [
                    "Full-price emphasis (premium positioning)",
                    "ROI calculator showing high payback",
                    "Focus on risk of not implementing",
                    "Peer benchmarking (other companies pay X)",
                ],
                "discount_authority": 0.08,
                "follow_up_cadence_hours": 72,
                "escalation_triggers": ["budget hard constraint", "competitor win"],
            },
        }
        return playbooks.get(strategy, playbooks[NegotiationStrategy.BALANCED])
