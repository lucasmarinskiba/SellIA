"""Tests para la capa de Skills/Knowledge y la política de autopiloto."""

import pytest

from app.domains.computer_use.skills import (
    SKILL_DOMAINS,
    SALES_TEAM_ROLES,
    detect_skill_domains,
    build_skill_brief,
    list_platform_skills,
    list_sales_team_roles,
    AutopilotMode,
    RiskLevel,
    AutopilotPolicy,
    classify_action_risk,
)


# ── knowledge base ──────────────────────────────────────────────────────
def test_sales_strategy_always_present():
    """Estrategia de ventas se incluye aunque la tarea sea genérica."""
    domains = detect_skill_domains("hacé algo", url=None)
    keys = [d.key for d in domains]
    assert "sales_strategy" in keys
    assert "tool_handling" in keys  # base operativa


def test_detect_by_keyword():
    domains = detect_skill_domains("crear un post con buen copy para Instagram")
    keys = [d.key for d in domains]
    assert "content_creator" in keys
    assert "social_media" in keys


def test_detect_by_url():
    domains = detect_skill_domains("revisar campaña", url="https://ads.google.com/aw/campaigns")
    keys = [d.key for d in domains]
    assert "ads_management" in keys


def test_build_skill_brief_compact():
    brief = build_skill_brief("vender producto y cerrar el deal", url=None)
    assert "Estrategia de Ventas" in brief
    # cap de dominios + principios → no explota el presupuesto de tokens
    assert brief.count("[") <= 4
    assert "BANT" in brief or "AIDA" in brief


def test_build_skill_brief_never_empty_for_real_task():
    assert build_skill_brief("publicar anuncio en Meta Ads") != ""


def test_list_platform_skills():
    mapping = list_platform_skills()
    assert "shopify" in mapping["sales_platforms"]
    assert "google_ads" in mapping["ads_management"]


def test_all_domains_have_principles():
    for d in SKILL_DOMAINS.values():
        assert d.principles, f"{d.key} sin principios"
        assert d.title


# ── full sales-department coverage ──────────────────────────────────────
def test_department_domains_registered():
    """Cubre el equipo de ventas completo, no solo el closer."""
    expected = {
        "prospecting", "outreach", "negotiation", "customer_success",
        "market_intel", "seo_marketing", "analytics", "crm_ops",
    }
    assert expected.issubset(set(SKILL_DOMAINS.keys()))


def test_every_domain_maps_to_a_role():
    for key in SKILL_DOMAINS:
        assert key in SALES_TEAM_ROLES, f"{key} sin rol de equipo"


def test_detect_prospecting_and_negotiation():
    assert "prospecting" in [d.key for d in detect_skill_domains("generar leads en LinkedIn")]
    assert "negotiation" in [d.key for d in detect_skill_domains("negociar descuento y cerrar contrato")]


def test_detect_crm_by_url():
    keys = [d.key for d in detect_skill_domains("actualizar pipeline", url="https://app.hubspot.com/contacts")]
    assert "crm_ops" in keys


def test_list_sales_team_roles_shape():
    roles = list_sales_team_roles()
    assert len(roles) == len(SKILL_DOMAINS)
    sample = roles[0]
    assert {"key", "role", "title", "competencies", "platforms"} <= set(sample.keys())
    assert all(r["competencies"] > 0 for r in roles)


# ── finance / business knowledge ────────────────────────────────────────
def test_finance_domains_registered():
    expected = {
        "crypto", "stock_market", "market_analysis", "financial_markets",
        "real_estate", "trading_platforms", "business_models",
    }
    assert expected.issubset(set(SKILL_DOMAINS.keys()))


def test_detect_crypto_and_real_estate():
    assert "crypto" in [d.key for d in detect_skill_domains("analizar bitcoin y ethereum")]
    assert "real_estate" in [d.key for d in detect_skill_domains("calcular cap rate de un departamento en alquiler")]


def test_trading_platform_by_url_is_read_only():
    domains = detect_skill_domains("ver precio", url="https://www.binance.com/trade")
    tp = next(d for d in domains if d.key == "trading_platforms")
    joined = " ".join(tp.principles).lower()
    assert "solo lectura" in joined or "read-only" in joined
    assert any("nunca" in p.lower() for p in tp.principles)


def test_finance_domains_carry_risk_guardrail():
    for key in ("crypto", "stock_market", "trading_platforms"):
        principles = " ".join(SKILL_DOMAINS[key].principles).lower()
        assert "nunca" in principles  # no ejecuta trades/credenciales
        assert ("riesgo" in principles or "advier" in principles or "read-only" in principles
                or "solo lectura" in principles)


# ── risk classification ─────────────────────────────────────────────────
def test_safe_actions():
    assert classify_action_risk("screenshot", {}) == RiskLevel.SAFE
    assert classify_action_risk("scroll", {"direction": "down"}) == RiskLevel.SAFE
    assert classify_action_risk("navigate", {"url": "https://x.com"}) == RiskLevel.SAFE


def test_medium_actions():
    assert classify_action_risk("click", {"x": 10, "y": 20}) == RiskLevel.MEDIUM
    assert classify_action_risk("type", {"text": "hola mundo"}) == RiskLevel.MEDIUM


def test_high_action_publish_selector():
    r = classify_action_risk("click_selector", {"selector": "button.publish-post"})
    assert r == RiskLevel.HIGH


def test_high_action_send_reason():
    r = classify_action_risk("click", {"x": 1, "y": 2}, reason="Enviar el mensaje al cliente")
    assert r == RiskLevel.HIGH


def test_critical_action_payment():
    r = classify_action_risk("click_text", {"text": "Pagar ahora"})
    assert r == RiskLevel.CRITICAL
    r2 = classify_action_risk("fill", {"selector": "#card", "value": "x"}, reason="ingresar tarjeta")
    assert r2 == RiskLevel.CRITICAL


# ── policy: supervised vs autopilot ─────────────────────────────────────
def test_supervised_blocks_high_for_confirmation():
    pol = AutopilotPolicy(AutopilotMode.SUPERVISED)
    d = pol.evaluate("click_text", {"text": "Publicar"})
    assert d.require_confirmation is True
    assert d.allow is False
    assert d.risk == RiskLevel.HIGH


def test_autopilot_allows_high_audited():
    pol = AutopilotPolicy(AutopilotMode.AUTOPILOT)
    d = pol.evaluate("click_text", {"text": "Publicar"})
    assert d.allow is True
    assert d.require_confirmation is False
    assert d.risk == RiskLevel.HIGH


def test_critical_always_requires_confirmation():
    for mode in (AutopilotMode.SUPERVISED, AutopilotMode.AUTOPILOT):
        pol = AutopilotPolicy(mode)
        d = pol.evaluate("click_text", {"text": "Comprar ahora"})
        assert d.require_confirmation is True
        assert d.allow is False
        assert d.risk == RiskLevel.CRITICAL


def test_medium_runs_in_both_modes():
    for mode in (AutopilotMode.SUPERVISED, AutopilotMode.AUTOPILOT):
        pol = AutopilotPolicy(mode)
        d = pol.evaluate("type", {"text": "consulta normal"})
        assert d.allow is True
        assert d.require_confirmation is False


def test_policy_accepts_string_mode():
    pol = AutopilotPolicy("autopilot")
    assert pol.mode == AutopilotMode.AUTOPILOT
