"""The semantic cache must never serve one business's answer to another, and must expire.

It was global (one tenant's answer, built from its catalog and prices, came back to another at
similarity >= 0.92), ignored its TTL, and tried Ollama and OpenAI, logging three warnings, on
every LLM call when no embedding provider is configured (production has none).

The vector tests need a PostgreSQL with pgvector (CI uses the pgvector image) and skip otherwise.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text, update

DIM = 768


def _vector(*lead: float) -> list[float]:
    return [*lead, *([0.0] * (DIM - len(lead)))]


@pytest.fixture
def fake_embeddings(monkeypatch):
    """Embeddings by keyword, so 'precio' and 'precio de envío' are neighbours."""
    from app.core import semantic_cache as module

    async def embed_text(query: str) -> list[float]:
        if "precio" in query:
            return _vector(1.0, 0.0)
        if "horario" in query:
            return _vector(0.0, 1.0)
        return _vector(0.5, 0.5)

    monkeypatch.setattr(module.embedding_service, "embed_text", embed_text)
    return module


@pytest.fixture
async def two_businesses(db_session, test_user):
    from app.domains.businesses.models import Business

    a = Business(user_id=test_user.id, name=f"Cache A {uuid.uuid4().hex[:6]}")
    b = Business(user_id=test_user.id, name=f"Cache B {uuid.uuid4().hex[:6]}")
    db_session.add_all([a, b])
    await db_session.commit()
    ids = (a.id, b.id)
    yield ids
    from app.core.semantic_cache import SemanticCacheEmbedding

    await db_session.execute(SemanticCacheEmbedding.__table__.delete().where(SemanticCacheEmbedding.business_id.in_(ids)))
    await db_session.execute(Business.__table__.delete().where(Business.id.in_(ids)))
    await db_session.commit()


@pytest.fixture
async def cache_table(db_session):
    exists = (await db_session.execute(text("SELECT to_regclass('semantic_cache_embeddings')"))).scalar_one()
    if exists is None:
        pytest.skip("this PostgreSQL has no pgvector, so semantic_cache_embeddings was not created")


async def test_an_answer_is_only_served_to_the_business_that_produced_it(
    fake_embeddings, cache_table, two_businesses
) -> None:
    cache = fake_embeddings.SemanticCache()
    a, b = two_businesses

    await cache.store("¿cuál es el precio?", "Cuesta $100 (negocio A)", business_id=a)

    assert await cache.get_similar("precio del producto", business_id=a) == "Cuesta $100 (negocio A)"
    assert await cache.get_similar("precio del producto", business_id=b) is None  # same meaning, other tenant


async def test_nothing_is_read_or_stored_without_a_business(fake_embeddings, cache_table, two_businesses, db_session) -> None:
    from app.core.semantic_cache import SemanticCacheEmbedding

    cache = fake_embeddings.SemanticCache()
    a, _ = two_businesses
    await cache.store("precio", "respuesta", business_id=a)

    assert await cache.get_similar("precio") is None
    await cache.store("precio otra vez", "respuesta global")
    rows = (await db_session.execute(select(SemanticCacheEmbedding.response_text))).scalars().all()
    assert "respuesta global" not in rows


async def test_unrelated_questions_do_not_hit(fake_embeddings, cache_table, two_businesses) -> None:
    cache = fake_embeddings.SemanticCache()
    a, _ = two_businesses
    await cache.store("precio", "respuesta de precio", business_id=a)
    assert await cache.get_similar("horario de atención", business_id=a) is None


async def test_entries_expire_after_the_ttl_and_are_cleaned_on_the_next_store(
    fake_embeddings, cache_table, two_businesses, db_session
) -> None:
    from app.core.semantic_cache import SemanticCacheEmbedding

    cache = fake_embeddings.SemanticCache(ttl_seconds=3600)
    a, _ = two_businesses
    await cache.store("precio", "respuesta vieja", business_id=a)
    assert await cache.get_similar("precio", business_id=a) == "respuesta vieja"

    await db_session.execute(
        update(SemanticCacheEmbedding).where(SemanticCacheEmbedding.business_id == a)
        .values(created_at=datetime.now(timezone.utc) - timedelta(hours=2))
    )
    await db_session.commit()
    assert await cache.get_similar("precio", business_id=a) is None  # expired, not served

    await cache.store("horario", "respuesta nueva", business_id=a)
    rows = (await db_session.execute(
        select(SemanticCacheEmbedding.response_text).where(SemanticCacheEmbedding.business_id == a)
    )).scalars().all()
    assert rows == ["respuesta nueva"]  # the expired one was deleted


async def test_deleting_a_business_deletes_its_cache(fake_embeddings, cache_table, db_session, test_user) -> None:
    from app.core.semantic_cache import SemanticCacheEmbedding
    from app.domains.businesses.models import Business

    biz = Business(user_id=test_user.id, name=f"Cache C {uuid.uuid4().hex[:6]}")
    db_session.add(biz)
    await db_session.commit()
    biz_id = biz.id
    await fake_embeddings.SemanticCache().store("precio", "x", business_id=biz_id)

    await db_session.execute(Business.__table__.delete().where(Business.id == biz_id))
    await db_session.commit()
    left = (await db_session.execute(select(SemanticCacheEmbedding.id).where(SemanticCacheEmbedding.business_id == biz_id))).all()
    assert left == []


# ── no embedding provider (production today): quiet and fast ─────────────────

async def test_without_an_embedding_provider_the_cache_pauses_and_stops_trying(monkeypatch) -> None:
    from app.core import semantic_cache as module

    calls = 0

    async def failing_embed(query: str):
        nonlocal calls
        calls += 1
        raise RuntimeError("All embedding providers failed (Ollama and OpenAI)")

    monkeypatch.setattr(module.embedding_service, "embed_text", failing_embed)
    cache, biz = module.SemanticCache(), uuid.uuid4()

    results = [await cache.get_similar("precio", business_id=biz) for _ in range(5)]
    await cache.store("precio", "x", business_id=biz)

    assert results == [None] * 5
    assert calls == 1  # one attempt, then it backs off instead of hitting Ollama/OpenAI on every call


async def test_the_cache_tries_again_after_the_backoff(monkeypatch) -> None:
    from app.core import semantic_cache as module

    calls = 0

    async def failing_embed(query: str):
        nonlocal calls
        calls += 1
        raise RuntimeError("down")

    monkeypatch.setattr(module.embedding_service, "embed_text", failing_embed)
    cache, biz = module.SemanticCache(), uuid.uuid4()

    await cache.get_similar("precio", business_id=biz)
    cache._unavailable_until = time.monotonic() - 1  # the pause is over
    await cache.get_similar("precio", business_id=biz)
    assert calls == 2


async def test_the_llm_provider_scopes_the_cache_by_business(monkeypatch) -> None:
    """generate_with_fallback must pass its business_id to both the lookup and the store."""
    from langchain_core.messages import HumanMessage

    from app.core import semantic_cache as module
    from app.domains.agents import llm_provider

    seen: dict[str, list] = {"get": [], "set": []}

    async def fake_get(prompt, business_id=None):
        seen["get"].append(business_id)

    async def fake_set(prompt, response, ttl=None, business_id=None):
        seen["set"].append(business_id)

    async def fake_keys(db, business_id):
        return {"ollama": False, "kimi": None, "openai": None, "anthropic": "k", "groq": None}

    class _Response:
        content = "respuesta"

    class _Provider:
        async def generate(self, **kwargs):
            return _Response()

    async def allow(db, business_id):
        return True

    monkeypatch.setattr(module.semantic_cache, "get", fake_get)
    monkeypatch.setattr(module.semantic_cache, "set", fake_set)
    monkeypatch.setattr(llm_provider, "resolve_api_keys", fake_keys)
    monkeypatch.setattr(llm_provider, "FallbackProvider", _Provider)
    monkeypatch.setattr(llm_provider, "_check_and_increment_daily_usage", allow)

    biz = uuid.uuid4()
    await llm_provider.generate_with_fallback(
        db=None, business_id=biz, messages=[HumanMessage(content="hola")], business_context={}, use_smart_router=False
    )
    assert seen == {"get": [biz], "set": [biz]}
