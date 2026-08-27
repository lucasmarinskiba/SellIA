"""Financial statements + period close, built on posted journal lines."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ledger.models import (
    AccountingPeriod,
    AccountType,
    JournalEntry,
    JournalLine,
    JournalSource,
    JournalStatus,
    LedgerAccount,
    PeriodStatus,
)
from app.domains.ledger.service import BALANCE_TOLERANCE, LedgerError, LedgerService, _q, _utcnow

logger = get_logger(__name__)

# subtype -> internal department bucket, for the inter-department orchestrator
DEPARTMENT_BY_SUBTYPE: dict[str, str] = {
    "ad_spend_meta": "advertising",
    "ad_spend_google": "advertising",
    "ad_spend_tiktok": "advertising",
    "ad_spend_other": "advertising",
    "marketing_tools": "marketing",
    "sales_expenses": "sales",
    "payroll": "people",
    "software_subscriptions": "operations",
    "professional_services": "operations",
    "rent_utilities": "operations",
    "shipping_costs": "operations",
    "payment_processing_fees": "finance",
    "marketplace_fees": "finance",
    "cogs": "operations",
    "misc_expenses": "operations",
    "tax_expense": "finance",
    "fx_gain_loss": "finance",
}

COGS_SUBTYPES = {"cogs", "payment_processing_fees", "marketplace_fees", "shipping_costs"}


class LedgerReports:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)

    async def _account_movements(
        self, business_id: uuid.UUID, start: Optional[datetime], end: Optional[datetime]
    ) -> dict[uuid.UUID, tuple[Decimal, Decimal]]:
        q = (
            select(
                JournalLine.account_id,
                func.coalesce(func.sum(JournalLine.debit), 0),
                func.coalesce(func.sum(JournalLine.credit), 0),
            )
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .where(
                JournalLine.business_id == business_id,
                JournalEntry.status == JournalStatus.POSTED.value,
            )
            .group_by(JournalLine.account_id)
        )
        if start is not None:
            q = q.where(JournalEntry.entry_date >= start)
        if end is not None:
            q = q.where(JournalEntry.entry_date < end)
        return {r[0]: (_q(r[1]), _q(r[2])) for r in (await self.db.execute(q)).all()}

    # ------------------------------------------------------------------
    # Income statement (P&L)
    # ------------------------------------------------------------------
    async def income_statement(
        self, business_id: uuid.UUID, start: datetime, end: datetime
    ) -> dict[str, Any]:
        accounts = {a.id: a for a in await self.ledger.get_accounts(business_id)}
        moves = await self._account_movements(business_id, start, end)

        revenue: dict[str, float] = {}
        cogs: dict[str, float] = {}
        opex: dict[str, float] = {}
        by_department: dict[str, Decimal] = {}
        total_revenue = Decimal("0")
        total_cogs = Decimal("0")
        total_opex = Decimal("0")

        for acc_id, (dr, cr) in moves.items():
            acc = accounts.get(acc_id)
            if not acc:
                continue
            if acc.type == AccountType.REVENUE.value:
                amount = cr - dr  # contra-revenue (discounts) net out
                total_revenue += amount
                revenue[acc.name] = float(_q(revenue.get(acc.name, 0) + amount))
            elif acc.type == AccountType.EXPENSE.value:
                amount = dr - cr
                dept = DEPARTMENT_BY_SUBTYPE.get(acc.subtype or "", "operations")
                by_department[dept] = by_department.get(dept, Decimal("0")) + amount
                if (acc.subtype or "") in COGS_SUBTYPES:
                    total_cogs += amount
                    cogs[acc.name] = float(_q(cogs.get(acc.name, 0) + amount))
                else:
                    total_opex += amount
                    opex[acc.name] = float(_q(opex.get(acc.name, 0) + amount))

        gross_profit = total_revenue - total_cogs
        operating_income = gross_profit - total_opex
        net_income = operating_income  # no separate non-operating section yet

        return {
            "period_start": start,
            "period_end": end,
            "currency": next(iter(accounts.values())).currency if accounts else "ARS",
            "revenue": revenue,
            "total_revenue": _q(total_revenue),
            "cogs": cogs,
            "total_cogs": _q(total_cogs),
            "gross_profit": _q(gross_profit),
            "operating_expenses": opex,
            "total_operating_expenses": _q(total_opex),
            "operating_income": _q(operating_income),
            "net_income": _q(net_income),
            "by_department": {k: float(_q(v)) for k, v in by_department.items()},
        }

    # ------------------------------------------------------------------
    # Balance sheet
    # ------------------------------------------------------------------
    async def balance_sheet(
        self, business_id: uuid.UUID, as_of: Optional[datetime] = None
    ) -> dict[str, Any]:
        as_of = as_of or _utcnow()
        accounts = {a.id: a for a in await self.ledger.get_accounts(business_id)}
        moves = await self._account_movements(business_id, None, as_of)

        assets: dict[str, float] = {}
        liabilities: dict[str, float] = {}
        equity: dict[str, float] = {}
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        total_equity = Decimal("0")
        earnings_ytd = Decimal("0")

        fy_start = datetime(as_of.year, 1, 1, tzinfo=timezone.utc)
        fy_moves = await self._account_movements(business_id, fy_start, as_of)
        for acc_id, (dr, cr) in fy_moves.items():
            acc = accounts.get(acc_id)
            if not acc:
                continue
            if acc.type == AccountType.REVENUE.value:
                earnings_ytd += cr - dr
            elif acc.type == AccountType.EXPENSE.value:
                earnings_ytd -= dr - cr

        for acc_id, (dr, cr) in moves.items():
            acc = accounts.get(acc_id)
            if not acc:
                continue
            if acc.type == AccountType.ASSET.value:
                bal = dr - cr
                total_assets += bal
                assets[acc.name] = float(_q(assets.get(acc.name, 0) + bal))
            elif acc.type == AccountType.LIABILITY.value:
                bal = cr - dr
                total_liabilities += bal
                liabilities[acc.name] = float(_q(liabilities.get(acc.name, 0) + bal))
            elif acc.type == AccountType.EQUITY.value:
                bal = cr - dr
                total_equity += bal
                equity[acc.name] = float(_q(equity.get(acc.name, 0) + bal))

        # Current-year earnings not yet closed to equity:
        retained_plus_current = total_equity + earnings_ytd
        if earnings_ytd != 0:
            equity["Resultado del ejercicio (no cerrado)"] = float(_q(earnings_ytd))

        total_equity_effective = total_equity + earnings_ytd
        return {
            "as_of": as_of,
            "currency": next(iter(accounts.values())).currency if accounts else "ARS",
            "assets": assets,
            "total_assets": _q(total_assets),
            "liabilities": liabilities,
            "total_liabilities": _q(total_liabilities),
            "equity": equity,
            "total_equity": _q(total_equity_effective),
            "retained_plus_current": _q(retained_plus_current),
            "balanced": abs(total_assets - (total_liabilities + total_equity_effective))
            <= BALANCE_TOLERANCE,
        }

    # ------------------------------------------------------------------
    # Cash flow (direct method, cash-account driven)
    # ------------------------------------------------------------------
    async def cash_flow_statement(
        self, business_id: uuid.UUID, start: datetime, end: datetime
    ) -> dict[str, Any]:
        accounts = {a.id: a for a in await self.ledger.get_accounts(business_id)}
        cash_ids = {
            a.id for a in accounts.values()
            if a.type == AccountType.ASSET.value and (a.subtype or "").startswith("cash")
        }

        # opening cash
        opening = Decimal("0")
        open_moves = await self._account_movements(business_id, None, start)
        for aid in cash_ids:
            dr, cr = open_moves.get(aid, (Decimal("0"), Decimal("0")))
            opening += dr - cr

        # entries in period that touch cash
        q = (
            select(JournalLine, JournalEntry.source, JournalEntry.id)
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .where(
                JournalLine.business_id == business_id,
                JournalEntry.status == JournalStatus.POSTED.value,
                JournalEntry.entry_date >= start,
                JournalEntry.entry_date < end,
            )
        )
        rows = (await self.db.execute(q)).all()
        entries: dict[uuid.UUID, list] = {}
        for line, source, eid in rows:
            entries.setdefault(eid, []).append((line, source))

        operating: dict[str, Decimal] = {}
        investing: dict[str, Decimal] = {}
        financing: dict[str, Decimal] = {}
        net_change = Decimal("0")

        for eid, lines in entries.items():
            cash_delta = Decimal("0")
            for ln, _ in lines:
                if ln.account_id in cash_ids:
                    cash_delta += ln.debit - ln.credit
            if cash_delta == 0:
                continue
            net_change += cash_delta
            # classify by the non-cash counterparty account type
            counter = [ln for ln, _ in lines if ln.account_id not in cash_ids]
            bucket = operating
            label = "Operaciones"
            for ln in counter:
                acc = accounts.get(ln.account_id)
                if not acc:
                    continue
                if acc.type == AccountType.EQUITY.value:
                    bucket, label = financing, "Aportes / retiros de capital"
                elif acc.subtype in ("loans_payable",):
                    bucket, label = financing, "Financiamiento"
                elif acc.subtype in ("fixed_assets",):
                    bucket, label = investing, "Inversiones"
            bucket[label] = bucket.get(label, Decimal("0")) + cash_delta

        return {
            "period_start": start,
            "period_end": end,
            "currency": next(iter(accounts.values())).currency if accounts else "ARS",
            "operating": {k: float(_q(v)) for k, v in operating.items()},
            "investing": {k: float(_q(v)) for k, v in investing.items()},
            "financing": {k: float(_q(v)) for k, v in financing.items()},
            "net_change": _q(net_change),
            "opening_cash": _q(opening),
            "closing_cash": _q(opening + net_change),
        }

    # ------------------------------------------------------------------
    # Period close
    # ------------------------------------------------------------------
    async def close_period(
        self,
        business_id: uuid.UUID,
        period_name: str,
        *,
        user_id: Optional[uuid.UUID] = None,
        lock: bool = False,
    ) -> dict[str, Any]:
        res = await self.db.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.business_id == business_id,
                AccountingPeriod.name == period_name,
            )
        )
        period = res.scalar_one_or_none()
        if not period:
            raise LedgerError(f"period {period_name} not found")
        if period.status == PeriodStatus.LOCKED.value:
            raise LedgerError(f"period {period_name} already locked")

        pnl = await self.income_statement(business_id, period.period_start, period.period_end)
        net_income = _q(pnl["net_income"])

        closing_entry_id = None
        if net_income != 0 or pnl["total_revenue"] or pnl["total_operating_expenses"]:
            acc_map = await self.ledger.account_map(business_id)
            cye = acc_map.get("current_year_earnings")
            if not cye:
                raise LedgerError("missing current_year_earnings account; run ensure_setup")

            # Build closing lines: zero every revenue/expense account for the period.
            moves = await self._account_movements(
                business_id, period.period_start, period.period_end
            )
            accounts = {a.id: a for a in await self.ledger.get_accounts(business_id)}
            lines: list[dict[str, Any]] = []
            net_to_equity = Decimal("0")
            for acc_id, (dr, cr) in moves.items():
                acc = accounts.get(acc_id)
                if not acc or acc.type not in (
                    AccountType.REVENUE.value,
                    AccountType.EXPENSE.value,
                ):
                    continue
                bal = dr - cr  # signed
                if bal == 0:
                    continue
                # Reverse the account's net movement
                if bal > 0:
                    lines.append({"account_id": acc_id, "credit": bal,
                                  "description": f"Cierre {period_name}: {acc.name}"})
                    net_to_equity -= bal
                else:
                    lines.append({"account_id": acc_id, "debit": -bal,
                                  "description": f"Cierre {period_name}: {acc.name}"})
                    net_to_equity += -bal

            # Balancing line to current-year earnings
            if net_to_equity > 0:
                lines.append({"account_id": cye.id, "credit": net_to_equity,
                              "description": f"Resultado {period_name}"})
            elif net_to_equity < 0:
                lines.append({"account_id": cye.id, "debit": -net_to_equity,
                              "description": f"Resultado {period_name}"})

            if len(lines) >= 2:
                # Date the closing entry on the last instant *inside* the period
                # so it lands in this period's balances, not the next one's.
                closing_date = period.period_end - timedelta(seconds=1)
                entry = await self.ledger.post_entry(
                    business_id,
                    lines,
                    entry_date=closing_date,
                    memo=f"Asiento de cierre {period_name}",
                    source=JournalSource.CLOSING.value,
                    source_ref=period_name,
                    idempotency_key=f"close:{business_id}:{period_name}",
                    created_by=user_id,
                    currency=pnl["currency"],
                    allow_closed_period=True,
                )
                closing_entry_id = entry.id

        period.status = PeriodStatus.LOCKED.value if lock else PeriodStatus.CLOSED.value
        period.closed_at = _utcnow()
        period.closed_by = user_id
        period.closing_entry_id = closing_entry_id
        period.net_income = net_income
        await self.db.commit()
        await self.db.refresh(period)

        return {
            "period": period,
            "closing_entry_id": closing_entry_id,
            "net_income": net_income,
            "message": f"Período {period_name} {'bloqueado' if lock else 'cerrado'}. Resultado: {net_income}",
        }

    async def reopen_period(self, business_id: uuid.UUID, period_name: str) -> AccountingPeriod:
        res = await self.db.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.business_id == business_id,
                AccountingPeriod.name == period_name,
            )
        )
        period = res.scalar_one_or_none()
        if not period:
            raise LedgerError(f"period {period_name} not found")
        if period.status == PeriodStatus.LOCKED.value:
            raise LedgerError("locked periods cannot be reopened")
        if period.closing_entry_id:
            await self.ledger.reverse_entry(
                business_id, period.closing_entry_id, reason=f"Reapertura {period_name}"
            )
        period.status = PeriodStatus.OPEN.value
        period.closed_at = None
        period.closing_entry_id = None
        await self.db.commit()
        await self.db.refresh(period)
        return period
