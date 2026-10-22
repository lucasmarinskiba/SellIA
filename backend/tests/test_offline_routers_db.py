"""Offline BI, offline tracking and offline sequences over HTTP against a real database (SQLite).

Three things are pinned here:

* access: dashboards need the owner or an ADMIN member; recording visits needs any active member; the
  sequence catalogue needs only a login; a stranger (including the owner of another business) gets 403 and
  writes nothing;
* numbers: every figure is computed from the stored visits. The dashboards used to return hard-coded values
  (156 visits, 45000 revenue, invented insights); a business with no visits must now see zeros and nulls;
* the write paths: a visit cannot be linked to another business's conversation, a visit cannot be closed twice,
  and the sequence endpoint says plainly that nothing was queued.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
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

from app.api.v1 import offline_bi, offline_sequences, offline_tracking
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.analytics.offline_models import (
    GeoProximityEvent,
    OfflineConversion,
    VisitType,
)
from app.domains.bi.offline_metrics import WEEKDAYS
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.channels.models import Conversation
from app.domains.orders.models import Order


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


def _make_aware(target, *_args) -> None:
    """timestamptz comes back timezone-aware from Postgres; SQLite hands back naive datetimes."""
    for key, value in list(target.__dict__.items()):
        if isinstance(value, datetime) and value.tzinfo is None:
            target.__dict__[key] = value.replace(tzinfo=timezone.utc)


event.listen(Base, "load", _make_aware, propagate=True)
event.listen(Base, "refresh", _make_aware, propagate=True)

MODELS = [
    Business, Location, BusinessMember, Conversation, Order, OfflineConversion, GeoProximityEvent,
]
COUNTED = [OfflineConversion, GeoProximityEvent]

ACTORS = ["OWNER", "ADMIN", "MEMBER", "MEMBER2", "INACTIVE", "STRANGER", "OTHER_OWNER"]
USERS = {name: SimpleNamespace(id=uuid.uuid4()) for name in ACTORS}

NOW = datetime.now(timezone.utc)
BA = {"latitude": -34.6, "longitude": -58.4}


def _at(days_ago: int, hour: int, minute: int = 0) -> datetime:
    return (NOW - timedelta(days=days_ago)).replace(hour=hour, minute=minute, second=0, microsecond=0)


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
    app.include_router(offline_bi.router, prefix="/api/v1/bi")  # as in app/main.py
    app.include_router(offline_tracking.router, prefix="/api/v1")
    app.include_router(offline_sequences.router, prefix="/api/v1")

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:  # None -> the real get_current_user (no token => rejected)
        app.dependency_overrides[get_current_user] = lambda: who["user"]
    return app


@pytest_asyncio.fixture
async def world(factory):
    u = {k: v.id for k, v in USERS.items() if k != "OTHER_OWNER"}
    u["OTHER_OWNER"] = USERS["OTHER_OWNER"].id
    async with factory() as s:
        biz_a = Business(user_id=u["OWNER"], name="A")
        biz_b = Business(user_id=u["OTHER_OWNER"], name="B")
        biz_c = Business(user_id=u["OWNER"], name="C (sin visitas)")
        s.add_all([biz_a, biz_b, biz_c])
        await s.flush()
        loc_a = Location(business_id=biz_a.id, name="A1", address="x", city="BA", **BA)
        loc_a2 = Location(business_id=biz_a.id, name="A2", address="y", city="BA", **BA)
        loc_b = Location(business_id=biz_b.id, name="B1", address="z", city="BA", **BA)
        s.add_all([loc_a, loc_a2, loc_b])
        s.add_all([
            BusinessMember(business_id=biz_a.id, user_id=u["ADMIN"], role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER2"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["INACTIVE"], role=BusinessMemberRole.ADMIN, is_active=False),
        ])
        conv_a = Conversation(business_id=biz_a.id)
        conv_b = Conversation(business_id=biz_b.id)
        s.add_all([conv_a, conv_b])
        await s.flush()

        def visit(loc, biz, when, vtype, dwell, purchased=False, amount=None, exit_time="auto"):
            return OfflineConversion(
                business_id=biz.id, location_id=loc.id, visit_type=vtype, entry_time=when, dwell_minutes=dwell,
                purchased=purchased, purchase_amount=Decimal(amount) if amount else None,
                exit_time=(when + timedelta(minutes=dwell or 0)) if exit_time == "auto" else exit_time,
            )

        v1 = visit(loc_a, biz_a, _at(1, 14), VisitType.WALK_IN, 20, True, "100.00")
        v2 = visit(loc_a, biz_a, _at(1, 14, 30), VisitType.QR_SCAN, 40)
        v3 = visit(loc_a, biz_a, _at(2, 9), VisitType.SCHEDULED_DEMO, None, True, "300.00")
        v_prev = visit(loc_a, biz_a, _at(45, 11), VisitType.WALK_IN, 10)
        v_b = visit(loc_b, biz_b, _at(1, 16), VisitType.WALK_IN, 15, True, "999.00")
        open_visit = visit(loc_a, biz_a, _at(3, 20), VisitType.WALK_IN, None, exit_time=None)  # still inside
        s.add_all([v1, v2, v3, v_prev, v_b, open_visit])
        s.add_all([
            GeoProximityEvent(business_id=biz_a.id, location_id=loc_a.id, conversation_id=conv_a.id,
                              user_latitude=-34.6, user_longitude=-58.4, distance_km=0.2, trigger_name="nearby",
                              automation_triggered=True, created_at=_at(1, 13)),
            GeoProximityEvent(business_id=biz_a.id, location_id=loc_a.id, conversation_id=conv_a.id,
                              user_latitude=-34.6, user_longitude=-58.4, distance_km=0.3, trigger_name="nearby",
                              automation_triggered=False, created_at=_at(1, 13, 5)),
            GeoProximityEvent(business_id=biz_a.id, location_id=loc_a.id, conversation_id=conv_a.id,
                              user_latitude=-34.6, user_longitude=-58.4, distance_km=0.4, trigger_name="exit",
                              automation_triggered=False, created_at=_at(1, 13, 10)),
        ])
        await s.commit()
        ids = SimpleNamespace(
            biz=biz_a.id, loc=loc_a.id, loc2=loc_a2.id, biz_b=biz_b.id, loc_b=loc_b.id, biz_c=biz_c.id,
            conv=conv_a.id, conv_b=conv_b.id, v1=v1.id, v2=v2.id, v3=v3.id, v_prev=v_prev.id, v_b=v_b.id,
            open=open_visit.id, M=u["MEMBER"],
        )

    who = {"user": USERS["OWNER"]}
    app = _build_app(factory, who)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


def _routes(w: SimpleNamespace) -> dict[str, tuple]:
    """name -> (method, url, body, level). Levels: manage / member / login."""
    return {
        "bi-foot": ("GET", f"/api/v1/bi/offline/foot-traffic/{w.loc}?days=30", None, "manage"),
        "bi-conv": ("GET", f"/api/v1/bi/offline/conversions/{w.loc}?days=30", None, "manage"),
        "bi-summary": ("GET", f"/api/v1/bi/offline/dashboard-summary?business_id={w.biz}", None, "manage"),
        "heatmap": ("GET", f"/api/v1/locations/{w.loc}/foot-traffic-heatmap", None, "manage"),
        "funnel": ("GET", f"/api/v1/businesses/{w.biz}/conversion-funnel", None, "manage"),
        "effectiveness": ("GET", f"/api/v1/proximity-triggers/nearby/effectiveness?business_id={w.biz}", None, "manage"),
        "trigger": ("POST", "/api/v1/offline-sequences/trigger", {
            "business_id": str(w.biz), "location_id": str(w.loc), "conversion_id": str(w.open), "visit_type": "walk_in",
        }, "manage"),
        "log-visit": ("POST", "/api/v1/offline-conversions", {"location_id": str(w.loc), "visit_type": "walk_in"}, "member"),
        "end-visit": ("PATCH", f"/api/v1/offline-conversions/{w.open}?purchased=false", None, "member"),
        "proximity": ("POST", "/api/v1/proximity-events", {
            "location_id": str(w.loc), "conversation_id": str(w.conv), "user_latitude": -34.6,
            "user_longitude": -58.4, "distance_km": 0.1, "trigger_name": "nearby"}, "member"),
        "templates": ("GET", "/api/v1/offline-sequences/templates", None, "login"),
        "triggers": ("GET", "/api/v1/offline-sequences/triggers", None, "login"),
        "mapping": ("GET", "/api/v1/offline-sequences/visit-type-mapping", None, "login"),
    }


def _ghost_routes(w: SimpleNamespace) -> dict[str, tuple]:
    g = SimpleNamespace(**vars(w))
    for name in ("loc", "biz", "open", "conv"):
        setattr(g, name, uuid.uuid4())
    return {k: v for k, v in _routes(g).items() if v[3] != "login"}


ALLOWED = {
    "manage": {"OWNER", "ADMIN"},
    "member": {"OWNER", "ADMIN", "MEMBER", "MEMBER2"},
    "login": set(ACTORS),
}
NAMES = sorted(_routes(SimpleNamespace(loc=0, loc2=0, biz=0, biz_b=0, loc_b=0, biz_c=0, conv=0, conv_b=0,
                                        v1=0, v2=0, v3=0, v_prev=0, v_b=0, open=0, M=0)))
CASES = [(n, a) for n in NAMES for a in ACTORS]


async def _call(client: httpx.AsyncClient, spec: tuple) -> httpx.Response:
    method, url, body, _level = spec
    return await client.request(method, url, json=body)


async def _snapshot(factory, open_visit_id) -> dict:
    async with factory() as s:
        counts = {m.__name__: (await s.execute(select(func.count()).select_from(m))).scalar_one() for m in COUNTED}
        open_row = await s.get(OfflineConversion, open_visit_id)
        return {"counts": counts, "open_exit": open_row.exit_time, "open_purchased": open_row.purchased}


# ------------------------------------------------------------------ access matrix


@pytest.mark.parametrize(("name", "actor"), CASES, ids=[f"{n}:{a}" for n, a in CASES])
async def test_access_matrix(world, name, actor) -> None:
    spec = _routes(world)[name]
    level = spec[3]
    world.who["user"] = USERS[actor]
    before = await _snapshot(world.factory, world.open)

    r = await _call(world.client, spec)

    if actor in ALLOWED[level]:
        assert r.status_code in (200, 201), f"{actor} on {name} ({level}): {r.status_code} {r.text[:300]}"
    else:
        assert r.status_code == 403, f"{actor} on {name} ({level}): {r.status_code} {r.text[:300]}"
        assert await _snapshot(world.factory, world.open) == before, f"{actor} changed data on {name} despite the 403"


@pytest.mark.parametrize("name", sorted(_ghost_routes(SimpleNamespace(
    loc=0, loc2=0, biz=0, biz_b=0, loc_b=0, biz_c=0, conv=0, conv_b=0, v1=0, v2=0, v3=0, v_prev=0, v_b=0, open=0, M=0))))
async def test_unknown_ids_are_404(world, name) -> None:
    r = await _call(world.client, _ghost_routes(world)[name])

    assert r.status_code == 404, f"{name}: {r.status_code} {r.text[:300]}"


@pytest.mark.parametrize("name", NAMES)
async def test_no_login_is_rejected(factory, world, name) -> None:
    app = _build_app(factory, None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as anon:
        r = await _call(anon, _routes(world)[name])

    assert r.status_code in (401, 403), f"{name}: {r.status_code} {r.text[:200]}"


# ------------------------------------------------------------------ the numbers


async def test_foot_traffic_is_computed_from_the_visits(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.get(f"/api/v1/bi/offline/foot-traffic/{world.loc}?days=30")

    assert r.status_code == 200, r.text
    body = r.json()
    # visits in the window: v1 (walk-in, 14h), v2 (QR, 14h), v3 (demo, 9h), the open one (3 days ago, 20h, no dwell)
    assert (body["total_visits"], body["walk_in_visits"], body["qr_scans"], body["scheduled_visits"]) == (4, 2, 1, 1)
    assert body["hourly_breakdown"]["14"] == 2 and body["hourly_breakdown"]["09"] == 1 and body["hourly_breakdown"]["20"] == 1
    assert body["peak_hour"] == "14:00-15:00"
    assert body["peak_day"] == WEEKDAYS[_at(1, 14).weekday()]  # two visits on that day, one on the next
    assert body["avg_dwell_minutes"] == 30  # (20 + 40) / 2; the open visit and the demo have no dwell recorded
    assert len(body["daily_visits_trend"]) == 30
    assert sum(d["visits"] for d in body["daily_visits_trend"]) == 4
    assert "156" not in r.text  # the old hard-coded figure


async def test_conversions_and_revenue_come_from_the_purchases(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.get(f"/api/v1/bi/offline/conversions/{world.loc}?days=30")

    assert r.status_code == 200, r.text
    body = r.json()
    # v1 (walk-in, 100) and v3 (demo, 300) were purchased; v2 and the open visit were not
    assert (body["total_visits"], body["visits_converted"]) == (4, 2)
    assert float(body["total_revenue"]) == 400.0
    assert float(body["avg_order_value"]) == 200.0
    assert body["by_visit_type"]["walk_in"]["visits"] == 2
    assert body["by_visit_type"]["walk_in"]["revenue"] == 100.0
    assert body["by_visit_type"]["scheduled_demo"]["revenue"] == 300.0
    assert "qr_scan" in body["by_visit_type"] and body["by_visit_type"]["qr_scan"]["converted"] == 0


async def test_dashboard_compares_with_the_previous_period(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.get(f"/api/v1/bi/offline/dashboard-summary?business_id={world.biz}&days=30")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_visits"] == 4
    assert body["visit_trend"] == "↑ +300%"  # 4 now vs 1 in the period before (v_prev)
    assert body["total_conversions"] == 2
    assert body["conversion_trend"].startswith("nuevo")  # nothing was purchased in the previous period
    assert float(body["total_revenue"]) == 400.0
    assert body["top_location"] == "A1" and body["top_location_visits"] == 4
    assert body["best_trigger"] == "nearby"  # 1 of 2 executed; 'exit' had 0 of 1
    assert body["best_trigger_roi"] is None  # no cost data recorded: no ROI is invented
    assert body["actionable_insights"] == []  # no generator is wired: nothing is written by hand
    assert body["peak_hour"] == "14:00-15:00"
    assert "Showroom" not in r.text and "45000" not in r.text  # the old hard-coded values


async def test_a_business_with_no_visits_sees_nulls_not_invented_numbers(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.get(f"/api/v1/bi/offline/dashboard-summary?business_id={world.biz_c}")

    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["total_visits"], body["total_conversions"], float(body["total_revenue"])) == (0, 0, 0.0)
    assert body["top_location"] is None and body["best_trigger"] is None
    assert body["peak_hour"] is None and body["peak_day"] is None and body["avg_dwell_minutes"] is None
    assert body["visit_trend"] == "sin datos del periodo anterior"


async def test_one_businesses_numbers_never_include_another_s(world) -> None:
    world.who["user"] = USERS["OTHER_OWNER"]  # owns B, which has one purchase of 999

    r = await world.client.get(f"/api/v1/bi/offline/dashboard-summary?business_id={world.biz_b}")

    assert r.status_code == 200, r.text
    assert (r.json()["total_visits"], float(r.json()["total_revenue"])) == (1, 999.0)


async def test_heatmap_reads_the_visits_not_the_empty_aggregate_table(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.get(f"/api/v1/locations/{world.loc}/foot-traffic-heatmap?days=30")

    assert r.status_code == 200, r.text
    heat = r.json()["hourly_heatmap"]
    assert (heat["09"], heat["14"], heat["20"]) == (1, 2, 1)  # v3, v1+v2, the open visit
    assert sum(heat.values()) == 4


async def test_funnel_and_effectiveness_return_their_contract(world) -> None:
    world.who["user"] = USERS["OWNER"]

    funnel = await world.client.get(f"/api/v1/businesses/{world.biz}/conversion-funnel?days=30")
    effect = await world.client.get(f"/api/v1/proximity-triggers/nearby/effectiveness?business_id={world.biz}&days=30")

    assert funnel.status_code == 200, funnel.text
    assert set(funnel.json()) >= {"total_visits", "visits_converted_to_purchase", "total_revenue", "conversion_rate"}
    assert effect.status_code == 200, effect.text
    assert (effect.json()["total_proximity_events"], effect.json()["automations_executed"]) == (2, 1)


# ------------------------------------------------------------------ write paths


async def test_a_member_logs_a_visit_for_the_location_business(world) -> None:
    world.who["user"] = USERS["MEMBER"]

    r = await world.client.post("/api/v1/offline-conversions", json={
        "location_id": str(world.loc), "visit_type": "qr_scan", "conversation_id": str(world.conv)})

    assert r.status_code == 201, r.text
    assert r.json()["business_id"] == str(world.biz)
    async with world.factory() as s:
        row = await s.get(OfflineConversion, uuid.UUID(r.json()["id"]))
    assert row.business_id == world.biz and row.location_id == world.loc


async def test_a_visit_cannot_link_another_businesss_conversation(world) -> None:
    world.who["user"] = USERS["MEMBER"]

    visit = await world.client.post("/api/v1/offline-conversions", json={
        "location_id": str(world.loc), "visit_type": "walk_in", "conversation_id": str(world.conv_b)})
    event_ = await world.client.post("/api/v1/proximity-events", json={
        "location_id": str(world.loc), "conversation_id": str(world.conv_b), "user_latitude": 0, "user_longitude": 0,
        "distance_km": 0.1, "trigger_name": "nearby"})

    assert visit.status_code == 404, visit.text
    assert event_.status_code == 404, event_.text


async def test_ending_a_visit_twice_keeps_the_first_exit_time(world) -> None:
    world.who["user"] = USERS["MEMBER"]

    first = await world.client.patch(f"/api/v1/offline-conversions/{world.open}?purchased=false")
    assert first.status_code == 200, first.text
    async with world.factory() as s:
        closed_at = (await s.get(OfflineConversion, world.open)).exit_time
        dwell = (await s.get(OfflineConversion, world.open)).dwell_minutes
    assert closed_at is not None and dwell is not None

    second = await world.client.patch(f"/api/v1/offline-conversions/{world.open}?purchased=true&purchase_amount=50")

    assert second.status_code == 200, second.text
    async with world.factory() as s:
        row = await s.get(OfflineConversion, world.open)
    assert row.exit_time == closed_at and row.dwell_minutes == dwell  # the purchase did not move the exit time
    assert row.purchased is True and float(row.purchase_amount) == 50.0


async def test_a_purchase_amount_cannot_be_negative(world) -> None:
    world.who["user"] = USERS["MEMBER"]

    r = await world.client.patch(f"/api/v1/offline-conversions/{world.open}?purchased=true&purchase_amount=-5")

    assert r.status_code == 422, r.text


async def test_trigger_picks_the_template_and_queues_nothing_while_sending_is_off(world) -> None:
    world.who["user"] = USERS["OWNER"]
    before = await _snapshot(world.factory, world.open)

    r = await world.client.post("/api/v1/offline-sequences/trigger", json={
        "business_id": str(world.biz), "location_id": str(world.loc), "conversion_id": str(world.v1),
        "visit_type": "walk_in"})

    assert r.status_code == 200, r.text
    body = r.json()
    # Sending is off by default (OFFLINE_SEQUENCE_SEND_ENABLED): the template is picked, nothing is queued.
    assert body["success"] is False
    assert "post_visit_thank_you" in body["message"] and "desactivado" in body["message"]
    assert body["sequence_id"] is None
    assert await _snapshot(world.factory, world.open) == before  # no rows written


async def test_trigger_uses_the_stored_visit_not_the_request_body(world) -> None:
    world.who["user"] = USERS["OWNER"]

    r = await world.client.post("/api/v1/offline-sequences/trigger", json={
        "business_id": str(world.biz), "location_id": str(world.loc), "conversion_id": str(world.v2),
        "visit_type": "walk_in"})  # v2 is a QR scan; the body lies about it

    assert r.status_code == 200, r.text
    assert "qr_scan_reward" in r.json()["message"]


async def test_trigger_rejects_a_visit_that_is_not_at_that_location_or_business(world) -> None:
    world.who["user"] = USERS["OWNER"]
    other_location = await world.client.post("/api/v1/offline-sequences/trigger", json={
        "business_id": str(world.biz), "location_id": str(world.loc2), "conversion_id": str(world.v1),
        "visit_type": "walk_in"})
    other_business = await world.client.post("/api/v1/offline-sequences/trigger", json={
        "business_id": str(world.biz), "location_id": str(world.loc_b), "conversion_id": str(world.v_b),
        "visit_type": "walk_in"})

    assert other_location.status_code == 404, other_location.text
    assert other_business.status_code == 404, other_business.text


async def test_catalogue_is_available_to_any_logged_in_user(world) -> None:
    world.who["user"] = USERS["STRANGER"]

    templates = await world.client.get("/api/v1/offline-sequences/templates")
    mapping = await world.client.get("/api/v1/offline-sequences/visit-type-mapping")

    assert templates.status_code == 200 and len(templates.json()) >= 7
    assert mapping.status_code == 200 and "walk_in" in mapping.json()["mappings"]
