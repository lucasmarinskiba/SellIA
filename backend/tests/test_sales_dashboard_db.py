"""Sales dashboard over HTTP against a real (SQLite) database.

The dashboard used to answer with random numbers and hard-coded figures. These tests
pin the numbers to deals this test inserts, and the access rules:

* no login             -> 401
* someone else's id    -> 403
* a malformed id       -> 422
* the owner            -> numbers computed from their deals, in the shape the apps read
* an owner with no deals (or no business) -> zeros, not someone else's numbers

No Postgres needed. JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import enterprise_analytics
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.models import Business
from app.domains.crm.models import Deal, LeadStage


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


MODELS = [Business, Deal]
NOW = datetime.now(timezone.utc)
OWNER = SimpleNamespace(id=uuid.uuid4())
STRANGER = SimpleNamespace(id=uuid.uuid4())
NO_DEALS = SimpleNamespace(id=uuid.uuid4())


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _deal(business_id, **fields) -> Deal:
    base = {"title": "Negocio", "currency": "ARS", "probability": 10, "is_active": True}
    base.update(fields)
    return Deal(business_id=business_id, **base)


@pytest_asyncio.fixture
async def world(factory):
    async with factory() as s:
        biz = Business(user_id=OWNER.id, name="Tienda")
        s.add(biz)
        await s.flush()
        s.add_all([
            # Won, inside the last 30 days: counts.
            _deal(biz.id, value=Decimal("100"), stage=LeadStage.CLOSED_WON, probability=100,
                  actual_close_date=NOW - timedelta(days=2)),
            _deal(biz.id, value=Decimal("300"), stage=LeadStage.CLOSED_WON, probability=100,
                  actual_close_date=NOW - timedelta(days=10)),
            # Won 60 days ago: outside the month window.
            _deal(biz.id, value=Decimal("9999"), stage=LeadStage.CLOSED_WON, probability=100,
                  actual_close_date=NOW - timedelta(days=60)),
            # Lost inside the window: lowers the close rate, adds no revenue.
            _deal(biz.id, value=Decimal("500"), stage=LeadStage.CLOSED_LOST, probability=0,
                  actual_close_date=NOW - timedelta(days=3)),
            # Open and due within 30 days: pipeline + forecast + projected revenue.
            _deal(biz.id, value=Decimal("500"), stage=LeadStage.QUALIFIED, probability=50,
                  expected_close_date=NOW + timedelta(days=5)),
            # Open, due in 90 days: pipeline + forecast, not projected.
            _deal(biz.id, value=Decimal("100"), stage=LeadStage.NEW_LEAD, probability=10,
                  expected_close_date=NOW + timedelta(days=90)),
            # Another currency: never added to the ARS totals.
            _deal(biz.id, value=Decimal("1000"), currency="USD", stage=LeadStage.QUALIFIED, probability=50),
            # Deactivated: ignored entirely.
            _deal(biz.id, value=Decimal("7777"), stage=LeadStage.QUALIFIED, probability=50, is_active=False),
        ])
        await s.commit()
    return SimpleNamespace(factory=factory)


def _build_app(factory, who) -> FastAPI:
    app = FastAPI()
    app.include_router(enterprise_analytics.router, prefix="/api/v1")  # as in app/main.py

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:  # None -> keep the real get_current_user, so no token is rejected
        app.dependency_overrides[get_current_user] = lambda: who
    return app


def _client(factory, who=OWNER) -> httpx.AsyncClient:
    app = _build_app(factory, who)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_owner_gets_numbers_computed_from_their_deals(world):
    async with _client(world.factory) as client:
        res = await client.get(f"/api/v1/analytics/dashboard/{OWNER.id}")

    assert res.status_code == 200
    body = res.json()
    assert body["currency"] == "ARS"
    assert body["other_currency_deals"] == 1  # the USD deal is counted, not summed
    # Shape the mobile app reads, top level.
    assert body["total_pipeline"] == 600.0  # 500 + 100 open
    assert body["deals_this_month"] == 2  # the two wins in the window
    assert body["avg_deal_value"] == 200.0  # (100 + 300) / 2
    assert body["close_rate"] == pytest.approx(2 / 3, abs=1e-4)  # 2 won / (2 won + 1 lost)
    assert body["revenue_forecast"] == 260.0  # 500 * 50% + 100 * 10%
    # Shape the enterprise web reads.
    assert [card["label"] for card in body["kpi_cards"]] == [
        "Pipeline abierto", "Ventas cerradas", "Ticket promedio", "Tasa de cierre", "Forecast ponderado",
    ]
    assert all(card["trend"] is None for card in body["kpi_cards"])  # no invented trends
    assert body["pipeline"]["total_value"] == 600.0
    assert body["pipeline"]["projected_revenue_30d"] == 250.0  # only the deal due within 30 days
    assert body["pipeline"]["stages"] == {"qualified": 1, "new_lead": 1}
    assert body["pipeline"]["forecast_confidence"] is None
    assert body["agent_performance"] == []
    assert body["segment_benchmarks"] is None


@pytest.mark.asyncio
async def test_shorter_window_counts_fewer_wins(world):
    async with _client(world.factory) as client:
        res = await client.get(f"/api/v1/analytics/dashboard/{OWNER.id}", params={"time_range": "week"})

    body = res.json()
    assert body["deals_this_month"] == 1  # only the win two days ago is inside 7 days
    assert body["close_rate"] == pytest.approx(1 / 2, abs=1e-4)  # 1 won / (1 won + 1 lost)


@pytest.mark.asyncio
async def test_someone_elses_dashboard_is_refused(world):
    async with _client(world.factory, who=STRANGER) as client:
        res = await client.get(f"/api/v1/analytics/dashboard/{OWNER.id}")

    assert res.status_code == 403


@pytest.mark.asyncio
async def test_no_login_is_refused(world):
    async with _client(world.factory, who=None) as client:
        res = await client.get(f"/api/v1/analytics/dashboard/{OWNER.id}")

    assert res.status_code == 401


@pytest.mark.asyncio
async def test_malformed_id_and_unknown_window_are_rejected(world):
    async with _client(world.factory) as client:
        bad_id = await client.get("/api/v1/analytics/dashboard/not-a-uuid")
        bad_window = await client.get(f"/api/v1/analytics/dashboard/{OWNER.id}", params={"time_range": "decade"})

    assert bad_id.status_code == 422
    assert bad_window.status_code == 422


@pytest.mark.asyncio
async def test_account_without_deals_sees_zeros(world):
    async with _client(world.factory, who=NO_DEALS) as client:
        res = await client.get(f"/api/v1/analytics/dashboard/{NO_DEALS.id}")

    assert res.status_code == 200
    body = res.json()
    assert body["total_pipeline"] == 0.0
    assert body["deals_this_month"] == 0
    assert body["close_rate"] == 0.0
    assert body["pipeline"]["stages"] == {}
    assert body["currency"] == "ARS"  # default when there is nothing to take the currency from
