"""Ad-budget autopilot — self-contained regression tests (isolated SQLite)."""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
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
def _uuid_sqlite(el, comp, **kw):  # noqa: ANN001
    return "CHAR(36)"


@compiles(PGJSONB, "sqlite")
def _jsonb_sqlite(el, comp, **kw):  # noqa: ANN001
    return "TEXT"


PGUUID.bind_processor = lambda self, d: (lambda v: None if v is None else str(v))
PGUUID.result_processor = lambda self, d, c: (
    lambda v: None if v is None else (_try_uuid(v))
)
PGJSONB.bind_processor = lambda self, d: (lambda v: None if v is None else json.dumps(v))
PGJSONB.result_processor = lambda self, d, c: (
    lambda v: None if v in (None, "") else (v if isinstance(v, (dict, list)) else json.loads(v))
)


def _try_uuid(v):
    try:
        return uuid.UUID(v)
    except (ValueError, TypeError, AttributeError):
        return v


from app.core.database import Base  # noqa: E402
from app.domains.ad_budget.models import AD_BUDGET_TABLES, AdPlatform  # noqa: E402
from app.domains.ad_budget.optimizer import ChannelInput, OptimizerConfig, optimize  # noqa: E402
from app.domains.ad_budget.service import AdBudgetService  # noqa: E402
from app.domains.ledger.models import LEDGER_TABLES  # noqa: E402
from app.domains.ledger.posting import PostingService  # noqa: E402
from app.domains.ledger.service import LedgerService  # noqa: E402
from app.domains.orders.models import Order  # noqa: E402


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    if "businesses" not in Base.metadata.tables:
        Table("businesses", Base.metadata, Column("id", String(36), primary_key=True))
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.tables["businesses"].create(bind=c, checkfirst=True))
        for t in LEDGER_TABLES + AD_BUDGET_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
        await conn.run_sync(lambda c: Order.__table__.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


async def _add_order(db, business_id, amount, channel, when):
    await db.execute(
        Order.__table__.insert().values(
            id=uuid.uuid4(),
            business_id=business_id,
            total_amount=Decimal(str(amount)),
            currency="ARS",
            status="paid",
            payment_status="completed",
            paid_at=when,
            source_channel=channel,
            source_campaign=f"{channel}-campaign-x",
            attribution_model="last_touch",
            items=[],
            shipping_address={},
        )
    )
    await db.commit()


# --------------------------------------------------------------------------
# optimizer
# --------------------------------------------------------------------------
def test_optimizer_shifts_to_best_roas():
    cfg = OptimizerConfig(target_roas=Decimal("2.0"), max_daily_shift_pct=Decimal("0.30"))
    r = optimize([
        ChannelInput("m", "meta", "Meta", Decimal("1000"), Decimal("1000"), Decimal("3500"), 40, Decimal("3.5")),
        ChannelInput("g", "google", "Google", Decimal("1000"), Decimal("1000"), Decimal("800"), 15, Decimal("0.8")),
    ], cfg)
    d = {x.name: x for x in r.decisions}
    assert d["Meta"].after > d["Meta"].before
    assert d["Google"].after < d["Google"].before
    assert abs(d["Meta"].after + d["Google"].after - r.pool) <= Decimal("0.05")


def test_optimizer_respects_max_shift_band():
    cfg = OptimizerConfig(target_roas=Decimal("2.0"), max_daily_shift_pct=Decimal("0.20"))
    r = optimize([
        ChannelInput("m", "meta", "Meta", Decimal("1000"), Decimal("1000"), Decimal("9000"), 90, Decimal("9.0")),
        ChannelInput("g", "google", "Google", Decimal("1000"), Decimal("1000"), Decimal("1900"), 20, Decimal("1.9")),
    ], cfg)
    meta = next(x for x in r.decisions if x.name == "Meta")
    assert meta.after <= Decimal("1200.00")  # +20% cap


def test_optimizer_kills_channel_below_threshold():
    cfg = OptimizerConfig(target_roas=Decimal("2.0"), kill_roas=Decimal("0.8"), allow_pause=True,
                          max_daily_shift_pct=Decimal("0.9"))
    r = optimize([
        ChannelInput("m", "meta", "Meta", Decimal("1000"), Decimal("1000"), Decimal("3000"), 40, Decimal("3.0")),
        ChannelInput("g", "google", "Google", Decimal("1000"), Decimal("1000"), Decimal("400"), 30, Decimal("0.4")),
    ], cfg)
    g = next(x for x in r.decisions if x.name == "Google")
    assert g.action == "pause" and g.after == Decimal("0")


def test_optimizer_noop_when_no_managed_channels():
    r = optimize([
        ChannelInput("m", "meta", "Meta", Decimal("1000"), Decimal("1000"), Decimal("3000"), 40, Decimal("3.0"),
                     is_managed=False),
    ], OptimizerConfig())
    assert r.noop


# --------------------------------------------------------------------------
# full cycle
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_cycle_recommend_only(db):
    biz = uuid.uuid4()
    svc = AdBudgetService(db)
    await svc.update_config(biz, is_active=True, requires_approval=True,
                            target_roas=Decimal("2.0"), optimization_window_days=14)

    await svc.create_channel(biz, platform=AdPlatform.META.value, display_name="Meta",
                             current_daily_budget=Decimal("1000"), attribution_match=["meta"])
    await svc.create_channel(biz, platform=AdPlatform.GOOGLE.value, display_name="Google",
                             current_daily_budget=Decimal("1000"), attribution_match=["google"])

    now = datetime.now(timezone.utc)
    # ledger spend
    await LedgerService(db).ensure_setup(biz)
    post = PostingService(db)
    await post.post_ad_spend(biz, platform="meta", amount=Decimal("700"), spend_ref="m-w1",
                             entry_date=now - timedelta(days=3))
    await post.post_ad_spend(biz, platform="google", amount=Decimal("700"), spend_ref="g-w1",
                             entry_date=now - timedelta(days=3))
    # revenue: meta converts well, google poorly
    await _add_order(db, biz, 3000, "meta", now - timedelta(days=2))
    await _add_order(db, biz, 300, "google", now - timedelta(days=2))

    res = await svc.run_cycle(biz)
    assert res["status"] == "ok"
    assert res["applied"] is False
    decisions = {d["name"]: d for d in res["decisions"]}
    assert decisions["Meta"]["after"] > decisions["Meta"]["before"]
    assert decisions["Google"]["after"] < decisions["Google"]["before"]

    dash = await svc.dashboard(biz)
    assert dash["pending_reallocation"] is not None
    assert dash["blended_roas"] > 0


@pytest.mark.asyncio
async def test_run_cycle_auto_apply_manual_required(db):
    biz = uuid.uuid4()
    svc = AdBudgetService(db)
    await svc.update_config(biz, is_active=True, requires_approval=False)
    await svc.create_channel(biz, platform=AdPlatform.GOOGLE.value, display_name="Google",
                             current_daily_budget=Decimal("1000"), attribution_match=["google"])
    await svc.create_channel(biz, platform=AdPlatform.TIKTOK.value, display_name="TikTok",
                             current_daily_budget=Decimal("1000"), attribution_match=["tiktok"])

    now = datetime.now(timezone.utc)
    await LedgerService(db).ensure_setup(biz)
    post = PostingService(db)
    await post.post_ad_spend(biz, platform="google", amount=Decimal("500"), spend_ref="g",
                             entry_date=now - timedelta(days=2))
    await post.post_ad_spend(biz, platform="tiktok", amount=Decimal("500"), spend_ref="t",
                             entry_date=now - timedelta(days=2))
    await _add_order(db, biz, 2000, "tiktok", now - timedelta(days=1))
    await _add_order(db, biz, 200, "google", now - timedelta(days=1))

    res = await svc.run_cycle(biz)
    assert res["status"] == "ok"
    assert res["applied"] is True
    # no connector linked -> manual_required, reallocation ends FAILED (nothing applied via API)
    hist = await svc.history(biz)
    assert hist[0].status in ("failed", "partially_applied")
    assert any(d.get("manual_required") for d in hist[0].decisions if d["action"] != "hold")


@pytest.mark.asyncio
async def test_run_cycle_skips_when_inactive(db):
    biz = uuid.uuid4()
    svc = AdBudgetService(db)
    await svc.create_channel(biz, platform=AdPlatform.META.value, display_name="Meta",
                             current_daily_budget=Decimal("1000"))
    res = await svc.run_cycle(biz)
    assert res["status"] == "skipped"
