"""Financial Dashboard tests — pure composition/derivation logic.

No DB fixture: _compose and _classify_cash_health are pure functions of
their inputs (no DB access), so they're tested directly with hand-built
fixtures mimicking what each sub-domain service returns.
"""

from app.domains.financial_dashboard.service import FinancialDashboardService


def _income_statement(**overrides) -> dict:
    base = {
        "total_revenue": 10000.0,
        "gross_profit": 6000.0,
        "net_income": 2000.0,
    }
    base.update(overrides)
    return base


def _invoice_stats(**overrides) -> dict:
    base = {
        "total_invoices": 20,
        "pending_revenue_aed": 1500.0,
        "overdue_count": 2,
        "avg_payment_days": 12.5,
    }
    base.update(overrides)
    return base


def _ad_dashboard(**overrides) -> dict:
    base = {
        "blended_roas": 3.5,
        "channels": [
            {"spend": 500.0, "revenue": 1750.0},
            {"spend": 300.0, "revenue": 1050.0},
        ],
    }
    base.update(overrides)
    return base


def _cash_snapshot(**overrides) -> dict:
    base = {"cash_balance": 25000.0, "beginning_balance": 20000.0, "min_balance": 18000.0, "runway_days": 120}
    base.update(overrides)
    return base


class TestComposeFullData:
    def test_revenue_section(self):
        payload = FinancialDashboardService._compose(
            _income_statement(), _invoice_stats(), _ad_dashboard(), _cash_snapshot(), 30
        )
        assert payload["revenue"]["total_revenue"] == 10000.0
        assert payload["revenue"]["gross_profit"] == 6000.0
        assert payload["revenue"]["net_income"] == 2000.0
        assert payload["revenue"]["gross_margin_pct"] == 60.0
        assert payload["revenue"]["net_margin_pct"] == 20.0

    def test_advertising_section(self):
        payload = FinancialDashboardService._compose(
            _income_statement(), _invoice_stats(), _ad_dashboard(), _cash_snapshot(), 30
        )
        assert payload["advertising"]["total_spend"] == 800.0  # 500+300
        assert payload["advertising"]["blended_roas"] == 3.5
        assert payload["advertising"]["active_channels"] == 2
        # MER = revenue / ad_spend = 10000 / 800 = 12.5
        assert payload["advertising"]["marketing_efficiency_ratio"] == 12.5

    def test_invoicing_section(self):
        payload = FinancialDashboardService._compose(
            _income_statement(), _invoice_stats(), _ad_dashboard(), _cash_snapshot(), 30
        )
        assert payload["invoicing"]["accounts_receivable"] == 1500.0
        assert payload["invoicing"]["overdue_invoices"] == 2
        assert payload["invoicing"]["avg_payment_days"] == 12.5
        assert payload["invoicing"]["total_invoices"] == 20

    def test_cash_section(self):
        payload = FinancialDashboardService._compose(
            _income_statement(), _invoice_stats(), _ad_dashboard(), _cash_snapshot(), 30
        )
        assert payload["cash"]["cash_balance"] == 25000.0
        assert payload["cash"]["runway_days"] == 120
        assert payload["cash"]["health"] == "healthy"

    def test_data_availability_all_true(self):
        payload = FinancialDashboardService._compose(
            _income_statement(), _invoice_stats(), _ad_dashboard(), _cash_snapshot(), 30
        )
        assert all(payload["data_availability"].values())

    def test_period_days_passthrough(self):
        payload = FinancialDashboardService._compose(
            _income_statement(), _invoice_stats(), _ad_dashboard(), _cash_snapshot(), 90
        )
        assert payload["period_days"] == 90


class TestComposeMissingData:
    def test_all_none_yields_zeroed_payload(self):
        """A brand-new business with nothing set up yet gets zeros, not a crash."""
        payload = FinancialDashboardService._compose(None, None, None, None, 30)
        assert payload["revenue"]["total_revenue"] == 0.0
        assert payload["advertising"]["total_spend"] == 0.0
        assert payload["advertising"]["marketing_efficiency_ratio"] is None
        assert payload["invoicing"]["accounts_receivable"] == 0.0
        assert payload["cash"]["cash_balance"] == 0.0
        assert payload["cash"]["health"] == "unknown"
        assert not any(payload["data_availability"].values())

    def test_missing_ledger_only(self):
        """Ledger unavailable but other domains have data -> partial payload."""
        payload = FinancialDashboardService._compose(
            None, _invoice_stats(), _ad_dashboard(), _cash_snapshot(), 30
        )
        assert payload["revenue"]["total_revenue"] == 0.0
        assert payload["data_availability"]["ledger"] is False
        assert payload["data_availability"]["invoicing"] is True
        assert payload["invoicing"]["accounts_receivable"] == 1500.0  # unaffected

    def test_zero_revenue_avoids_division_by_zero(self):
        """total_revenue == 0 must not raise on margin_pct calculation."""
        payload = FinancialDashboardService._compose(
            _income_statement(total_revenue=0.0, gross_profit=0.0, net_income=0.0),
            None, None, None, 30,
        )
        assert payload["revenue"]["gross_margin_pct"] == 0.0
        assert payload["revenue"]["net_margin_pct"] == 0.0

    def test_zero_ad_spend_yields_none_mer(self):
        """No ad spend -> marketing_efficiency_ratio is None, not a ZeroDivisionError."""
        payload = FinancialDashboardService._compose(
            _income_statement(), None, _ad_dashboard(channels=[]), None, 30
        )
        assert payload["advertising"]["total_spend"] == 0.0
        assert payload["advertising"]["marketing_efficiency_ratio"] is None
        assert payload["advertising"]["active_channels"] == 0


class TestCashHealthClassification:
    def test_unknown_when_no_runway_data(self):
        assert FinancialDashboardService._classify_cash_health(None) == "unknown"

    def test_critical_below_30_days(self):
        assert FinancialDashboardService._classify_cash_health(15) == "critical"
        assert FinancialDashboardService._classify_cash_health(29) == "critical"

    def test_at_risk_30_to_59_days(self):
        assert FinancialDashboardService._classify_cash_health(30) == "at_risk"
        assert FinancialDashboardService._classify_cash_health(59) == "at_risk"

    def test_stable_60_to_89_days(self):
        assert FinancialDashboardService._classify_cash_health(60) == "stable"
        assert FinancialDashboardService._classify_cash_health(89) == "stable"

    def test_healthy_90_days_and_above(self):
        assert FinancialDashboardService._classify_cash_health(90) == "healthy"
        assert FinancialDashboardService._classify_cash_health(365) == "healthy"
