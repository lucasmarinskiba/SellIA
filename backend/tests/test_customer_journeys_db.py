"""Contact journeys over HTTP against a real database (SQLite): access, stage rules, validation and metrics.

Access: starting journeys and recording touchpoints needs any active member; reading one journey's history needs
a member of its business; the metrics and the funnel are dashboards (owner or ADMIN). A stranger, including the
owner of another business, gets 403 and writes nothing. No Postgres needed.
"""

import uuid
from datetime import datetime, timedelta, timezone
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

from app.api.v1 import customer_journeys
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.journeys.contact_journey_models import (
    ContactJourney,
    ContactJourneyTouchpoint,
)


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

MODELS = [Business, Location, BusinessMember, ContactJourney, ContactJourneyTouchpoint]
ACTORS = ["OWNER", "ADMIN", "MEMBER", "MEMBER2", "INACTIVE", "STRANGER", "OTHER_OWNER"]
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
    app.include_router(customer_journeys.router)

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
        biz_a = Business(user_id=u["OWNER"], name="A")
        biz_b = Business(user_id=u["OTHER_OWNER"], name="B")
        s.add_all([biz_a, biz_b])
        await s.flush()
        loc_a = Location(business_id=biz_a.id, name="A1", address="x", city="BA", latitude=-34.6, longitude=-58.4)
        loc_b = Location(business_id=biz_b.id, name="B1", address="y", city="BA", latitude=-34.6, longitude=-58.4)
        s.add_all([loc_a, loc_b])
        s.add_all([
            BusinessMember(business_id=biz_a.id, user_id=u["ADMIN"], role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER2"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["INACTIVE"], role=BusinessMemberRole.ADMIN, is_active=False),
        ])
        await s.flush()
        journey = ContactJourney(business_id=biz_a.id, channel="email", customer_email="lead@x.test",
                                 awareness_date=NOW - timedelta(days=5))
        journey_b = ContactJourney(business_id=biz_b.id, channel="email", customer_email="other@x.test")
        s.add_all([journey, journey_b])
        await s.commit()
        ids = SimpleNamespace(biz=biz_a.id, biz_b=biz_b.id, loc=loc_a.id, loc_b=loc_b.id,
                              journey=journey.id, journey_b=journey_b.id)

    who = {"user": USERS["OWNER"]}
    app = _build_app(factory, who)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


def _routes(w: SimpleNamespace) -> dict[str, tuple]:
    return {
        "start": ("POST", "/api/v1/journeys/start", {"business_id": str(w.biz), "channel": "social",
                                                    "customer_phone": "+5491155550000"}, "member"),
        "touch": ("POST", "/api/v1/journeys/touchpoint", {"journey_id": str(w.journey), "business_id": str(w.biz),
                                                         "touchpoint_type": "email_opened", "channel": "email"}, "member"),
        "details": ("GET", f"/api/v1/journeys/{w.journey}", None, "member"),
        "metrics": ("POST", f"/api/v1/businesses/{w.biz}/journey-metrics?days=30", None, "manage"),
        "funnel": ("GET", f"/api/v1/businesses/{w.biz}/journey-funnel?days=30", None, "manage"),
    }


ALLOWED = {"member": {"OWNER", "ADMIN", "MEMBER", "MEMBER2"}, "manage": {"OWNER", "ADMIN"}}
NAMES = sorted(_routes(SimpleNamespace(biz=0, journey=0, loc=0, biz_b=0, loc_b=0, journey_b=0)))
CASES = [(n, a) for n in NAMES for a in ACTORS]


async def _snapshot(factory) -> dict:
    async with factory() as s:
        return {
            "journeys": (await s.execute(select(func.count()).select_from(ContactJourney))).scalar_one(),
            "touchpoints": (await s.execute(select(func.count()).select_from(ContactJourneyTouchpoint))).scalar_one(),
        }


@pytest.mark.parametrize(("name", "actor"), CASES, ids=[f"{n}:{a}" for n, a in CASES])
async def test_access_matrix(world, name, actor) -> None:
    spec = _routes(world)[name]
    world.who["user"] = USERS[actor]
    before = await _snapshot(world.factory)

    r = await world.client.request(spec[0], spec[1], json=spec[2])

    if actor in ALLOWED[spec[3]]:
        assert r.status_code in (200, 201), f"{actor} on {name}: {r.status_code} {r.text[:200]}"
    else:
        assert r.status_code == 403, f"{actor} on {name}: {r.status_code} {r.text[:200]}"
        assert await _snapshot(world.factory) == before, f"{actor} wrote on {name} despite the 403"


async def test_unknown_journey_is_404_and_no_login_is_rejected(factory, world) -> None:
    world.who["user"] = USERS["OWNER"]
    assert (await world.client.get(f"/api/v1/journeys/{uuid.uuid4()}")).status_code == 404
    anon = _build_app(factory, None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=anon), base_url="http://test") as c:
        assert (await c.get(f"/api/v1/journeys/{world.journey}")).status_code in (401, 403)


