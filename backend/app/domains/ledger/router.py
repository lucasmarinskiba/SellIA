"""Ledger API — /api/v1/businesses/{business_id}/ledger/*"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.ledger.posting import PostingService
from app.domains.ledger.reconciliation import ReconciliationService
from app.domains.ledger.reports import LedgerReports
from app.domains.ledger.schemas import (
    AccountCreate,
    AccountResponse,
    BalanceSheetResponse,
    BankImportRequest,
    BankTransactionResponse,
    CashFlowStatementResponse,
    IncomeStatementResponse,
    JournalEntryCreate,
    JournalEntryResponse,
    PeriodCloseResult,
    PeriodResponse,
    ReconcileRunResponse,
    TrialBalanceResponse,
)
from app.domains.ledger.service import LedgerError, LedgerService, PeriodLockedError
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/ledger", tags=["Ledger"])


def _month_range(month: int, year: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, PeriodLockedError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, LedgerError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# Setup + chart of accounts
# ---------------------------------------------------------------------------
@router.post("/setup")
async def setup_ledger(
    business_id: UUID,
    currency: str = Query("ARS"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LedgerService(db).ensure_setup(business_id, currency)


@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(
    business_id: UUID,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LedgerService(db).get_accounts(business_id, active_only=active_only)


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    business_id: UUID,
    body: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await LedgerService(db).create_account(business_id, **body.model_dump(exclude_none=True))
    except Exception as e:  # noqa: BLE001
        raise _handle(e)


# ---------------------------------------------------------------------------
# Journal entries
# ---------------------------------------------------------------------------
@router.post("/journal-entries", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    business_id: UUID,
    body: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = LedgerService(db)
    lines = [ln.model_dump(exclude_none=True) for ln in body.lines]
    try:
        return await svc.post_entry(
            business_id,
            lines,
            entry_date=body.entry_date,
            memo=body.memo,
            source=body.source,
            source_ref=body.source_ref,
            idempotency_key=body.idempotency_key,
            created_by=getattr(current_user, "id", None),
            currency=body.currency,
        )
    except Exception as e:  # noqa: BLE001
        raise _handle(e)


@router.get("/journal-entries", response_model=list[JournalEntryResponse])
async def list_journal_entries(
    business_id: UUID,
    source: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LedgerService(db).list_entries(business_id, source=source, status=status_filter, limit=limit)


@router.post("/journal-entries/{entry_id}/reverse", response_model=JournalEntryResponse)
async def reverse_journal_entry(
    business_id: UUID,
    entry_id: UUID,
    reason: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await LedgerService(db).reverse_entry(
            business_id, entry_id, reason=reason, created_by=getattr(current_user, "id", None)
        )
    except Exception as e:  # noqa: BLE001
        raise _handle(e)


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------
@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def trial_balance(
    business_id: UUID,
    as_of: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LedgerService(db).trial_balance(business_id, as_of)


@router.get("/reports/income-statement", response_model=IncomeStatementResponse)
async def income_statement(
    business_id: UUID,
    month: int = Query(datetime.now(timezone.utc).month, ge=1, le=12),
    year: int = Query(datetime.now(timezone.utc).year, ge=2020, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start, end = _month_range(month, year)
    return await LedgerReports(db).income_statement(business_id, start, end)


@router.get("/reports/balance-sheet", response_model=BalanceSheetResponse)
async def balance_sheet(
    business_id: UUID,
    as_of: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LedgerReports(db).balance_sheet(business_id, as_of)


@router.get("/reports/cash-flow", response_model=CashFlowStatementResponse)
async def cash_flow(
    business_id: UUID,
    month: int = Query(datetime.now(timezone.utc).month, ge=1, le=12),
    year: int = Query(datetime.now(timezone.utc).year, ge=2020, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start, end = _month_range(month, year)
    return await LedgerReports(db).cash_flow_statement(business_id, start, end)


# ---------------------------------------------------------------------------
# Periods
# ---------------------------------------------------------------------------
@router.get("/periods", response_model=list[PeriodResponse])
async def list_periods(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LedgerService(db).get_periods(business_id)


@router.post("/periods/{period_name}/close", response_model=PeriodCloseResult)
async def close_period(
    business_id: UUID,
    period_name: str,
    lock: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await LedgerReports(db).close_period(
            business_id, period_name, user_id=getattr(current_user, "id", None), lock=lock
        )
    except Exception as e:  # noqa: BLE001
        raise _handle(e)


@router.post("/periods/{period_name}/reopen", response_model=PeriodResponse)
async def reopen_period(
    business_id: UUID,
    period_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await LedgerReports(db).reopen_period(business_id, period_name)
    except Exception as e:  # noqa: BLE001
        raise _handle(e)


@router.post("/backfill-orders")
async def backfill_orders(
    business_id: UUID,
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await LedgerService(db).ensure_setup(business_id)
    return await PostingService(db).backfill_orders(business_id, limit=limit)


# ---------------------------------------------------------------------------
# Bank reconciliation
# ---------------------------------------------------------------------------
@router.post("/bank-accounts", status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    business_id: UUID,
    name: str,
    currency: str = "ARS",
    institution: str | None = None,
    provider: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acc = await ReconciliationService(db).create_bank_account(
        business_id, name=name, currency=currency, institution=institution, provider=provider
    )
    return {"id": str(acc.id), "name": acc.name, "currency": acc.currency}


@router.post("/bank/import")
async def import_bank_transactions(
    business_id: UUID,
    body: BankImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ReconciliationService(db).import_transactions(
            business_id,
            body.bank_account_id,
            [t.model_dump() for t in body.transactions],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bank/reconcile", response_model=ReconcileRunResponse)
async def run_reconciliation(
    business_id: UUID,
    bank_account_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ReconciliationService(db).run_reconciliation(business_id, bank_account_id)


@router.get("/bank/transactions", response_model=list[BankTransactionResponse])
async def list_bank_transactions(
    business_id: UUID,
    status_filter: str | None = Query(None, alias="status"),
    bank_account_id: UUID | None = None,
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ReconciliationService(db).list_transactions(
        business_id, status=status_filter, bank_account_id=bank_account_id, limit=limit
    )


@router.post("/bank/transactions/{txn_id}/categorize", response_model=JournalEntryResponse)
async def categorize_bank_transaction(
    business_id: UUID,
    txn_id: UUID,
    account_subtype: str | None = None,
    account_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ReconciliationService(db).manual_categorize(
            business_id, txn_id, account_id=account_id, account_subtype=account_subtype
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise _handle(e)


@router.post("/bank/rules", status_code=status.HTTP_201_CREATED)
async def create_reconciliation_rule(
    business_id: UUID,
    name: str,
    account_id: UUID,
    match_contains: str | None = None,
    direction: str | None = None,
    priority: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = await ReconciliationService(db).create_rule(
        business_id,
        name=name,
        account_id=account_id,
        match_contains=match_contains,
        direction=direction,
        priority=priority,
    )
    return {"id": str(rule.id), "name": rule.name}
