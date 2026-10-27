"""Seasonal campaign suggestions: the calendar, and the read-only endpoint over a real database (SQLite).

Pinned here:
* Easter, the third Sunday of October and June, and the open/upcoming logic against known dates;
* a country without a calendar for a season gets only the global seasons, with a note saying so;
* any member can read the suggestions; a stranger cannot; the draft follows the business language and carries the
  business name, and makes no offer.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import seasonal_suggestions
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.sequences.seasonal import easter_sunday, next_occurrences, nth_weekday


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

MODELS = [Business, Location, BusinessMember]


# ------------------------------------------------------------------ calendar


@pytest.mark.parametrize(
    ("year", "expected"),
    [(2024, date(2024, 3, 31)), (2025, date(2025, 4, 20)), (2026, date(2026, 4, 5)), (2027, date(2027, 3, 28))],
)
def test_easter_matches_known_dates(year: int, expected: date) -> None:
    assert easter_sunday(year) == expected


def test_third_sunday_of_october_and_june() -> None:
    assert nth_weekday(2026, 10, 6, 3) == date(2026, 10, 18)  # Día de la Madre (AR)
    assert nth_weekday(2026, 6, 6, 3) == date(2026, 6, 21)  # Día del Padre (AR)


def test_an_open_window_is_marked_open_with_no_countdown() -> None:
    keys = {s.key: (s, is_open) for s, is_open in next_occurrences("AR", date(2026, 10, 10))}
    season, is_open = keys["mothers_day"]
    assert is_open is True
    assert season.start == date(2026, 10, 4) and season.end == date(2026, 10, 18)


def test_a_passed_window_rolls_to_next_year() -> None:
    keys = {s.key: (s, is_open) for s, is_open in next_occurrences("AR", date(2026, 12, 26))}
    christmas, is_open = keys["christmas"]
    assert is_open is False
    assert christmas.start == date(2027, 12, 1)


def test_a_country_without_a_calendar_gets_only_the_global_seasons() -> None:
    keys = {s.key for s, _ in next_occurrences("UY", date(2026, 7, 15))}
    assert keys == {"christmas", "easter"}


def test_argentina_gets_the_local_seasons_and_winter_is_approximate() -> None:
    by_key = {s.key: s for s, _ in next_occurrences("AR", date(2026, 7, 15))}
    assert {"mothers_day", "fathers_day", "winter_holidays", "summer_holidays"} <= set(by_key)
    assert by_key["winter_holidays"].approximate is True
    assert by_key["christmas"].approximate is False


# ------------------------------------------------------------------ endpoint


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
        es = Business(user_id=owner, name="Panadería Sol")  # no locations yet: default country
        uy = Business(user_id=owner, name="Tienda Norte", config={"language": "en"})
        s.add_all([es, uy])
        await s.flush()
        s.add(Location(business_id=uy.id, name="Montevideo", address="x", city="MVD", country_code="UY",
                       latitude=-34.9, longitude=-56.2))
        s.add(BusinessMember(business_id=es.id, user_id=member, role=BusinessMemberRole.MEMBER))
        await s.commit()
        ids = SimpleNamespace(es=es.id, uy=uy.id, owner=owner, member=member, stranger=stranger)

    who = {"user": SimpleNamespace(id=owner)}
    app = FastAPI()
    app.include_router(seasonal_suggestions.router)

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: who["user"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, **vars(ids))


def _url(business_id, as_of="2026-10-10") -> str:
    return f"/api/v1/businesses/{business_id}/seasonal-suggestions?as_of={as_of}"


async def test_owner_gets_the_argentine_calendar_with_spanish_drafts(world) -> None:
    r = await world.client.get(_url(world.es))
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["country"], body["country_source"], body["language"]) == ("AR", "default", "es")
    assert body["coverage_note"] is None
    mothers = next(s for s in body["seasons"] if s["key"] == "mothers_day")
    assert mothers["status"] == "open" and mothers["days_until"] is None
    assert mothers["draft"]["subject"] == "Por el Día de la Madre"
    assert "Panadería Sol" not in mothers["draft"]["body"]


async def test_a_member_can_read_and_a_stranger_cannot(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.member)
    assert (await world.client.get(_url(world.es))).status_code == 200
    world.who["user"] = SimpleNamespace(id=world.stranger)
    assert (await world.client.get(_url(world.es))).status_code == 403


async def test_the_location_country_and_the_english_language_are_used(world) -> None:
    r = await world.client.get(_url(world.uy))
    body = r.json()
    assert (body["country"], body["country_source"], body["language"]) == ("UY", "locations", "en")
    assert body["coverage_note"] == "Para UY sólo hay calendario de Navidad y Pascua."
    assert {s["key"] for s in body["seasons"]} == {"christmas", "easter"}
    christmas = next(s for s in body["seasons"] if s["key"] == "christmas")
    assert christmas["name"] == "Happy holidays"
    assert christmas["draft"]["subject"] == "Happy holidays from Tienda Norte"


async def test_upcoming_seasons_report_how_many_days_away(world) -> None:
    body = (await world.client.get(_url(world.uy, as_of="2026-07-15"))).json()
    christmas = next(s for s in body["seasons"] if s["key"] == "christmas")
    assert christmas["status"] == "upcoming"
    assert christmas["days_until"] == (date(2026, 12, 1) - date(2026, 7, 15)).days


async def test_no_draft_promises_an_offer(world) -> None:
    body = (await world.client.get(_url(world.es, as_of="2026-12-05"))).json()
    text = " ".join(s["draft"]["subject"] + " " + s["draft"]["body"] for s in body["seasons"]).lower()
    for promise in ("descuento", "discount", "% off", "gratis", "free shipping"):
        assert promise not in text


@pytest.mark.parametrize("as_of", ["2026-01-15", "2026-07-15"])
async def test_every_season_draft_has_a_subject_and_body(world, as_of) -> None:
    body = (await world.client.get(_url(world.es, as_of=as_of))).json()
    assert body["seasons"]
    assert all(s["draft"]["subject"] and s["draft"]["body"] for s in body["seasons"])
