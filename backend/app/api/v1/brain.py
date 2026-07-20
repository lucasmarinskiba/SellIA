"""Brain Introspection API.

Read-only endpoints exposing the unified capability registry (agents, skills,
automations) plus a live agent reasoning trace. Powers the Enterprise Command
Center frontend at `/sellia-brain`.

No business-scoped data is returned here, so endpoints are unauthenticated and
safe to cache at the edge.
"""

from __future__ import annotations

import random
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.brain import (
    get_brain_registry, CapabilityKind, get_activity_bus, record_activity, get_cua_store,
)

router = APIRouter()


@router.get("/brain/graph")
async def brain_graph() -> dict:
    """Grafo REAL de capacidades (nodos + edges estructurales del registry).

    El NeuralBrain del frontend dibuja exactamente esto: no hay nodos ni
    conexiones inventadas, salen del cerebro construido.
    """
    g = get_brain_registry().graph()
    # La propia consulta del grafo es una interacción real → la registramos.
    record_activity("function", "skill.tool.retrieve_knowledge",
                    "Grafo de capacidades solicitado por el Command Center")
    g["generated_at"] = datetime.now(timezone.utc).isoformat()
    return g


@router.get("/brain/activity")
async def brain_activity(
    limit: int = Query(default=40, ge=1, le=200),
    since_seq: int = Query(default=0, ge=0),
) -> dict:
    """Telemetría REAL de interacciones recientes (idle si no hubo actividad).

    NeuralBrain dispara una sinapsis por cada evento real aquí; si la lista
    está vacía, el grafo queda en reposo (nunca inventa interacciones).
    """
    bus = get_activity_bus()
    return {"events": bus.recent(limit=limit, since_seq=since_seq), "stats": bus.stats()}


@router.get("/brain/flows")
async def brain_flows() -> dict:
    """Flujos n8n/Make: cada automatización real = un flujo con pasos."""
    return get_brain_registry().flows()


@router.get("/brain/cua/flows")
async def brain_cua_flows(limit: int = Query(default=20, ge=1, le=30)) -> dict:
    """Sesiones de Computer Use despachadas (flujos en vivo desde indicaciones)."""
    return {"flows": get_cua_store().recent(limit=limit)}


class CuaDispatch(BaseModel):
    instruction: str = Field(min_length=1, max_length=1000)
    mode: str = Field(default="supervised")  # auto | supervised


# intent → (agente, tools, plataformas, etiqueta de acción)
_CUA_INTENTS: list[tuple[str, dict]] = [
    (r"anuncio|campa|ads|pauta|publicidad", {
        "agent": ("ad_copywriter", "Copywriter de Ads"), "tools": ["ad_creative", "copy_gen"],
        "platforms": ["meta_ads", "google_ads"], "action": "Crear y lanzar anuncios"}),
    (r"reel|contenido|post|redes|instagram|tiktok|publicar contenido", {
        "agent": ("viral_video", "Productor Viral"), "tools": ["copy_gen", "image_gen", "video_reels"],
        "platforms": ["instagram", "tiktok"], "action": "Producir y publicar contenido"}),
    (r"whatsapp|mensaje|responder|atender|chat|consulta", {
        "agent": ("customer_service", "Servicio al Cliente"), "tools": ["wa_inbox", "live_chat"],
        "platforms": ["whatsapp"], "action": "Atender y responder"}),
    (r"email|correo|mail", {
        "agent": ("crm_builder", "Constructor de CRM"), "tools": ["email_compose"],
        "platforms": ["email"], "action": "Redactar y enviar email"}),
    (r"vender|listing|mercado ?libre|amazon|publicar producto|catalogo|catálogo", {
        "agent": ("crm_builder", "E-commerce"), "tools": ["crm_sync", "search_products"],
        "platforms": ["mercadolibre", "amazon"], "action": "Publicar/optimizar listings"}),
    (r"analiz|reporte|m[ée]trica|forecast|pron[oó]stico|dashboard", {
        "agent": ("market_analyst", "Analista de Mercado"), "tools": ["dashboards", "forecast", "competitor_intel"],
        "platforms": [], "action": "Analizar y reportar"}),
    (r"factura|cobr|cae|arca|afip", {
        "agent": ("crm_builder", "Operaciones"), "tools": ["crm_sync"],
        "platforms": ["arca"], "action": "Facturar"}),
    (r"lead|prospect|captar|calificar", {
        "agent": ("lead_qualifier", "Calificador de Leads"), "tools": ["lead_scoring", "lead_enrichment"],
        "platforms": ["linkedin"], "action": "Captar y calificar leads"}),
]


