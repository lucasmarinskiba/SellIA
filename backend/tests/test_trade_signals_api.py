"""Tests de integración para la API copy-trade supervisado.

Fija el contrato HTTP: presencia (heartbeat) → propuesta → aprobación →
handoff. El backend nunca ejecuta: el handoff siempre trae agent_executes=False.

Self-contained (sin DB/Redis): los endpoints copy-trade mantienen estado en
memoria, así que se usa un AsyncClient ASGI propio y un usuario falso vía
dependency override — no se tocan fixtures de base de datos.

`get_store` también se override con un Redis falso in-memory (ver
`_FakeRedis` abajo) — RedisCopyTradeStore.submit()/approve()/etc. llaman a
self.redis.{setex,exists,hget,hset,expire,hgetall,hdel} directamente; sin
este override, cada test intenta conectar a un Redis real (REDIS_URL) que no
existe en este proceso de test, y `is_active()`'s postura fail-closed
convierte cualquier RedisError en "usuario inactivo" silenciosamente —
antes rompía con `KeyError: 'proposal'` en vez de fallar por la razón real.
Reutiliza el 100% de la lógica real de RedisCopyTradeStore; solo se falsea
el transporte.

Cada ruta también trae `Depends(RateLimit(...))` (fastapi_limiter), que
exige `FastAPILimiter.init(redis)` corrido en el startup real — inalcanzable
acá. `_FakeRedis.script_load`/`evalsha` alcanza para satisfacer ese init sin
Redis real (evalsha siempre devuelve 0 → nunca limita).
"""

import time
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi_limiter import FastAPILimiter

from app.main import app
from app.core.deps import get_current_active_user
from app.api.v1.trade_signals import get_store
from app.domains.computer_use.skills.trade_store import RedisCopyTradeStore


class _FakeRedis:
    """In-memory stand-in for redis.asyncio.Redis — implements exactly the
    subset of calls RedisCopyTradeStore issues (strings w/ TTL + hashes)."""

    def __init__(self) -> None:
        self._strings: dict[str, tuple[str, float | None]] = {}  # key -> (value, expires_at)
        self._hashes: dict[str, dict[str, str]] = {}

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self._strings[key] = (value, time.monotonic() + ttl)
        return True

    async def exists(self, key: str) -> int:
        entry = self._strings.get(key)
        if entry is None:
            return 0
        _, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._strings[key]
            return 0
        return 1

    async def hset(self, key: str, field: str, value: str) -> int:
        self._hashes.setdefault(key, {})[field] = value
        return 1

    async def hget(self, key: str, field: str) -> str | None:
        return self._hashes.get(key, {}).get(field)

    async def hgetall(self, key: str) -> dict[str, str]:
        return dict(self._hashes.get(key, {}))

    async def hdel(self, key: str, field: str) -> int:
        return 1 if self._hashes.get(key, {}).pop(field, None) is not None else 0

    async def expire(self, key: str, ttl: int) -> bool:
        return True  # hash TTL is cosmetic here — no expiry semantics needed for these tests

    # ── fastapi_limiter compatibility (RateLimiter._check) ──────────────
    async def script_load(self, script: str) -> str:
        return "fake-sha"

    async def evalsha(self, sha: str, numkeys: int, *args) -> int:
        return 0  # pexpire=0 → never rate-limited


@pytest_asyncio.fixture
async def auth_client():
    fake_user = SimpleNamespace(id=uuid4())
    fake_store = RedisCopyTradeStore(_FakeRedis())
    if FastAPILimiter.redis is None:
        await FastAPILimiter.init(_FakeRedis())
    app.dependency_overrides[get_current_active_user] = lambda: fake_user
    app.dependency_overrides[get_store] = lambda: fake_store
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


def _proposal_body(**kw) -> dict:
    base = {
        "asset": "BTC/USDT",
        "asset_class": "crypto",
        "side": "buy",
        "rationale": "Tendencia alcista + soporte on-chain.",
        "analysis_styles": ["technical", "on_chain"],
        "risk": "high",
        "confidence": 0.7,
        "market": "Binance",
    }
    base.update(kw)
    return base


@pytest.mark.asyncio
async def test_submit_blocked_without_heartbeat(auth_client):
    res = await auth_client.post("/api/v1/computer-use/trade/proposals", json=_proposal_body())
    assert res.status_code == 409
    assert "inactivo" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_heartbeat_then_full_flow_returns_handoff(auth_client):
    hb = await auth_client.post("/api/v1/computer-use/trade/heartbeat")
    assert hb.status_code == 200
    assert hb.json()["active"] is True

    sub = await auth_client.post("/api/v1/computer-use/trade/proposals", json=_proposal_body())
    assert sub.status_code == 200
    assert sub.json()["accepted"] is True
    pid = sub.json()["proposal"]["id"]

    pend = await auth_client.get("/api/v1/computer-use/trade/proposals")
    assert pend.json()["count"] == 1

    appr = await auth_client.post(f"/api/v1/computer-use/trade/proposals/{pid}/approve")
    assert appr.status_code == 200
    body = appr.json()
    assert body["ok"] is True
    assert body["status"] == "approved"
    # Invariante de seguridad: el backend nunca ejecuta.
    assert body["handoff"]["agent_executes"] is False

    pend2 = await auth_client.get("/api/v1/computer-use/trade/proposals")
    assert pend2.json()["count"] == 0


@pytest.mark.asyncio
async def test_reject_flow(auth_client):
    await auth_client.post("/api/v1/computer-use/trade/heartbeat")
    sub = await auth_client.post("/api/v1/computer-use/trade/proposals", json=_proposal_body())
    pid = sub.json()["proposal"]["id"]
    rej = await auth_client.post(f"/api/v1/computer-use/trade/proposals/{pid}/reject")
    assert rej.status_code == 200
    assert rej.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_approve_unknown_proposal_409(auth_client):
    await auth_client.post("/api/v1/computer-use/trade/heartbeat")
    res = await auth_client.post("/api/v1/computer-use/trade/proposals/deadbeef/approve")
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_analysis_styles_introspection(auth_client):
    res = await auth_client.get("/api/v1/computer-use/trade/analysis-styles")
    assert res.status_code == 200
    data = res.json()
    assert "crypto" in data
    assert "technical" in data["crypto"]
