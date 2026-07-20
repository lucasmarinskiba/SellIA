"""Financial Analysis — Budgeting, Costs, Cash Flow, Sensitivity Analysis."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class CostType(str, Enum):
    FIXED = "fixed"
    VARIABLE = "variable"
    SEMI_VARIABLE = "semi_variable"


@dataclass
class CostItem:
    """Single cost line item."""

    name: str
    cost_type: CostType
    monthly_amount: float
    annual_amount: Optional[float] = None
    category: str = "general"
    is_recurring: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def get_annual_cost(self) -> float:
        """Calculate annual cost."""
        if self.annual_amount:
            return self.annual_amount
        return self.monthly_amount * 12


@dataclass
class RevenueItem:
    """Single revenue line item."""

    name: str
    monthly_amount: float
    growth_rate: float = 0.0  # Monthly growth rate
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def get_annual_revenue(self) -> float:
        """Calculate annual revenue."""
        # Account for growth
        total = 0
        for month in range(12):
            total += self.monthly_amount * (1 + self.growth_rate) ** month
        return total


class BudgetPlanner:
    """Project costs, revenue, and identify breakeven point."""

    def __init__(self, currency: str = "USD"):
        self.currency = currency
        self.costs: Dict[str, CostItem] = {}
        self.revenues: Dict[str, RevenueItem] = {}
        self.budget_periods: List[Dict[str, Any]] = []

    def add_cost(self, cost: CostItem) -> None:
        """Add cost item."""
        self.costs[cost.name] = cost
        logger.info(f"Added cost: {cost.name} ({cost.cost_type.value})")

    def add_revenue(self, revenue: RevenueItem) -> None:
        """Add revenue item."""
        self.revenues[revenue.name] = revenue
        logger.info(f"Added revenue: {revenue.name}")

    def project_budget(self, months: int = 12) -> Dict[str, Any]:
        """Project budget for specified months."""
        monthly_budgets = []
        cumulative_profit = 0

        for month in range(months):
            month_date = datetime.utcnow() + timedelta(days=30 * month)

            # Calculate costs
            total_costs = 0
            for cost in self.costs.values():
                if self._is_active(cost.start_date, cost.end_date, month_date):
                    total_costs += cost.monthly_amount

            # Calculate revenues
            total_revenue = 0
            for i, revenue in enumerate(self.revenues.values()):
                if self._is_active(revenue.start_date, revenue.end_date, month_date):
                    monthly_revenue = revenue.monthly_amount * (1 + revenue.growth_rate) ** month
                    total_revenue += monthly_revenue

            profit = total_revenue - total_costs
            cumulative_profit += profit

            monthly_budgets.append({
                "month": month + 1,
                "date": month_date.isoformat(),
                "revenue": float(total_revenue),
                "costs": float(total_costs),
                "profit": float(profit),
                "cumulative_profit": float(cumulative_profit),
            })

        self.budget_periods = monthly_budgets

        return {
            "currency": self.currency,
            "months": months,
            "monthly_budgets": monthly_budgets,
            "total_revenue": float(sum(b["revenue"] for b in monthly_budgets)),
            "total_costs": float(sum(b["costs"] for b in monthly_budgets)),
            "net_profit": float(cumulative_profit),
            "breakeven_month": self._find_breakeven_month(monthly_budgets),
        }

    def _is_active(self, start_date: Optional[datetime], end_date: Optional[datetime], check_date: datetime) -> bool:
        """Check if item is active on given date."""
        if start_date and check_date < start_date:
            return False
        if end_date and check_date > end_date:
            return False
        return True

    def _find_breakeven_month(self, monthly_budgets: List[Dict[str, Any]]) -> Optional[int]:
        """Find month when cumulative profit becomes positive."""
        for i, budget in enumerate(monthly_budgets):
            if budget["cumulative_profit"] >= 0:
                return i + 1
        return None


class CostAnalyzer:
    """Analyze fixed, variable, and marginal costs."""

    def __init__(self):
        self.cost_data: List[Tuple[float, float]] = []  # (units, cost)
        self.fixed_costs: float = 0.0
        self.variable_cost_per_unit: float = 0.0

    def add_cost_observation(self, units_produced: float, total_cost: float) -> None:
        """Add cost observation."""
        self.cost_data.append((units_produced, total_cost))

    def analyze_costs(self) -> Dict[str, Any]:
        """Analyze cost structure."""
        if len(self.cost_data) < 2:
            return {"error": "Need at least 2 observations"}

        units = np.array([u for u, _ in self.cost_data])
        costs = np.array([c for _, c in self.cost_data])

        # Linear regression to separate fixed and variable costs
        coefficients = np.polyfit(units, costs, 1)
        variable_cost = coefficients[0]
        fixed_cost = coefficients[1]

        # Calculate R-squared
        predicted_costs = variable_cost * units + fixed_cost
        ss_res = np.sum((costs - predicted_costs) ** 2)
        ss_tot = np.sum((costs - np.mean(costs)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        self.fixed_costs = float(fixed_cost)
        self.variable_cost_per_unit = float(variable_cost)

        return {
            "fixed_costs": float(fixed_cost),
            "variable_cost_per_unit": float(variable_cost),
            "r_squared": float(r_squared),
            "total_observations": len(self.cost_data),
            "cost_function": f"TC = {fixed_cost:.2f} + {variable_cost:.2f}Q",
        }

    def calculate_marginal_cost(self, units: float) -> float:
        """Calculate marginal cost (derivative of cost function)."""
        # For linear cost function, marginal cost = variable cost per unit
        return self.variable_cost_per_unit

    def calculate_average_cost(self, units: float) -> float:
        """Calculate average cost per unit."""
        if units <= 0:
            return 0.0
        return (self.fixed_costs + self.variable_cost_per_unit * units) / units


class ProfitMarginCalculator:
    """Calculate gross/net margins, ROI, payback period."""

    def __init__(self):
        self.transactions: List[Dict[str, float]] = []

    def add_transaction(self, revenue: float, cost_of_goods: float, operating_expenses: float, taxes: float = 0.0) -> None:
        """Add transaction for analysis."""
        self.transactions.append({
            "revenue": revenue,
            "cogs": cost_of_goods,
            "opex": operating_expenses,
            "taxes": taxes,
        })

    def gross_profit_margin(self) -> float:
        """Calculate gross profit margin."""
        if not self.transactions:
            return 0.0

        total_revenue = sum(t["revenue"] for t in self.transactions)
        total_cogs = sum(t["cogs"] for t in self.transactions)

        if total_revenue <= 0:
            return 0.0

        return ((total_revenue - total_cogs) / total_revenue) * 100

    def operating_profit_margin(self) -> float:
        """Calculate operating profit margin."""
        if not self.transactions:
            return 0.0

        total_revenue = sum(t["revenue"] for t in self.transactions)
        total_cogs = sum(t["cogs"] for t in self.transactions)
        total_opex = sum(t["opex"] for t in self.transactions)

        if total_revenue <= 0:
            return 0.0

        operating_profit = total_revenue - total_cogs - total_opex
        return (operating_profit / total_revenue) * 100

    def net_profit_margin(self) -> float:
        """Calculate net profit margin."""
        if not self.transactions:
            return 0.0

        total_revenue = sum(t["revenue"] for t in self.transactions)
        total_expenses = sum(t["cogs"] + t["opex"] + t["taxes"] for t in self.transactions)

        if total_revenue <= 0:
            return 0.0

        return ((total_revenue - total_expenses) / total_revenue) * 100

    def calculate_roi(self, initial_investment: float, profit: float, years: int = 1) -> float:
        """Calculate return on investment."""
        if initial_investment <= 0:
            return 0.0
        return (profit / initial_investment) * 100

    def payback_period(self, initial_investment: float, monthly_profit: float) -> Optional[float]:
        """Calculate payback period in months."""
        if monthly_profit <= 0:
            return None
        return initial_investment / monthly_profit


class AssetsLiabilitiesTracker:
    """Track balance sheet (assets, liabilities, equity)."""

    def __init__(self):
        self.assets: Dict[str, float] = {}
        self.liabilities: Dict[str, float] = {}
        self.equity: Dict[str, float] = {}
        self.snapshots: List[Dict[str, Any]] = []

    def add_asset(self, name: str, value: float) -> None:
        """Add asset."""
        self.assets[name] = value

    def add_liability(self, name: str, value: float) -> None:
        """Add liability."""
        self.liabilities[name] = value

    def add_equity(self, name: str, value: float) -> None:
        """Add equity."""
        self.equity[name] = value

    def get_balance_sheet(self) -> Dict[str, Any]:
        """Generate balance sheet."""
        total_assets = sum(self.assets.values())
        total_liabilities = sum(self.liabilities.values())
        total_equity = sum(self.equity.values())

        # Verify accounting equation: Assets = Liabilities + Equity
        balance_check = abs(total_assets - (total_liabilities + total_equity))

        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "assets": {"items": self.assets, "total": float(total_assets)},
            "liabilities": {"items": self.liabilities, "total": float(total_liabilities)},
            "equity": {"items": self.equity, "total": float(total_equity)},
            "balanced": bool(balance_check < 1.0),  # Allow for rounding
        }

        self.snapshots.append(snapshot)
        return snapshot

    def calculate_financial_ratios(self) -> Dict[str, float]:
        """Calculate key financial ratios."""
        total_assets = sum(self.assets.values())
        total_liabilities = sum(self.liabilities.values())
        total_equity = sum(self.equity.values())

        if total_assets <= 0 or total_equity <= 0:
            return {}

        return {
            "debt_to_equity": float(total_liabilities / total_equity) if total_equity > 0 else 0,
            "debt_to_assets": float(total_liabilities / total_assets),
            "equity_ratio": float(total_equity / total_assets),
            "asset_turnover": 1.0,  # Would need revenue data
        }


class CashFlowProjector:
    """Project monthly, quarterly, annual cash flows."""

    def __init__(self):
        self.cash_inflows: List[Dict[str, Any]] = []
        self.cash_outflows: List[Dict[str, Any]] = []
        self.starting_balance: float = 0.0

    def set_starting_balance(self, amount: float) -> None:
        """Set initial cash balance."""
        self.starting_balance = amount

    def add_inflow(self, name: str, amount: float, frequency: str = "monthly", start_month: int = 1) -> None:
        """Add cash inflow."""
        self.cash_inflows.append({
            "name": name,
            "amount": amount,
            "frequency": frequency,
            "start_month": start_month,
        })

    def add_outflow(self, name: str, amount: float, frequency: str = "monthly", start_month: int = 1) -> None:
        """Add cash outflow."""
        self.cash_outflows.append({
            "name": name,
            "amount": amount,
            "frequency": frequency,
            "start_month": start_month,
        })

    def project(self, months: int = 12) -> Dict[str, Any]:
        """Project cash flow."""
        cash_balance = self.starting_balance
        monthly_flows = []

        for month in range(1, months + 1):
            inflows = self._calculate_period_inflows(month)
            outflows = self._calculate_period_outflows(month)
            net_flow = inflows - outflows
            cash_balance += net_flow

            monthly_flows.append({
                "month": month,
                "inflows": float(inflows),
                "outflows": float(outflows),
                "net_flow": float(net_flow),
                "ending_balance": float(cash_balance),
            })

        # Calculate metrics
        min_balance = min(mf["ending_balance"] for mf in monthly_flows)
        total_inflows = sum(mf["inflows"] for mf in monthly_flows)
        total_outflows = sum(mf["outflows"] for mf in monthly_flows)

        return {
            "starting_balance": float(self.starting_balance),
            "monthly_flows": monthly_flows,
            "ending_balance": float(cash_balance),
            "total_inflows": float(total_inflows),
            "total_outflows": float(total_outflows),
            "net_cash_flow": float(cash_balance - self.starting_balance),
            "minimum_balance": float(min_balance),
            "is_negative_at_any_point": min_balance < 0,
        }

    def _calculate_period_inflows(self, month: int) -> float:
        """Calculate total inflows for a month."""
        total = 0
        for inflow in self.cash_inflows:
            if month >= inflow["start_month"]:
                if inflow["frequency"] == "monthly":
                    total += inflow["amount"]
                elif inflow["frequency"] == "quarterly" and month % 3 == 0:
                    total += inflow["amount"]
                elif inflow["frequency"] == "annual" and month == 12:
                    total += inflow["amount"]
        return total

    def _calculate_period_outflows(self, month: int) -> float:
        """Calculate total outflows for a month."""
        total = 0
        for outflow in self.cash_outflows:
            if month >= outflow["start_month"]:
                if outflow["frequency"] == "monthly":
                    total += outflow["amount"]
                elif outflow["frequency"] == "quarterly" and month % 3 == 0:
                    total += outflow["amount"]
                elif outflow["frequency"] == "annual" and month == 12:
                    total += outflow["amount"]
        return total


class SensitivityAnalyzer:
    """What-if scenarios and sensitivity analysis."""

    def __init__(self):
        self.base_case: Dict[str, float] = {}
        self.scenarios: Dict[str, Dict[str, float]] = {}

    def set_base_case(self, variables: Dict[str, float]) -> None:
        """Set baseline assumptions."""
        self.base_case = variables.copy()

    def create_scenario(self, name: str, variables: Dict[str, float]) -> None:
        """Create alternative scenario."""
        self.scenarios[name] = variables.copy()

    def analyze_sensitivity(self, outcome_fn: callable, variable: str, range_pct: float = 0.2) -> Dict[str, Any]:
        """Analyze impact of variable on outcome."""
        if not self.base_case:
            return {"error": "Base case not set"}

        base_value = self.base_case.get(variable, 0)
        if base_value <= 0:
            return {"error": f"Invalid base value for {variable}"}

        results = []

        for pct_change in np.linspace(-range_pct, range_pct, 11):
            test_vars = self.base_case.copy()
            test_vars[variable] = base_value * (1 + pct_change)
            outcome = outcome_fn(test_vars)

            results.append({
                "change_percent": float(pct_change * 100),
                "variable_value": float(test_vars[variable]),
                "outcome": float(outcome),
            })

        # Calculate elasticity
        base_outcome = outcome_fn(self.base_case)
        elasticities = []
        for result in results[1:]:
            outcome_change = (result["outcome"] - base_outcome) / base_outcome if base_outcome != 0 else 0
            variable_change = result["change_percent"] / 100
            elasticity = outcome_change / variable_change if variable_change != 0 else 0
            elasticities.append(elasticity)

        return {
            "variable": variable,
            "base_value": float(base_value),
            "base_outcome": float(base_outcome),
            "results": results,
            "elasticity": float(np.mean(elasticities)) if elasticities else 0,
            "sensitivity_level": "high" if abs(np.mean(elasticities)) > 1 else "moderate" if abs(np.mean(elasticities)) > 0.5 else "low",
        }

    def scenario_comparison(self, outcome_fn: callable) -> Dict[str, Any]:
        """Compare outcomes across scenarios."""
        if not self.base_case:
            return {"error": "Base case not set"}

        results = {"base_case": {"outcome": float(outcome_fn(self.base_case))}}

        for name, variables in self.scenarios.items():
            results[name] = {"outcome": float(outcome_fn(variables)), "variables": variables}

        return results
