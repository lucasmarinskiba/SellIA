"""Ledger models — double-entry general ledger.

Tables
------
ledger_accounts        Chart of accounts (per business, hierarchical).
accounting_periods     Monthly/annual periods with open/closed/locked state.
journal_entries        Balanced entries (sum debit == sum credit).
journal_lines          Individual debit/credit postings against an account.
bank_accounts          Real bank / wallet accounts mapped to a GL account.
bank_transactions      Imported bank movements awaiting reconciliation.
reconciliation_rules   Auto-categorisation rules for bank transactions.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AccountType(str, enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class NormalBalance(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


# Which side increases a balance, by account type (standard accounting).
NORMAL_BALANCE_BY_TYPE: dict[str, str] = {
    AccountType.ASSET.value: NormalBalance.DEBIT.value,
    AccountType.EXPENSE.value: NormalBalance.DEBIT.value,
    AccountType.LIABILITY.value: NormalBalance.CREDIT.value,
    AccountType.EQUITY.value: NormalBalance.CREDIT.value,
    AccountType.REVENUE.value: NormalBalance.CREDIT.value,
}


class PeriodStatus(str, enum.Enum):
    OPEN = "open"          # postings allowed
    CLOSED = "closed"      # soft close — reopenable by an admin
    LOCKED = "locked"      # hard close — immutable (tax filed)


class JournalStatus(str, enum.Enum):
    DRAFT = "draft"
    POSTED = "posted"
    VOID = "void"


class JournalSource(str, enum.Enum):
    MANUAL = "manual"
    ORDER = "order"
    REFUND = "refund"
    PAYOUT = "payout"
    AD_SPEND = "ad_spend"
    SUBSCRIPTION = "subscription"
    INVOICE = "invoice"
    BANK = "bank"
    ADJUSTMENT = "adjustment"
    CLOSING = "closing"
    OPENING = "opening"


class BankTxnStatus(str, enum.Enum):
    UNMATCHED = "unmatched"
    MATCHED = "matched"
    IGNORED = "ignored"


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id", ondelete="SET NULL"), nullable=True)

    code = Column(String(20), nullable=False)          # e.g. "1000", "4000.01"
    name = Column(String(160), nullable=False)
    type = Column(String(20), nullable=False)          # AccountType
    subtype = Column(String(60), nullable=True)        # "cash", "accounts_receivable", "cogs"...
    normal_balance = Column(String(10), nullable=False)  # NormalBalance
    currency = Column(String(3), default="ARS", nullable=False)

    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # seeded, cannot be deleted
    tax_code = Column(String(30), nullable=True)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    lines = relationship("JournalLine", back_populates="account", lazy="noload")

    __table_args__ = (
        UniqueConstraint("business_id", "code", name="uq_ledger_account_business_code"),
        Index("ix_ledger_accounts_business_type", "business_id", "type"),
    )


class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(20), nullable=False)          # "2026-08"
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(10), default=PeriodStatus.OPEN.value, nullable=False)

    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(UUID(as_uuid=True), nullable=True)
    closing_entry_id = Column(UUID(as_uuid=True), nullable=True)
    net_income = Column(Numeric(18, 2), nullable=True)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_accounting_period_business_name"),
        Index("ix_accounting_periods_business_status", "business_id", "status"),
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    period_id = Column(UUID(as_uuid=True), ForeignKey("accounting_periods.id", ondelete="SET NULL"), nullable=True)

    entry_number = Column(String(40), nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    memo = Column(Text, nullable=True)

    source = Column(String(20), default=JournalSource.MANUAL.value, nullable=False)
    source_ref = Column(String(120), nullable=True, index=True)   # order id, payout id...
    idempotency_key = Column(String(160), nullable=True)

    status = Column(String(10), default=JournalStatus.DRAFT.value, nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    reversal_of_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True)

    total_debit = Column(Numeric(18, 2), default=0, nullable=False)
    total_credit = Column(Numeric(18, 2), default=0, nullable=False)
    currency = Column(String(3), default="ARS", nullable=False)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    lines = relationship(
        "JournalLine",
        back_populates="entry",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("business_id", "entry_number", name="uq_journal_entry_business_number"),
        UniqueConstraint("business_id", "idempotency_key", name="uq_journal_entry_business_idem"),
        Index("ix_journal_entries_business_date", "business_id", "entry_date"),
        Index("ix_journal_entries_business_status", "business_id", "status"),
        Index("ix_journal_entries_business_source", "business_id", "source", "source_ref"),
    )


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)

    description = Column(Text, nullable=True)
    debit = Column(Numeric(18, 2), default=0, nullable=False)
    credit = Column(Numeric(18, 2), default=0, nullable=False)
    currency = Column(String(3), default="ARS", nullable=False)
    fx_rate = Column(Numeric(18, 8), default=1, nullable=False)
    base_amount = Column(Numeric(18, 2), default=0, nullable=False)  # signed, in business base currency

    contact_type = Column(String(20), nullable=True)   # customer / vendor / employee
    contact_id = Column(UUID(as_uuid=True), nullable=True)
    tax_code = Column(String(30), nullable=True)
    line_index = Column(Integer, default=0, nullable=False)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("LedgerAccount", back_populates="lines")

    __table_args__ = (
        Index("ix_journal_lines_business_account", "business_id", "account_id"),
    )


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(120), nullable=False)
    institution = Column(String(120), nullable=True)
    account_ref_masked = Column(String(60), nullable=True)   # "****4321"
    provider = Column(String(40), nullable=True)              # mercadopago, stripe, manual, plaid...
    currency = Column(String(3), default="ARS", nullable=False)

    current_balance = Column(Numeric(18, 2), default=0, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    txn_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(18, 2), nullable=False)   # signed: +inflow / -outflow
    currency = Column(String(3), default="ARS", nullable=False)
    external_id = Column(String(160), nullable=True)

    status = Column(String(12), default=BankTxnStatus.UNMATCHED.value, nullable=False)
    matched_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True)
    matched_at = Column(DateTime(timezone=True), nullable=True)
    match_confidence = Column(Numeric(5, 4), nullable=True)
    reconciled = Column(Boolean, default=False, nullable=False)

    raw = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("bank_account_id", "external_id", name="uq_bank_txn_account_external"),
        Index("ix_bank_transactions_business_status", "business_id", "status"),
    )


class ReconciliationRule(Base):
    __tablename__ = "reconciliation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(120), nullable=False)
    match_contains = Column(String(200), nullable=True)   # substring in description (case-insensitive)
    match_min_amount = Column(Numeric(18, 2), nullable=True)
    match_max_amount = Column(Numeric(18, 2), nullable=True)
    direction = Column(String(10), nullable=True)         # inflow / outflow / any
    contact_type = Column(String(20), nullable=True)
    contact_id = Column(UUID(as_uuid=True), nullable=True)
    priority = Column(Integer, default=100, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# Convenience export used by the bootstrap/create_all helper.
LEDGER_TABLES = [
    LedgerAccount.__table__,
    AccountingPeriod.__table__,
    JournalEntry.__table__,
    JournalLine.__table__,
    BankAccount.__table__,
    BankTransaction.__table__,
    ReconciliationRule.__table__,
]
