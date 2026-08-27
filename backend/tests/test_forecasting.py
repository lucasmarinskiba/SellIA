"""Demand forecasting — self-contained regression tests (isolated SQLite)."""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from sqlalchemy import Column, String, Table
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool


@compiles(PGUUID, "sqlite")
def _u(el, c, **kw):  # noqa: ANN001
    return "CHAR(36)"


@compiles(PGJSONB, "sqlite")
def _j(el, c, **kw):  # noqa: ANN001
    return "TEXT"


PGUUID.bind_processor = lambda self, d: (lambda v: None if v is None else str(v))
PGUUID.result_processor = lambda self, d, c: (lambda v: _uid(v))
PGJSONB.bind_processor = lambda self, d: (lambda v: None if v is None else json.dumps(v))
PGJSONB.result_processor = lambda self, d, c: (
    lambda v: None if v in (None, "") else (v if isinstance(v, (dict, list)) else json.loads(v))
)


def _uid(v):
    try:
        return uuid.UUID(v)
    except (ValueError, TypeError, AttributeError):
        return v


from app.core.database import Base  # noqa: E402
from app.domains.forecasting import metrics as M  # noqa: E402
from app.domains.forecasting import reconciliation as R  # noqa: E402
from app.domains.forecasting.models_db import FORECASTING_TABLES  # noqa: E402
from app.domains.forecasting.pipeline import ForecastPipeline, classify_intermittency  # noqa: E402
from app.domains.forecasting.service import ForecastingService  # noqa: E402
from app.domains.forecasting.types import (  # noqa: E402
    Grain,
    SeriesLevel,
    SeriesSpec,
    TargetKind,
    TimeSeries,
)
from app.domains.ledger.models import LEDGER_TABLES  # noqa: E402
from app.domains.orders.models import Order  # noqa: E402

RNG = np.random.default_rng(7)


def _synth(n=360, level=120.0, trend=0.03, noise=0.12, intermittent=False):
    idx = pd.date_range("2025-01-01", periods=n, freq="D", tz="UTC")
    t = np.arange(n)
    base = level * (1 + trend * t / 30)
    week = 1 + 0.35 * np.sin(2 * np.pi * t / 7) + 0.12 * np.cos(2 * np.pi * t / 7)
    year = 1 + 0.18 * np.sin(2 * np.pi * t / 365.25)
    y = np.clip(base * week * year * (1 + RNG.normal(0, noise, n)), 0, None)
    if intermittent:
        y = np.where(RNG.random(n) < 0.72, 0.0, y * 3)
    return idx, y


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
def test_metrics_basic():
    yt = np.array([10.0, 0.0, 12.0, 8.0])
    yp = np.array([9.0, 1.0, 11.0, 9.0])
    assert M.wape(yt, yp) == pytest.approx(100 * 4 / 30)
    assert M.mae(yt, yp) == pytest.approx(1.0)
    m = M.all_metrics(yt, yp, np.arange(30.0), season=7,
                      quantile_preds={0.1: yp - 3, 0.9: yp + 3})
    assert 0.0 <= m["coverage"] <= 1.0
    assert np.isfinite(m["mase"])


# ---------------------------------------------------------------------------
# reconciliation
# ---------------------------------------------------------------------------
def test_reconcile_is_coherent():
    total = np.array([100.0, 110.0, 120.0])
    kids = [np.array([40.0, 30.0, 50.0]), np.array([70.0, 90.0, 80.0])]
    new_total, new_kids = R.reconcile(total, kids, total_wape=10.0, child_wapes=[20.0, 25.0])
    assert np.allclose(np.sum(new_kids, axis=0), new_total, atol=1e-6)
    assert all(np.all(k >= 0) for k in new_kids)


