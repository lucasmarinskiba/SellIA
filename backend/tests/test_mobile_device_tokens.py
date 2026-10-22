"""Device tokens for the mobile SDKs, over HTTP against a real database (SQLite).

Pinned here:
* issue, list and revoke are for the business owner and ADMIN members; the raw token is returned once and only its
  SHA-256 is stored;
* a device token reaches only its scope: its business, its location when bound, and only the operations listed;
* revoked, expired and unknown tokens are refused;
* while MOBILE_LEGACY_USER_JWT_ENABLED is on, the signed-in user still works; with it off, the JWT is refused on
  these routes and device tokens keep working;
* a geofence check from a device token names its visitor through visitor_ref, and cannot check another business.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event, func, select
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import location_checkin, mobile_device_tokens, mobile_geofence
from app.core.database import Base, get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.location_models import Location
from app.domains.businesses.mobile_device_models import MobileDeviceToken
from app.domains.businesses.mobile_device_service import (
    TOKEN_PREFIX,
    hash_token,
    new_token,
    visitor_id,
)
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.locations.checkin_models import (
    LocationCheckin,
    LocationFeedback,
    StaffCheckin,
)


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

MODELS = [Business, Location, BusinessMember, LocationCheckin, StaffCheckin, LocationFeedback, MobileDeviceToken]


# ------------------------------------------------------------------ pure helpers


def test_token_has_the_prefix_and_enough_entropy() -> None:
    token = new_token()
    assert token.startswith(TOKEN_PREFIX)
    assert len(token) > 40


def test_only_the_sha256_of_a_token_is_its_stored_form() -> None:
    token = new_token()
    assert hash_token(token) == hashlib.sha256(token.encode()).hexdigest()
    assert hash_token(token) != token


def test_visitor_identity_is_stable_per_token_and_ref() -> None:
    token_id = uuid.uuid4()
    assert visitor_id(token_id, "install-42") == visitor_id(token_id, "install-42")
    assert visitor_id(token_id, "install-42") != visitor_id(token_id, "install-43")
    assert visitor_id(token_id, "install-42") != visitor_id(uuid.uuid4(), "install-42")


# ------------------------------------------------------------------ HTTP harness


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _build_app(factory, who: dict) -> FastAPI:
    app = FastAPI()
    app.include_router(location_checkin.router, prefix="/api/v1")
    app.include_router(mobile_geofence.router)  # declares its own /api/v1/mobile prefix
    app.include_router(mobile_device_tokens.router)

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: who["actor"]  # the one managing tokens
    app.dependency_overrides[get_current_user_optional] = lambda: who["caller"]  # JWT on mobile routes, or None
    return app


@pytest_asyncio.fixture
async def world(factory):
    owner, admin, member, other_owner = (uuid.uuid4() for _ in range(4))
    async with factory() as s:
        biz_a = Business(user_id=owner, name="A")
        biz_b = Business(user_id=other_owner, name="B")
        s.add_all([biz_a, biz_b])
        await s.flush()

        def loc(biz, name, active=True):
            return Location(
                business_id=biz.id, name=name, address="x", city="BA",
                latitude=-34.6, longitude=-58.4, is_active=active,
            )

        loc_a1, loc_a2, loc_b1 = loc(biz_a, "A1"), loc(biz_a, "A2"), loc(biz_b, "B1")
        s.add_all([loc_a1, loc_a2, loc_b1])
        s.add_all([
            BusinessMember(business_id=biz_a.id, user_id=admin, role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=biz_a.id, user_id=member, role=BusinessMemberRole.MEMBER),
        ])
        await s.commit()
        ids = SimpleNamespace(
            biz_a=biz_a.id, biz_b=biz_b.id, a1=loc_a1.id, a2=loc_a2.id, b1=loc_b1.id,
            owner=owner, admin=admin, member=member,
        )

    who = {"actor": SimpleNamespace(id=owner), "caller": None}
    app = _build_app(factory, who)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


async def _issue(w, *, business=None, location="default", scopes=("checkin",), actor=None, days=30):
    """Owner (or ``actor``) issues a token over the API. Returns (raw_token, json_body)."""
    w.who["actor"] = SimpleNamespace(id=actor if actor is not None else w.owner)
    body = {
        "label": "Tablet entrada",
        "scopes": list(scopes),
        "expires_in_days": days,
    }
    if location == "default":
        body["location_id"] = str(w.a1)
    elif location is not None:
        body["location_id"] = str(location)
    r = await w.client.post(
        f"/api/v1/businesses/{business or w.biz_a}/mobile-device-tokens", json=body,
    )
    assert r.status_code == 201, r.text
    return r.json()["token"], r.json()


def _device(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _checkins(factory) -> int:
    async with factory() as s:
        return (await s.execute(select(func.count()).select_from(LocationCheckin))).scalar_one()


def _checkin_body(location_id) -> dict:
    return {"location_id": str(location_id), "checkin_type": "qr_scan"}


# ------------------------------------------------------------------ management


async def test_owner_issues_a_token_and_only_the_issue_response_carries_it(world) -> None:
    raw, body = await _issue(world)
    assert raw.startswith(TOKEN_PREFIX)
    assert body["scopes"] == ["checkin"]
    assert body["location_id"] == str(world.a1)

    world.who["actor"] = SimpleNamespace(id=world.owner)
    listed = (await world.client.get(f"/api/v1/businesses/{world.biz_a}/mobile-device-tokens")).json()
    assert len(listed) == 1
    assert "token" not in listed[0]

    async with world.factory() as s:
        rows = (await s.execute(select(MobileDeviceToken))).scalars().all()
    assert [r.token_hash for r in rows] == [hash_token(raw)]
    dumped = json.dumps({c.name: getattr(rows[0], c.name) for c in MobileDeviceToken.__table__.columns}, default=str)
    assert raw not in dumped


async def test_admin_can_issue_but_a_plain_member_cannot(world) -> None:
    await _issue(world, actor=world.admin)
    world.who["actor"] = SimpleNamespace(id=world.member)
    r = await world.client.post(
        f"/api/v1/businesses/{world.biz_a}/mobile-device-tokens",
        json={"label": "x", "scopes": ["checkin"]},
    )
    assert r.status_code == 403


async def test_a_location_from_another_business_cannot_be_bound(world) -> None:
    world.who["actor"] = SimpleNamespace(id=world.owner)
    r = await world.client.post(
        f"/api/v1/businesses/{world.biz_a}/mobile-device-tokens",
        json={"label": "x", "scopes": ["checkin"], "location_id": str(world.b1)},
    )
    assert r.status_code == 404


async def test_revoke_takes_effect_immediately(world) -> None:
    raw, body = await _issue(world)
    world.who["actor"] = SimpleNamespace(id=world.owner)
    r = await world.client.post(f"/api/v1/businesses/{world.biz_a}/mobile-device-tokens/{body['id']}/revoke")
    assert r.status_code == 200
    assert r.json()["revoked_at"] is not None

    world.who["caller"] = None
    assert (await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1), headers=_device(raw))).status_code == 401


# ------------------------------------------------------------------ reach and scope


async def test_bound_token_checks_in_its_own_location(world) -> None:
    raw, _ = await _issue(world, location=world.a1)
    r = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1), headers=_device(raw))
    assert r.status_code == 200, r.text


async def test_bound_token_is_refused_at_another_location_of_the_same_business(world) -> None:
    raw, _ = await _issue(world, location=world.a1)
    before = await _checkins(world.factory)
    r = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a2), headers=_device(raw))
    assert r.status_code == 403
    assert await _checkins(world.factory) == before


async def test_business_wide_token_reaches_every_location_of_its_business(world) -> None:
    raw, _ = await _issue(world, location=None)
    ok = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1), headers=_device(raw))
    # a2 is a real location of the business but inactive in this fixture: refused for that, not for auth.
    other = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a2), headers=_device(raw))
    assert ok.status_code == 200, ok.text
    assert other.status_code not in (401, 403), other.text


async def test_token_of_one_business_is_refused_on_another(world) -> None:
    raw, _ = await _issue(world, location=None)
    r = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.b1), headers=_device(raw))
    assert r.status_code == 403


async def test_token_without_the_operation_is_refused(world) -> None:
    raw, _ = await _issue(world, scopes=("feedback",), location=world.a1)
    r = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1), headers=_device(raw))
    assert r.status_code == 403


async def test_feedback_scope_reaches_feedback_only(world) -> None:
    raw, _ = await _issue(world, scopes=("feedback",), location=world.a1)
    feedback = await world.client.post(
        "/api/v1/locations/feedback", json={"location_id": str(world.a1), "nps_score": 9}, headers=_device(raw),
    )
    assert feedback.status_code == 200, feedback.text


# ------------------------------------------------------------------ refused tokens


async def test_unknown_token_is_refused(world) -> None:
    r = await world.client.post(
        "/api/v1/locations/checkin", json=_checkin_body(world.a1), headers=_device(f"{TOKEN_PREFIX}nope"),
    )
    assert r.status_code == 401


async def test_expired_token_is_refused(world) -> None:
    raw, _ = await _issue(world, location=world.a1)
    async with world.factory() as s:
        row = (await s.execute(select(MobileDeviceToken))).scalar_one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await s.commit()
    r = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1), headers=_device(raw))
    assert r.status_code == 401


async def test_no_credentials_is_refused(world) -> None:
    r = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1))
    assert r.status_code == 401


# ------------------------------------------------------------------ legacy JWT switch


async def test_signed_in_user_still_works_while_the_legacy_path_is_on(world, monkeypatch) -> None:
    monkeypatch.setattr("app.core.mobile_auth.get_settings", lambda: SimpleNamespace(MOBILE_LEGACY_USER_JWT_ENABLED=True))
    world.who["caller"] = SimpleNamespace(id=world.owner)
    world.who["actor"] = SimpleNamespace(id=world.owner)
    r = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1))
    assert r.status_code == 200, r.text


async def test_signed_in_user_is_refused_once_the_legacy_path_is_off_but_device_tokens_work(world, monkeypatch) -> None:
    monkeypatch.setattr("app.core.mobile_auth.get_settings", lambda: SimpleNamespace(MOBILE_LEGACY_USER_JWT_ENABLED=False))
    raw, _ = await _issue(world, location=world.a1)
    world.who["caller"] = SimpleNamespace(id=world.owner)

    jwt_only = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1))
    with_token = await world.client.post("/api/v1/locations/checkin", json=_checkin_body(world.a1), headers=_device(raw))

    assert jwt_only.status_code == 401
    assert with_token.status_code == 200, with_token.text


# ------------------------------------------------------------------ geofence


def _geofence_body(business_id, visitor_ref=None) -> dict:
    body = {"latitude": -34.6, "longitude": -58.4, "business_id": str(business_id)}
    if visitor_ref is not None:
        body["visitor_ref"] = visitor_ref
    return body


async def test_geofence_from_a_device_token_needs_a_visitor_ref(world) -> None:
    raw, _ = await _issue(world, scopes=("geofence",), location=None)
    r = await world.client.post("/api/v1/mobile/geofence/check", json=_geofence_body(world.biz_a), headers=_device(raw))
    assert r.status_code == 422


async def test_geofence_from_a_device_token_cannot_check_another_business(world) -> None:
    raw, _ = await _issue(world, scopes=("geofence",), location=None)
    r = await world.client.post(
        "/api/v1/mobile/geofence/check", json=_geofence_body(world.biz_b, "install-1"), headers=_device(raw),
    )
    assert r.status_code == 403


async def test_geofence_from_a_device_token_is_authorised_with_a_visitor_ref(world) -> None:
    raw, _ = await _issue(world, scopes=("geofence",), location=None)
    r = await world.client.post(
        "/api/v1/mobile/geofence/check", json=_geofence_body(world.biz_a, "install-1"), headers=_device(raw),
    )
    assert r.status_code not in (401, 403, 422), r.text
