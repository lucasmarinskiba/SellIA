"""location_checkin / location_qr over HTTP against a real database (SQLite).

Before: the services are sync but get_db yields an AsyncSession, so every call 400'd on
``'AsyncSession' object has no attribute 'query'`` (fail closed). Fixing that with ``run_sync`` alone would
have made them live with no access checks and a hard-coded all-zero business_id; this file pins the access
rules and the data they write.

Callers: the business owner, an ADMIN member, a plain MEMBER, a second MEMBER, an inactive member and a
stranger. Every test gets a fresh database. Levels (see app.core.business_access):

* ``member``  owner, admin and any active member;
* ``self``    the staff member the route is about (here MEMBER) plus managers (owner / admin).

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
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

from app.api.v1 import location_checkin, location_qr
from app.core.database import Base, get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.locations.checkin_models import (
    CheckinStatus,
    CheckinType,
    LocationCheckin,
    LocationFeedback,
    StaffCheckin,
)
from app.domains.locations.qr_generator import LocationQRGenerator


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

MODELS = [Business, Location, BusinessMember, LocationCheckin, StaffCheckin, LocationFeedback]
COUNTED = [LocationCheckin, StaffCheckin, LocationFeedback]

ACTORS = ["OWNER", "ADMIN", "MEMBER", "MEMBER2", "INACTIVE", "STRANGER"]
USERS = {name: SimpleNamespace(id=uuid.uuid4()) for name in ACTORS + ["OTHER_OWNER"]}


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
    for module in (location_checkin, location_qr):
        app.include_router(module.router, prefix="/api/v1")  # as in app/main.py

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:  # None -> the real get_current_user (no token => rejected)
        app.dependency_overrides[get_current_user] = lambda: who["user"]
        # The mobile routes read the caller through get_current_user_optional (so a device token can fall
        # through to the JWT check). Overriding only get_current_user would leave that path unauthenticated.
        app.dependency_overrides[get_current_user_optional] = lambda: who["user"]
    return app


@pytest_asyncio.fixture
async def world(factory):
    u = {k: v.id for k, v in USERS.items()}
    async with factory() as s:
        biz_a, biz_b = Business(user_id=u["OWNER"], name="A"), Business(user_id=u["OTHER_OWNER"], name="B")
        s.add_all([biz_a, biz_b])
        await s.flush()

        def loc(biz, name, active=True):
            return Location(business_id=biz.id, name=name, address="x", city="BA", latitude=-34.6,
                            longitude=-58.4, is_active=active)

        loc_a, loc_a_off, loc_b = loc(biz_a, "A1"), loc(biz_a, "A2", active=False), loc(biz_b, "B1")
        s.add_all([loc_a, loc_a_off, loc_b])
        s.add_all([
            BusinessMember(business_id=biz_a.id, user_id=u["ADMIN"], role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["MEMBER2"], role=BusinessMemberRole.MEMBER),
            BusinessMember(business_id=biz_a.id, user_id=u["INACTIVE"], role=BusinessMemberRole.ADMIN, is_active=False),
        ])
        await s.flush()
        visit = LocationCheckin(location_id=loc_a.id, business_id=biz_a.id, checkin_type=CheckinType.QR_SCAN,
                                checkin_time=datetime.now(timezone.utc) - timedelta(minutes=30))
        visit_b = LocationCheckin(location_id=loc_b.id, business_id=biz_b.id, checkin_type=CheckinType.QR_SCAN)
        shift = StaffCheckin(location_id=loc_a.id, business_id=biz_a.id, staff_id=u["MEMBER"],
                             staff_name="Ana", staff_role="sales")
        s.add_all([visit, visit_b, shift])
        await s.commit()
        ids = SimpleNamespace(biz=biz_a.id, loc=loc_a.id, loc_off=loc_a_off.id, biz_b=biz_b.id, loc_b=loc_b.id,
                              visit=visit.id, visit_b=visit_b.id, shift=shift.id, M=u["MEMBER"], M2=u["MEMBER2"])

    who = {"user": USERS["OWNER"]}
    app = _build_app(factory, who)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


def _ghost(w: SimpleNamespace) -> SimpleNamespace:
    g = SimpleNamespace(**vars(w))
    for name in ("loc", "visit", "shift"):
        setattr(g, name, uuid.uuid4())
    return g


def _routes(w: SimpleNamespace) -> dict[str, tuple]:
    """name -> (method, url, body, level)"""
    return {
        "checkin": ("POST", "/api/v1/locations/checkin", {"location_id": str(w.loc), "checkin_type": "qr_scan"}, "member"),
        "checkout": ("POST", "/api/v1/locations/checkout", {"checkin_id": str(w.visit)}, "member"),
        "feedback": ("POST", "/api/v1/locations/feedback", {"location_id": str(w.loc), "nps_score": 9}, "member"),
        "staff-checkin": ("POST", "/api/v1/staff/checkin", {
            "location_id": str(w.loc), "staff_id": str(w.M), "staff_name": "Ana", "staff_role": "sales"}, "self"),
        "staff-checkout": ("POST", "/api/v1/staff/checkout", {"staff_checkin_id": str(w.shift)}, "self"),
        "summary": ("GET", f"/api/v1/locations/{w.loc}/checkin-summary", None, "member"),
        "performance": ("GET", f"/api/v1/staff/{w.M}/performance?location_id={w.loc}", None, "self"),
        "qr-codes": ("GET", f"/api/v1/locations/{w.loc}/qr-codes", None, "member"),
        "qr-code": ("GET", f"/api/v1/locations/{w.loc}/qr-code?qr_type=feedback", None, "member"),
    }


ALLOWED = {
    "member": {"OWNER", "ADMIN", "MEMBER", "MEMBER2"},
    "self": {"OWNER", "ADMIN", "MEMBER"},
}
_PLACEHOLDER = SimpleNamespace(loc=0, visit=0, shift=0, M=0)
NAMES = sorted(_routes(_PLACEHOLDER))
CASES = [(n, a) for n in NAMES for a in ACTORS]


async def _call(client: httpx.AsyncClient, spec: tuple) -> httpx.Response:
    method, url, body, _level = spec
    return await client.request(method, url, json=body)


async def _snapshot(factory) -> dict:
    async with factory() as s:
        counts = {m.__name__: (await s.execute(select(func.count()).select_from(m))).scalar_one() for m in COUNTED}
        visits = sorted(str(x) for x in (await s.execute(select(LocationCheckin.status))).scalars())
        shifts = sorted(str(x) for x in (await s.execute(select(StaffCheckin.checkout_time))).scalars())
    return {"counts": counts, "visits": visits, "shifts": shifts}


# ------------------------------------------------------------------ the access matrix


@pytest.mark.parametrize(("name", "actor"), CASES, ids=[f"{n}:{a}" for n, a in CASES])
async def test_access_matrix(world, name, actor) -> None:
    spec = _routes(world)[name]
    world.who["user"] = USERS[actor]
    before = await _snapshot(world.factory)

    r = await _call(world.client, spec)

    if actor in ALLOWED[spec[3]]:
        assert r.status_code == 200, f"{actor} on {name} ({spec[3]}): {r.status_code} {r.text[:300]}"
    else:
        assert r.status_code == 403, f"{actor} on {name} ({spec[3]}): {r.status_code} {r.text[:300]}"
        assert await _snapshot(world.factory) == before, f"{actor} changed data on {name} despite the 403"


@pytest.mark.parametrize("name", NAMES)
async def test_unknown_ids_are_404(world, name) -> None:
    r = await _call(world.client, _routes(_ghost(world))[name])

    assert r.status_code == 404, f"{name}: {r.status_code} {r.text[:300]}"


@pytest.mark.parametrize("name", [*NAMES, "qr-parse"])
async def test_no_login_is_rejected(factory, world, name) -> None:
    spec = _routes(world).get(name) or ("POST", "/api/v1/qr-parse?payload=x", None, "")
    app = _build_app(factory, None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as anon:
        r = await _call(anon, spec)

    assert r.status_code in (401, 403), f"{name}: {r.status_code} {r.text[:200]}"


async def test_another_businesses_ids_are_403_even_for_an_owner(world) -> None:
    probes = [
        ("POST", "/api/v1/locations/checkin", {"location_id": str(world.loc_b), "checkin_type": "qr_scan"}),
        ("POST", "/api/v1/locations/checkout", {"checkin_id": str(world.visit_b)}),
        ("POST", "/api/v1/locations/feedback", {"location_id": str(world.loc_b), "nps_score": 9}),
        ("GET", f"/api/v1/locations/{world.loc_b}/checkin-summary", None),
        ("GET", f"/api/v1/locations/{world.loc_b}/qr-codes", None),
    ]
    for method, url, body in probes:
        r = await world.client.request(method, url, json=body)
        assert r.status_code == 403, f"{method} {url}: {r.status_code}"


# ------------------------------------------------------------------ visitor flow


async def test_checkin_stores_the_locations_real_business_and_the_visitor_data(world) -> None:
    r = await world.client.post("/api/v1/locations/checkin", json={
        "location_id": str(world.loc), "checkin_type": "QR_SCAN", "visitor_name": "Lu", "visitor_phone": "+54 11 5555",
        "qr_code": "selliaapp://checkin?location=x"})

    assert r.status_code == 200 and r.json()["status"] == "checked_in", r.text
    async with world.factory() as s:
        row = await s.get(LocationCheckin, uuid.UUID(r.json()["checkin_id"]))
    assert row.business_id == world.biz  # used to be the all-zero UUID
    assert (row.location_id, row.status, row.checkin_type) == (world.loc, CheckinStatus.CHECKED_IN, CheckinType.QR_SCAN)
    assert (row.visitor_name, row.visitor_phone) == ("Lu", "+54 11 5555")


@pytest.mark.parametrize(("checkin_type", "status"), [("staff_checkin", 422), ("nonsense", 422), ("", 422)])
async def test_checkin_rejects_staff_and_unknown_types(world, checkin_type, status) -> None:
    r = await world.client.post("/api/v1/locations/checkin", json={"location_id": str(world.loc), "checkin_type": checkin_type})

    assert r.status_code == status, r.text


async def test_checkin_at_an_inactive_location_is_refused(world) -> None:
    r = await world.client.post("/api/v1/locations/checkin", json={"location_id": str(world.loc_off), "checkin_type": "qr_scan"})

    assert r.status_code == 400, r.text
    assert await _count(world.factory, LocationCheckin) == 2  # only the two seeded visits


async def test_checkin_rejects_oversized_input(world) -> None:
    r = await world.client.post("/api/v1/locations/checkin", json={
        "location_id": str(world.loc), "checkin_type": "qr_scan", "visitor_phone": "1" * 21})

    assert r.status_code == 422, r.text


async def test_checkout_records_dwell_time_once(world) -> None:
    first = await world.client.post("/api/v1/locations/checkout", json={"checkin_id": str(world.visit), "visited_sections": ["demo_area"]})

    assert first.status_code == 200, first.text
    assert first.json()["dwell_minutes"] >= 29  # the seeded visit started 30 minutes ago
    async with world.factory() as s:
        row = await s.get(LocationCheckin, world.visit)
    assert (row.status, row.visited_sections) == (CheckinStatus.CHECKED_OUT, ["demo_area"])

    dwell_before = row.dwell_seconds
    second = await world.client.post("/api/v1/locations/checkout", json={"checkin_id": str(world.visit)})
    assert second.status_code == 409, second.text
    async with world.factory() as s:
        assert (await s.get(LocationCheckin, world.visit)).dwell_seconds == dwell_before  # not inflated


async def test_feedback_maps_nps_to_sentiment_and_uses_the_real_business(world) -> None:
    out = {}
    for score in (9, 7, 3):
        r = await world.client.post("/api/v1/locations/feedback", json={
            "location_id": str(world.loc), "nps_score": score, "comment": "ok", "topics": ["wait_time"],
            "checkin_id": str(world.visit)})
        assert r.status_code == 200, r.text
        out[score] = (r.json()["sentiment"], r.json()["requires_followup"])

    assert out == {9: ("positive", False), 7: ("neutral", False), 3: ("negative", True)}
    async with world.factory() as s:
        rows = (await s.execute(select(LocationFeedback))).scalars().all()
    assert {r.business_id for r in rows} == {world.biz} and {r.checkin_id for r in rows} == {world.visit}


async def test_feedback_cannot_point_at_a_checkin_from_another_location_or_that_does_not_exist(world) -> None:
    for checkin_id in (world.visit_b, uuid.uuid4()):
        r = await world.client.post("/api/v1/locations/feedback", json={
            "location_id": str(world.loc), "nps_score": 5, "checkin_id": str(checkin_id)})
        assert r.status_code == 404, (checkin_id, r.text)
    assert await _count(world.factory, LocationFeedback) == 0


@pytest.mark.parametrize("payload", [{"nps_score": -1}, {"nps_score": 11}, {"comment": "x" * 1001}, {"topics": ["t"] * 21}])
async def test_feedback_validates_its_input(world, payload) -> None:
    """nps_score used a Query(...) default inside a BaseModel, which validates nothing."""
    r = await world.client.post("/api/v1/locations/feedback", json={"location_id": str(world.loc), **payload})

    assert r.status_code == 422, r.text
    assert await _count(world.factory, LocationFeedback) == 0


async def test_summary_counts_the_activity(world) -> None:
    await world.client.post("/api/v1/locations/checkin", json={"location_id": str(world.loc), "checkin_type": "manual_entry"})
    await world.client.post("/api/v1/locations/checkout", json={"checkin_id": str(world.visit)})

    r = await world.client.get(f"/api/v1/locations/{world.loc}/checkin-summary")

    assert r.status_code == 200, r.text
    assert (r.json()["total_visitors_today"], r.json()["active_visitors"], r.json()["staff_on_shift"]) == (2, 1, 1)


# ------------------------------------------------------------------ staff flow


async def test_a_member_checks_themselves_in_but_not_a_colleague(world) -> None:
    body = {"location_id": str(world.loc), "staff_id": str(world.M), "staff_name": "Ana", "staff_role": "sales"}
    world.who["user"] = USERS["MEMBER"]
    mine = await world.client.post("/api/v1/staff/checkin", json=body)
    other = await world.client.post("/api/v1/staff/checkin", json={**body, "staff_id": str(world.M2)})

    assert mine.status_code == 200, mine.text
    assert other.status_code == 403, other.text

    world.who["user"] = USERS["ADMIN"]  # a manager may check a colleague in
    by_admin = await world.client.post("/api/v1/staff/checkin", json={**body, "staff_id": str(world.M2), "staff_name": "Beto"})
    assert by_admin.status_code == 200, by_admin.text
    async with world.factory() as s:
        rows = (await s.execute(select(StaffCheckin).where(StaffCheckin.staff_name == "Beto"))).scalars().all()
    assert [(r.business_id, r.staff_id) for r in rows] == [(world.biz, world.M2)]


async def test_cannot_check_in_someone_who_is_not_in_the_business(world) -> None:
    for who in ("STRANGER", "INACTIVE"):
        r = await world.client.post("/api/v1/staff/checkin", json={
            "location_id": str(world.loc), "staff_id": str(USERS[who].id), "staff_name": "x", "staff_role": "y"})
        assert r.status_code == 400, (who, r.text)


async def test_staff_checkout_records_the_shift_once(world) -> None:
    world.who["user"] = USERS["MEMBER"]
    first = await world.client.post("/api/v1/staff/checkout", json={
        "staff_checkin_id": str(world.shift), "visitors_engaged": 5, "demos_conducted": 2, "sales_assisted": 1})

    assert first.status_code == 200, first.text
    assert (first.json()["visitors_engaged"], first.json()["demos"], first.json()["sales"]) == (5, 2, 1)
    again = await world.client.post("/api/v1/staff/checkout", json={"staff_checkin_id": str(world.shift), "visitors_engaged": 99})
    assert again.status_code == 409, again.text
    async with world.factory() as s:
        assert (await s.get(StaffCheckin, world.shift)).visitors_engaged == 5  # not overwritten


async def test_staff_checkout_rejects_negative_counters(world) -> None:
    r = await world.client.post("/api/v1/staff/checkout", json={"staff_checkin_id": str(world.shift), "sales_assisted": -3})

    assert r.status_code == 422, r.text


async def test_performance_reports_the_shifts_at_that_location(world) -> None:
    await world.client.post("/api/v1/staff/checkout", json={"staff_checkin_id": str(world.shift), "visitors_engaged": 4, "sales_assisted": 2})

    r = await world.client.get(f"/api/v1/staff/{world.M}/performance?location_id={world.loc}")

    assert r.status_code == 200, r.text
    assert (r.json()["total_shifts"], r.json()["total_visitors_engaged"], r.json()["total_sales_assisted"]) == (1, 4, 2)


# ------------------------------------------------------------------ QR


async def test_qr_payloads_follow_the_documented_format_without_business_none(world) -> None:
    r = await world.client.get(f"/api/v1/locations/{world.loc}/qr-codes")

    assert r.status_code == 200, r.text
    codes = r.json()["qr_codes"]
    assert set(codes) == {"visitor_checkin", "feedback", "staff_checkin"}
    for qr_type, payload in codes.items():
        assert payload == f"selliaapp://checkin?location={world.loc}&type={qr_type}", payload
        assert "None" not in payload and "business" not in payload  # a printed poster: no business id, no "None"


async def test_single_qr_validates_its_type(world) -> None:
    ok = await world.client.get(f"/api/v1/locations/{world.loc}/qr-code?qr_type=staff_checkin")
    bad = await world.client.get(f"/api/v1/locations/{world.loc}/qr-code?qr_type=admin")

    assert ok.status_code == 200 and ok.json()["qr_type"] == "staff_checkin", ok.text
    assert bad.status_code == 400, bad.text


async def test_qr_parse_round_trips_what_the_generator_prints(world) -> None:
    payload = LocationQRGenerator.generate_checkin_qr(world.loc, None, "feedback")["qr_payload"]
    world.who["user"] = USERS["STRANGER"]  # parsing needs a login, not a business

    r = await world.client.post("/api/v1/qr-parse", params={"payload": payload})

    assert r.status_code == 200, r.text
    assert (r.json()["valid"], r.json()["location_id"], r.json()["type"], r.json()["business_id"]) == (
        True, str(world.loc), "feedback", None)


_LOC = str(uuid.uuid4())


@pytest.mark.parametrize(("payload", "reason"), [
    (f"https://evil.example/checkin?location={_LOC}", "Invalid QR format"),
    (f"selliaapp://other?location={_LOC}", "Invalid QR format"),
    ("garbage", "Invalid QR format"),
    ("selliaapp://checkin?type=feedback", "valid location"),
    ("selliaapp://checkin?location=not-a-uuid", "valid location"),
    ("selliaapp://checkin?location", "valid location"),
    (f"selliaapp://checkin?location={_LOC}&business=nope", "valid location"),
    (f"selliaapp://checkin?location={_LOC}&type=admin", "QR type must be one of"),
])
async def test_qr_parse_rejects_malformed_payloads_for_the_right_reason(world, payload, reason) -> None:
    r = await world.client.post("/api/v1/qr-parse", params={"payload": payload})

    assert r.status_code == 400, (payload, r.text)
    assert reason in r.json()["detail"], (payload, r.text)  # not just "some 400"


def test_the_generator_refuses_an_unknown_type_and_keeps_business_optional() -> None:
    loc, biz = uuid.uuid4(), uuid.uuid4()

    with pytest.raises(ValueError):
        LocationQRGenerator.generate_checkin_qr(loc, None, "admin")
    with_business = LocationQRGenerator.generate_checkin_qr(loc, biz)["qr_payload"]
    assert with_business == f"selliaapp://checkin?location={loc}&business={biz}&type=visitor_checkin"
    parsed = LocationQRGenerator.parse_qr_payload(with_business)
    assert (parsed["location_id"], parsed["business_id"]) == (str(loc), str(biz))


async def _count(factory, model) -> int:
    async with factory() as s:
        return (await s.execute(select(func.count()).select_from(model))).scalar_one()
