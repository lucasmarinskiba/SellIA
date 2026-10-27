"""Legacy /business-context API and service, scoped to a business, over a real database (SQLite).

Pinned here:
* a named business must be one the caller can read (members) or manage (owner, ADMIN); a stranger gets 403 and no
  context row is created for that business;
* a user with several business contexts who names no business gets 409, not one of the profiles picked at random:
  the service raises AmbiguousBusinessContext instead of mixing one business's profile into another's;
* a user with exactly one context keeps getting it without naming a business, as before.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import datetime, timezone
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
from app.domains.business_context import api as legacy_api
from app.domains.business_context.models import BusinessContext
from app.domains.business_context.service import AmbiguousBusinessContext, BusinessContextService
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole


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

MODELS = [Business, BusinessMember, Location, BusinessContext]


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def world(factory):
    owner, member, stranger = (uuid.uuid4() for _ in range(3))
    async with factory() as s:
        cafe = Business(user_id=owner, name="Café Norte")
        shop = Business(user_id=owner, name="Tienda Sur")
        solo = Business(user_id=owner, name="Solo")  # used by the single-context user below
        s.add_all([cafe, shop, solo])
        await s.flush()
        s.add(BusinessMember(business_id=cafe.id, user_id=member, role=BusinessMemberRole.MEMBER))
        await s.commit()
        ids = SimpleNamespace(cafe=cafe.id, shop=shop.id, solo=solo.id, owner=owner, member=member, stranger=stranger)

    who = {"user": SimpleNamespace(id=owner)}
    app = FastAPI()
    app.include_router(legacy_api.router, prefix="/api/v1")

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: who["user"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


async def _contexts(factory) -> int:
    async with factory() as s:
        return (await s.execute(select(func.count()).select_from(BusinessContext))).scalar_one()


async def test_the_owner_reads_and_creates_the_context_of_a_named_business(world) -> None:
    r = await world.client.get("/api/v1/business-context", params={"business_id": str(world.cafe)})
    assert r.status_code == 200, r.text
    assert r.json()["business_id"] == str(world.cafe)
    assert await _contexts(world.factory) == 1


async def test_a_stranger_is_refused_and_no_context_is_created(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.stranger)
    r = await world.client.get("/api/v1/business-context", params={"business_id": str(world.cafe)})
    assert r.status_code == 403
    assert await _contexts(world.factory) == 0


async def test_a_member_reads_but_cannot_write(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.member)
    assert (await world.client.get("/api/v1/business-context", params={"business_id": str(world.cafe)})).status_code == 200
    write = await world.client.post(
        "/api/v1/business-context", params={"business_id": str(world.cafe)}, json={"industry": "x"},
    )
    assert write.status_code == 403


async def test_an_unknown_business_is_404(world) -> None:
    r = await world.client.get("/api/v1/business-context", params={"business_id": str(uuid.uuid4())})
    assert r.status_code == 404


async def test_several_contexts_and_no_business_named_is_409(world) -> None:
    for business in (world.cafe, world.shop):
        assert (await world.client.get("/api/v1/business-context", params={"business_id": str(business)})).status_code == 200

    r = await world.client.get("/api/v1/business-context")
    assert r.status_code == 409
    assert "indicá business_id" in r.json()["detail"]


async def test_a_single_context_is_still_returned_without_a_business(world) -> None:
    await world.client.get("/api/v1/business-context", params={"business_id": str(world.solo)})
    r = await world.client.get("/api/v1/business-context")
    assert r.status_code == 200
    assert r.json()["business_id"] == str(world.solo)


async def test_the_service_refuses_to_guess_between_several_contexts(world) -> None:
    for business in (world.cafe, world.shop):
        await world.client.get("/api/v1/business-context", params={"business_id": str(business)})
    async with world.factory() as s:
        with pytest.raises(AmbiguousBusinessContext):
            await BusinessContextService(s).get_or_create_context(world.owner, None)
        named = await BusinessContextService(s).get_or_create_context(world.owner, world.shop)
        assert named.business_id == world.shop


async def test_the_detect_endpoint_checks_the_business_too(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.stranger)
    r = await world.client.get("/api/v1/business-context/detect", params={"business_id": str(world.cafe)})
    assert r.status_code == 403
