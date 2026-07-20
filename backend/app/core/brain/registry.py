"""Brain Capability Registry.

Single source of truth describing what the SellIA brain can do. It unifies:

  * AGENTS       — specialized AI agents (pipeline stages + expert roles + legends).
  * SKILLS       — internal know-how: knowledge library (loaded dynamically from
                   ``core/knowledge/library/*.json``) + ReAct tools.
  * AUTOMATIONS  — autonomous workflows orchestrating agents and skills.

The registry is read-only and cheap to build; it powers the Enterprise Command
Center frontend (`/sellia-brain`) and any orchestration layer that needs to
introspect available capabilities before planning.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge" / "library"


class CapabilityKind(str, Enum):
    AGENT = "agent"
    SKILL = "skill"
    AUTOMATION = "automation"
    PLATFORM = "platform"


@dataclass(frozen=True)
class Capability:
    """One brain capability — an agent, a skill or an automation."""

    id: str
    kind: CapabilityKind
    name: str
    category: str
    description: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    # 0.0–1.0 readiness / maturity signal surfaced in the command center.
    health: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["tags"] = list(self.tags)
        return d


# ─────────────────────────────────────────────────────────────────────────
# STATIC AGENT CATALOG
#   Pipeline-stage agents + expert role agents + world-class legend personas.
#   Kept declarative (no heavy imports) so the registry stays import-safe.
# ─────────────────────────────────────────────────────────────────────────
_PIPELINE_AGENTS: list[tuple[str, str, str]] = [
    ("captador", "Captador", "Prospección y captura multicanal de leads."),
    ("calificador", "Calificador", "Scoring y filtrado de prospectos (BANT/SPICED)."),
    ("nutridor", "Nutridor", "Warming y educación del lead hasta sales-ready."),
    ("diagnostico", "Diagnóstico", "Descubrimiento de necesidades con SPIN."),
    ("propuesta", "Propuesta", "Construcción y presentación de oferta de valor."),
    ("objeciones", "Gestor de Objeciones", "Manejo y conversión de objeciones."),
    ("cerrador", "Cerrador", "Cierre, confirmación y firma."),
    ("onboarding", "Onboarding", "Bienvenida y entrega del valor prometido."),
    ("retentor", "Retentor", "LTV, recompra y upsell."),
]

_EXPERT_AGENTS: list[tuple[str, str, str]] = [
    ("acquisition_strategist", "Estratega de Adquisición", "Diseña funnels y canales de captación rentables."),
    ("market_analyst", "Analista de Mercado", "Estudio de mercado, TAM/SAM/SOM y tendencias."),
    ("financial_planner", "Planificador Financiero", "Proyecciones, unit economics y cashflow."),
    ("kpi_architect", "Arquitecto de KPIs", "Define métricas norte y tableros de control."),
    ("ad_copywriter", "Copywriter de Ads", "Creatividades de alto CTR para paid media."),
    ("brand_visual", "Director de Marca", "Identidad visual y consistencia de marca."),
    ("crm_builder", "Constructor de CRM", "Modela pipelines y automatiza el CRM."),
    ("landing_builder", "Constructor de Landings", "Genera landings optimizadas a conversión."),
    ("app_builder", "Constructor de Apps", "Ensambla micro-apps internas para ventas."),
    ("investor_pitch", "Pitch a Inversores", "Narrativa y deck para fundraising."),
    ("viral_video", "Productor Viral", "Guiones y reels para crecimiento orgánico."),
    ("music_agent", "Agente de Audio", "Voz humana y jingles para campañas."),
    ("customer_service", "Servicio al Cliente", "Soporte empático y resolución 24/7."),
    ("lead_qualifier", "Calificador de Leads", "Califica en tiempo real con señales de intención."),
    # ── Finanzas / estructura / producto ──
    ("product_scout", "Buscador de Productos Ganadores", "Detecta productos con demanda, margen y baja competencia."),
    ("budget_analyst", "Analista de Costos/Presupuesto", "Estructura costos, márgenes, breakeven y presupuesto."),
    ("wealth_strategist", "Estratega Patrimonial", "Activos vs pasivos, flujo de caja e inversión a largo plazo."),
    ("blockchain_analyst", "Analista Cripto/Blockchain", "Mercado on-chain y tecnología (educativo, sin ejecutar trades)."),
    ("realestate_analyst", "Analista Inmobiliario", "Valuación, cap rate y oportunidades (educativo)."),
    ("startup_architect", "Arquitecto de Emprendimientos", "Modelo de negocio, estructura legal/fiscal y go-to-market."),
    ("portfolio_strategist", "Gestor de Cartera (señales)", "Estrategias DCA/grid/swing; PROPONE señales, NUNCA ejecuta operaciones."),
    ("design_studio", "Estudio de Diseño (Canva)", "Crea piezas de marca en Canva con tu identidad."),
    # ── Lead intelligence + marketing + branding ──
    ("lead_filter", "Filtro de Leads (ManyChat)", "Califica y descarta leads que nunca van a comprar; deja pasar solo los calientes."),
    ("campaign_architect", "Arquitecto de Campañas", "Convierte un brief en una campaña 360° (estrategia + copys + creativos + medición)."),
    ("brand_designer", "Diseñador de Identidad de Marca", "Genera identidad de marca completa (propósito, tono, naming, paleta, logo)."),
    ("impossible_seller", "Vendedor de lo Invendible", "Genera reframes, ángulos creativos y pitch para vender productos donde parecen innecesarios (arena al Sahara, hielo a esquimales)."),
    ("sales_architect", "Arquitecto de Sistemas de Venta", "Diseña la venta óptima por escenario (transaccional vs consultativa, ticket, ciclo, decisores)."),
    ("master_seller", "Vendedor Maestro", "Agente síntesis que integra Belfort+SPIN+Hermozi+Vaynerchuk+Cialdini. Responde como mejor vendedor del mundo."),
    # ── Lifecycle management ──
    ("lifecycle_manager", "Gestor de Ciclo de Vida", "Orquesta estrategias por etapa: onboarding → engagement → upsell → retention → churn prevention."),
    ("onboarding_specialist", "Especialista en Onboarding", "Logra 'aha moment' en 48h. Primer resultado que enganche al cliente."),
    ("retention_specialist", "Especialista en Retención", "Mantiene clientes activos + happy. Success manager, QBR trimestral, advocacy."),
    ("churn_preventer", "Prevensor de Churn", "Detecta señales de riesgo. Intervención 48h. Win-back o salida ordenada."),
]

_LEGEND_AGENTS: list[tuple[str, str, str]] = [
    ("buffett", "Warren Buffett", "Inversión en valor y pensamiento a largo plazo."),
    ("hormozi", "Alex Hormozi", "Ofertas irresistibles y economía de la oferta."),
    ("cardone", "Grant Cardone", "Mentalidad 10X y follow-up implacable."),
    ("godin", "Seth Godin", "Marketing de permiso y tribus."),
    ("belfort", "Jordan Belfort", "Straight-line selling y tonalidad."),
    ("vaynerchuk", "Gary Vaynerchuk", "Atención, contenido y social-first."),
    ("hopkins", "Tom Hopkins", "Maestro de cierre: 101 técnicas, assumptive close, objeciones como señal."),
    ("woolworth", "Frank Woolworth", "Padre de ventas modernas: precio fijo, volumen, experiencia de tienda."),
    ("ross", "Aaron Ross", "Rey del Outbound: Predictable Revenue, ICP, lead scoring, personalización sin spam."),
]


def _agent_caps() -> list[Capability]:
    out: list[Capability] = []
    for slug, name, desc in _PIPELINE_AGENTS:
        out.append(Capability(
            id=f"agent.pipeline.{slug}", kind=CapabilityKind.AGENT, name=name,
            category="Pipeline", description=desc, tags=("pipeline", "ventas"),
            health=1.0, metadata={"tier": "core"},
        ))
    for slug, name, desc in _EXPERT_AGENTS:
        out.append(Capability(
            id=f"agent.expert.{slug}", kind=CapabilityKind.AGENT, name=name,
            category="Experto", description=desc, tags=("experto",),
            health=0.95, metadata={"tier": "expert"},
        ))
    for slug, name, desc in _LEGEND_AGENTS:
        out.append(Capability(
            id=f"agent.legend.{slug}", kind=CapabilityKind.AGENT, name=name,
            category="Leyenda", description=desc, tags=("leyenda", "mentor"),
            health=0.9, metadata={"tier": "persona"},
        ))
    return out


# ─────────────────────────────────────────────────────────────────────────
# SKILLS — dynamic knowledge library + static tool surface
# ─────────────────────────────────────────────────────────────────────────
def _knowledge_caps() -> list[Capability]:
    out: list[Capability] = []
    if not _KNOWLEDGE_DIR.exists():
        logger.warning("Knowledge library dir missing: %s", _KNOWLEDGE_DIR)
        return out
    for jf in sorted(_KNOWLEDGE_DIR.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skip knowledge file %s: %s", jf.name, exc)
            continue
        category = str(data.get("category", jf.stem))
        items = data.get("items", []) or []
        out.append(Capability(
            id=f"skill.knowledge.{category}",
            kind=CapabilityKind.SKILL,
            name=category.replace("_", " ").title(),
            category="Conocimiento",
            description=str(data.get("description", f"Base de conocimiento: {category}")),
            tags=("conocimiento", category),
            health=min(1.0, 0.6 + len(items) / 50),
            metadata={"items": len(items), "source": jf.name},
        ))
    return out


# (slug, name, desc, group, health). group ∈ {datos, conocimiento, analisis, creatividad, chat, seo}
# health < 1.0 = capacidad en roadmap / parcial.
_TOOL_SKILLS: list[tuple[str, str, str, str, float]] = [
    # datos / CRM
    ("search_products", "Búsqueda de Catálogo", "Encuentra productos por query, categoría y precio.", "datos", 1.0),
    ("customer_history", "Historial de Cliente", "Recupera interacciones y compras previas.", "datos", 1.0),
    ("check_inventory", "Chequeo de Inventario", "Stock en tiempo real por canal.", "datos", 1.0),
    ("search_memory", "Memoria de Largo Plazo", "Busca en la memoria del cliente/conversación.", "datos", 1.0),
    ("crm_sync", "Sincronía CRM", "Crea/actualiza contactos, deals y etapas en el CRM.", "datos", 0.9),
    ("lead_enrichment", "Enriquecimiento de Leads", "Completa firmographics y datos de contacto.", "datos", 0.85),
    # conocimiento (RAG)
    ("retrieve_knowledge", "Recuperar Conocimiento", "RAG sobre la biblioteca interna.", "conocimiento", 1.0),
    ("retrieve_documents", "Recuperar Documentos", "RAG sobre documentos del negocio.", "conocimiento", 1.0),
    # análisis
    ("deal_scoring", "Scoring de Deals", "Probabilidad de cierre por modelo ML.", "analisis", 1.0),
    ("lead_scoring", "Lead Scoring", "Score 0–100 de intención de compra.", "analisis", 1.0),
    ("dashboards", "Dashboards", "Tableros de KPIs en tiempo real.", "analisis", 0.9),
    ("forecast", "Pronóstico de Ventas", "Proyección de pipeline e ingresos.", "analisis", 0.8),
    ("cohort_analysis", "Análisis de Cohortes", "Retención e ingreso por cohorte de alta.", "analisis", 0.8),
    ("ab_testing", "A/B Testing", "Experimentos y significancia estadística.", "analisis", 0.75),
    ("competitor_intel", "Inteligencia Competitiva", "Monitoreo de competidores y mercado.", "analisis", 0.8),
    # creatividad
    ("image_gen", "Generación de Imágenes", "Imágenes y mockups con IA (Flux/SD).", "creatividad", 0.8),
    ("copy_gen", "Generación de Copy", "Copys de venta y anuncios (AIDA).", "creatividad", 0.9),
    ("video_reels", "Generación de Reels", "Guion + video corto para redes.", "creatividad", 0.7),
    ("ad_creative", "Creativos de Ads", "Variantes de anuncio para paid media.", "creatividad", 0.8),
    ("brand_design", "Diseño de Marca", "Identidad visual y consistencia.", "creatividad", 0.7),
    # chat / conversacional
    ("wa_inbox", "Inbox WhatsApp", "Lee y responde conversaciones de WhatsApp.", "chat", 0.95),
    ("ig_dm", "DMs Instagram", "Gestiona mensajes directos de Instagram.", "chat", 0.85),
    ("email_compose", "Redacción de Email", "Compone y envía emails personalizados.", "chat", 0.9),
    ("live_chat", "Chat en Vivo", "Atención en chat web del sitio.", "chat", 0.8),
    ("voice_session", "Sesión de Voz", "Conversación por voz (manos libres).", "chat", 0.8),
    # seo
    ("seo_audit", "Auditoría SEO", "On-page, técnico y oportunidades de ranking.", "seo", 0.75),
    ("keyword_research", "Keyword Research", "Volumen, dificultad y oportunidades de keywords.", "seo", 0.75),
    ("content_brief", "Brief de Contenido", "Estructura y SERP-intent para artículos.", "seo", 0.7),
    ("schema_markup", "Schema/SEO técnico", "Datos estructurados y rich results.", "seo", 0.7),
    # creatividad (ampliado)
    ("carousel_gen", "Generador de Carruseles", "Carruseles para IG/LinkedIn.", "creatividad", 0.75),
    ("thumbnail_gen", "Thumbnails", "Miniaturas de alto CTR para video.", "creatividad", 0.7),
    ("logo_gen", "Generador de Logos", "Identidad y variaciones de logo.", "creatividad", 0.65),
    ("voiceover", "Voz IA", "Locución/voiceover para video y anuncios.", "creatividad", 0.7),
    ("ugc_script", "Guiones UGC", "Scripts estilo creador para ads.", "creatividad", 0.7),
    ("landing_gen", "Generador de Landings", "Páginas de conversión a partir de un brief.", "creatividad", 0.8),
    # análisis (ampliado)
    ("roas_tracker", "Tracker de ROAS", "Retorno de inversión publicitaria por campaña.", "analisis", 0.85),
    ("attribution", "Atribución", "Modelo de atribución multi-touch.", "analisis", 0.75),
    ("churn_predict", "Predicción de Churn", "Riesgo de cancelación por cuenta.", "analisis", 0.75),
    ("sentiment", "Análisis de Sentimiento", "Tono de reseñas y conversaciones.", "analisis", 0.8),
    ("price_optimizer", "Optimizador de Precios", "Pricing dinámico y elasticidad.", "analisis", 0.7),
    ("funnel_analytics", "Analítica de Embudo", "Conversión por etapa y cuellos de botella.", "analisis", 0.8),
    # chat / conversacional (ampliado)
    ("messenger_inbox", "Inbox Messenger", "Conversaciones de Facebook Messenger.", "chat", 0.8),
    ("sms_send", "Envío de SMS", "Campañas y recordatorios por SMS.", "chat", 0.8),
    ("comment_responder", "Respuesta a Comentarios", "Responde comentarios en redes.", "chat", 0.75),
    ("dm_outreach", "Outreach por DM", "Mensajería en frío en IG/LinkedIn.", "chat", 0.75),
    ("faq_bot", "Bot de FAQ", "Responde preguntas frecuentes 24/7.", "chat", 0.85),
    ("appointment_booker", "Agendador", "Reserva y confirma turnos/demos.", "chat", 0.85),
    # datos / CRM (ampliado)
    # finanzas / producto / inversión
    ("winning_product_finder", "Buscador de Producto Ganador", "Tendencias, demanda y margen por nicho.", "analisis", 0.75),
    ("cost_estimator", "Estimador de Costos", "Costos unitarios, fijos/variables y margen.", "analisis", 0.85),
    ("cashflow_planner", "Planificador de Caja", "Proyección de flujo de caja y runway.", "analisis", 0.8),
    ("asset_liability_tracker", "Activos vs Pasivos", "Balance patrimonial y salud financiera.", "analisis", 0.8),
    ("breakeven_calc", "Cálculo de Breakeven", "Punto de equilibrio y sensibilidad.", "analisis", 0.85),
    ("budget_forecaster", "Pronóstico Presupuestario", "Estimación y análisis de presupuesto.", "analisis", 0.8),
    ("crypto_screener", "Screener Cripto", "Métricas on-chain y de mercado (educativo).", "analisis", 0.7),
    ("property_valuator", "Valuador Inmobiliario", "Cap rate, comparables y plusvalía.", "analisis", 0.7),
    ("trading_signals", "Señales de Trading", "DCA/grid/swing → propone señales (NO ejecuta).", "analisis", 0.7),
    ("crypto_dca", "Bot DCA Cripto", "Compra periódica para promediar costo (sólo señal).", "analisis", 0.7),
    ("risk_sizing", "Gestión de Riesgo", "Stop-loss y tamaño de posición sugeridos.", "analisis", 0.8),
    ("design_canva", "Diseño en Canva", "Genera piezas de marca para publicar.", "creatividad", 0.8),
    ("crm_dedupe", "Deduplicación CRM", "Limpia y unifica contactos duplicados.", "datos", 0.8),
    ("segment_builder", "Segmentador", "Crea segmentos y audiencias.", "datos", 0.8),
    ("sheet_sync", "Sync Planillas", "Lee/escribe Google Sheets.", "datos", 0.85),
    ("calendar_sync", "Sync Calendario", "Gestiona Google Calendar.", "datos", 0.85),
    ("data_export", "Exportar Datos", "Exporta a CSV/BI.", "datos", 0.85),
    ("contract_gen", "Generador de Contratos", "Contratos y propuestas con firma.", "datos", 0.7),
    ("invoice_gen", "Generador de Facturas", "Emite facturas electrónicas.", "datos", 0.85),
    ("payment_link", "Link de Pago", "Genera y envía links de cobro.", "datos", 0.85),
    # ── Lead intelligence + marketing + branding ──
    ("manychat_flow", "Flujo ManyChat", "Construye y opera flujos de calificación/descarte en ManyChat.", "chat", 0.85),
    ("lead_disqualify", "Descalificación de Leads", "Filtra y descarta leads sin intención real (con trazabilidad).", "analisis", 0.9),
    ("brief_intake", "Toma de Brief", "Estructura un brief de marketing en inputs accionables.", "datos", 0.9),
    ("campaign_planner", "Planificador de Campañas", "Plan 360°: objetivo, audiencias, canales, presupuesto, KPI.", "analisis", 0.85),
    ("brand_naming", "Naming de Marca", "Genera nombres y eslóganes para una propuesta de valor.", "creatividad", 0.8),
    ("brand_palette", "Paleta de Marca", "Define color, tipografía y estilo visual.", "creatividad", 0.85),
    ("brand_voice", "Tono de Voz", "Define do's y dont's de voz de marca.", "creatividad", 0.85),
    ("brand_kit_export", "Exportador de Brand Kit", "Empaqueta la identidad para Canva/Figma.", "creatividad", 0.8),
    # ── Vender lo invendible ──
    ("reframe_engine", "Motor de Reframe de Valor", "Reescribe el significado del producto: ritual, estatus, recuerdo, arte, identidad.", "creatividad", 0.85),
    ("pivot_matrix", "Matriz de Pivote", "Cambia audiencia / categoría / propósito / tiempo / packaging para abrir mercado.", "analisis", 0.85),
    ("objection_reframe", "Reframe de Objeciones", "Disuelve 'no lo necesito' con cambio de propósito + prueba social.", "chat", 0.85),
    ("irresistible_offer", "Constructor de Oferta Irresistible", "Aplica fórmula Hormozi (sueño/prueba/tiempo/esfuerzo + bonos + garantía).", "creatividad", 0.85),
    ("origin_storyteller", "Narrador de Origen", "Construye historia 5-actos del producto: origen/héroe/conflicto/revelación/prueba.", "creatividad", 0.85),
    # ── Sistemas avanzados de venta ──
    ("method_selector", "Selector de Método", "Elige entre 15 frameworks de venta según ticket/ciclo/decisores.", "analisis", 0.9),
    ("roadmap_builder", "Constructor de Roadmap", "Arma fases de venta (30/60/90) con acciones por semana.", "datos", 0.85),
    ("objection_master", "Maestro de Objeciones", "Script calibrado para 7 objeciones por escenario (sin presión).", "chat", 0.85),
    ("sales_metrics", "Métricas de Venta", "Tasa de avance, conversión por fase, detección de banderas rojas.", "analisis", 0.8),
    ("spin_executor", "Ejecutor SPIN", "Guía preguntas SPIN (Situation/Problem/Implication/Payoff) paso a paso.", "chat", 0.85),
    ("meddic_tracker", "Tracker MEDDIC", "Monitorea 6 líneas MEDDIC (Metrics/Economic/Decision/Criteria/Pain/Champion).", "datos", 0.85),
    ("consultative_guide", "Guía Consultativa", "3 sesiones: diagnóstico → análisis → recomendación (escucha 70%).", "chat", 0.85),
    # ── Agente Vendedor Maestro ──
    ("master_script_gen", "Generador Script Maestro", "Script de venta en 5 pasos integrados (Belfort+SPIN+Hermozi+Vaynerchuk+Cialdini).", "chat", 0.95),
    ("five_step_sales", "Venta en 5 Pasos", "Rapport → Diagnóstico → Reframe → Oferta → Cierre (tonalidad por paso).", "chat", 0.9),
    ("tone_calibrator", "Calibrador de Tonalidad", "Tonalidad exacta por etapa de venta (curiosidad/comprensión/autoridad/entusiasmo/decisión).", "chat", 0.85),
    ("objection_master_final", "Maestro de Objeciones Final", "7 objeciones + respuesta maestra (valida → diagnostica → reframe → confirma).", "chat", 0.9),
    ("irresistible_offer_final", "Oferta Irresistible Final", "Oferta = sueño+prueba−tiempo−esfuerzo+bono+garantía+escasez (fórmula exacta).", "analisis", 0.9),
    ("master_close", "Cierre Maestro", "Cierre progresivo (pequeños síes → firma) + garantía real + seguimiento 48h.", "chat", 0.85),
    # ── Lifecycle + CRM ──
    ("lifecycle_detector", "Detector de Etapa Lifecycle", "Determina en qué etapa está cliente (onboard/engagement/upsell/retention/churn risk).", "analisis", 0.9),
    ("aha_moment_tracker", "Rastreador de Aha Moment", "Detecta cuándo cliente logra primer resultado (objetivo en 48h).", "analisis", 0.85),
    ("crm_sync", "Sincronizador de CRM", "Sincroniza contacto con Salesforce/HubSpot/Pipedrive (bidireccional).", "datos", 0.85),
    ("smart_scheduler", "Programador Inteligente", "Agenda follow-ups óptimos (zona horaria + patrón respuesta + presión calibrada).", "analisis", 0.8),
    ("churn_detector", "Detector de Churn", "Alerta caída 30%+ en uso. Riesgo ALTO de pérdida.", "analisis", 0.85),
    ("qbr_builder", "Constructor de QBR", "Genera review trimestral con métricas + benchmarking + roadmap.", "datos", 0.8),
    ("ab_test_runner", "Ejecutor de A/B Tests", "Testea variantes de copy/mensaje. Mide open/response/conversion. Retorna ganador.", "analisis", 0.75),
]


def _tool_caps() -> list[Capability]:
    return [
        Capability(
            id=f"skill.tool.{slug}", kind=CapabilityKind.SKILL, name=name,
            category="Herramienta", description=desc, tags=("tool", "react", group),
            health=health, metadata={"runtime": "react_orchestrator", "group": group},
        )
        for slug, name, desc, group, health in _TOOL_SKILLS
    ]


def _computer_use_skill_caps() -> list[Capability]:
    """Computer Use skill domains (venta, contenido, ads, finanzas, etc.).

    Cada dominio del knowledge base se expone como una skill del cerebro,
    con el rol de equipo equivalente. Import perezoso para mantener el
    registry import-safe.
    """
    try:
        from app.domains.computer_use.skills.knowledge_base import (
            SKILL_DOMAINS, SALES_TEAM_ROLES,
        )
    except Exception as exc:  # pragma: no cover - defensivo
        logger.warning("Computer Use skills no disponibles: %s", exc)
        return []

    out: list[Capability] = []
    for key, domain in SKILL_DOMAINS.items():
        role = SALES_TEAM_ROLES.get(key, "Especialista")
        group = _CU_DOMAIN_GROUP.get(key, "conocimiento")
        out.append(Capability(
            id=f"skill.computer_use.{key}",
            kind=CapabilityKind.SKILL,
            name=domain.title,
            category="Dominio Computer Use",
            description=f"{role} — {len(domain.principles)} competencias operativas.",
            tags=("computer_use", "skill_domain", key, group),
            health=min(1.0, 0.7 + len(domain.principles) / 30),
            metadata={
                "role": role,
                "competencies": len(domain.principles),
                "platforms": list(domain.platforms),
                "group": group,
            },
        ))
    return out


# Mapa dominio Computer Use → categoría (group) para el mapa de interacciones.
_CU_DOMAIN_GROUP: dict[str, str] = {
    "sales_strategy": "conocimiento", "prospecting": "chat", "outreach": "chat",
    "negotiation": "conocimiento", "customer_success": "chat",
    "content_creator": "creatividad", "social_media": "creatividad",
    "ads_management": "analisis", "sales_platforms": "datos",
    "seo_marketing": "seo", "market_intel": "analisis", "analytics": "analisis",
    "crm_ops": "datos", "crypto": "analisis", "stock_market": "analisis",
    "market_analysis": "analisis", "financial_markets": "analisis",
    "real_estate": "analisis", "trading_platforms": "datos",
    "risk_management": "analisis", "business_models": "conocimiento",
    "tool_handling": "datos",
}


# ─────────────────────────────────────────────────────────────────────────
# GROUP (categoría) — taxonomía transversal para el mapa de interacciones
# ─────────────────────────────────────────────────────────────────────────
GROUP_LABEL: dict[str, str] = {
    "ventas": "Ventas", "publicacion": "Publicación", "anuncios": "Anuncios",
    "mensajeria": "Mensajería", "pagos": "Pagos", "fiscal": "Fiscal", "web": "Web",
    "crm": "CRM/Integraciones",
    "captacion": "Captación", "conversion": "Conversión", "retencion": "Retención",
    "experto": "Experto", "leyenda": "Leyenda",
    "adquisicion": "Adquisición", "core": "Core", "finanzas": "Finanzas",
    "creatividad": "Creatividad", "analisis": "Análisis", "chat": "Chat",
    "datos": "Datos/CRM", "seo": "SEO", "conocimiento": "Conocimiento",
}

_PLATFORM_GROUP: dict[str, str] = {
    "mercadolibre": "ventas", "amazon": "ventas", "shopify": "ventas",
    "tiendanube": "ventas", "hotmart": "ventas",
    "woocommerce": "ventas", "vtex": "ventas", "etsy": "ventas", "ebay": "ventas",
    "instagram": "publicacion", "facebook": "publicacion", "tiktok": "publicacion",
    "linkedin": "publicacion", "youtube": "publicacion", "twitter": "publicacion",
    "pinterest": "publicacion", "threads": "publicacion",
    "meta_ads": "anuncios", "google_ads": "anuncios", "tiktok_ads": "anuncios", "linkedin_ads": "anuncios",
    "whatsapp": "mensajeria", "telegram": "mensajeria", "email": "mensajeria",
    "messenger": "mensajeria", "sms": "mensajeria",
    "stripe": "pagos", "mercadopago": "pagos", "paypal": "pagos", "getnet": "pagos",
    "arca": "fiscal", "sat": "fiscal", "dian": "fiscal", "web": "web",
    "hubspot": "crm", "salesforce": "crm", "notion": "crm", "google_sheets": "crm",
    "google_calendar": "crm", "slack": "crm", "zapier": "crm", "webhooks": "crm",
    "github": "web", "linktree": "web", "beacons": "web", "canva": "creatividad",
}

_PIPELINE_GROUP: dict[str, str] = {
    "captador": "captacion", "calificador": "captacion", "nutridor": "captacion",
    "diagnostico": "conversion", "propuesta": "conversion",
    "objeciones": "conversion", "cerrador": "conversion",
    "onboarding": "retencion", "retentor": "retencion",
}

_AUTO_CAT_GROUP: dict[str, str] = {
    "Adquisición": "adquisicion", "Conversión": "conversion",
    "Retención": "retencion", "Core": "core", "Finanzas": "finanzas",
}

_TOOL_GROUP: dict[str, str] = {slug: group for slug, _n, _d, group, _h in _TOOL_SKILLS}


def _group_of(cap: "Capability") -> str:
    """Categoría transversal de una capability para clusterizar el mapa."""
    cid = cap.id
    if cid.startswith("platform."):
        return _PLATFORM_GROUP.get(cid.split(".")[-1], "web")
    if cid.startswith("agent.pipeline."):
        return _PIPELINE_GROUP.get(cid.split(".")[-1], "captacion")
    if cid.startswith("agent.expert."):
        return "experto"
    if cid.startswith("agent.legend."):
        return "leyenda"
    if cid.startswith("automation."):
        return _AUTO_CAT_GROUP.get(cap.category, "core")
    if cid.startswith("skill.knowledge."):
        return "conocimiento"
    # tools + computer_use: group viene en metadata
    g = cap.metadata.get("group")
    return g if isinstance(g, str) else "conocimiento"


# ─────────────────────────────────────────────────────────────────────────
# PLATFORMS — canales e integraciones externas reales que el cerebro opera
# ─────────────────────────────────────────────────────────────────────────
_PLATFORMS: list[tuple[str, str, str]] = [
    ("whatsapp", "WhatsApp", "Mensajería · ventas y soporte 1:1"),
    ("instagram", "Instagram", "DMs, comentarios y contenido"),
    ("facebook", "Facebook", "Páginas, Messenger y comunidad"),
    ("tiktok", "TikTok", "Contenido viral y TikTok Shop"),
    ("linkedin", "LinkedIn", "Outbound B2B y prospección"),
    ("email", "Email", "Secuencias y campañas"),
    ("telegram", "Telegram", "Mensajería y bots"),
    ("mercadolibre", "Mercado Libre", "Marketplace · listings y preguntas"),
    ("amazon", "Amazon", "Marketplace global"),
    ("shopify", "Shopify", "E-commerce propio"),
    ("tiendanube", "Tienda Nube", "E-commerce LATAM"),
    ("hotmart", "Hotmart", "Productos digitales"),
    ("meta_ads", "Meta Ads", "Pauta en Facebook/Instagram"),
    ("google_ads", "Google Ads", "Search y display"),
    ("stripe", "Stripe", "Cobros y suscripciones"),
    ("mercadopago", "Mercado Pago", "Cobros LATAM"),
    ("arca", "ARCA/AFIP", "Facturación electrónica"),
    ("web", "Web/Landing", "Sitio y formularios de captura"),
    # ── más canales/integraciones reales ──
    ("messenger", "Messenger", "Mensajería de Facebook"),
    ("sms", "SMS", "Mensajes de texto (Twilio)"),
    ("youtube", "YouTube", "Video largo y Shorts"),
    ("twitter", "X (Twitter)", "Posts y DMs"),
    ("pinterest", "Pinterest", "Pins y catálogos visuales"),
    ("threads", "Threads", "Microblogging Meta"),
    ("woocommerce", "WooCommerce", "E-commerce WordPress"),
    ("vtex", "VTEX", "E-commerce enterprise LATAM"),
    ("etsy", "Etsy", "Marketplace de hechos a mano"),
    ("ebay", "eBay", "Marketplace global"),
    ("tiktok_ads", "TikTok Ads", "Pauta en TikTok"),
    ("linkedin_ads", "LinkedIn Ads", "Pauta B2B"),
    ("paypal", "PayPal", "Cobros internacionales"),
    ("getnet", "Getnet", "Cobros y POS"),
    ("sat", "SAT (MX)", "Facturación México"),
    ("dian", "DIAN (CO)", "Facturación Colombia"),
    ("hubspot", "HubSpot", "CRM y marketing"),
    ("salesforce", "Salesforce", "CRM enterprise"),
    ("notion", "Notion", "Docs y base de datos"),
    ("google_sheets", "Google Sheets", "Planillas y datos"),
    ("google_calendar", "Google Calendar", "Agenda y reuniones"),
    ("slack", "Slack", "Comunicación de equipo"),
    ("zapier", "Zapier", "Integraciones no-code"),
    ("webhooks", "Webhooks", "Integraciones por API"),
    ("github", "GitHub", "Repos, releases y docs"),
    ("linktree", "Linktree", "Link-in-bio"),
    ("beacons", "Beacons", "Link-in-bio y tienda"),
    ("canva", "Canva", "Diseño de piezas de marca"),
    ("manychat", "ManyChat", "Automatización de chat para IG/FB/WA · captura y filtra leads"),
]


def _platform_caps() -> list[Capability]:
    return [
        Capability(
            id=f"platform.{slug}", kind=CapabilityKind.PLATFORM, name=name,
            category="Plataforma", description=desc, tags=("platform", "canal", slug),
            health=1.0, metadata={"integration": slug},
        )
        for slug, name, desc in _PLATFORMS
    ]


# ─────────────────────────────────────────────────────────────────────────
# AUTOMATIONS
# ─────────────────────────────────────────────────────────────────────────
_AUTOMATIONS: list[tuple[str, str, str, str]] = [
    ("cart_recovery", "Recuperación de Carritos", "Retención", "Secuencia WA+email tras abandono."),
    ("wa_bot_247", "Bot WhatsApp 24/7", "Conversión", "Responde, califica y cierra sin humanos."),
    ("lead_nurturing", "Nurturing de Leads", "Adquisición", "Drip multicanal hasta sales-ready."),
    ("meta_ads_optimizer", "Optimizador Meta Ads", "Adquisición", "Crea, monitorea y escala campañas."),
    ("google_ads_optimizer", "Optimizador Google Ads", "Adquisición", "Search+display con puja automática."),
    ("social_content", "Contenido Social Diario", "Adquisición", "Genera y publica posts/reels/stories."),
    ("email_lifecycle", "Email Lifecycle", "Retención", "Secuencias por comportamiento."),
    ("review_responder", "Gestor de Reseñas", "Retención", "Responde reseñas <5 min, mantiene 4.8★."),
    ("deal_reactivation", "Reactivación de Deals", "Conversión", "Detecta estancados y reactiva."),
    ("invoicing", "Facturación Electrónica", "Core", "Emite y registra factura por venta."),
    ("referral_engine", "Motor de Referidos", "Adquisición", "Links, tracking y recompensas auto."),
    ("inventory_sync", "Sincronía de Inventario", "Retención", "Stock unificado + reposición."),
    # ── Finanzas / estructura / producto ──
    ("research_winning_products", "Research de Producto Ganador", "Adquisición", "Detecta productos con demanda y margen."),
    ("budget_costing", "Costos y Presupuesto", "Finanzas", "Estructura de costos, márgenes y presupuesto."),
    ("financial_dashboard", "Tablero Financiero", "Finanzas", "Activos, pasivos, caja y P&L en vivo."),
    ("business_structuring", "Estructuración del Negocio", "Core", "Estructura legal/fiscal/societaria y procesos."),
    ("crypto_watchlist", "Watchlist Cripto (educativa)", "Finanzas", "Seguimiento on-chain y de mercado, sólo lectura."),
    ("real_estate_scan", "Análisis Inmobiliario", "Finanzas", "Cap rate, plusvalía y oportunidades (educativo)."),
    # ── Lead intelligence + marketing + branding ──
    ("manychat_qualify", "ManyChat: Filtrar Leads Malos", "Adquisición", "Califica en ManyChat y descarta leads que nunca van a comprar."),
    ("lead_capture", "Captación Inteligente de Leads", "Adquisición", "Lead magnet + scoring automático en IG/WA/landing."),
    ("brief_to_campaign", "Brief → Campaña 360°", "Adquisición", "Convierte un brief en estrategia + copys + creativos + medición."),
    ("brand_identity", "Generador de Identidad de Marca", "Core", "Genera propósito, tono, naming, paleta, tipografía y logo."),
    ("impossible_sale", "Vender lo Invendible", "Conversión", "Reframes + ángulos + pitch para vender donde parece imposible."),
    ("advanced_sales_system", "Sistema Avanzado de Ventas", "Conversión", "Elige método óptimo (15 frameworks) por ticket/ciclo/decisores + roadmap 30/60/90 + objeciones + métricas."),
    ("master_seller_dispatch", "Vendedor Maestro Activado", "Conversión", "Agente unificado: Belfort+SPIN+Hermozi+Vaynerchuk+Cialdini. Script de venta irresistible en 5 pasos + objeciones + cierre."),
    # ── Lifecycle automations ──
    ("onboarding_sequence", "Secuencia de Onboarding", "Retención", "Email welcome + video priming + guía paso a paso + call celebrando primer win."),
    ("engagement_loops", "Loops de Engagement", "Retención", "Email tips semanales + check-in diario + notificaciones ausencia + webinars comunitarios."),
    ("upsell_detection", "Detección Automática de Upsell", "Expansión", "Monitorea uso. Al 70%+ features → sugiere upgrade o cross-sell complemento."),
    ("retention_qbr", "QBR Trimestral Automatizada", "Retención", "Success metrics, benchmarking, innovación, programa de referral."),
    ("churn_alerts", "Alertas de Churn Automáticas", "Retención", "Detecta caída 30%+ en uso. Intervención 48h. Diagnóstico + win-back."),
]


def _automation_caps() -> list[Capability]:
    return [
        Capability(
            id=f"automation.{slug}", kind=CapabilityKind.AUTOMATION, name=name,
            category=cat, description=desc, tags=("automation", cat.lower()),
            health=0.97, metadata={"trigger": "event|schedule"},
        )
        for slug, name, cat, desc in _AUTOMATIONS
    ]


# ─────────────────────────────────────────────────────────────────────────
# SNAPSHOT + REGISTRY
# ─────────────────────────────────────────────────────────────────────────
@dataclass
class BrainSnapshot:
    agents: list[Capability]
    skills: list[Capability]
    automations: list[Capability]
    platforms: list[Capability] = field(default_factory=list)

    def _all(self) -> list[Capability]:
        return self.agents + self.skills + self.automations + self.platforms

    @property
    def counts(self) -> dict[str, int]:
        return {
            "agents": len(self.agents),
            "skills": len(self.skills),
            "automations": len(self.automations),
            "platforms": len(self.platforms),
            "total": len(self._all()),
        }

    @property
    def health(self) -> float:
        caps = self._all()
        return round(sum(c.health for c in caps) / len(caps), 4) if caps else 0.0

    def categories(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self._all():
            out[c.category] = out.get(c.category, 0) + 1
        return out

    def as_dict(self) -> dict[str, Any]:
        return {
            "counts": self.counts,
            "health": self.health,
            "categories": self.categories(),
            "agents": [c.as_dict() for c in self.agents],
            "skills": [c.as_dict() for c in self.skills],
            "automations": [c.as_dict() for c in self.automations],
            "platforms": [c.as_dict() for c in self.platforms],
        }


class BrainRegistry:
    """Builds and serves the unified capability snapshot."""

    def snapshot(self) -> BrainSnapshot:
        return BrainSnapshot(
            agents=_agent_caps(),
            skills=_knowledge_caps() + _tool_caps() + _computer_use_skill_caps(),
            automations=_automation_caps(),
            platforms=_platform_caps(),
        )

    def all_capabilities(self) -> list[Capability]:
        s = self.snapshot()
        return s._all()

    def graph(self) -> dict[str, Any]:
        """Grafo REAL de capacidades: nodos = capabilities, edges = relaciones
        estructurales reales del sistema (no inventadas).

        Capas (layer) — flujo izquierda→derecha con flechas direccionales:
          0 = platforms (canales/integraciones: WhatsApp, ML, Amazon, Ads…)
          1 = skills (conocimiento, tools, dominios Computer Use)
          2 = agents (pipeline, expertos, leyendas)
          3 = automations

        Edges reales (source → target, con flecha):
          * platform → agent : el canal alimenta al pipeline (entrada de leads).
          * agent → skill    : el agente invoca/consulta skills.
          * automation → agent : la automatización orquesta agentes de su etapa.
          * automation → platform : la automatización actúa sobre la plataforma.
        """
        snap = self.snapshot()

        def node(c: Capability, layer: int) -> dict[str, Any]:
            g = _group_of(c)
            return {
                "id": c.id, "label": c.name, "kind": c.kind.value,
                "category": c.category, "layer": layer,
                "group": g, "group_label": GROUP_LABEL.get(g, g),
                "health": c.health, "tags": list(c.tags),
            }

        nodes: list[dict[str, Any]] = (
            [node(c, 0) for c in snap.platforms]
            + [node(c, 1) for c in snap.skills]
            + [node(c, 2) for c in snap.agents]
            + [node(c, 3) for c in snap.automations]
        )

        skill_ids = {c.id for c in snap.skills}
        platform_ids = {c.id for c in snap.platforms}
        edges: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def link(src: str, dst: str, rel: str) -> None:
            key = (src, dst)
            if src != dst and dst and key not in seen:
                seen.add(key)
                edges.append({"source": src, "target": dst, "rel": rel})

        # platform → agente de entrada (canal alimenta al pipeline)
        messaging = {"whatsapp", "instagram", "facebook", "tiktok", "linkedin", "email", "telegram",
                     "web", "messenger", "sms", "twitter", "threads", "youtube"}
        marketplaces = {"mercadolibre", "amazon", "shopify", "tiendanube", "hotmart",
                        "woocommerce", "vtex", "etsy", "ebay"}
        for slug in (s for s, _n, _d in _PLATFORMS):
            pid = f"platform.{slug}"
            link(pid, "agent.pipeline.captador", "alimenta")
            if slug in messaging:
                link(pid, "agent.expert.customer_service", "atiende")
            if slug in marketplaces:
                link(pid, "agent.pipeline.retentor", "recompra")

        # automation → plataforma sobre la que actúa (acción real)
        auto_to_platform = {
            "automation.cart_recovery": ("whatsapp", "email"),
            "automation.wa_bot_247": ("whatsapp",),
            "automation.lead_nurturing": ("email", "whatsapp"),
            "automation.meta_ads_optimizer": ("meta_ads",),
            "automation.google_ads_optimizer": ("google_ads",),
            "automation.social_content": ("instagram", "tiktok", "facebook"),
            "automation.email_lifecycle": ("email",),
            "automation.review_responder": ("mercadolibre",),
            "automation.deal_reactivation": ("whatsapp", "email"),
            "automation.invoicing": ("arca",),
            "automation.referral_engine": ("whatsapp",),
            "automation.inventory_sync": ("mercadolibre", "shopify", "tiendanube"),
        }
        for aid, plats in auto_to_platform.items():
            for slug in plats:
                if f"platform.{slug}" in platform_ids:
                    link(aid, f"platform.{slug}", "opera")

        # automation → agentes de su etapa de funnel (mapeo real categoría→stages)
        cat_to_stages = {
            "Adquisición": ("captador", "calificador", "nutridor"),
            "Conversión": ("diagnostico", "propuesta", "objeciones", "cerrador"),
            "Retención": ("onboarding", "retentor"),
            "Core": ("cerrador",),
        }
        for a in snap.automations:
            for slug in cat_to_stages.get(a.category, ()):  # type: ignore[arg-type]
                link(a.id, f"agent.pipeline.{slug}", "orquesta")

        # tools universales que cualquier agente del pipeline invoca
        universal_tools = [
            t for t in ("skill.tool.retrieve_knowledge", "skill.tool.search_memory",
                        "skill.tool.lead_scoring")
            if t in skill_ids
        ]
        for slug, _name, _desc in _PIPELINE_AGENTS:
            aid = f"agent.pipeline.{slug}"
            for tid in universal_tools:
                link(aid, tid, "usa")

        # agent → skill de conocimiento por afinidad de tags (relación real por dominio)
        for a in snap.agents:
            atoks = set(a.id.lower().replace(".", "_").split("_")) | {t.lower() for t in a.tags}
            for s in snap.skills:
                if s.id.startswith("skill.knowledge.") or s.id.startswith("skill.computer_use."):
                    stoks = set(s.id.lower().split(".")[-1].split("_")) | {t.lower() for t in s.tags}
                    if atoks & stoks:
                        link(a.id, s.id, "consulta")

        # agente experto → tool específica (relación real por rol)
        expert_tools = {
            "ad_copywriter": ("copy_gen", "ad_creative"),
            "brand_visual": ("brand_design", "image_gen"),
            "market_analyst": ("competitor_intel", "dashboards", "forecast"),
            "kpi_architect": ("dashboards", "cohort_analysis"),
            "crm_builder": ("crm_sync", "lead_enrichment"),
            "landing_builder": ("ab_testing", "seo_audit"),
            "viral_video": ("video_reels",),
            "customer_service": ("wa_inbox", "live_chat", "voice_session"),
            "lead_qualifier": ("lead_scoring", "lead_enrichment"),
        }
        for slug, tools in expert_tools.items():
            for tslug in tools:
                if f"skill.tool.{tslug}" in skill_ids:
                    link(f"agent.expert.{slug}", f"skill.tool.{tslug}", "usa")

        # tool (chat/creatividad) → plataforma sobre la que produce/actúa (real)
        tool_to_platform = {
            "wa_inbox": ("whatsapp",), "ig_dm": ("instagram",),
            "email_compose": ("email",), "live_chat": ("web",),
            "voice_session": ("whatsapp",),
            "ad_creative": ("meta_ads", "google_ads", "tiktok_ads", "linkedin_ads"),
            "image_gen": ("instagram", "meta_ads", "pinterest"),
            "copy_gen": ("meta_ads", "email", "twitter"),
            "video_reels": ("tiktok", "instagram", "youtube"),
            "brand_design": ("web",),
            "seo_audit": ("web",), "schema_markup": ("web",), "landing_gen": ("web",),
            "carousel_gen": ("instagram", "linkedin"),
            "thumbnail_gen": ("youtube",), "voiceover": ("youtube", "tiktok"),
            "ugc_script": ("tiktok", "instagram"),
            "messenger_inbox": ("messenger",), "sms_send": ("sms",),
            "comment_responder": ("instagram", "facebook"),
            "dm_outreach": ("linkedin", "instagram", "twitter"),
            "faq_bot": ("web", "whatsapp"), "appointment_booker": ("google_calendar",),
            "calendar_sync": ("google_calendar",), "sheet_sync": ("google_sheets",),
            "crm_sync": ("hubspot", "salesforce"), "crm_dedupe": ("hubspot",),
            "segment_builder": ("hubspot",), "data_export": ("google_sheets",),
            "invoice_gen": ("arca", "sat", "dian"), "payment_link": ("stripe", "mercadopago", "paypal"),
            "contract_gen": ("notion",),
        }
        for tslug, plats in tool_to_platform.items():
            tid = f"skill.tool.{tslug}"
            if tid not in skill_ids:
                continue
            for slug in plats:
                if f"platform.{slug}" in platform_ids:
                    link(tid, f"platform.{slug}", "produce")

        return {
            "nodes": nodes,
            "edges": edges,
            "counts": snap.counts,
            "health": snap.health,
        }

    def flows(self) -> dict[str, Any]:
        """Flujos estilo n8n/Make: cada automatización REAL = un flujo con pasos
        (trigger → agentes → tools → plataformas) y conexiones.

        El frontend dibuja cada flujo como un mini-canvas tipo n8n. Los pasos
        salen del grafo real (mismas relaciones que `graph()`), no inventados.
        """
        snap = self.snapshot()
        skill_ids = {c.id for c in snap.skills}
        platform_ids = {c.id for c in snap.platforms}
        agent_by_id = {c.id: c for c in snap.agents}

        cat_to_stages = {
            "Adquisición": ("captador", "calificador"),
            "Conversión": ("diagnostico", "cerrador"),
            "Retención": ("onboarding", "retentor"),
            "Core": ("cerrador",),
        }
        auto_to_platform = {
            "automation.cart_recovery": ("whatsapp", "email"),
            "automation.wa_bot_247": ("whatsapp",),
            "automation.lead_nurturing": ("email", "whatsapp"),
            "automation.meta_ads_optimizer": ("meta_ads",),
            "automation.google_ads_optimizer": ("google_ads",),
            "automation.social_content": ("instagram", "tiktok"),
            "automation.email_lifecycle": ("email",),
            "automation.review_responder": ("mercadolibre",),
            "automation.deal_reactivation": ("whatsapp",),
            "automation.invoicing": ("arca",),
            "automation.referral_engine": ("whatsapp",),
            "automation.inventory_sync": ("mercadolibre", "shopify"),
        }
        auto_tool = {
            "automation.meta_ads_optimizer": "ad_creative",
            "automation.google_ads_optimizer": "ad_creative",
            "automation.social_content": "copy_gen",
            "automation.email_lifecycle": "email_compose",
            "automation.cart_recovery": "wa_inbox",
            "automation.wa_bot_247": "wa_inbox",
            "automation.lead_nurturing": "email_compose",
            "automation.deal_reactivation": "lead_scoring",
            "automation.review_responder": "competitor_intel",
            "automation.referral_engine": "crm_sync",
            "automation.inventory_sync": "crm_sync",
            "automation.invoicing": "crm_sync",
        }

        flows: list[dict[str, Any]] = []
        for a in snap.automations:
            steps: list[dict[str, Any]] = []
            edges: list[dict[str, Any]] = []

            def step(sid: str, label: str, kind: str, group: str, col: int) -> str:
                steps.append({"id": sid, "label": label, "kind": kind, "group": group, "col": col})
                return sid

            trigger = step(a.id, a.name, "automation", _group_of(a), 0)
            # agentes de la etapa
            agent_ids: list[str] = []
            for slug in cat_to_stages.get(a.category, ()):  # type: ignore[arg-type]
                aid = f"agent.pipeline.{slug}"
                if aid in agent_by_id:
                    agent_ids.append(step(aid, agent_by_id[aid].name, "agent", _group_of(agent_by_id[aid]), 1))
                    edges.append({"source": trigger, "target": aid, "rel": "orquesta"})
            # tool
            tslug = auto_tool.get(a.id)
            tool_id = None
            if tslug and f"skill.tool.{tslug}" in skill_ids:
                tool_id = step(f"skill.tool.{tslug}", tslug.replace("_", " ").title(), "skill",
                               _TOOL_GROUP.get(tslug, "datos"), 2)
                for aid in (agent_ids or [trigger]):
                    edges.append({"source": aid, "target": tool_id, "rel": "usa"})
            # plataformas
            for slug in auto_to_platform.get(a.id, ()):
                pid = f"platform.{slug}"
                if pid in platform_ids:
                    step(pid, slug.replace("_", " ").title(), "platform", _PLATFORM_GROUP.get(slug, "web"), 3)
                    edges.append({"source": tool_id or (agent_ids[0] if agent_ids else trigger),
                                  "target": pid, "rel": "opera"})

            flows.append({
                "id": f"flow.{a.id}", "name": a.name, "category": a.category,
                "group": _group_of(a), "kind": "automation",
                "steps": steps, "edges": edges,
            })
        return {"flows": flows}

    def find(self, kind: CapabilityKind | None = None, query: str | None = None) -> list[Capability]:
        caps = self.all_capabilities()
        if kind is not None:
            caps = [c for c in caps if c.kind == kind]
        if query:
            q = query.lower()
            caps = [
                c for c in caps
                if q in c.name.lower() or q in c.description.lower()
                or any(q in t for t in c.tags)
            ]
        return caps


@lru_cache(maxsize=1)
def get_brain_registry() -> BrainRegistry:
    return BrainRegistry()