async def test_another_businesses_journey_is_403_even_for_its_owner(world) -> None:
    world.who["user"] = USERS["OWNER"]
    assert (await world.client.get(f"/api/v1/journeys/{world.journey_b}")).status_code == 403
    assert (await world.client.post("/api/v1/journeys/touchpoint", json={
        "journey_id": str(world.journey_b), "business_id": str(world.biz), "touchpoint_type": "email_sent",
        "channel": "email"})).status_code == 404  # the journey is not under this business


async def test_stage_rules_follow_the_first_touchpoint_and_repeat_orders(world) -> None:
    world.who["user"] = USERS["MEMBER"]
    base = {"journey_id": str(world.journey), "business_id": str(world.biz), "channel": "email"}

    await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "email_sent"})
    first = (await world.client.get(f"/api/v1/journeys/{world.journey}")).json()["stages"]["consideration"]
    await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "email_opened"})
    second = (await world.client.get(f"/api/v1/journeys/{world.journey}")).json()["stages"]["consideration"]
    assert first is not None and first == second  # a later email does not move the stage date

    await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "proximity_check"})
    await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "location_visit", "location_id": str(world.loc)})
    await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "order_placed", "order_id": "o-1"})
    await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "order_placed", "order_id": "o-2"})

    body = (await world.client.get(f"/api/v1/journeys/{world.journey}")).json()
    assert body["stages"]["intent"] and body["stages"]["visit"] and body["stages"]["purchase"]
    assert body["repeat_purchase_count"] == 1
    assert [t["type"] for t in body["touchpoints"]].count("order_placed") == 2  # every event is kept


async def test_touchpoint_rejects_unknown_type_and_foreign_location(world) -> None:
    world.who["user"] = USERS["MEMBER"]
    base = {"journey_id": str(world.journey), "business_id": str(world.biz), "channel": "email"}

    unknown = await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "carrier_pigeon"})
    foreign = await world.client.post("/api/v1/journeys/touchpoint", json={**base, "touchpoint_type": "location_visit", "location_id": str(world.loc_b)})

    assert unknown.status_code == 422, unknown.text
    assert foreign.status_code == 422, foreign.text
    assert await _snapshot(world.factory) == {"journeys": 2, "touchpoints": 0}


async def test_start_needs_a_way_to_reach_the_contact(world) -> None:
    world.who["user"] = USERS["MEMBER"]

    r = await world.client.post("/api/v1/journeys/start", json={"business_id": str(world.biz), "channel": "social"})

    assert r.status_code == 422, r.text
    assert await _snapshot(world.factory) == {"journeys": 2, "touchpoints": 0}


async def test_metrics_and_funnel_are_computed_and_empty_rates_are_null(world) -> None:
    async with world.factory() as s:
        won = ContactJourney(business_id=world.biz, channel="email", customer_email="won@x.test",
                             awareness_date=NOW - timedelta(days=10), purchase_date=NOW - timedelta(days=6),
                             consideration_date=NOW - timedelta(days=9), repeat_purchase_count=2)
        s.add(won)
        await s.commit()
    world.who["user"] = USERS["OWNER"]

    metrics = (await world.client.post(f"/api/v1/businesses/{world.biz}/journey-metrics?days=30")).json()
    funnel = (await world.client.get(f"/api/v1/businesses/{world.biz}/journey-funnel?days=30")).json()

    assert (metrics["total_journeys"], metrics["purchased"]) == (2, 1)
    assert metrics["conversion_rate"] == 50.0
    assert metrics["avg_days_to_purchase"] == pytest.approx(4.0, abs=0.01)  # 10 days in, purchase 6 days ago
    assert metrics["repeat_purchases"] == 2
    assert metrics["by_channel"]["email"] == {"journeys": 2, "purchased": 1, "conversion_rate": 50.0}
    assert funnel["funnel"]["awareness"] == 2 and funnel["funnel"]["purchase"] == 1
    assert funnel["conversion_rates"]["awareness_to_consideration"] == 50.0
    assert funnel["conversion_rates"]["visit_to_purchase"] is None  # no visits at all: not a 0% rate

    world.who["user"] = USERS["OTHER_OWNER"]
    empty = (await world.client.get(f"/api/v1/businesses/{world.biz_b}/journey-funnel?days=30")).json()
    assert empty["funnel"]["awareness"] == 1 and empty["conversion_rates"]["awareness_to_consideration"] == 0.0