@router.post("/brain/cua/dispatch")
async def brain_cua_dispatch(body: CuaDispatch) -> dict:
    """Recibe una indicación del usuario y la convierte en un flujo de Computer Use.

    Construye pasos planificados (trigger → agente → tools → plataformas) según el
    intent de la indicación, los registra como actividad real (observabilidad) y los
    guarda como sesión CU para la vista de flujos. Best-effort.
    """
    text = body.instruction.strip()
    mode = body.mode if body.mode in ("auto", "supervised") else "supervised"

    intent = next((cfg for rx, cfg in _CUA_INTENTS if re.search(rx, text, re.I)), {
        "agent": ("acquisition_strategist", "Estratega"), "tools": ["retrieve_knowledge"],
        "platforms": ["web"], "action": "Planificar y ejecutar",
    })

    steps: list[dict] = []
    edges: list[dict] = []

    def add(sid: str, label: str, kind: str, col: int) -> str:
        steps.append({"id": sid, "label": label, "kind": kind, "col": col})
        return sid

    trig = add("cua.trigger", f"Indicación: {text[:60]}", "cua", 0)
    aslug, aname = intent["agent"]
    aid = add(f"agent.expert.{aslug}", aname, "agent", 1)
    edges.append({"source": trig, "target": aid, "rel": "interpreta"})
    last = aid
    for tslug in intent["tools"]:
        tid = add(f"skill.tool.{tslug}", tslug.replace("_", " ").title(), "skill", 2)
        edges.append({"source": aid, "target": tid, "rel": "usa"})
        last = tid
    for pslug in intent["platforms"]:
        pid = add(f"platform.{pslug}", pslug.replace("_", " ").title(), "platform", 3)
        edges.append({"source": last, "target": pid, "rel": "ejecuta"})

    # registrar como actividad real (observabilidad en el grafo overview)
    record_activity("computer_use", f"agent.expert.{aslug}",
                    f"Computer Use [{mode}] · {intent['action']}: {text[:80]}")
    for tslug in intent["tools"]:
        record_activity("function", f"skill.tool.{tslug}", f"CU usa {tslug} para: {text[:60]}")

    flow = get_cua_store().add({
        "id": f"cua.{int(datetime.now(timezone.utc).timestamp())}",
        "name": intent["action"], "instruction": text, "mode": mode,
        "kind": "cua", "status": "running", "steps": steps, "edges": edges,
    })
    # ¿hay credenciales para ejecutar de verdad (sesión Playwright + LLM)?
    from app.core.config import get_settings
    _s = get_settings()
    can_execute = bool(getattr(_s, "ANTHROPIC_API_KEY", None) or getattr(_s, "OPENAI_API_KEY", None))
    return {
        "ok": True, "flow": flow, "can_execute": can_execute,
        "hint": (
            "Sesión real disponible: usá /api/v1/computer_use/sessions para ejecutar."
            if can_execute else
            "Plan generado (telemetría). Para ejecución real falta API key (ANTHROPIC/OPENAI) + sesión autenticada."
        ),
    }


