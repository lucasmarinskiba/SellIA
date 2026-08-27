"""Double-entry ledger — self-contained regression tests.

Runs on an isolated in-process SQLite engine (StaticPool) with small
compile/roundtrip shims for the Postgres UUID/JSONB column types, so it
needs no external database.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from sqlalchemy import Column, String, Table, text
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool


@compiles(PGUUID, "sqlite")
def _uuid_sqlite(element, compiler, **kw):  # noqa: ANN001
    return "CHAR(36)"


@compiles(PGJSONB, "sqlite")
def _jsonb_sqlite(element, compiler, **kw):  # noqa: ANN001
    return "TEXT"


def _uuid_bind(self, dialect):  # noqa: ANN001
    return lambda v: None if v is None else str(v)


def _uuid_result(self, dialect, coltype):  # noqa: ANN001
    def process(v):
        if v is None:
            return None
        try:
            return uuid.UUID(v)
        except (ValueError, TypeError, AttributeError):
            return v
    return process


def _json_bind(self, dialect):  # noqa: ANN001
    return lambda v: None if v is None else json.dumps(v)


def _json_result(self, dialect, coltype):  # noqa: ANN001
    def process(v):
        if v is None or v == "":
            return None
        return v if isinstance(v, (dict, list)) else json.loads(v)
    return process


PGUUID.bind_processor = _uuid_bind
PGUUID.result_processor = _uuid_result
PGJSONB.bind_processor = _json_bind
PGJSONB.result_processor = _json_result

from app.core.database import Base  # noqa: E402
from app.domains.ledger.models import LEDGER_TABLES  # noqa: E402
from app.domains.ledger.posting import PostingService  # noqa: E402
from app.domains.ledger.reconciliation import ReconciliationService  # noqa: E402
from app.domains.ledger.reports import LedgerReports  # noqa: E402
from app.domains.ledger.service import LedgerError, LedgerService  # noqa: E402

AUG_START = datetime(2026, 8, 1, tzinfo=timezone.utc)
SEP_START = datetime(2026, 9, 1, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    if "businesses" not in Base.metadata.tables:
        Table("businesses", Base.metadata, Column("id", String(36), primary_key=True))
    biz_tbl = Base.metadata.tables["businesses"]
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: biz_tbl.create(bind=c, checkfirst=True))
        for t in LEDGER_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_setup_seeds_chart_of_accounts(db):
    biz = uuid.uuid4()
    result = await LedgerService(db).ensure_setup(biz, "ARS")
    assert result["accounts_created"] > 30
    assert result["current_period"] == datetime.now(timezone.utc).strftime("%Y-%m")
    # idempotent
    again = await LedgerService(db).ensure_setup(biz, "ARS")
    assert again["accounts_created"] == 0


@pytest.mark.asyncio
async def test_unbalanced_entry_rejected(db):
    biz = uuid.uuid4()
    svc = LedgerService(db)
    await svc.ensure_setup(biz)
    with pytest.raises(LedgerError):
        await svc.post_entry(
            biz,
            [
                {"account_subtype": "cash", "debit": Decimal("100")},
                {"account_subtype": "product_sales", "credit": Decimal("90")},
            ],
        )


@pytest.mark.asyncio
async def test_order_posting_and_statements(db):
    biz = uuid.uuid4()
    svc = LedgerService(db)
    await svc.ensure_setup(biz)
    post = PostingService(db)

    await post.post_order_paid(
        biz, order_id=uuid.uuid4(), total_amount=Decimal("12100"),
        tax_amount=Decimal("2100"), processing_fee=Decimal("400"),
        gateway="mercadopago", entry_date=datetime(2026, 8, 5, tzinfo=timezone.utc),
    )
    await post.post_ad_spend(
        biz, platform="meta", amount=Decimal("3000"), spend_ref="c1",
        entry_date=datetime(2026, 8, 6, tzinfo=timezone.utc),
    )

    tb = await svc.trial_balance(biz, SEP_START)
    assert tb["balanced"]
    assert tb["total_debit"] == tb["total_credit"]

    pnl = await LedgerReports(db).income_statement(biz, AUG_START, SEP_START)
    assert pnl["total_revenue"] == Decimal("10000.00")
    assert pnl["total_cogs"] == Decimal("400.00")       # gateway fee
    assert pnl["net_income"] == Decimal("6600.00")      # 10000 - 400 - 3000
    assert pnl["by_department"]["advertising"] == 3000.0

    bs = await LedgerReports(db).balance_sheet(biz, SEP_START)
    assert bs["balanced"]


@pytest.mark.asyncio
async def test_idempotent_posting(db):
    biz = uuid.uuid4()
    await LedgerService(db).ensure_setup(biz)
    post = PostingService(db)
    oid = uuid.uuid4()
    e1 = await post.post_order_paid(biz, order_id=oid, total_amount=Decimal("1000"), gateway="cash")
    e2 = await post.post_order_paid(biz, order_id=oid, total_amount=Decimal("1000"), gateway="cash")
    assert e1.id == e2.id


@pytest.mark.asyncio
async def test_reversal(db):
    biz = uuid.uuid4()
    svc = LedgerService(db)
    await svc.ensure_setup(biz)
    entry = await svc.post_entry(
        biz,
        [
            {"account_subtype": "cash", "debit": Decimal("500")},
            {"account_subtype": "other_income", "credit": Decimal("500")},
        ],
    )
    rev = await svc.reverse_entry(biz, entry.id, reason="test")
    assert rev.reversal_of_id == entry.id
    tb = await svc.trial_balance(biz, SEP_START)
    assert tb["total_debit"] == tb["total_credit"]
    # cash nets to zero
    cash = await svc.resolve_account(biz, subtype="cash")
    acts = await svc.account_activity(biz, cash.id)
    net = sum(a["debit"] - a["credit"] for a in acts)
    assert net == 0


@pytest.mark.asyncio
async def test_period_close_zeroes_income_accounts(db):
    biz = uuid.uuid4()
    svc = LedgerService(db)
    await svc.ensure_setup(biz)
    post = PostingService(db)
    await post.post_order_paid(
        biz, order_id=uuid.uuid4(), total_amount=Decimal("5000"),
        gateway="cash", entry_date=datetime(2026, 8, 10, tzinfo=timezone.utc),
    )
    res = await LedgerReports(db).close_period(biz, "2026-08")
    assert res["net_income"] == Decimal("5000.00")

    pnl_after = await LedgerReports(db).income_statement(biz, AUG_START, SEP_START)
    assert pnl_after["net_income"] == Decimal("0.00")

    # posting into a closed period is refused
    with pytest.raises(LedgerError):
        await post.post_order_paid(
            biz, order_id=uuid.uuid4(), total_amount=Decimal("1"),
            gateway="cash", entry_date=datetime(2026, 8, 20, tzinfo=timezone.utc),
        )


@pytest.mark.asyncio
async def test_bank_reconciliation_auto_match(db):
    biz = uuid.uuid4()
    svc = LedgerService(db)
    await svc.ensure_setup(biz)
    post = PostingService(db)
    await post.post_ad_spend(
        biz, platform="google", amount=Decimal("2500"), spend_ref="g1",
        entry_date=datetime(2026, 8, 6, tzinfo=timezone.utc),
    )
    rsvc = ReconciliationService(db)
    bank = await rsvc.create_bank_account(biz, name="Main", currency="ARS")
    imported = await rsvc.import_transactions(biz, bank.id, [
        {"txn_date": datetime(2026, 8, 6, tzinfo=timezone.utc),
         "description": "GOOGLE ADS", "amount": Decimal("-2500"), "external_id": "x1"},
    ])
    assert imported["inserted"] == 1
    # re-import is deduped
    again = await rsvc.import_transactions(biz, bank.id, [
        {"txn_date": datetime(2026, 8, 6, tzinfo=timezone.utc),
         "description": "GOOGLE ADS", "amount": Decimal("-2500"), "external_id": "x1"},
    ])
    assert again["inserted"] == 0

    recon = await rsvc.run_reconciliation(biz, bank.id)
    assert recon["auto_matched"] == 1
    assert recon["still_unmatched"] == 0
