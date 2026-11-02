"""Channel rankings over HTTP against a real (SQLite) database.

The ranking used to be built from a fixed mock engine. These tests pin it to deals
inserted here, and the access rules:

* no login             -> 401
* someone else's id    -> 403
* the owner            -> channels ranked by won revenue in the window
* channel names are normalised ("Instagram " and "instagram" are one channel)
* a channel with no closed deals in the window gets conversion None, not a made-up rate

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

from app.api.v1 import advanced_automation
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
            _deal(biz.id, source_channel="instagram", value=Decimal("500"), stage=LeadStage.CLOSED_WON,
                  actual_close_date=NOW - timedelta(days=2)),
            _deal(biz.id, source_channel=" Instagram ", value=Decimal("300"), stage=LeadStage.CLOSED_WON,
                  actual_close_date=NOW - timedelta(days=10)),
            # Won, but 60 days ago: counted as a deal, not as a win in the month window.
            _deal(biz.id, source_channel="instagram", value=Decimal("9000"), stage=LeadStage.CLOSED_WON,
                  actual_close_date=NOW - timedelta(days=60)),
            _deal(biz.id, source_channel="google", value=Decimal("100"), stage=LeadStage.CLOSED_LOST,
                  actual_close_date=NOW - timedelta(days=3)),
            _deal(biz.id, source_channel="google", value=Decimal("200"), stage=LeadStage.QUALIFIED),
            # No channel recorded.
            _deal(biz.id, source_channel=None, value=Decimal("50"), stage=LeadStage.NEW_LEAD),
            # Other currency: not ranked alongside the ARS deals.
            _deal(biz.id, source_channel="meta", value=Decimal("1000"), currency="USD",
                  stage=LeadStage.CLOSED_WON, actual_close_date=NOW - timedelta(days=1)),
        ])
        await s.commit()
    return SimpleNamespace(factory=factory)


def _build_app(factory, who) -> FastAPI:
    app = FastAPI()
    app.include_router(advanced_automation.router, prefix="/api/v1")

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:
        app.dependency_overrides[get_current_user] = lambda: who
    return app


def _client(factory, who=OWNER) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=_build_app(factory, who)), base_url="http://test")


@pytest.mark.asyncio
async def test_owner_gets_channels_ranked_by_won_revenue(world):
    async with _client(world.factory) as client:
        res = await client.get(f"/api/v1/analytics/channel-rankings/{OWNER.id}")

    assert res.status_code == 200
    channels = res.json()["channels"]
    assert [c["channel"] for c in channels] == ["instagram", "google", "sin origen"]
    instagram, google, unknown = channels
    assert instagram == {
        "rank": 1, "channel": "instagram", "deals": 3, "won": 2, "revenue": 800.0,
        "conversion": 1.0, "currency": "ARS",
    }
    assert google["won"] == 0 and google["revenue"] == 0.0
    assert google["conversion"] == 0.0  # 0 won of 1 closed
    assert unknown["deals"] == 1 and unknown["conversion"] is None  # nothing closed, no invented rate


@pytest.mark.asyncio
async def test_shorter_window_only_counts_recent_wins(world):
    async with _client(world.factory) as client:
        res = await client.get(
            f"/api/v1/analytics/channel-rankings/{OWNER.id}", params={"time_range": "week"}
        )

    instagram = res.json()["channels"][0]
    assert instagram["won"] == 1 and instagram["revenue"] == 500.0  # the 10- and 60-day-old wins are out


@pytest.mark.asyncio
async def test_someone_elses_ranking_is_refused(world):
    async with _client(world.factory, who=STRANGER) as client:
        res = await client.get(f"/api/v1/analytics/channel-rankings/{OWNER.id}")

    assert res.status_code == 403


@pytest.mark.asyncio
async def test_no_login_is_refused(world):
    async with _client(world.factory, who=None) as client:
        res = await client.get(f"/api/v1/analytics/channel-rankings/{OWNER.id}")

    assert res.status_code == 401
