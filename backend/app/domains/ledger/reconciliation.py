"""Bank statement import + reconciliation against the general ledger."""

from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ledger.models import (
    BankAccount,
    BankTransaction,
    BankTxnStatus,
    JournalEntry,
    JournalLine,
    JournalSource,
    JournalStatus,
    ReconciliationRule,
)
from app.domains.ledger.service import LedgerService, _q, _utcnow

logger = get_logger(__name__)

AMOUNT_TOLERANCE = Decimal("0.02")
DATE_WINDOW_DAYS = 5


class ReconciliationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)

    async def get_bank_account(
        self, business_id: uuid.UUID, bank_account_id: uuid.UUID
    ) -> BankAccount:
        res = await self.db.execute(
            select(BankAccount).where(
                BankAccount.id == bank_account_id,
                BankAccount.business_id == business_id,
            )
        )
        acc = res.scalar_one_or_none()
        if not acc:
            raise ValueError("bank account not found")
        return acc

    async def create_bank_account(self, business_id: uuid.UUID, **data: Any) -> BankAccount:
        acc = BankAccount(business_id=business_id, **data)
        self.db.add(acc)
        await self.db.commit()
        await self.db.refresh(acc)
        return acc

    # ------------------------------------------------------------------
    async def import_transactions(
        self,
        business_id: uuid.UUID,
        bank_account_id: uuid.UUID,
        transactions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        bank = await self.get_bank_account(business_id, bank_account_id)
        existing_res = await self.db.execute(
            select(BankTransaction.external_id).where(
                BankTransaction.bank_account_id == bank_account_id,
                BankTransaction.external_id.isnot(None),
            )
        )
        seen = {e for (e,) in existing_res.all()}

        inserted = 0
        for t in transactions:
            ext = t.get("external_id")
            if ext and ext in seen:
                continue
            self.db.add(
                BankTransaction(
                    business_id=business_id,
                    bank_account_id=bank_account_id,
                    txn_date=t["txn_date"],
                    description=t.get("description"),
                    amount=_q(t["amount"]),
                    currency=t.get("currency") or bank.currency,
                    external_id=ext,
                    raw=t.get("raw") or {},
                    status=BankTxnStatus.UNMATCHED.value,
                )
            )
            if ext:
                seen.add(ext)
            inserted += 1

        bank.last_synced_at = _utcnow()
        await self.db.commit()
        return {"received": len(transactions), "inserted": inserted, "skipped": len(transactions) - inserted}

    # ------------------------------------------------------------------
    async def run_reconciliation(
        self, business_id: uuid.UUID, bank_account_id: Optional[uuid.UUID] = None
    ) -> dict[str, Any]:
        q = select(BankTransaction).where(
            BankTransaction.business_id == business_id,
            BankTransaction.status == BankTxnStatus.UNMATCHED.value,
        )
        if bank_account_id:
            q = q.where(BankTransaction.bank_account_id == bank_account_id)
        txns = list((await self.db.execute(q)).scalars().all())

        rules = list(
            (
                await self.db.execute(
                    select(ReconciliationRule)
                    .where(
                        ReconciliationRule.business_id == business_id,
                        ReconciliationRule.is_active.is_(True),
                    )
                    .order_by(ReconciliationRule.priority)
                )
            ).scalars().all()
        )

        auto_matched = 0
        rule_categorized = 0
        for txn in txns:
            entry = await self._find_matching_entry(business_id, txn)
            if entry:
                txn.matched_entry_id = entry.id
                txn.status = BankTxnStatus.MATCHED.value
                txn.matched_at = _utcnow()
                txn.match_confidence = Decimal("0.95")
                txn.reconciled = True
                auto_matched += 1
                continue

            rule = self._first_matching_rule(rules, txn)
            if rule:
                await self._categorize(business_id, txn, account_id=rule.account_id,
                                       contact_type=rule.contact_type, contact_id=rule.contact_id)
                txn.match_confidence = Decimal("0.80")
                rule_categorized += 1

        await self.db.commit()
        still = sum(1 for t in txns if t.status == BankTxnStatus.UNMATCHED.value)
        return {
            "scanned": len(txns),
            "auto_matched": auto_matched,
            "rule_categorized": rule_categorized,
            "still_unmatched": still,
        }

    async def _find_matching_entry(
        self, business_id: uuid.UUID, txn: BankTransaction
    ) -> Optional[JournalEntry]:
        """Match a bank movement to an existing posted entry whose net cash
        movement equals the bank amount, within a date window."""
        lo = txn.txn_date - timedelta(days=DATE_WINDOW_DAYS)
        hi = txn.txn_date + timedelta(days=DATE_WINDOW_DAYS)
        cash_ids = await self._cash_account_ids(business_id)
        if not cash_ids:
            return None

        rows = (
            await self.db.execute(
                select(JournalLine, JournalEntry)
                .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
                .where(
                    JournalLine.business_id == business_id,
                    JournalLine.account_id.in_(cash_ids),
                    JournalEntry.status == JournalStatus.POSTED.value,
                    JournalEntry.entry_date >= lo,
                    JournalEntry.entry_date <= hi,
                )
            )
        ).all()

        by_entry: dict[uuid.UUID, tuple[JournalEntry, Decimal]] = {}
        for line, entry in rows:
            _, delta = by_entry.get(entry.id, (entry, Decimal("0")))
            by_entry[entry.id] = (entry, delta + (line.debit - line.credit))

        for entry, delta in by_entry.values():
            already = await self.db.execute(
                select(BankTransaction.id).where(BankTransaction.matched_entry_id == entry.id)
            )
            if already.first():
                continue
            if abs(_q(delta) - _q(txn.amount)) <= AMOUNT_TOLERANCE:
                return entry
        return None

    def _first_matching_rule(
        self, rules: list[ReconciliationRule], txn: BankTransaction
    ) -> Optional[ReconciliationRule]:
        desc = (txn.description or "").lower()
        amt = _q(txn.amount)
        direction = "inflow" if amt >= 0 else "outflow"
        for rule in rules:
            if rule.match_contains and rule.match_contains.lower() not in desc:
                continue
            if rule.direction and rule.direction != "any" and rule.direction != direction:
                continue
            mag = abs(amt)
            if rule.match_min_amount is not None and mag < _q(rule.match_min_amount):
                continue
            if rule.match_max_amount is not None and mag > _q(rule.match_max_amount):
                continue
            return rule
        return None

    async def _cash_account_ids(self, business_id: uuid.UUID) -> list[uuid.UUID]:
        accounts = await self.ledger.get_accounts(business_id)
        return [
            a.id for a in accounts
            if a.type == "asset" and (a.subtype or "").startswith("cash")
        ]

    async def _default_cash_account_id(self, business_id: uuid.UUID) -> uuid.UUID:
        acc = await self.ledger.resolve_account(business_id, subtype="cash")
        return acc.id

    async def _categorize(
        self,
        business_id: uuid.UUID,
        txn: BankTransaction,
        *,
        account_id: uuid.UUID,
        contact_type: Optional[str] = None,
        contact_id: Optional[uuid.UUID] = None,
    ) -> JournalEntry:
        """Post a categorization entry for an uncategorized bank movement."""
        cash_id = await self._default_cash_account_id(business_id)
        amt = _q(abs(txn.amount))
        if txn.amount >= 0:  # inflow: Dr cash / Cr category
            lines = [
                {"account_id": cash_id, "debit": amt, "description": txn.description or "Ingreso banco"},
                {"account_id": account_id, "credit": amt, "description": txn.description or "Ingreso",
                 "contact_type": contact_type, "contact_id": contact_id},
            ]
        else:  # outflow: Dr category / Cr cash
            lines = [
                {"account_id": account_id, "debit": amt, "description": txn.description or "Egreso",
                 "contact_type": contact_type, "contact_id": contact_id},
                {"account_id": cash_id, "credit": amt, "description": txn.description or "Egreso banco"},
            ]
        entry = await self.ledger.post_entry(
            business_id,
            lines,
            entry_date=txn.txn_date,
            memo=f"Conciliación bancaria: {txn.description or txn.id}",
            source=JournalSource.BANK.value,
            source_ref=str(txn.id),
            idempotency_key=f"bank_txn:{business_id}:{txn.id}",
            currency=txn.currency,
        )
        txn.matched_entry_id = entry.id
        txn.status = BankTxnStatus.MATCHED.value
        txn.matched_at = _utcnow()
        txn.reconciled = True
        return entry

    # ------------------------------------------------------------------
    async def manual_match(
        self, business_id: uuid.UUID, txn_id: uuid.UUID, entry_id: uuid.UUID
    ) -> BankTransaction:
        res = await self.db.execute(
            select(BankTransaction).where(
                BankTransaction.id == txn_id,
                BankTransaction.business_id == business_id,
            )
        )
        txn = res.scalar_one_or_none()
        if not txn:
            raise ValueError("bank transaction not found")
        txn.matched_entry_id = entry_id
        txn.status = BankTxnStatus.MATCHED.value
        txn.matched_at = _utcnow()
        txn.match_confidence = Decimal("1.0")
        txn.reconciled = True
        await self.db.commit()
        await self.db.refresh(txn)
        return txn

    async def manual_categorize(
        self,
        business_id: uuid.UUID,
        txn_id: uuid.UUID,
        *,
        account_id: Optional[uuid.UUID] = None,
        account_subtype: Optional[str] = None,
    ) -> JournalEntry:
        res = await self.db.execute(
            select(BankTransaction).where(
                BankTransaction.id == txn_id,
                BankTransaction.business_id == business_id,
            )
        )
        txn = res.scalar_one_or_none()
        if not txn:
            raise ValueError("bank transaction not found")
        if account_id is None:
            acc = await self.ledger.resolve_account(business_id, subtype=account_subtype)
            account_id = acc.id
        entry = await self._categorize(business_id, txn, account_id=account_id)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def list_transactions(
        self,
        business_id: uuid.UUID,
        *,
        status: Optional[str] = None,
        bank_account_id: Optional[uuid.UUID] = None,
        limit: int = 200,
    ) -> list[BankTransaction]:
        q = select(BankTransaction).where(BankTransaction.business_id == business_id)
        if status:
            q = q.where(BankTransaction.status == status)
        if bank_account_id:
            q = q.where(BankTransaction.bank_account_id == bank_account_id)
        q = q.order_by(BankTransaction.txn_date.desc()).limit(limit)
        return list((await self.db.execute(q)).scalars().all())

    async def create_rule(self, business_id: uuid.UUID, **data: Any) -> ReconciliationRule:
        rule = ReconciliationRule(business_id=business_id, **data)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule
