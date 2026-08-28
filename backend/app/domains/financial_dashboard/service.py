"""FinancialDashboardService — aggregates real data across ledger, invoicing,
ad_budget, and cashflow into one unified financial reporting payload.

Unlike app/api/v1/analytics_dashboard.py (hardcoded mock KPIs — see its
module docstring's TODOs), every number here is a real query against a
domain that already tracks it. Each sub-domain fetch is independently
wrapped so a business missing one type of data (e.g. no ledger entries yet)
still gets the sections that ARE available, flagged via `data_availability`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ledger.reports import LedgerReports
from app.domains.invoicing.service import InvoicingService
from app.domains.ad_budget.service import AdBudgetService
from app.domains.cashflow.service import CashFlowService

logger = get_logger(__name__)


class FinancialDashboardService:
    """Read-only aggregator. Never writes to any domain — pure reporting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(
        self,
        business_id: uuid.UUID,
        period_days: int = 30,
    ) -> dict[str, Any]:
        """Fetch + compose the unified financial dashboard for a business."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=period_days)

        income_statement = await self._fetch_income_statement(business_id, start, now)
        invoice_stats = await self._fetch_invoice_stats(business_id)
        ad_dashboard = await self._fetch_ad_dashboard(business_id)
        cash_snapshot = await self._fetch_cash_snapshot(business_id)

        payload = self._compose(income_statement, invoice_stats, ad_dashboard, cash_snapshot, period_days)
        payload["business_id"] = str(business_id)
        logger.info(
            f"Financial dashboard composed for {business_id}: "
            f"ledger={payload['data_availability']['ledger']} "
            f"invoicing={payload['data_availability']['invoicing']} "
            f"ad_budget={payload['data_availability']['ad_budget']} "
            f"cashflow={payload['data_availability']['cashflow']}"
        )
        return payload

    async def _fetch_income_statement(
        self, business_id: uuid.UUID, start: datetime, end: datetime
    ) -> Optional[dict]:
        try:
            return await LedgerReports(self.db).income_statement(business_id, start, end)
        except Exception as e:  # noqa: BLE001 — missing ledger setup for this business is expected
            logger.warning(f"Income statement unavailable for {business_id}: {e}")
            return None

    async def _fetch_invoice_stats(self, business_id: uuid.UUID) -> Optional[dict]:
        try:
            return await InvoicingService(self.db).invoice_stats(business_id)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Invoice stats unavailable for {business_id}: {e}")
            return None

    async def _fetch_ad_dashboard(self, business_id: uuid.UUID) -> Optional[dict]:
        try:
            return await AdBudgetService(self.db).dashboard(business_id)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Ad budget dashboard unavailable for {business_id}: {e}")
            return None

    async def _fetch_cash_snapshot(self, business_id: uuid.UUID) -> Optional[dict]:
        try:
            cf = await CashFlowService(self.db).forecast(business_id, horizon_days=30)
            return {
                "cash_balance": float(cf.end_balance),
                "beginning_balance": float(cf.beginning_balance),
                "min_balance": float(cf.min_balance),
                "runway_days": cf.runway_days,
            }
        except Exception as e:  # noqa: BLE001 — no forecast data yet is expected for new businesses
            logger.warning(f"Cash snapshot unavailable for {business_id}: {e}")
            return None

    @staticmethod
    def _compose(
        income_statement: Optional[dict],
        invoice_stats: Optional[dict],
        ad_dashboard: Optional[dict],
        cash_snapshot: Optional[dict],
        period_days: int,
    ) -> dict[str, Any]:
        """Merge + derive cross-domain KPIs. Pure function of its inputs —
        no DB access — so it's directly unit-testable with hand-built fixtures.
        """
        revenue = float(income_statement["total_revenue"]) if income_statement else 0.0
        gross_profit = float(income_statement["gross_profit"]) if income_statement else 0.0
        net_income = float(income_statement["net_income"]) if income_statement else 0.0
        gross_margin_pct = round((gross_profit / revenue * 100), 1) if revenue > 0 else 0.0
        net_margin_pct = round((net_income / revenue * 100), 1) if revenue > 0 else 0.0

        ad_channels = ad_dashboard.get("channels", []) if ad_dashboard else []
        ad_spend = sum(c.get("spend", 0.0) for c in ad_channels)
        blended_roas = ad_dashboard.get("blended_roas", 0.0) if ad_dashboard else 0.0
        # Marketing Efficiency Ratio: total revenue generated per $1 of ad spend
        marketing_efficiency_ratio = round(revenue / ad_spend, 2) if ad_spend > 0 else None

        accounts_receivable = invoice_stats.get("pending_revenue_aed", 0.0) if invoice_stats else 0.0
        overdue_invoices = invoice_stats.get("overdue_count", 0) if invoice_stats else 0
        avg_payment_days = invoice_stats.get("avg_payment_days", 0.0) if invoice_stats else 0.0

        cash_balance = cash_snapshot.get("cash_balance", 0.0) if cash_snapshot else 0.0
        runway_days = cash_snapshot.get("runway_days") if cash_snapshot else None
        cash_health = FinancialDashboardService._classify_cash_health(runway_days)

        return {
            "period_days": period_days,
            "data_availability": {
                "ledger": income_statement is not None,
                "invoicing": invoice_stats is not None,
                "ad_budget": ad_dashboard is not None,
                "cashflow": cash_snapshot is not None,
            },
            "revenue": {
                "total_revenue": round(revenue, 2),
                "gross_profit": round(gross_profit, 2),
                "net_income": round(net_income, 2),
                "gross_margin_pct": gross_margin_pct,
                "net_margin_pct": net_margin_pct,
            },
            "advertising": {
                "total_spend": round(ad_spend, 2),
                "blended_roas": blended_roas,
                "marketing_efficiency_ratio": marketing_efficiency_ratio,
                "active_channels": len(ad_channels),
            },
            "invoicing": {
                "accounts_receivable": round(accounts_receivable, 2),
                "overdue_invoices": overdue_invoices,
                "avg_payment_days": round(avg_payment_days, 1),
                "total_invoices": invoice_stats.get("total_invoices", 0) if invoice_stats else 0,
            },
            "cash": {
                "cash_balance": round(cash_balance, 2),
                "runway_days": runway_days,
                "health": cash_health,
            },
        }

    @staticmethod
    def _classify_cash_health(runway_days: Optional[int]) -> str:
        """No runway data -> 'unknown'. Otherwise bands matching the
        orchestrator domain's Priority thresholds (runway<30 critical, <60 at_risk, <90 stable, else healthy)."""
        if runway_days is None:
            return "unknown"
        if runway_days < 30:
            return "critical"
        elif runway_days < 60:
            return "at_risk"
        elif runway_days < 90:
            return "stable"
        return "healthy"
