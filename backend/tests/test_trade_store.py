"""Tests para RedisCopyTradeStore — copy-trade respaldado en Redis.

Usa un fake async mínimo de Redis (sin servidor) para fijar el contrato:
presencia → propuesta → aprobación → handoff. Invariante: el backend nunca
ejecuta (agent_executes=False). También cubre serialización to_state/from_state.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domains.computer_use.skills import AssetClass, TradeSide, AnalysisStyle, RiskRating
from app.domains.computer_use.skills.trade_signals import TradeProposal, ProposalStatus
from app.domains.computer_use.skills.trade_store import RedisCopyTradeStore


# ── fake async Redis (solo los métodos usados por el store) ───────────────
class FakeAsyncRedis:
    def __init__(self):
        self.kv = {}
        self.hashes = {}

    async def setex(self, key, ttl, val):
        self.kv[key] = val

    async def exists(self, key):
        return 1 if key in self.kv else 0

    async def delete(self, key):
        self.kv.pop(key, None)

    async def hset(self, name, field, val):
        self.hashes.setdefault(name, {})[field] = val

    async def hget(self, name, field):
        return self.hashes.get(name, {}).get(field)

    async def hgetall(self, name):
        return dict(self.hashes.get(name, {}))

    async def hdel(self, name, field):
        self.hashes.get(name, {}).pop(field, None)

    async def expire(self, key, ttl):
        return True


def _t(offset_sec: int = 0) -> datetime:
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_sec)


def _proposal(**kw) -> TradeProposal:
    base = dict(
        asset="BTC/USDT",
        asset_class=AssetClass.CRYPTO,
        side=TradeSide.BUY,
        rationale="Tendencia alcista + soporte on-chain.",
        analysis_styles=[AnalysisStyle.TECHNICAL, AnalysisStyle.ON_CHAIN],
        risk=RiskRating.HIGH,
        confidence=0.7,
        market="Binance",
    )
    base.update(kw)
    return TradeProposal(**base)


UID = "user-123"


# ── serialización ──────────────────────────────────────────────────────────
def test_state_round_trip_preserves_fields():
    p = _proposal(stop_loss="61000", take_profit="72000", suggested_allocation_pct=5.0)
    p.status = ProposalStatus.APPROVED
    p.decided_at = _t(10)
    r = TradeProposal.from_state(p.to_state())
    assert r.id == p.id
    assert r.asset == p.asset
    assert r.asset_class == p.asset_class
    assert r.side == p.side
    assert r.analysis_styles == p.analysis_styles
    assert r.status == ProposalStatus.APPROVED
    assert r.decided_at == _t(10)
    assert r.suggested_allocation_pct == 5.0


# ── flujo del store ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_submit_blocked_without_presence():
    store = RedisCopyTradeStore(FakeAsyncRedis(), window_sec=120)
    res = await store.submit(UID, _proposal())
    assert res["accepted"] is False
    assert "inactivo" in res["reason"].lower()


@pytest.mark.asyncio
async def test_full_flow_approve_returns_handoff():
    store = RedisCopyTradeStore(FakeAsyncRedis(), window_sec=120)
    await store.heartbeat(UID)
    p = _proposal()
    assert (await store.submit(UID, p))["accepted"] is True
    pend = await store.pending(UID, now=_t(1))
    assert len(pend) == 1

    res = await store.approve(UID, p.id, now=_t(2))
    assert res["ok"] is True
    assert res["status"] == ProposalStatus.APPROVED.value
    assert res["handoff"]["agent_executes"] is False
    assert await store.pending(UID, now=_t(3)) == []


@pytest.mark.asyncio
async def test_pending_empty_when_inactive():
    fake = FakeAsyncRedis()
    store = RedisCopyTradeStore(fake, window_sec=120)
    await store.heartbeat(UID)
    await store.submit(UID, _proposal())
    # usuario se va: borramos la clave de presencia
    await fake.delete(f"ct:presence:{UID}")
    assert await store.pending(UID, now=_t(1)) == []


@pytest.mark.asyncio
async def test_approve_unknown_returns_not_found():
    store = RedisCopyTradeStore(FakeAsyncRedis(), window_sec=120)
    await store.heartbeat(UID)
    res = await store.approve(UID, "deadbeef", now=_t(1))
    assert res["ok"] is False


@pytest.mark.asyncio
async def test_approve_expired_blocked():
    store = RedisCopyTradeStore(FakeAsyncRedis(), window_sec=120)
    await store.heartbeat(UID)
    p = _proposal(ttl_sec=300, created_at=_t(1))
    await store.submit(UID, p)
    res = await store.approve(UID, p.id, now=_t(400))
    assert res["ok"] is False
    assert "expir" in res["reason"].lower()


@pytest.mark.asyncio
async def test_pending_purges_expired_from_hash():
    fake = FakeAsyncRedis()
    store = RedisCopyTradeStore(fake, window_sec=10_000)
    await store.heartbeat(UID)
    p = _proposal(ttl_sec=300, created_at=_t(1))
    await store.submit(UID, p)
    # tras la ventana: pending vacío Y la propuesta se borra del hash (anti-fuga)
    assert await store.pending(UID, now=_t(400)) == []
    assert fake.hashes.get(f"ct:proposals:{UID}", {}) == {}


@pytest.mark.asyncio
async def test_reject_flow():
    store = RedisCopyTradeStore(FakeAsyncRedis(), window_sec=120)
    await store.heartbeat(UID)
    p = _proposal()
    await store.submit(UID, p)
    res = await store.reject(UID, p.id, now=_t(2))
    assert res["ok"] is True
    assert res["status"] == ProposalStatus.REJECTED.value
