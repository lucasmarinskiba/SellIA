"""BI funnel and insight alerts over HTTP against a real database (SQLite).

The funnel is computed from the business's own records and nothing is stored (asserted here), so the table that
the old code wrote is never touched. Figures that cannot be computed are null, not zero. Access: the funnel is a
dashboard (owner or admin); the insight alerts are read-only for any member. No Postgres needed.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event, func, select
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.analytics.models import FunnelMetric, InsightAlert
from app.domains.bi.router import router as bi_router
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.channels.models import Conversation
from app.domains.orders.models import Order, OrderStatus
from app.domains.users.models import User


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


def _make_aware(target, *_args) -> None:
    for key, value in list(target.__dict__.items()):
        if isinstance(value, datetime) and value.tzinfo is None:
            target.__dict__[key] = value.replace(tzinfo=timezone.utc)


event.listen(Base, "load", _make_aware, propagate=True)
event.listen(Base, "refresh", _make_aware, propagate=True)

MODELS = [User, Business, BusinessMember, Conversation, Order, InsightAlert, FunnelMetric]
ACTORS = ["OWNER", "ADMIN", "MEMBER", "STRANGER", "OTHER_OWNER"]
USERS = {name: SimpleNamespace(id=uuid.uuid4()) for name in ACTORS}
NOW = datetime.now(timezone.utc)


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _build_app(factory, who: dict | None) -> FastAPI:
    app = FastAPI()
    app.include_router(bi_router, prefix="/api/v1/businesses")  # as mounted in app/main.py

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:
        app.dependency_overrides[get_current_user] = lambda: who["user"]
    return app


@pytest_asyncio.fixture
async def world(factory):
    u = {k: v.id for k, v in USERS.items()}
    async with factory() as s:
        for name in ACTORS:
            s.add(User(id=u[name], email=f"{name.lower()}-{u[name].hex[:6]}@t.test", hashed_password="x", full_name=name))
        await s.flush()
        biz = Business(user_id=u["OWNER"], name="A")
        empty = Business(user_id=u["OWNER"], name="sin datos")
        other = Business(user_id=u["OTHER_OWNER"], name="B")
        s.add_all([biz, empty, other])
        await s.flush()
        s.add_all([
            BusinessMember(business_id=biz.id, user_id=u["ADMIN"], role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=biz.id, user_id=u["MEMBER"], role=BusinessMemberRole.MEMBER),
        ])
        s.add_all([
            Conversation(business_id=biz.id, created_at=NOW - timedelta(days=2)),
            Conversation(business_id=biz.id, created_at=NOW - timedelta(days=3)),
            Conversation(business_id=biz.id, created_at=NOW - timedelta(days=9)),
            Conversation(business_id=biz.id, created_at=NOW - timedelta(days=90)),  # outside the month
        ])
        s.add_all([
            Order(business_id=biz.id, items=[], total_amount=Decimal("100.00"), status=OrderStatus.PAID, created_at=NOW - timedelta(days=1)),
            Order(business_id=biz.id, items=[], total_amount=Decimal("50.00"), status=OrderStatus.DELIVERED, created_at=NOW - timedelta(days=4)),
            Order(business_id=biz.id, items=[], total_amount=Decimal("999.00"), status=OrderStatus.PENDING, created_at=NOW - timedelta(days=1)),
            Order(business_id=biz.id, items=[], total_amount=Decimal("500.00"), status=OrderStatus.CANCELLED, created_at=NOW - timedelta(days=1)),
            Order(business_id=biz.id, items=[], total_amount=Decimal("700.00"), status=OrderStatus.PAID, created_at=NOW - timedelta(days=90)),
            Order(business_id=other.id, items=[], total_amount=Decimal("1.00"), status=OrderStatus.PAID, created_at=NOW - timedelta(days=1)),
        ])
        s.add_all([
            InsightAlert(business_id=biz.id, insight_type="churn", title="Caída de conversión", description="d", severity="high", is_active=True),
            InsightAlert(business_id=biz.id, insight_type="churn", title="Ya resuelta", description="d", severity="low", is_active=False),
            InsightAlert(business_id=biz.id, insight_type="upsell", title="Oportunidad", description="d", severity="low", is_active=True),
        ])
        await s.commit()
        ids = SimpleNamespace(biz=biz.id, empty=empty.id, other=other.id)

    who = {"user": USERS["OWNER"]}
    app = _build_app(factory, who)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


def _routes(w: SimpleNamespace) -> dict[str, tuple]:
    return {
        "funnel": ("POST", f"/api/v1/businesses/{w.biz}/bi/funnel?period=2026-10&period_type=monthly", "manage"),
        "latest": ("GET", f"/api/v1/businesses/{w.biz}/bi/funnel/latest", "manage"),
        "insights": ("GET", f"/api/v1/businesses/{w.biz}/bi/insights", "member"),
    }


ALLOWED = {"manage": {"OWNER", "ADMIN"}, "member": {"OWNER", "ADMIN", "MEMBER"}}
CASES = [(n, a) for n in ("funnel", "latest", "insights") for a in ACTORS]


@pytest.mark.parametrize(("name", "actor"), CASES, ids=[f"{n}:{a}" for n, a in CASES])
async def test_access_matrix(world, name, actor) -> None:
    method, url, level = _routes(world)[name]
    world.who["user"] = USERS[actor]

    r = await world.client.request(method, url)

    if actor in ALLOWED[level]:
        assert r.status_code == 200, f"{actor} on {name}: {r.status_code} {r.text[:200]}"
    else:
        assert r.status_code == 403, f"{actor} on {name}: {r.status_code} {r.text[:200]}"


async def test_unknown_business_is_404(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.get(f"/api/v1/businesses/{uuid.uuid4()}/bi/funnel/latest")

    assert r.status_code == 404, r.text


async def test_funnel_counts_only_real_records_in_the_window(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.post(f"/api/v1/businesses/{world.biz}/bi/funnel?period=2026-10&period_type=monthly")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["leads_count"] == 3  # the conversation from 90 days ago is outside the month
    assert body["orders_count"] == 2  # paid + delivered only; pending, cancelled and old orders are out
    assert float(body["revenue_total"]) == 150.0
    assert float(body["avg_order_value"]) == 75.0


async def test_figures_that_cannot_be_computed_are_null_not_zero(world) -> None:
    world.who["user"] = USERS["OWNER"]

    body = (await world.client.get(f"/api/v1/businesses/{world.biz}/bi/funnel/latest")).json()

    for field in ("qualified_count", "deals_count", "repeat_orders_count", "conversion_lead_to_qualified",
                  "conversion_qualified_to_deal", "conversion_deal_to_order", "conversion_order_to_repeat"):
        assert body[field] is None, field


async def test_a_business_without_orders_has_no_average(world) -> None:
    world.who["user"] = USERS["OWNER"]

    body = (await world.client.get(f"/api/v1/businesses/{world.empty}/bi/funnel/latest")).json()

    assert (body["leads_count"], body["orders_count"], float(body["revenue_total"])) == (0, 0, 0.0)
    assert body["avg_order_value"] is None


async def test_nothing_is_persisted_by_the_funnel(world) -> None:
    world.who["user"] = USERS["OWNER"]

    await world.client.post(f"/api/v1/businesses/{world.biz}/bi/funnel?period=2026-10&period_type=monthly")
    await world.client.get(f"/api/v1/businesses/{world.biz}/bi/funnel/latest")

    async with world.factory() as s:
        assert (await s.execute(select(func.count()).select_from(FunnelMetric))).scalar_one() == 0


async def test_insights_show_only_active_alerts_and_can_be_filtered(world) -> None:
    world.who["user"] = USERS["MEMBER"]

    everything = (await world.client.get(f"/api/v1/businesses/{world.biz}/bi/insights")).json()
    churn = (await world.client.get(f"/api/v1/businesses/{world.biz}/bi/insights?insight_type=churn")).json()

    assert sorted(a["title"] for a in everything) == ["Caída de conversión", "Oportunidad"]  # the inactive one is hidden
    assert [a["title"] for a in churn] == ["Caída de conversión"]


async def test_invalid_period_type_is_refused(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.post(f"/api/v1/businesses/{world.biz}/bi/funnel?period=2026-10&period_type=yearly")

    assert r.status_code == 422, r.text
