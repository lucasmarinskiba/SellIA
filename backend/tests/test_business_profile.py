"""Per-business profile over HTTP against a real database (SQLite).

Pinned here:
* each business of one user keeps its own profile: editing one never changes the other;
* members can read a profile, only owners and ADMIN members can edit it, strangers get 403 and change nothing;
* values are validated (an unknown language or enum is 422), and an omitted or null field is left as it was;
* the language is written to businesses.config, where the triggers, the post-visit worker and the seasonal
  suggestions read it; geography comes from the locations, not from the profile.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event, select
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import business_profile
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.business_context.models import BusinessContext
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
    owner, manager, member, stranger = (uuid.uuid4() for _ in range(4))
    async with factory() as s:
        # One owner, two businesses: the case the legacy per-user endpoint gets wrong.
        cafe = Business(user_id=owner, name="Café Norte")
        shop = Business(user_id=owner, name="Tienda Sur")
        s.add_all([cafe, shop])
        await s.flush()
        s.add(Location(business_id=cafe.id, name="Centro", address="x", city="Rosario", country_code="AR",
                       latitude=-32.9, longitude=-60.6))
        s.add(Location(business_id=cafe.id, name="Norte", address="y", city="Rosario", country_code="AR",
                       latitude=-32.9, longitude=-60.6))
        s.add_all([
            BusinessMember(business_id=cafe.id, user_id=manager, role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=cafe.id, user_id=member, role=BusinessMemberRole.MEMBER),
        ])
        await s.commit()
        ids = SimpleNamespace(cafe=cafe.id, shop=shop.id, owner=owner, manager=manager,
                              member=member, stranger=stranger)

    who = {"user": SimpleNamespace(id=owner)}
    app = FastAPI()
    app.include_router(business_profile.router)

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: who["user"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


def _url(business_id) -> str:
    return f"/api/v1/businesses/{business_id}/profile"


async def test_reading_creates_a_default_profile_with_the_location_summary(world) -> None:
    r = await world.client.get(_url(world.cafe))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Café Norte"
    assert (body["language"], body["business_type"], body["presence_type"]) == ("es", "other", "online_only")
    assert body["locations"] == {"count": 2, "countries": ["AR"], "cities": ["Rosario"]}


async def test_each_business_of_one_owner_keeps_its_own_profile(world) -> None:
    await world.client.patch(_url(world.cafe), json={"business_type": "food_beverage",
                                                     "target_audience": "vecinos del barrio"})
    await world.client.patch(_url(world.shop), json={"business_type": "fashion_beauty",
                                                     "target_audience": "mujeres 25-40"})

    cafe = (await world.client.get(_url(world.cafe))).json()
    shop = (await world.client.get(_url(world.shop))).json()
    assert (cafe["business_type"], cafe["target_audience"]) == ("food_beverage", "vecinos del barrio")
    assert (shop["business_type"], shop["target_audience"]) == ("fashion_beauty", "mujeres 25-40")

    async with world.factory() as s:
        rows = (await s.execute(select(BusinessContext))).scalars().all()
    assert len(rows) == 2 and {r.business_id for r in rows} == {world.cafe, world.shop}


async def test_a_partial_update_leaves_the_other_fields_alone(world) -> None:
    await world.client.patch(_url(world.cafe), json={"value_proposition": "café de especialidad", "does_delivery": True})
    body = (await world.client.patch(_url(world.cafe), json={"primary_goal": "more_sales"})).json()
    assert body["value_proposition"] == "café de especialidad"
    assert body["does_delivery"] is True
    assert body["primary_goal"] == "more_sales"


async def test_a_null_field_means_no_change(world) -> None:
    await world.client.patch(_url(world.cafe), json={"industry": "gastronomía"})
    body = (await world.client.patch(_url(world.cafe), json={"industry": None})).json()
    assert body["industry"] == "gastronomía"


async def test_the_language_is_stored_on_the_business_and_read_back(world) -> None:
    body = (await world.client.patch(_url(world.cafe), json={"language": "en"})).json()
    assert body["language"] == "en"
    async with world.factory() as s:
        business = await s.get(Business, world.cafe)
    assert business.config["language"] == "en"
    assert (await world.client.get(_url(world.shop))).json()["language"] == "es"


async def test_a_manager_can_edit_a_member_can_only_read(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.manager)
    assert (await world.client.patch(_url(world.cafe), json={"industry": "x"})).status_code == 200

    world.who["user"] = SimpleNamespace(id=world.member)
    assert (await world.client.get(_url(world.cafe))).status_code == 200
    assert (await world.client.patch(_url(world.cafe), json={"industry": "y"})).status_code == 403


async def test_a_stranger_can_neither_read_nor_change(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.stranger)
    assert (await world.client.get(_url(world.cafe))).status_code == 403
    assert (await world.client.patch(_url(world.cafe), json={"industry": "z"})).status_code == 403


async def test_unknown_values_are_rejected(world) -> None:
    assert (await world.client.patch(_url(world.cafe), json={"language": "fr"})).status_code == 422
    assert (await world.client.patch(_url(world.cafe), json={"business_type": "not_a_type"})).status_code == 422
    assert (await world.client.patch(_url(world.cafe), json={"price_range": "cheap"})).status_code == 422
    assert (await world.client.patch(_url(world.cafe), json={"industry": "x" * 101})).status_code == 422
