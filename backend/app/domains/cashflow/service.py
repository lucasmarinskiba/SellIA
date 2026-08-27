"""CashFlowService — demand-driven liquidity projection."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.cashflow.types import CashFlowAssumptions, CashFlowForecast, CashFlowPoint
from app.domains.forecasting.service import ForecastingService
from app.domains.ledger.models import JournalEntry, LedgerAccount
from app.domains.orders.models import Order

logger = get_logger(__name__)


class CashFlowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def forecast(
        self,
        business_id: uuid.UUID,
        *,
        horizon_days: int = 90,
        payment_delay_days: int = 3,
        cogs_pct: Decimal = Decimal("0.35"),
        opex_daily: Decimal = Decimal("500.00"),
        tax_rate: Decimal = Decimal("0.21"),
    ) -> CashFlowForecast:
        """Project cash balance for next `horizon_days` from today.

        Flow:
        1. Fetch latest revenue + units forecast from forecasting domain
        2. Estimate COGS from forecast units (using historical %)
        3. Compute daily operating cash flow: revenue - cogs - opex
        4. Reorder prior sales (payment lag) to get cash collections
        5. Accumulate balance day-by-day
        6. Confidence intervals from forecast quantiles
        """
        assumptions = CashFlowAssumptions(
            avg_payment_delay_days=payment_delay_days,
            cogs_pct_revenue=cogs_pct,
            opex_daily=opex_daily,
            tax_rate=tax_rate,
            beginning_balance=await self._get_cash_balance(business_id),
        )

        # 1. Get revenue forecast
        fc_svc = ForecastingService(self.db)
        revenue_forecast = await fc_svc.get_forecast(
            business_id, series_key="total:revenue:daily:*", horizon=horizon_days
        )
        if not revenue_forecast or not revenue_forecast.get("points"):
            raise ValueError(f"No revenue forecast for business {business_id}")

        start_date = date.today()
        points_data = revenue_forecast["points"]
        if not points_data:
            raise ValueError("Empty forecast points")

        # 2. Load historical daily orders to model payment delay
        order_stream = await self._load_order_stream(business_id, days=90)

        # 3. Compute daily cash flows
        points: list[CashFlowPoint] = []
        cumul_balance = assumptions.beginning_balance
        min_balance = cumul_balance
        min_date = start_date
        cumul_tax_reserve = Decimal("0")

        for i, p in enumerate(points_data[:horizon_days]):
            target_date = start_date + timedelta(days=i)
            revenue = Decimal(str(p.get("yhat", 0)))
            q10 = Decimal(str(p.get("q10", 0)))
            q90 = Decimal(str(p.get("q90", 0)))

            cogs = revenue * cogs_pct
            opex = opex_daily

            # Cash inflow: orders from `payment_delay_days` ago
            prior_revenue = self._get_order_revenue_for_date(
                order_stream, target_date - timedelta(days=payment_delay_days)
            )
            inflow = prior_revenue

            # Profit and tax provision (accrual, not paid yet)
            profit_before_tax = revenue - cogs - opex
            tax_prov = profit_before_tax * tax_rate if profit_before_tax > 0 else Decimal("0")
            cumul_tax_reserve += tax_prov

            # Operating cash flow: revenue - cogs - opex (tax paid lazily, quarterly)
            ocf = revenue - cogs - opex

            # Net cash impact: inflow + ocf
            net_flow = inflow + ocf
            cumul_balance += net_flow

            if cumul_balance < min_balance:
                min_balance = cumul_balance
                min_date = target_date

            # Confidence intervals scale from forecast quantiles
            inflow_q10 = prior_revenue  # same regardless
            ocf_q10 = q10 - cogs - opex
            balance_q10 = cumul_balance + (ocf_q10 - ocf)

            inflow_q90 = prior_revenue
            ocf_q90 = q90 - cogs - opex
            balance_q90 = cumul_balance + (ocf_q90 - ocf)

            point = CashFlowPoint(
                date=target_date,
                revenue_forecast=revenue,
                cogs_forecast=cogs,
                opex=opex,
                tax_provision=tax_prov,
                inflow_from_prior_sales=inflow,
                operating_cash_flow=ocf,
                net_cash_flow=net_flow,
                cumulative_balance=cumul_balance,
                confidence_q10=balance_q10,
                confidence_q90=balance_q90,
            )
            points.append(point)

        # Compute runway (days until zero if negative burn)
        runway = None
        if cumul_balance < 0:
            daily_burn = (cumul_balance - assumptions.beginning_balance) / max(1, len(points))
            if daily_burn < 0:
                runway = int(-cumul_balance / daily_burn)

        return CashFlowForecast(
            business_id=str(business_id),
            start_date=start_date,
            horizon_days=horizon_days,
            points=points,
            beginning_balance=assumptions.beginning_balance,
            end_balance=cumul_balance,
            min_balance=min_balance,
            max_balance=max(p.cumulative_balance for p in points),
            min_balance_date=min_date,
            runway_days=runway,
            assumptions=assumptions,
            computed_at=datetime.now(timezone.utc),
        )

    async def _get_cash_balance(self, business_id: uuid.UUID) -> Decimal:
        """Fetch current cash balance from GL."""
        rows = await self.db.execute(
            select(LedgerAccount).where(
                LedgerAccount.business_id == business_id,
                LedgerAccount.account_type == "asset",
                LedgerAccount.name.ilike("%cash%"),
            )
        )
        cash_accts = rows.scalars().all()
        if not cash_accts:
            return Decimal("0")

        total = Decimal("0")
        for acct in cash_accts:
            balance_row = await self.db.execute(
                select(func.sum(JournalEntry.debit_amount - JournalEntry.credit_amount))
                .where(JournalEntry.account_id == acct.id)
            )
            bal = balance_row.scalar() or 0
            total += Decimal(str(bal))
        return total

    async def _load_order_stream(
        self, business_id: uuid.UUID, days: int = 90
    ) -> dict[date, Decimal]:
        """Load historical revenue by day for payment delay model."""
        cutoff = date.today() - timedelta(days=days)
        rows = await self.db.execute(
            select(func.date(Order.paid_at).label("day"), func.sum(Order.total_amount))
            .where(
                Order.business_id == business_id,
                Order.paid_at >= cutoff,
                Order.status == "paid",
            )
            .group_by(func.date(Order.paid_at))
        )
        return {row[0]: Decimal(str(row[1] or 0)) for row in rows.all()}

    def _get_order_revenue_for_date(
        self, order_stream: dict[date, Decimal], target_date: date
    ) -> Decimal:
        """Return revenue from orders on that date."""
        return order_stream.get(target_date, Decimal("0"))