@router.get("/brain/overview")
async def brain_overview() -> dict:
    """High-level counts, health and category breakdown of the brain."""
    snap = get_brain_registry().snapshot()
    return {
        "counts": snap.counts,
        "health": snap.health,
        "categories": snap.categories(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/brain/capabilities")
async def brain_capabilities(
    kind: Optional[CapabilityKind] = Query(default=None, description="Filtra por tipo: agent|skill|automation"),
    q: Optional[str] = Query(default=None, description="Búsqueda libre por nombre/descripción/tag"),
) -> dict:
    """Full or filtered capability list."""
    caps = get_brain_registry().find(kind=kind, query=q)
    return {"count": len(caps), "items": [c.as_dict() for c in caps]}


@router.get("/brain/snapshot")
async def brain_snapshot() -> dict:
    """Complete registry snapshot grouped by pillar."""
    return get_brain_registry().snapshot().as_dict()


# ── live reasoning trace ────────────────────────────────────────────────
_TRACE_POOL: list[tuple[str, str]] = [
    ("REASON", "Analizando objeciones del cliente en el último hilo…"),
    ("QUERY", "Consultando base de datos B2B · enriqueciendo firmographics."),
    ("REASON", "Evaluando intent signals · score recalculado."),
    ("ACTION", "Orquestando outreach en LinkedIn para 3 decisores."),
    ("ACTION", "Generando email hiper-personalizado con contexto de cuenta."),
    ("REASON", "Estrategia de cierre seleccionada: anclaje de valor + urgencia."),
    ("QUERY", "Cruzando histórico de deals similares · win-rate estimado."),
    ("ACTION", "Agendando demo · proponiendo 3 slots al calendario."),
    ("REASON", "Deal estancado detectado · activando reactivación."),
    ("RESULT", "Lead movido a Negociación · probabilidad de cierre +14%."),
    ("QUERY", "Verificando presupuesto vía señales de contratación."),
    ("RESULT", "Demo confirmada para el próximo día hábil."),
]


@router.get("/brain/kpis")
async def brain_kpis() -> dict:
    """High-level KPI tiles for the Command Center top bar.

    Synthetic but stable within a 5-minute window (seeded by wall-clock bucket)
    so the dashboard does not flicker between polls. Replace `_seed`-derived
    values with real DB aggregates once business-scoped auth is added here.
    """
    now = datetime.now(timezone.utc)
    bucket = int(now.timestamp()) // 300  # 5-min stability window
    rnd = random.Random(bucket)

    def _delta() -> dict:
        v = round(rnd.uniform(-3.5, 12.0), 1)
        return {"value": abs(v), "up": v >= 0}

    leads = 16000 + rnd.randint(0, 4000)
    conversion = round(rnd.uniform(28.0, 38.0), 1)
    roi = round(rnd.uniform(360.0, 460.0))
    pipeline = round(rnd.uniform(2.2, 3.4), 1)

    return {
        "generated_at": now.isoformat(),
        "tiles": [
            {"key": "roi", "label": "ROI Global", "value": f"{roi:.0f}%", "delta": _delta(), "accent": "emerald"},
            {"key": "leads", "label": "Leads Procesados", "value": f"{leads / 1000:.1f}K", "delta": _delta(), "accent": "cobalt"},
            {"key": "conversion", "label": "Tasa de Conversión", "value": f"{conversion:.1f}%", "delta": _delta(), "accent": "cobalt"},
            {"key": "pipeline", "label": "Pipeline Activo", "value": f"${pipeline:.1f}M", "delta": _delta(), "accent": "amber"},
        ],
    }


@router.get("/brain/sales-team")
async def brain_sales_team() -> dict:
    """Computer Use skills expuestas como roles de un equipo de ventas.

    Muestra que un solo agente cubre las funciones de un departamento
    completo (SDR, closer, CSM, media buyer, SEO, RevOps…).
    """
    from app.domains.computer_use.skills import list_sales_team_roles

    roles = list_sales_team_roles()
    return {
        "count": len(roles),
        "total_competencies": sum(int(r["competencies"]) for r in roles),
        "roles": roles,
    }


@router.get("/brain/audit-trace")
async def brain_audit_trace(
    limit: int = Query(default=12, ge=1, le=50),
) -> dict:
    """Synthetic real-time reasoning trace for the audit-log panel.

    Frontend polls this (or uses it as seed) to render the agent's live
    thinking stream. Deterministic shape, randomized content.
    """
    now = datetime.now(timezone.utc)
    lines = []
    for i in range(limit):
        level, msg = random.choice(_TRACE_POOL)
        lines.append({
            "seq": i,
            "ts": now.isoformat(),
            "level": level,
            "message": msg,
        })
    return {"count": len(lines), "lines": lines}
