"""Negotiation Strategies — Proveedores, clientes, empleados."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class NegotiationType(str, Enum):
    """Negotiation context types."""
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"


@dataclass
class NegotiationContext:
    """Context for negotiation."""
    negotiation_type: NegotiationType
    counterparty: str  # Name of supplier/customer/employee
    current_terms: Dict[str, Any]  # Current agreement terms
    target_outcomes: Dict[str, Any]  # What we want to achieve
    constraints: List[str]  # What we can't do


@dataclass
class OptimalTerms:
    """Recommended negotiation terms."""
    price: float
    payment_terms: str  # 30/60/90 days, etc.
    volume_commitment: str
    exclusivity: bool
    contract_duration_months: int
    additional_benefits: List[str]
    reasoning: str


@dataclass
class OptimalDeal:
    """Recommended customer deal structure."""
    product_bundle: List[str]
    price: float
    payment_plan: str  # One-time, monthly, custom
    risk_reversal: str  # Money-back guarantee, trial, etc.
    scarcity_element: Optional[str]  # Limited spots, expiring offer
    upsell_opportunity: Optional[str]
    expected_close_rate: float
    reasoning: str


@dataclass
class OptimalPackage:
    """Recommended employee compensation package."""
    base_salary: float
    equity_percent: float
    equity_vest_months: int
    bonus_percent: float
    remote_flexibility: bool
    pto_days: int
    growth_path: str
    benefits: List[str]
    total_comp_value: float


class NegotiationStrategist:
    """Strategist for negotiating with suppliers, customers, and employees."""

    def __init__(self):
        """Initialize negotiation strategist."""
        pass

    def supplier_negotiation(
        self,
        supplier_name: str,
        current_terms: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> OptimalTerms:
        """
        Negotiate better supplier terms.

        Focuses on:
        - Volume discounts (buy more → price drops)
        - Payment terms (30/60/90 days vs cash)
        - Commitment (annual vs month-to-month)
        - Exclusivity (single vs multi-vendor)

        Args:
            supplier_name: Name of supplier
            current_terms: Current contract terms
            business_profile: Business profile for context

        Returns:
            Recommended negotiated terms
        """
        logger.info(f"Negotiating with supplier: {supplier_name}")

        # Determine leverage based on volume
        annual_spend = current_terms.get("annual_spend", 0)
        volume_leverage = self._calculate_volume_leverage(annual_spend)

        # Determine price opportunity
        current_price = current_terms.get("unit_price", 0)
        negotiated_price = self._calculate_negotiated_price(
            current_price,
            volume_leverage,
            current_terms.get("order_volume", 0),
        )

        # Determine payment terms
        current_payment_terms = current_terms.get("payment_terms", "Net 30")
        negotiated_payment_terms = self._negotiate_payment_terms(
            current_payment_terms,
            volume_leverage,
            annual_spend,
        )

        # Determine commitment strategy
        commitment = self._optimize_commitment_strategy(
            annual_spend,
            business_profile.stage,
        )

        # Determine exclusivity
        exclusivity = self._evaluate_exclusivity(
            supplier_name,
            business_profile,
            current_terms,
        )

        return OptimalTerms(
            price=negotiated_price,
            payment_terms=negotiated_payment_terms,
            volume_commitment=commitment,
            exclusivity=exclusivity,
            contract_duration_months=12 if exclusivity else 6,
            additional_benefits=[
                "Volume discount on future orders",
                "Priority support",
                "Early access to new products" if volume_leverage > 1.5 else "",
            ],
            reasoning=f"Volume leverage {volume_leverage:.1f}x justifies price reduction. "
            f"Payment terms improve cash flow. "
            f"Commitment ensures relationship stability.",
        )

    def customer_negotiation(
        self,
        customer_name: str,
        customer_data: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> OptimalDeal:
        """
        Structure offer for maximum conversion.

        Focuses on:
        - Bundle products → higher AOV, better deal
        - Payment plans → reduce friction, increase close rate
        - Risk reversal → money-back guarantee, trial period
        - Scarcity → limited spots, expiring offer

        Args:
            customer_name: Customer name
            customer_data: Customer profile (budget, needs, etc.)
            business_profile: Business profile

        Returns:
            Recommended deal structure
        """
        logger.info(f"Structuring deal for customer: {customer_name}")

        # Determine bundle opportunity
        product_bundle = self._build_customer_bundle(
            customer_data.get("needs", []),
            customer_data.get("budget", 0),
        )

        # Calculate bundle price
        base_price = customer_data.get("budget", 5000)
        bundle_price = self._calculate_bundle_price(
            product_bundle,
            base_price,
            business_profile,
        )

        # Determine payment plan
        payment_plan = self._optimize_payment_plan(
            bundle_price,
            customer_data.get("budget", 0),
            customer_data.get("payment_frequency", "monthly"),
        )

        # Determine risk reversal
        risk_reversal = self._select_risk_reversal(
            customer_data.get("risk_level", "medium"),
            product_bundle,
        )

        # Determine scarcity element
        scarcity = self._create_scarcity_element(
            customer_data.get("decision_speed", "slow"),
        )

        # Determine upsell opportunity
        upsell = self._identify_upsell_opportunity(
            customer_data.get("needs", []),
            product_bundle,
        )

        # Estimate close rate
        close_rate = self._estimate_close_rate(
            risk_reversal,
            scarcity,
            payment_plan,
        )

        return OptimalDeal(
            product_bundle=product_bundle,
            price=bundle_price,
            payment_plan=payment_plan,
            risk_reversal=risk_reversal,
            scarcity_element=scarcity,
            upsell_opportunity=upsell,
            expected_close_rate=close_rate,
            reasoning=f"Bundle reduces friction and increases AOV. "
            f"Payment plan lowers barrier to entry. "
            f"Risk reversal removes objections. "
            f"Expected close rate: {close_rate:.0%}",
        )

    def employee_negotiation(
        self,
        employee_name: str,
        employee_data: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> OptimalPackage:
        """
        Structure compensation to retain talent without burning cash.

        Focuses on:
        - Base salary vs equity vs options
        - Remote/flexibility
        - Growth path (title, responsibility)
        - Benefits (health, 401k, PTO)

        Args:
            employee_name: Employee name
            employee_data: Employee profile (salary expectations, role, etc.)
            business_profile: Business profile

        Returns:
            Recommended compensation package
        """
        logger.info(f"Structuring package for employee: {employee_name}")

        # Determine salary
        market_salary = employee_data.get("market_salary", 80000)
        affordable_salary = self._calculate_affordable_salary(
            business_profile,
            employee_data.get("seniority", "mid"),
        )
        final_salary = min(market_salary, affordable_salary)

        # Determine equity
        equity_percent, vest_months = self._optimize_equity(
            business_profile,
            employee_data.get("seniority", "mid"),
        )

        # Determine bonus
        bonus_percent = self._determine_bonus(
            employee_data.get("seniority", "mid"),
            business_profile.stage,
        )

        # Determine remote flexibility
        remote = employee_data.get("remote_required", False)

        # Determine PTO
        pto_days = self._determine_pto(business_profile.stage)

        # Determine growth path
        growth_path = self._create_growth_path(employee_data.get("role", ""))

        # Determine benefits
        benefits = self._select_benefits(business_profile.stage)

        # Calculate total comp
        total_comp = final_salary + (final_salary * bonus_percent) + (equity_percent * 100000)

        return OptimalPackage(
            base_salary=final_salary,
            equity_percent=equity_percent,
            equity_vest_months=vest_months,
            bonus_percent=bonus_percent,
            remote_flexibility=remote,
            pto_days=pto_days,
            growth_path=growth_path,
            benefits=benefits,
            total_comp_value=total_comp,
        )

    # Private helper methods

    def _calculate_volume_leverage(self, annual_spend: float) -> float:
        """Calculate negotiation leverage from volume."""
        if annual_spend > 1_000_000:
            return 2.0
        elif annual_spend > 500_000:
            return 1.75
        elif annual_spend > 100_000:
            return 1.5
        elif annual_spend > 50_000:
            return 1.25
        else:
            return 1.0

    def _calculate_negotiated_price(
        self,
        current_price: float,
        volume_leverage: float,
        order_volume: int,
    ) -> float:
        """Calculate negotiated price."""
        discount_percent = min((volume_leverage - 1.0) * 0.15, 0.25)  # 0-25% discount
        return current_price * (1 - discount_percent)

    def _negotiate_payment_terms(
        self,
        current_terms: str,
        volume_leverage: float,
        annual_spend: float,
    ) -> str:
        """Negotiate payment terms."""
        if volume_leverage > 1.5 and annual_spend > 500_000:
            return "Net 60"
        elif volume_leverage > 1.2:
            return "Net 45"
        else:
            return current_terms

    def _optimize_commitment_strategy(self, annual_spend: float, stage: str) -> str:
        """Determine optimal commitment level."""
        if stage in ["startup", "growth"]:
            return "Quarterly with annual discount option"
        else:
            return "Annual with quarterly reviews"

    def _evaluate_exclusivity(
        self,
        supplier_name: str,
        business_profile: "BusinessProfile",
        current_terms: Dict[str, Any],
    ) -> bool:
        """Evaluate whether exclusivity makes sense."""
        # Only commit to exclusivity if:
        # - Supplier is strategic
        # - We have leverage
        # - We get significant price concession
        return current_terms.get("strategic", False)

    def _build_customer_bundle(self, needs: List[str], budget: float) -> List[str]:
        """Build product bundle based on customer needs."""
        bundle = []

        if "core" in str(needs).lower():
            bundle.append("Core Product")
        if "support" in str(needs).lower():
            bundle.append("Premium Support")
        if "training" in str(needs).lower():
            bundle.append("Training & Onboarding")
        if "analytics" in str(needs).lower():
            bundle.append("Analytics Dashboard")

        return bundle or ["Core Product", "Standard Support"]

    def _calculate_bundle_price(
        self,
        bundle: List[str],
        base_price: float,
        business_profile: "BusinessProfile",
    ) -> float:
        """Calculate bundle price with appropriate markup."""
        bundle_multiplier = 1.0 + (len(bundle) - 1) * 0.25  # Each item adds 25%
        return base_price * bundle_multiplier

    def _optimize_payment_plan(
        self,
        total_price: float,
        customer_budget: float,
        frequency: str,
    ) -> str:
        """Optimize payment plan for conversion."""
        if total_price > customer_budget * 2:
            return f"6 monthly installments of ${total_price / 6:.0f}"
        elif total_price > customer_budget:
            return f"3 monthly installments of ${total_price / 3:.0f}"
        else:
            return f"One-time payment of ${total_price:.0f}"

    def _select_risk_reversal(self, risk_level: str, bundle: List[str]) -> str:
        """Select risk reversal strategy."""
        if risk_level == "high":
            return "30-day money-back guarantee, no questions asked"
        elif risk_level == "medium":
            return "14-day trial period"
        else:
            return "Satisfaction guarantee"

    def _create_scarcity_element(self, decision_speed: str) -> Optional[str]:
        """Create appropriate scarcity element."""
        if decision_speed == "fast":
            return None  # Already decided
        elif decision_speed == "slow":
            return "Offer valid for 7 days (expires Friday)"
        else:
            return "Only 3 spots remaining at this price"

    def _identify_upsell_opportunity(
        self,
        needs: List[str],
        bundle: List[str],
    ) -> Optional[str]:
        """Identify natural upsell opportunity."""
        if "training" not in bundle:
            return "Advanced Training Program (+$999)"
        elif "analytics" not in bundle:
            return "Advanced Analytics & Reporting (+$499)"
        else:
            return None

    def _estimate_close_rate(
        self,
        risk_reversal: str,
        scarcity: Optional[str],
        payment_plan: str,
    ) -> float:
        """Estimate close rate based on deal structure."""
        base_rate = 0.20
        if risk_reversal:
            base_rate += 0.15
        if scarcity:
            base_rate += 0.10
        if "monthly" in payment_plan:
            base_rate += 0.10
        return min(base_rate, 0.60)

    def _calculate_affordable_salary(self, business_profile: "BusinessProfile", seniority: str) -> float:
        """Calculate what we can afford to pay."""
        annual_revenue = business_profile.financials.annual_revenue
        payroll_percent = 0.30 if business_profile.stage in ["startup", "growth"] else 0.35

        available_for_payroll = annual_revenue * payroll_percent
        # Divide by existing team to get per-person average
        per_person_budget = available_for_payroll / max(business_profile.team_size, 1)

        seniority_multiplier = {"junior": 0.8, "mid": 1.0, "senior": 1.3}
        return per_person_budget * seniority_multiplier.get(seniority, 1.0)

    def _optimize_equity(self, business_profile: "BusinessProfile", seniority: str) -> tuple:
        """Optimize equity grant."""
        if business_profile.stage == "startup":
            equity_ranges = {"junior": 0.10, "mid": 0.25, "senior": 0.50}
            vest_months = 48
        elif business_profile.stage == "growth":
            equity_ranges = {"junior": 0.05, "mid": 0.15, "senior": 0.30}
            vest_months = 48
        else:
            equity_ranges = {"junior": 0.01, "mid": 0.05, "senior": 0.10}
            vest_months = 36

        return equity_ranges.get(seniority, 0.1), vest_months

    def _determine_bonus(self, seniority: str, stage: str) -> float:
        """Determine bonus percentage."""
        if stage in ["startup", "growth"]:
            return 0.15 if seniority in ["mid", "senior"] else 0.05
        else:
            return 0.25 if seniority in ["mid", "senior"] else 0.10

    def _determine_pto(self, stage: str) -> int:
        """Determine PTO days based on stage."""
        return 25 if stage in ["scale", "mature"] else 20

    def _create_growth_path(self, role: str) -> str:
        """Create growth path description."""
        return f"6-month check-in → potential promotion to {role} lead within 12-18 months"

    def _select_benefits(self, stage: str) -> List[str]:
        """Select benefits package."""
        benefits = ["Health insurance", "401k matching (3%)"]

        if stage in ["scale", "mature"]:
            benefits.extend(["Gym membership", "Conference budget ($2k/year)", "Home office stipend"])

        return benefits
