"""Brain Introspection API.

Read-only endpoints exposing the unified capability registry (agents, skills,
automations) plus real activity telemetry. Powers the Enterprise Command
Center frontend at `/sellia-brain`.

No business-scoped data is returned here, so endpoints are unauthenticated and
safe to cache at the edge.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.brain import (
    get_brain_registry, CapabilityKind, get_activity_bus, record_activity, get_cua_store,
)
from app.core.database import get_db

router = APIRouter()


async def _optional_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Best-effort auth for the one mutating endpoint in this otherwise-public,
    unauthenticated router (see module docstring). Returns None on any missing/
    invalid/absent token -- callers must treat that as "anonymous/demo visitor"
    and keep behaving exactly as before, never raise 401 here."""
    try:
        from app.core.deps import get_token_from_request
        from app.core.security import decode_access_token
        from app.domains.users.models import User

        token = await get_token_from_request(request)
        if not token:
            return None
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            return None
        result = await db.execute(select(User).where(User.id == payload["sub"]))
        user = result.scalar_one_or_none()
        return user if (user and user.is_active) else None
    except Exception:
        return None


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
    # Capability ids (e.g. "agent.expert.ad_copywriter", "platform.whatsapp")
    # the caller has toggled OFF via the Brain Interaction Map's ON/OFF
    # buttons. This page is public/unauthenticated (no per-visitor login), so
    # there is no server-side per-user state to persist here -- the toggle
    # lives in the caller's own browser (localStorage) and is sent with every
    # dispatch. Real enforcement: an intent whose agent or ALL of whose
    # platforms are disabled is skipped in favor of the next matching intent,
    # never silently ignored.
    disabled: list[str] = Field(default_factory=list)


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


_FALLBACK_INTENT: dict = {
    "agent": ("acquisition_strategist", "Estratega"), "tools": ["retrieve_knowledge"],
    "platforms": ["web"], "action": "Planificar y ejecutar",
}


@router.post("/brain/cua/dispatch")
async def brain_cua_dispatch(body: CuaDispatch, request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Recibe una indicación del usuario y la convierte en un flujo de Computer Use.

    Construye pasos planificados (trigger → agente → tools → plataformas) según el
    intent de la indicación, los registra como actividad real (observabilidad) y los
    guarda como sesión CU para la vista de flujos. Best-effort.

    Sigue siendo accesible sin login (ver docstring del módulo) -- pero si la
    llamada trae un Bearer token válido de un usuario real, esa acción queda
    además persistida en ai_action_logs (ver app/domains/ai_activity), visible
    después vía GET /api/v1/ai-activity para ese usuario. Un visitante anónimo
    ve exactamente el mismo comportamiento que antes: cero cambios ahí.

    Respeta `body.disabled` (los toggles ON/OFF del Brain Interaction Map): un
    intent cuyo agente está apagado se salta a favor del siguiente intent que
    matchee, y las tools/platforms individuales apagadas se excluyen del plan
    en lugar de romperlo -- nunca se ignora el toggle en silencio.
    """
    text = body.instruction.strip()
    mode = body.mode if body.mode in ("auto", "supervised") else "supervised"
    disabled = set(body.disabled)

    candidates = [cfg for rx, cfg in _CUA_INTENTS if re.search(rx, text, re.I)]
    candidates.append(_FALLBACK_INTENT)

    intent = None
    skipped: list[str] = []
    for cfg in candidates:
        aslug, aname = cfg["agent"]
        if f"agent.expert.{aslug}" in disabled:
            skipped.append(aname)
            continue
        intent = cfg
        break
    if intent is None:
        # Every matching intent's agent (fallback included) was disabled --
        # still respond honestly instead of silently doing nothing.
        return {
            "ok": False, "flow": None, "can_execute": False,
            "skipped_disabled_agents": skipped,
            "hint": "Todos los agentes para esta indicación están desactivados en el mapa. Activá alguno para continuar.",
        }

    active_tools = [t for t in intent["tools"] if f"skill.tool.{t}" not in disabled]
    active_platforms = [p for p in intent["platforms"] if f"platform.{p}" not in disabled]

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
    for tslug in active_tools:
        tid = add(f"skill.tool.{tslug}", tslug.replace("_", " ").title(), "skill", 2)
        edges.append({"source": aid, "target": tid, "rel": "usa"})
        last = tid
    for pslug in active_platforms:
        pid = add(f"platform.{pslug}", pslug.replace("_", " ").title(), "platform", 3)
        edges.append({"source": last, "target": pid, "rel": "ejecuta"})

    # registrar como actividad real (observabilidad en el grafo overview)
    record_activity("computer_use", f"agent.expert.{aslug}",
                    f"Computer Use [{mode}] · {intent['action']}: {text[:80]}")
    for tslug in active_tools:
        record_activity("function", f"skill.tool.{tslug}", f"CU usa {tslug} para: {text[:60]}")

    flow = get_cua_store().add({
        "id": f"cua.{int(datetime.now(timezone.utc).timestamp())}",
        "name": intent["action"], "instruction": text, "mode": mode,
        "kind": "cua", "status": "running", "steps": steps, "edges": edges,
    })

    # Persistencia real per-user (además del ring buffer en memoria de arriba,
    # que es global/proceso y se pierde en cada redeploy -- ver ai_activity/models.py).
    user = await _optional_user(request, db)
    if user is not None:
        from app.domains.businesses.models import Business
        from app.domains.ai_activity.service import log_ai_action
        biz_result = await db.execute(
            select(Business.id).where(Business.user_id == user.id).limit(1)
        )
        business_id = biz_result.scalar_one_or_none()
        await log_ai_action(
            user_id=user.id,
            business_id=business_id,
            actor_type="brain",
            actor_id=f"agent.expert.{aslug}",
            action="brain_plan_dispatched",
            summary=f"{intent['action']}: {text[:120]}",
            payload={"mode": mode, "tools": active_tools, "platforms": active_platforms, "skipped_disabled_agents": skipped},
        )

    # ¿hay credenciales para ejecutar de verdad (sesión Playwright + LLM)?
    from app.core.config import get_settings
    _s = get_settings()
    can_execute = bool(getattr(_s, "ANTHROPIC_API_KEY", None) or getattr(_s, "OPENAI_API_KEY", None))
    return {
        "ok": True, "flow": flow, "can_execute": can_execute,
        "skipped_disabled_agents": skipped,
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


# NOTE: no /brain/kpis here. The real one (total_leads/won_leads/active_leads/
# conversion_rate/pipeline_value, aggregated from the actual leads table) lives
# in app/api/v1/brain_live.py's GET /kpis, mounted at the same /api/v1/brain
# prefix -- EnterpriseCommandCenter.tsx already calls it and already expects
# that exact shape. A second /brain/kpis handler here previously returned
# random.Random()-seeded "ROI/leads/conversion/pipeline" tiles with no real
# backing data and no frontend consumer (this whole router was never even
# wired into main.py) -- removed rather than fixed, since brain_live's
# version already does this correctly and nothing else called this one.


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

# NOTE: no /brain/audit-trace here either. It previously returned a fake
# "agent reasoning" stream picked at random from a fixed line pool -- not
# derived from any real activity, and nothing in the frontend ever called it
# (grepped: zero consumers). The real equivalent for "what is the agent
# actually doing" is /brain/activity (real BrainActivityBus events, idle when
# nothing has happened) and brain_live.py's /audit-log (real computer-use
# audit trail) -- both already wired and already honest.
