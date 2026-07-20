"""Tests del gate de gobernanza de Computer Use (autopilot_policy).

Verifica que acciones irreversibles (publicar/enviar/comprar/pagar) pidan
confirmación humana en modo supervisado y que las críticas (pago/credenciales)
se bloqueen en ambos modos. No reemplaza al ActionValidator (seguridad dura).
"""

from app.domains.computer_use.skills.autopilot_policy import (
    AutopilotPolicy, AutopilotMode, RiskLevel, classify_action_risk,
)


# ── clasificación de riesgo ──────────────────────────────────────────────
def test_safe_actions():
    for act in ("screenshot", "scroll", "navigate", "wait"):
        assert classify_action_risk(act, {}) == RiskLevel.SAFE


def test_high_risk_publish_send():
    assert classify_action_risk("click_text", {"text": "Publicar"}) == RiskLevel.HIGH
    assert classify_action_risk("click_selector", {"selector": "button.submit"}) == RiskLevel.HIGH
    assert classify_action_risk("type", {"text": "enviar ahora"}) == RiskLevel.HIGH


def test_critical_payment_credentials():
    assert classify_action_risk("click_text", {"text": "Pagar"}) == RiskLevel.CRITICAL
    assert classify_action_risk("fill", {"selector": "#card", "value": "comprar", "text": "checkout"}) == RiskLevel.CRITICAL
    assert classify_action_risk("type", {"text": "mi password es x"}) == RiskLevel.CRITICAL


# ── modo SUPERVISADO: irreversibles piden confirmación ───────────────────
def test_supervised_confirms_irreversible():
    p = AutopilotPolicy(AutopilotMode.SUPERVISED)
    d = p.evaluate("click_text", {"text": "Publicar"})
    assert d.require_confirmation is True
    assert d.allow is False
    assert d.risk == RiskLevel.HIGH


def test_supervised_executes_safe():
    p = AutopilotPolicy(AutopilotMode.SUPERVISED)
    d = p.evaluate("screenshot", {})
    assert d.allow is True and d.require_confirmation is False


# ── modo AUTOPILOT: HIGH auto (auditado), CRITICAL siempre bloquea ───────
def test_autopilot_executes_high_audited():
    p = AutopilotPolicy(AutopilotMode.AUTOPILOT)
    d = p.evaluate("click_text", {"text": "Publicar"})
    assert d.allow is True and d.require_confirmation is False
    assert d.risk == RiskLevel.HIGH


def test_critical_always_requires_confirmation():
    for mode in (AutopilotMode.SUPERVISED, AutopilotMode.AUTOPILOT):
        p = AutopilotPolicy(mode)
        d = p.evaluate("click_text", {"text": "Pagar con tarjeta"})
        assert d.allow is False
        assert d.require_confirmation is True
        assert d.risk == RiskLevel.CRITICAL
