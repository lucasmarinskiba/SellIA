"""Financing Advisor Agent — Mortgage options, financing structures."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class MortgageOption:
    """Mortgage product option."""

    product_name: str
    interest_rate: float
    loan_amount: float
    term_years: int
    monthly_payment: float
    total_interest: float
    points: float = 0.0
    arm: bool = False  # Adjustable rate mortgage
    down_payment_required: float = 0.0


class FinancingAdvisorAgent:
    """Guide buyers through financing options."""

    def __init__(self):
        self.financing_plans: Dict[str, Dict[str, Any]] = {}

    def calculate_mortgage_options(self, purchase_price: float, down_payment_pct: float, credit_score: int) -> List[MortgageOption]:
        """Calculate mortgage options based on buyer profile."""
        down_payment = purchase_price * (down_payment_pct / 100)
        loan_amount = purchase_price - down_payment

        # Estimate interest rate based on credit score
        base_rate = self._estimate_interest_rate(credit_score)

        options = []

        # 30-year fixed (most common)
        monthly_30yr = self._calculate_monthly_payment(loan_amount, base_rate, 360)
        total_interest_30yr = (monthly_30yr * 360) - loan_amount
        options.append(
            MortgageOption(
                product_name="30-Year Fixed",
                interest_rate=base_rate,
                loan_amount=loan_amount,
                term_years=30,
                monthly_payment=monthly_30yr,
                total_interest=total_interest_30yr,
                down_payment_required=down_payment,
            )
        )

        # 15-year fixed
        rate_15yr = base_rate - 0.25  # Usually lower
        monthly_15yr = self._calculate_monthly_payment(loan_amount, rate_15yr, 180)
        total_interest_15yr = (monthly_15yr * 180) - loan_amount
        options.append(
            MortgageOption(
                product_name="15-Year Fixed",
                interest_rate=rate_15yr,
                loan_amount=loan_amount,
                term_years=15,
                monthly_payment=monthly_15yr,
                total_interest=total_interest_15yr,
                down_payment_required=down_payment,
            )
        )

        # 5/1 ARM (Adjustable Rate Mortgage)
        arm_initial_rate = base_rate - 0.5
        monthly_arm = self._calculate_monthly_payment(loan_amount, arm_initial_rate, 360)
        options.append(
            MortgageOption(
                product_name="5/1 ARM",
                interest_rate=arm_initial_rate,
                loan_amount=loan_amount,
                term_years=30,
                monthly_payment=monthly_arm,
                total_interest=(monthly_arm * 60) + (self._calculate_monthly_payment(loan_amount, base_rate + 1.5, 300) * 300),
                arm=True,
                down_payment_required=down_payment,
            )
        )

        logger.info(f"Generated {len(options)} mortgage options")
        return options

    def _estimate_interest_rate(self, credit_score: int) -> float:
        """Estimate interest rate based on credit score."""
        if credit_score >= 760:
            return 6.5
        elif credit_score >= 700:
            return 6.8
        elif credit_score >= 660:
            return 7.2
        elif credit_score >= 620:
            return 7.8
        else:
            return 8.5  # Subprime

    def _calculate_monthly_payment(self, principal: float, annual_rate: float, num_payments: int) -> float:
        """Calculate monthly mortgage payment using amortization formula."""
        monthly_rate = annual_rate / 100 / 12
        if monthly_rate == 0:
            return principal / num_payments
        return principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / (((1 + monthly_rate) ** num_payments) - 1)

    def prequalify_buyer(self, buyer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prequalify buyer for financing."""
        monthly_income = buyer_data.get("monthly_income", 0)
        monthly_debts = buyer_data.get("monthly_debts", 0)
        down_payment_savings = buyer_data.get("down_payment_savings", 0)
        credit_score = buyer_data.get("credit_score", 650)

        # Calculate maximum affordable price
        dti_ratio = 0.43  # Debt-to-income limit
        max_monthly_payment = (monthly_income * dti_ratio) - monthly_debts

        # Convert monthly payment to max loan amount (using 7% rate, 360 months)
        max_loan = max_monthly_payment / (0.07 / 12 * (1 + 0.07 / 12) ** 360 / (((1 + 0.07 / 12) ** 360) - 1))

        # Add down payment
        max_purchase_price = max_loan + down_payment_savings

        return {
            "buyer_id": buyer_data.get("buyer_id"),
            "prequalified": credit_score >= 620,
            "max_purchase_price": max_purchase_price,
            "max_loan_amount": max_loan,
            "credit_score": credit_score,
            "monthly_payment_capacity": max_monthly_payment,
            "dti_ratio": (monthly_debts + max_monthly_payment) / monthly_income,
            "recommendations": self._get_financing_recommendations(credit_score, buyer_data),
        }

    def _get_financing_recommendations(self, credit_score: int, buyer_data: Dict[str, Any]) -> List[str]:
        """Get financing recommendations for buyer."""
        recommendations = []

        if credit_score < 620:
            recommendations.append("Credit score too low - work on improving credit before applying")
        elif credit_score < 660:
            recommendations.append("Credit score could be improved - aim for 660+ for better rates")

        monthly_debts = buyer_data.get("monthly_debts", 0)
        if monthly_debts > buyer_data.get("monthly_income", 0) * 0.35:
            recommendations.append("Pay down existing debts to improve debt-to-income ratio")

        if buyer_data.get("down_payment_savings", 0) < buyer_data.get("target_price", 300000) * 0.15:
            recommendations.append("Save more for down payment to avoid PMI (private mortgage insurance)")

        if not recommendations:
            recommendations.append("You are in good position for favorable financing terms")

        return recommendations

    def estimate_closing_costs(self, purchase_price: float) -> Dict[str, float]:
        """Estimate closing costs (typically 2-5% of purchase price)."""
        return {
            "loan_origination": purchase_price * 0.01,
            "appraisal": 500,
            "credit_report": 50,
            "title_search": 150,
            "title_insurance": purchase_price * 0.006,
            "home_inspection": 400,
            "survey": 250,
            "homeowners_insurance": 1200,
            "property_taxes_escrow": purchase_price * 0.01,
            "hoa_transfer": 150,
            "misc_fees": 500,
            "total": purchase_price * 0.035,  # Average 3.5%
        }

    def calculate_affordability(self, annual_income: float, monthly_debts: float, down_payment: float) -> Dict[str, Any]:
        """Calculate home affordability."""
        monthly_income = annual_income / 12
        max_monthly_payment = (monthly_income * 0.43) - monthly_debts

        # Estimated loan amount at 7% for 30 years
        max_loan = max_monthly_payment / 0.00665  # Rough estimate

        return {
            "annual_income": annual_income,
            "max_home_price": max_loan + down_payment,
            "monthly_payment_capacity": max_monthly_payment,
            "debt_to_income_ratio": (monthly_debts + max_monthly_payment) / monthly_income,
        }
