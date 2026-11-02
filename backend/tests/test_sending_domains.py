"""A business's sending domain over HTTP against a real database (SQLite), with Resend stubbed.

Pinned here:
* registering a domain stores the DNS records Resend returns and starts it as pending; the same domain again does
  not register a second time in Resend; a new alias alone updates the row;
* malformed domains and aliases are refused before Resend is called;
* members can read, only owners and ADMIN members can register or verify, strangers get 403;
* verify asks Resend to check, reads the status back, and marks verified with a timestamp only when Resend says so;
* a missing key is 503 and a Resend error is 502, with no provider detail leaked.

The Resend calls are stubbed: the live API has not been exercised from here.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import sending_domains
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.core.integrations.resend_domains import ResendError, ResendNotConfigured
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.business_context.models import BusinessContext
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember, BusinessMemberRole
from app.domains.sequences.sending_domain_models import BusinessSendingDomain


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

MODELS = [Business, BusinessMember, BusinessContext, BusinessSendingDomain]
RECORDS = [{"record": "DKIM", "type": "TXT", "name": "resend._domainkey", "value": "p=MIG...", "status": "pending"}]


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def world(factory, monkeypatch):
    owner, manager, member, stranger = (uuid.uuid4() for _ in range(4))
    async with factory() as s:
        biz = Business(user_id=owner, name="Concesionaria Norte")
        s.add(biz)
        await s.flush()
        s.add_all([
            BusinessMember(business_id=biz.id, user_id=manager, role=BusinessMemberRole.ADMIN),
            BusinessMember(business_id=biz.id, user_id=member, role=BusinessMemberRole.MEMBER),
        ])
        await s.commit()
        biz_id = biz.id

    calls = SimpleNamespace(create=[], get=[], verify=[], status="pending")

    async def fake_create(name: str) -> dict:
        calls.create.append(name)
        return {"id": f"rd_{len(calls.create)}", "status": "pending", "records": RECORDS}

    async def fake_verify(domain_id: str) -> None:
        calls.verify.append(domain_id)

    async def fake_get(domain_id: str) -> dict:
        calls.get.append(domain_id)
        return {"id": domain_id, "status": calls.status, "records": RECORDS}

    monkeypatch.setattr(sending_domains, "create_domain", fake_create)
    monkeypatch.setattr(sending_domains, "verify_domain", fake_verify)
    monkeypatch.setattr(sending_domains, "get_domain", fake_get)

    who = {"user": SimpleNamespace(id=owner)}
    app = FastAPI()
    app.include_router(sending_domains.router)

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: who["user"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(
            client=client, who=who, calls=calls, biz=biz_id,
            owner=owner, manager=manager, member=member, stranger=stranger,
        )


def _url(w, suffix: str = "") -> str:
    return f"/api/v1/businesses/{w.biz}/sending-domain{suffix}"


async def test_registering_stores_the_records_and_starts_pending(world) -> None:
    r = await world.client.put(_url(world), json={"domain": "Concesionaria.com.ar", "local_part": "Ventas"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["configured"] is True
    assert (body["domain"], body["local_part"]) == ("concesionaria.com.ar", "ventas")
    assert body["from_address"] == "ventas@concesionaria.com.ar"
    assert body["status"] == "pending"
    assert body["records"] == RECORDS
    assert world.calls.create == ["concesionaria.com.ar"]


async def test_registering_the_same_domain_again_does_not_register_twice(world) -> None:
    await world.client.put(_url(world), json={"domain": "concesionaria.com.ar", "local_part": "ventas"})
    r = await world.client.put(_url(world), json={"domain": "concesionaria.com.ar", "local_part": "asesor"})
    assert r.status_code == 200
    assert r.json()["from_address"] == "asesor@concesionaria.com.ar"
    assert world.calls.create == ["concesionaria.com.ar"]


async def test_malformed_domains_and_aliases_are_refused_before_resend(world) -> None:
    for domain in ("localhost", "192.168.0.1", "concesionaria", "con cesion.com"):
        r = await world.client.put(_url(world), json={"domain": domain})
        assert r.status_code == 422, domain
    r = await world.client.put(_url(world), json={"domain": "concesionaria.com.ar", "local_part": "Ventas Pro!"})
    assert r.status_code == 422
    assert world.calls.create == []


async def test_a_member_reads_but_cannot_register_and_a_manager_can(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.member)
    assert (await world.client.get(_url(world))).status_code == 200
    assert (await world.client.put(_url(world), json={"domain": "concesionaria.com.ar"})).status_code == 403

    world.who["user"] = SimpleNamespace(id=world.manager)
    assert (await world.client.put(_url(world), json={"domain": "concesionaria.com.ar"})).status_code == 200


async def test_a_stranger_is_refused(world) -> None:
    world.who["user"] = SimpleNamespace(id=world.stranger)
    assert (await world.client.get(_url(world))).status_code == 403
    assert (await world.client.put(_url(world), json={"domain": "concesionaria.com.ar"})).status_code == 403


async def test_no_domain_yet_reads_as_not_configured(world) -> None:
    body = (await world.client.get(_url(world))).json()
    assert body == {"configured": False, "domain": None, "local_part": None, "from_address": None,
                    "status": None, "records": [], "verified_at": None}


async def test_verify_marks_verified_only_when_resend_says_so(world) -> None:
    await world.client.put(_url(world), json={"domain": "concesionaria.com.ar"})

    world.calls.status = "pending"
    body = (await world.client.post(_url(world, "/verify"))).json()
    assert body["status"] == "pending" and body["verified_at"] is None

    world.calls.status = "verified"
    body = (await world.client.post(_url(world, "/verify"))).json()
    assert body["status"] == "verified"
    assert body["verified_at"] is not None
    assert world.calls.verify == ["rd_1", "rd_1"]


async def test_verify_before_registering_is_404(world) -> None:
    assert (await world.client.post(_url(world, "/verify"))).status_code == 404


async def test_a_missing_key_is_503(world, monkeypatch) -> None:
    async def not_configured(name: str) -> dict:
        raise ResendNotConfigured("RESEND_API_KEY no está configurada")

    monkeypatch.setattr(sending_domains, "create_domain", not_configured)
    r = await world.client.put(_url(world), json={"domain": "concesionaria.com.ar"})
    assert r.status_code == 503


async def test_a_resend_error_is_502_without_provider_detail(world, monkeypatch) -> None:
    async def rejected(name: str) -> dict:
        raise ResendError("Resend respondió 422")

    monkeypatch.setattr(sending_domains, "create_domain", rejected)
    r = await world.client.put(_url(world), json={"domain": "concesionaria.com.ar"})
    assert r.status_code == 502
    assert "422" not in r.json()["detail"]