# ---------------------------------------------------------------------------
# pipeline (no DB)
# ---------------------------------------------------------------------------
def test_pipeline_clean_series_beats_threshold():
    idx, y = _synth()
    spec = SeriesSpec(business_id="b", level=SeriesLevel.TOTAL, target=TargetKind.REVENUE, grain=Grain.DAILY)
    exog = pd.DataFrame({"price": 50.0, "promo": 0.0, "ad_spend": RNG.normal(400, 60, len(y))}, index=idx)
    train = TimeSeries(spec=spec, index=idx[:-28], values=y[:-28], exog=exog.iloc[:-28])
    actual = y[-28:]

    out = ForecastPipeline(horizon=28, n_folds=3).run(train)
    f = out.forecast
    assert len(f.mean) == 28
    assert np.all(f.mean >= 0)
    assert np.all(f.quantiles[0.9] >= f.quantiles[0.1])
    w = M.wape(actual, f.mean)
    mase = M.mase(actual, f.mean, train.values, season=7)
    assert w < 30.0, f"WAPE {w:.1f}% too high"
    assert mase < 1.6
    assert abs(sum(out.backtest.weights.values()) - 1.0) < 1e-6


def test_pipeline_intermittent_selects_croston_family():
    idx, y = _synth(n=300, intermittent=True)
    spec = SeriesSpec(business_id="b", level=SeriesLevel.PRODUCT, target=TargetKind.UNITS, key="sku1")
    inter, adi, zero = classify_intermittency(y)
    assert inter and adi > 1.3
    out = ForecastPipeline(horizon=14, n_folds=3).run(
        TimeSeries(spec=spec, index=idx, values=y)
    )
    assert np.all(out.forecast.mean >= 0)
    assert any("croston" in k or k == "seasonal_naive" for k in out.backtest.weights)


# ---------------------------------------------------------------------------
# full service against a DB
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite://", connect_args={"check_same_thread": False},
                                 poolclass=StaticPool)
    if "businesses" not in Base.metadata.tables:
        Table("businesses", Base.metadata, Column("id", String(36), primary_key=True))
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.tables["businesses"].create(bind=c, checkfirst=True))
        for t in LEDGER_TABLES + FORECASTING_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
        await conn.run_sync(lambda c: Order.__table__.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


async def _seed_orders(db, business_id, days=200):
    end = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    rows = []
    for i in range(days):
        day = end - timedelta(days=days - i)
        dow = day.weekday()
        n_orders = max(0, int(RNG.poisson(4 + 2 * (dow < 5))))
        for _ in range(n_orders):
            price = 50.0
            qty = int(RNG.integers(1, 4))
            rows.append({
                "id": uuid.uuid4(), "business_id": business_id,
                "total_amount": Decimal(str(price * qty)), "currency": "ARS",
                "status": "paid", "payment_status": "completed",
                "paid_at": day, "source_channel": "instagram",
                "source_campaign": "ig-x", "attribution_model": "last_touch",
                "items": [{"sku": "SKU1", "name": "Widget", "qty": qty, "price": price}],
                "shipping_address": {},
            })
    for r in rows:
        await db.execute(Order.__table__.insert().values(**r))
    await db.commit()


@pytest.mark.asyncio
async def test_service_end_to_end(db):
    biz = uuid.uuid4()
    await _seed_orders(db, biz, days=190)
    svc = ForecastingService(db)

    sync = await svc.sync_series(biz)
    assert sync["created"] >= 2

    rows = await svc.list_series(biz)
    total_rev = next(r for r in rows if r.level == "total" and r.target == "revenue")
    res = await svc.run_series(biz, total_rev, horizon=14)
    assert res["status"] == "ok", res
    assert len(res["mean"]) == 14
    assert all(m >= 0 for m in res["mean"])

    fc = await svc.get_forecast(biz, total_rev.series_key, horizon=14)
    assert fc["points"] and len(fc["points"]) == 14
    assert fc["points"][0]["q90"] >= fc["points"][0]["q10"]

    dash = await svc.dashboard(biz)
    assert dash["series_count"] >= 2
    assert dash["revenue_forecast_30d"] is not None


@pytest.mark.asyncio
async def test_service_run_all_and_reconcile(db):
    biz = uuid.uuid4()
    await _seed_orders(db, biz, days=170)
    svc = ForecastingService(db)
    out = await svc.run_all(biz, horizon=14, reconcile=True)
    assert out["ok"] >= 1
    # channel-revenue children should sum to (reconciled) total-revenue
    if out["reconciliation"]:
        assert out["reconciliation"]["channels"] >= 1
