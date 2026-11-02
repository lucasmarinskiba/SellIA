"""POST /api/v1/sequences/cold-email: login, an active business, and the owner's AI allowance.

Each call is a paid model call. These tests pin that:

* no login                       -> 401, nothing is generated
* a login with no business       -> 409
* the owner within their allowance -> 5 emails, and the tokens are recorded
* the owner over their allowance -> 429, nothing is generated

The model call itself is replaced; no network. No Postgres needed.
"""

import uuid
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

from app.api.v1 import email_sequences
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.businesses.models import Business
from app.domains.harvey import ai_budget


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


OWNER = SimpleNamespace(id=uuid.uuid4())
NO_BUSINESS = SimpleNamespace(id=uuid.uuid4())

BODY = {
    "lead": {
        "name": "Ana",
        "email": "ana@example.com",
        "company": "Acme",
        "title": "CEO",
        "pain_point": "poco tráfico",
        "industry": "retail",
    },
    "offer": "Campañas de WhatsApp",
    "sender_email": "ventas@example.com",
}


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[Business.__table__]))
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add(Business(user_id=OWNER.id, name="Tienda"))
        await session.commit()
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _build_app(factory, who) -> FastAPI:
    app = FastAPI()
    app.include_router(email_sequences.router, prefix="/api/v1")  # as in app/main.py

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:  # None -> keep the real get_current_user, so no token is rejected
        app.dependency_overrides[get_current_user] = lambda: who
    return app


def _client(factory, who=OWNER) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=_build_app(factory, who)), base_url="http://test")


@pytest.fixture
def generated(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Replace the model call; records how many times it ran."""
    calls: list[int] = []

    async def fake_generate(lead, offer):
        calls.append(1)
        return [email_sequences.EmailInSequence(day=d, subject=f"Asunto {d}", body="Hola") for d in (1, 3, 5, 7, 10)]

    monkeypatch.setattr(email_sequences, "_generate_cold_email_sequence", fake_generate)
    return calls


@pytest.mark.asyncio
async def test_no_login_is_refused_and_nothing_is_generated(factory, generated):
    async with _client(factory, who=None) as client:
        res = await client.post("/api/v1/sequences/cold-email", json=BODY)

    assert res.status_code == 401
    assert generated == []


@pytest.mark.asyncio
async def test_account_without_a_business_is_refused(factory, generated):
    async with _client(factory, who=NO_BUSINESS) as client:
        res = await client.post("/api/v1/sequences/cold-email", json=BODY)

    assert res.status_code == 409
    assert generated == []


@pytest.mark.asyncio
async def test_owner_within_allowance_gets_five_emails(factory, generated):
    async with _client(factory) as client:
        res = await client.post("/api/v1/sequences/cold-email", json=BODY)

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "generated"
    assert [e["day"] for e in body["emails"]] == [1, 3, 5, 7, 10]
    assert generated == [1]


@pytest.mark.asyncio
async def test_tokens_from_the_model_are_recorded_against_the_owner(factory, monkeypatch):
    recorded: list[tuple] = []

    async def capture(db, user_id, business_id, tokens):
        recorded.append((user_id, tokens))

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "usage": {"input_tokens": 100, "output_tokens": 23},
                "content": [{"text": '[{"day": 1, "subject": "Hola", "body": "Texto"}]'}],
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    async def within_allowance(db, user_id):
        return {"exceeded": False}

    # The test client is created before httpx.AsyncClient is replaced: the replacement is global.
    async with _client(factory) as client:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(email_sequences.httpx, "AsyncClient", lambda *a, **k: FakeClient())
        monkeypatch.setattr(ai_budget, "status", within_allowance)
        monkeypatch.setattr(ai_budget, "_persist", capture)
        res = await client.post("/api/v1/sequences/cold-email", json=BODY)

    assert res.status_code == 200, res.text
    assert recorded == [(OWNER.id, 123)]


@pytest.mark.asyncio
async def test_owner_over_allowance_is_refused_and_nothing_is_generated(factory, generated, monkeypatch):
    async def used_up(db, user_id):
        return {"exceeded": True}

    monkeypatch.setattr(ai_budget, "status", used_up)

    async with _client(factory) as client:
        res = await client.post("/api/v1/sequences/cold-email", json=BODY)

    assert res.status_code == 429
    assert generated == []
