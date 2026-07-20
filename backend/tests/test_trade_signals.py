"""Tests para la capa de copy-trade supervisado (trade_signals).

Invariante clave de seguridad: el agente NUNCA ejecuta; solo propone y, tras
aprobación de un usuario ACTIVO, entrega instrucciones para que el usuario
ejecute. Estos tests fijan ese contrato.
"""

from datetime import datetime, timedelta, timezone

from app.domains.computer_use.skills import (
    AssetClass,
    TradeSide,
    AnalysisStyle,
    RiskRating,
    ProposalStatus,
    ANALYSIS_BY_ASSET,
    TradeProposal,
    UserPresenceGate,
    CopyTradeReviewQueue,
    SKILL_DOMAINS,
)


def _t(offset_sec: int = 0) -> datetime:
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=offset_sec)


def _proposal(**kw) -> TradeProposal:
    base = dict(
        asset="BTC/USDT",
        asset_class=AssetClass.CRYPTO,
        side=TradeSide.BUY,
        rationale="Tendencia alcista multi-temporal + soporte on-chain.",
        analysis_styles=[AnalysisStyle.TECHNICAL, AnalysisStyle.ON_CHAIN],
        risk=RiskRating.HIGH,
        confidence=0.7,
        market="Binance",
    )
    base.update(kw)
    return TradeProposal(**base)


# ── proposal validation ─────────────────────────────────────────────────
def test_confidence_clamped():
    p = _proposal(confidence=5.0)
    assert p.confidence == 1.0
    p2 = _proposal(confidence=-3)
    assert p2.confidence == 0.0


def test_allocation_clamped():
    p = _proposal(suggested_allocation_pct=250)
    assert p.suggested_allocation_pct == 100.0


def test_analysis_styles_filtered_by_asset_class():
    # FUNDAMENTAL no aplica a CRYPTO en el mapa → se filtra.
    p = _proposal(analysis_styles=[AnalysisStyle.FUNDAMENTAL])
    for s in p.analysis_styles:
        assert s in ANALYSIS_BY_ASSET[AssetClass.CRYPTO]


def test_requires_human_execution_default_true():
    assert _proposal().requires_human_execution is True


def test_execution_handoff_never_executes():
    p = _proposal()
    h = p.execution_handoff()
    assert h["agent_executes"] is False
    assert "NO ejecuta" in h["instruction"]


# ── presence gate ───────────────────────────────────────────────────────
def test_presence_inactive_by_default():
    gate = UserPresenceGate(window_sec=120)
    assert gate.is_active(_t(0)) is False


def test_presence_active_within_window():
    gate = UserPresenceGate(window_sec=120)
    gate.heartbeat(_t(0))
    assert gate.is_active(_t(60)) is True
    assert gate.is_active(_t(200)) is False  # fuera de ventana


# ── review queue ────────────────────────────────────────────────────────
def test_submit_blocked_without_presence():
    q = CopyTradeReviewQueue(UserPresenceGate(120))
    res = q.submit(_proposal(), now=_t(0))
    assert res["accepted"] is False
    assert "inactivo" in res["reason"].lower()


def test_full_flow_approve_returns_handoff():
    gate = UserPresenceGate(120)
    q = CopyTradeReviewQueue(gate)
    gate.heartbeat(_t(0))
    p = _proposal()
    assert q.submit(p, now=_t(1))["accepted"] is True
    assert len(q.pending(_t(2))) == 1

    gate.heartbeat(_t(3))  # sigue activo
    res = q.approve(p.id, now=_t(4))
    assert res["ok"] is True
    assert res["status"] == ProposalStatus.APPROVED.value
    assert res["handoff"]["agent_executes"] is False
    # ya no está pendiente
    assert q.pending(_t(5)) == []


def test_approve_blocked_when_user_goes_inactive():
    gate = UserPresenceGate(120)
    q = CopyTradeReviewQueue(gate)
    gate.heartbeat(_t(0))
    p = _proposal()
    q.submit(p, now=_t(1))
    # usuario inactivo al momento de aprobar (pasó la ventana)
    res = q.approve(p.id, now=_t(500))
    assert res["ok"] is False


def test_proposal_expires_by_ttl():
    gate = UserPresenceGate(window_sec=10_000)
    q = CopyTradeReviewQueue(gate)
    gate.heartbeat(_t(0))
    p = _proposal(ttl_sec=300, created_at=_t(1))
    q.submit(p, now=_t(1))
    gate.heartbeat(_t(400))
    res = q.approve(p.id, now=_t(400))
    assert res["ok"] is False
    assert "expir" in res["reason"].lower()


def test_reject_flow():
    gate = UserPresenceGate(120)
    q = CopyTradeReviewQueue(gate)
    gate.heartbeat(_t(0))
    p = _proposal()
    q.submit(p, now=_t(1))
    res = q.reject(p.id, now=_t(2))
    assert res["ok"] is True
    assert res["status"] == ProposalStatus.REJECTED.value


# ── knowledge coverage ──────────────────────────────────────────────────
def test_risk_management_domain_registered():
    assert "risk_management" in SKILL_DOMAINS
    principles = " ".join(SKILL_DOMAINS["risk_management"].principles).lower()
    assert "stop" in principles


def test_every_asset_class_has_analysis_styles():
    for ac in AssetClass:
        assert ANALYSIS_BY_ASSET.get(ac), f"{ac} sin estilos de análisis"
