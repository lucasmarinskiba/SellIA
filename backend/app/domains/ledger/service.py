"""LedgerService — the double-entry posting core.

All money movements land here as balanced journal entries. Nothing else
in the platform is allowed to mutate `journal_entries` / `journal_lines`
directly; go through `post_entry` so balance validation, period
resolution and idempotency are enforced in one place.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ledger.chart_of_accounts import REQUIRED_SUBTYPES, build_default_accounts
from app.domains.ledger.models import (
    NORMAL_BALANCE_BY_TYPE,
    AccountingPeriod,
    AccountType,
    JournalEntry,
    JournalLine,
    JournalSource,
    JournalStatus,
    LedgerAccount,
    PeriodStatus,
)

logger = get_logger(__name__)

CENT = Decimal("0.01")
BALANCE_TOLERANCE = Decimal("0.01")


def _q(value: Any) -> Decimal:
    if not isinstance(value, Decimal):
        value = Decimal(str(value or 0))
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _month_bounds(dt: datetime) -> tuple[datetime, datetime, str]:
    start = datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)
    if dt.month == 12:
        end = datetime(dt.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(dt.year, dt.month + 1, 1, tzinfo=timezone.utc)
    return start, end, start.strftime("%Y-%m")


class LedgerError(Exception):
    """Raised for accounting-rule violations (unbalanced entry, locked period...)."""


class PeriodLockedError(LedgerError):
    pass


class LedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    async def ensure_setup(self, business_id: uuid.UUID, currency: str = "ARS") -> dict[str, Any]:
        """Idempotently seed the chart of accounts and open the current period."""
        existing = await self.db.execute(
            select(func.count(LedgerAccount.id)).where(LedgerAccount.business_id == business_id)
        )
        count = existing.scalar() or 0
        created = 0
        if count == 0:
            for row in build_default_accounts(currency):
                self.db.add(LedgerAccount(business_id=business_id, **row))
                created += 1
            await self.db.flush()

        # Backfill any required subtype missing from an older seed.
        present = await self._subtypes_present(business_id)
        for row in build_default_accounts(currency):
            if row["subtype"] in REQUIRED_SUBTYPES and row["subtype"] not in present:
                self.db.add(LedgerAccount(business_id=business_id, **row))
                created += 1

        period = await self._get_or_create_period(business_id, _utcnow())
        await self.db.commit()
        return {"accounts_created": created, "current_period": period.name}

    async def _subtypes_present(self, business_id: uuid.UUID) -> set[str]:
        res = await self.db.execute(
            select(LedgerAccount.subtype).where(LedgerAccount.business_id == business_id)
        )
        return {s for (s,) in res.all() if s}

    # ------------------------------------------------------------------
    # Account lookup
    # ------------------------------------------------------------------
    async def get_accounts(self, business_id: uuid.UUID, active_only: bool = False) -> list[LedgerAccount]:
        q = select(LedgerAccount).where(LedgerAccount.business_id == business_id)
        if active_only:
            q = q.where(LedgerAccount.is_active.is_(True))
        q = q.order_by(LedgerAccount.code)
        return list((await self.db.execute(q)).scalars().all())

    async def account_map(self, business_id: uuid.UUID) -> dict[str, LedgerAccount]:
        """Map of subtype -> account (first match by code order)."""
        accounts = await self.get_accounts(business_id)
        out: dict[str, LedgerAccount] = {}
        for acc in accounts:
            if acc.subtype and acc.subtype not in out:
                out[acc.subtype] = acc
        return out

    async def resolve_account(
        self,
        business_id: uuid.UUID,
        *,
        account_id: Optional[uuid.UUID] = None,
        code: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> LedgerAccount:
        q = select(LedgerAccount).where(LedgerAccount.business_id == business_id)
        if account_id:
            q = q.where(LedgerAccount.id == account_id)
        elif code:
            q = q.where(LedgerAccount.code == code)
        elif subtype:
            q = q.where(LedgerAccount.subtype == subtype).order_by(LedgerAccount.code)
        else:
            raise LedgerError("resolve_account needs account_id, code or subtype")
        acc = (await self.db.execute(q)).scalars().first()
        if not acc:
            raise LedgerError(f"account not found (id={account_id} code={code} subtype={subtype})")
        return acc

    async def create_account(self, business_id: uuid.UUID, **data: Any) -> LedgerAccount:
        acc_type = data["type"]
        if acc_type not in NORMAL_BALANCE_BY_TYPE:
            raise LedgerError(f"invalid account type: {acc_type}")
        acc = LedgerAccount(
            business_id=business_id,
            normal_balance=NORMAL_BALANCE_BY_TYPE[acc_type],
            **data,
        )
        self.db.add(acc)
        await self.db.commit()
        await self.db.refresh(acc)
        return acc

    # ------------------------------------------------------------------
    # Periods
    # ------------------------------------------------------------------
    async def _get_or_create_period(self, business_id: uuid.UUID, dt: datetime) -> AccountingPeriod:
        start, end, name = _month_bounds(dt)
        res = await self.db.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.business_id == business_id,
                AccountingPeriod.name == name,
            )
        )
        period = res.scalar_one_or_none()
        if period:
            return period
        period = AccountingPeriod(
            business_id=business_id,
            name=name,
            period_start=start,
            period_end=end,
            status=PeriodStatus.OPEN.value,
        )
        self.db.add(period)
        await self.db.flush()
        return period

    async def get_periods(self, business_id: uuid.UUID) -> list[AccountingPeriod]:
        res = await self.db.execute(
            select(AccountingPeriod)
            .where(AccountingPeriod.business_id == business_id)
            .order_by(AccountingPeriod.period_start.desc())
        )
        return list(res.scalars().all())

    # ------------------------------------------------------------------
    # Posting
    # ------------------------------------------------------------------
    async def _next_entry_number(self, business_id: uuid.UUID, period_name: str) -> str:
        res = await self.db.execute(
            select(func.count(JournalEntry.id)).where(
                JournalEntry.business_id == business_id,
                JournalEntry.entry_number.like(f"JE-{period_name}-%"),
            )
        )
        seq = (res.scalar() or 0) + 1
        return f"JE-{period_name}-{seq:05d}"

    async def find_by_idempotency(
        self, business_id: uuid.UUID, key: str
    ) -> Optional[JournalEntry]:
        if not key:
            return None
        res = await self.db.execute(
            select(JournalEntry).where(
                JournalEntry.business_id == business_id,
                JournalEntry.idempotency_key == key,
            )
        )
        return res.scalar_one_or_none()

    async def find_by_source(
        self, business_id: uuid.UUID, source: str, source_ref: str
    ) -> list[JournalEntry]:
        res = await self.db.execute(
            select(JournalEntry).where(
                JournalEntry.business_id == business_id,
                JournalEntry.source == source,
                JournalEntry.source_ref == str(source_ref),
                JournalEntry.status == JournalStatus.POSTED.value,
            )
        )
        return list(res.scalars().all())

    async def post_entry(
        self,
        business_id: uuid.UUID,
        lines: list[dict[str, Any]],
        *,
        entry_date: Optional[datetime] = None,
        memo: Optional[str] = None,
        source: str = JournalSource.MANUAL.value,
        source_ref: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
        currency: str = "ARS",
        allow_closed_period: bool = False,
        commit: bool = True,
    ) -> JournalEntry:
        """Create and post a balanced journal entry.

        `lines` items: {account_id|account_code|account_subtype, debit, credit,
        description, contact_type, contact_id, tax_code}
        """
        if idempotency_key:
            dup = await self.find_by_idempotency(business_id, idempotency_key)
            if dup:
                logger.info("Ledger: idempotent hit for key=%s -> entry %s", idempotency_key, dup.id)
                return dup

        entry_date = entry_date or _utcnow()
        if entry_date.tzinfo is None:
            entry_date = entry_date.replace(tzinfo=timezone.utc)

        # Resolve + validate lines
        resolved: list[dict[str, Any]] = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        for idx, raw in enumerate(lines):
            debit = _q(raw.get("debit", 0))
            credit = _q(raw.get("credit", 0))
            if debit < 0 or credit < 0:
                raise LedgerError("negative debit/credit not allowed")
            if debit > 0 and credit > 0:
                raise LedgerError("line has both debit and credit")
            if debit == 0 and credit == 0:
                raise LedgerError("line has zero amount")
            account = await self.resolve_account(
                business_id,
                account_id=raw.get("account_id"),
                code=raw.get("account_code"),
                subtype=raw.get("account_subtype"),
            )
            total_debit += debit
            total_credit += credit
            base = debit - credit  # signed, base currency (fx == 1 for now)
            resolved.append(
                {
                    "account_id": account.id,
                    "description": raw.get("description"),
                    "debit": debit,
                    "credit": credit,
                    "currency": currency,
                    "base_amount": base,
                    "contact_type": raw.get("contact_type"),
                    "contact_id": raw.get("contact_id"),
                    "tax_code": raw.get("tax_code"),
                    "line_index": idx,
                }
            )

        if len(resolved) < 2:
            raise LedgerError("a journal entry needs at least two lines")
        if abs(total_debit - total_credit) > BALANCE_TOLERANCE:
            raise LedgerError(
                f"unbalanced entry: debit {total_debit} != credit {total_credit}"
            )

        period = await self._get_or_create_period(business_id, entry_date)
        if period.status == PeriodStatus.LOCKED.value:
            raise PeriodLockedError(f"period {period.name} is locked")
        if period.status == PeriodStatus.CLOSED.value and not allow_closed_period:
            raise PeriodLockedError(f"period {period.name} is closed")

        entry = JournalEntry(
            business_id=business_id,
            period_id=period.id,
            entry_number=await self._next_entry_number(business_id, period.name),
            entry_date=entry_date,
            memo=memo,
            source=source,
            source_ref=str(source_ref) if source_ref is not None else None,
            idempotency_key=idempotency_key,
            status=JournalStatus.POSTED.value,
            posted_at=_utcnow(),
            created_by=created_by,
            total_debit=_q(total_debit),
            total_credit=_q(total_credit),
            currency=currency,
        )
        self.db.add(entry)
        await self.db.flush()

        for line in resolved:
            self.db.add(JournalLine(entry_id=entry.id, business_id=business_id, **line))

        if commit:
            await self.db.commit()
            await self.db.refresh(entry, ["lines"])
        logger.info(
            "Ledger: posted %s (%s) %s lines total %s",
            entry.entry_number, source, len(resolved), _q(total_debit),
        )
        return entry

    async def reverse_entry(
        self,
        business_id: uuid.UUID,
        entry_id: uuid.UUID,
        *,
        reason: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> JournalEntry:
        res = await self.db.execute(
            select(JournalEntry).where(
                JournalEntry.id == entry_id,
                JournalEntry.business_id == business_id,
            )
        )
        original = res.scalar_one_or_none()
        if not original:
            raise LedgerError("entry not found")
        if original.status != JournalStatus.POSTED.value:
            raise LedgerError("only posted entries can be reversed")
        if (original.extra_data or {}).get("reversed_by"):
            raise LedgerError("entry already reversed")
        if original.reversal_of_id:
            raise LedgerError("cannot reverse a reversal entry")

        lines_res = await self.db.execute(
            select(JournalLine).where(JournalLine.entry_id == entry_id)
        )
        mirrored = [
            {
                "account_id": ln.account_id,
                "description": f"Reversión: {ln.description or ''}".strip(),
                "debit": ln.credit,
                "credit": ln.debit,
                "contact_type": ln.contact_type,
                "contact_id": ln.contact_id,
                "tax_code": ln.tax_code,
            }
            for ln in lines_res.scalars().all()
        ]
        reversal = await self.post_entry(
            business_id,
            mirrored,
            memo=reason or f"Reversión de {original.entry_number}",
            source=JournalSource.ADJUSTMENT.value,
            source_ref=str(original.id),
            created_by=created_by,
            currency=original.currency,
            allow_closed_period=True,
        )
        # Both entries stay POSTED — the reversal offsets the original in every
        # balance/report. (VOID is only for entries cancelled without a
        # reversing entry.) Flag the original so the UI can grey it out.
        reversal.reversal_of_id = original.id
        extra = dict(original.extra_data or {})
        extra["reversed_by"] = str(reversal.id)
        extra["reversed_at"] = _utcnow().isoformat()
        original.extra_data = extra
        await self.db.commit()
        await self.db.refresh(reversal, ["lines"])
        return reversal

    # ------------------------------------------------------------------
    # Balances
    # ------------------------------------------------------------------
    async def _balance_query(
        self,
        business_id: uuid.UUID,
        *,
        account_ids: Optional[Iterable[uuid.UUID]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ):
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
        if account_ids is not None:
            q = q.where(JournalLine.account_id.in_(list(account_ids)))
        if start is not None:
            q = q.where(JournalEntry.entry_date >= start)
        if end is not None:
            q = q.where(JournalEntry.entry_date < end)
        return {row[0]: (_q(row[1]), _q(row[2])) for row in (await self.db.execute(q)).all()}

    async def trial_balance(
        self, business_id: uuid.UUID, as_of: Optional[datetime] = None
    ) -> dict[str, Any]:
        as_of = as_of or _utcnow()
        accounts = await self.get_accounts(business_id)
        balances = await self._balance_query(business_id, end=as_of)
        rows = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        for acc in accounts:
            dr, cr = balances.get(acc.id, (Decimal("0"), Decimal("0")))
            net = dr - cr
            if net == 0 and acc.id not in balances:
                continue
            if acc.normal_balance == "debit":
                row_dr, row_cr = (net, Decimal("0")) if net >= 0 else (Decimal("0"), -net)
            else:
                row_cr, row_dr = (-net, Decimal("0")) if net <= 0 else (Decimal("0"), net)
            total_debit += row_dr
            total_credit += row_cr
            rows.append(
                {
                    "account_id": acc.id,
                    "code": acc.code,
                    "name": acc.name,
                    "type": acc.type,
                    "debit": _q(row_dr),
                    "credit": _q(row_cr),
                }
            )
        return {
            "as_of": as_of,
            "currency": accounts[0].currency if accounts else "ARS",
            "rows": rows,
            "total_debit": _q(total_debit),
            "total_credit": _q(total_credit),
            "balanced": abs(total_debit - total_credit) <= BALANCE_TOLERANCE,
        }

    async def account_activity(
        self,
        business_id: uuid.UUID,
        account_id: uuid.UUID,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        q = (
            select(JournalLine, JournalEntry)
            .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
            .where(
                JournalLine.business_id == business_id,
                JournalLine.account_id == account_id,
                JournalEntry.status == JournalStatus.POSTED.value,
            )
            .order_by(JournalEntry.entry_date.desc())
            .limit(limit)
        )
        if start:
            q = q.where(JournalEntry.entry_date >= start)
        if end:
            q = q.where(JournalEntry.entry_date < end)
        out = []
        for line, entry in (await self.db.execute(q)).all():
            out.append(
                {
                    "entry_id": entry.id,
                    "entry_number": entry.entry_number,
                    "date": entry.entry_date,
                    "memo": entry.memo,
                    "source": entry.source,
                    "debit": _q(line.debit),
                    "credit": _q(line.credit),
                }
            )
        return out

    async def list_entries(
        self,
        business_id: uuid.UUID,
        *,
        source: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[JournalEntry]:
        q = select(JournalEntry).where(JournalEntry.business_id == business_id)
        if source:
            q = q.where(JournalEntry.source == source)
        if status:
            q = q.where(JournalEntry.status == status)
        q = q.order_by(JournalEntry.entry_date.desc()).limit(limit)
        return list((await self.db.execute(q)).scalars().all())
