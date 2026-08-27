"""Ledger Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AccountCreate(BaseModel):
    code: str
    name: str
    type: str  # asset|liability|equity|revenue|expense
    subtype: Optional[str] = None
    currency: str = "ARS"
    parent_id: Optional[UUID] = None
    description: Optional[str] = None
    tax_code: Optional[str] = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    parent_id: Optional[UUID]
    code: str
    name: str
    type: str
    subtype: Optional[str]
    normal_balance: str
    currency: str
    is_active: bool
    is_system: bool


class JournalLineInput(BaseModel):
    account_id: Optional[UUID] = None
    account_code: Optional[str] = None
    account_subtype: Optional[str] = None
    description: Optional[str] = None
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    contact_type: Optional[str] = None
    contact_id: Optional[UUID] = None
    tax_code: Optional[str] = None

    @model_validator(mode="after")
    def _one_side_only(self) -> "JournalLineInput":
        if self.debit < 0 or self.credit < 0:
            raise ValueError("debit/credit must be non-negative")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("a line cannot have both a debit and a credit")
        if self.debit == 0 and self.credit == 0:
            raise ValueError("a line must have a non-zero debit or credit")
        if not (self.account_id or self.account_code or self.account_subtype):
            raise ValueError("account_id, account_code or account_subtype is required")
        return self


class JournalEntryCreate(BaseModel):
    entry_date: Optional[datetime] = None
    memo: Optional[str] = None
    source: str = "manual"
    source_ref: Optional[str] = None
    idempotency_key: Optional[str] = None
    currency: str = "ARS"
    lines: list[JournalLineInput] = Field(min_length=2)


class JournalLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    account_id: UUID
    description: Optional[str]
    debit: Decimal
    credit: Decimal
    currency: str
    contact_type: Optional[str]
    contact_id: Optional[UUID]
    tax_code: Optional[str]


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    period_id: Optional[UUID]
    entry_number: str
    entry_date: datetime
    memo: Optional[str]
    source: str
    source_ref: Optional[str]
    status: str
    posted_at: Optional[datetime]
    reversal_of_id: Optional[UUID]
    total_debit: Decimal
    total_credit: Decimal
    currency: str
    lines: list[JournalLineResponse] = []


class TrialBalanceRow(BaseModel):
    account_id: UUID
    code: str
    name: str
    type: str
    debit: Decimal
    credit: Decimal


class TrialBalanceResponse(BaseModel):
    as_of: datetime
    currency: str
    rows: list[TrialBalanceRow]
    total_debit: Decimal
    total_credit: Decimal
    balanced: bool


class IncomeStatementResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    currency: str
    revenue: dict
    total_revenue: Decimal
    cogs: dict
    total_cogs: Decimal
    gross_profit: Decimal
    operating_expenses: dict
    total_operating_expenses: Decimal
    operating_income: Decimal
    net_income: Decimal
    by_department: dict


class BalanceSheetResponse(BaseModel):
    as_of: datetime
    currency: str
    assets: dict
    total_assets: Decimal
    liabilities: dict
    total_liabilities: Decimal
    equity: dict
    total_equity: Decimal
    retained_plus_current: Decimal
    balanced: bool


class CashFlowStatementResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    currency: str
    operating: dict
    investing: dict
    financing: dict
    net_change: Decimal
    opening_cash: Decimal
    closing_cash: Decimal


class PeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    name: str
    period_start: datetime
    period_end: datetime
    status: str
    closed_at: Optional[datetime]
    net_income: Optional[Decimal]


class PeriodCloseResult(BaseModel):
    period: PeriodResponse
    closing_entry_id: Optional[UUID]
    net_income: Decimal
    message: str


class BankTransactionImport(BaseModel):
    txn_date: datetime
    description: Optional[str] = None
    amount: Decimal
    currency: str = "ARS"
    external_id: Optional[str] = None
    raw: dict = {}


class BankImportRequest(BaseModel):
    bank_account_id: UUID
    transactions: list[BankTransactionImport]


class BankTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    bank_account_id: UUID
    txn_date: datetime
    description: Optional[str]
    amount: Decimal
    currency: str
    status: str
    matched_entry_id: Optional[UUID]
    match_confidence: Optional[Decimal]
    reconciled: bool


class ReconcileRunResponse(BaseModel):
    scanned: int
    auto_matched: int
    rule_categorized: int
    still_unmatched: int
