"""Cash-flow forecasting — types + service smoke tests."""

from decimal import Decimal
from datetime import date

from app.domains.cashflow.types import CashFlowAssumptions, CashFlowPoint


def test_cashflow_assumptions():
    """Verify assumptions structure."""
    a = CashFlowAssumptions(
        avg_payment_delay_days=3,
        cogs_pct_revenue=Decimal("0.35"),
        opex_daily=Decimal("500.00"),
    )
    assert a.avg_payment_delay_days == 3
    assert a.cogs_pct_revenue == Decimal("0.35")
    assert a.tax_rate == Decimal("0.21")


def test_cashflow_point():
    """Verify point structure."""
    today = date.today()
    p = CashFlowPoint(
        date=today,
        revenue_forecast=Decimal("1000.00"),
        cogs_forecast=Decimal("350.00"),
        opex=Decimal("100.00"),
        tax_provision=Decimal("112.50"),
        inflow_from_prior_sales=Decimal("800.00"),
        operating_cash_flow=Decimal("550.00"),
        net_cash_flow=Decimal("1350.00"),
        cumulative_balance=Decimal("5000.00"),
        confidence_q10=Decimal("4500.00"),
        confidence_q90=Decimal("5500.00"),
    )
    assert p.revenue_forecast == Decimal("1000.00")
    assert p.cumulative_balance == Decimal("5000.00")
    assert p.confidence_q90 > p.confidence_q10
