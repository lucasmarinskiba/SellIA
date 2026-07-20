"""Tests de integración para la API copy-trade supervisado.

Fija el contrato HTTP: presencia (heartbeat) → propuesta → aprobación →
handoff. El backend nunca ejecuta: el handoff siempre trae agent_executes=False.

Self-contained (sin DB/Redis): los endpoints copy-trade mantienen estado en
memoria, así que se usa un AsyncClient ASGI propio y un usuario falso vía
dependency override — no se tocan fixtures de base de datos.
"""

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

from app.main import app
from app.core.deps import get_current_active_user


@pytest_asyncio.fixture
async def auth_client():
    fake_user = SimpleNamespace(id=uuid4())
    app.dependency_overrides[get_current_active_user] = lambda: fake_user
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
