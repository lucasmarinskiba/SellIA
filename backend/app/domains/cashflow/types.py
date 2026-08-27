"""Cash-flow forecast types."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class CashFlowAssumptions:
    """Input assumptions for cash projection."""
    avg_payment_delay_days: int  # days after sale before cash received
    cogs_pct_revenue: Decimal  # cost of goods as % of revenue
    opex_daily: Decimal  # fixed daily operating expense
    tax_rate: Decimal = Decimal("0.21")  # Argentina default
    beginning_balance: Decimal = Decimal("0")


@dataclass
class CashFlowPoint:
    """Day-level cash forecast point."""
    date: date
    revenue_forecast: Decimal
    cogs_forecast: Decimal
    opex: Decimal
    tax_provision: Decimal  # incremental tax on profit
    inflow_from_prior_sales: Decimal  # cash collected from old orders
    operating_cash_flow: Decimal  # revenue - cogs - opex - tax
    net_cash_flow: Decimal  # OCF + inflow - operating balance adj
    cumulative_balance: Decimal
    confidence_q10: Decimal  # conservative (low) cash scenario
    confidence_q90: Decimal  # optimistic (high) cash scenario


@dataclass
class CashFlowForecast:
    """Complete cash projection for a horizon."""
    business_id: str
    start_date: date
    horizon_days: int
    points: list[CashFlowPoint]
    beginning_balance: Decimal
    end_balance: Decimal
    min_balance: Decimal
    max_balance: Decimal
    min_balance_date: date
    runway_days: Optional[int]  # days until zero if negative burn
    assumptions: CashFlowAssumptions
    computed_at: datetime
