import os
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uuid

import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

from app.api.v1 import auth, users, businesses, catalog, channels, conversations, subscriptions, agents, automations, analytics, tracking, shipments, services, assistant as assistant_router, computer_use as computer_use_router, computer_use_extended as computer_use_extended_router, computer_use_brain as computer_use_brain_router, computer_use_audit_log as computer_use_audit_log_router, computer_use_webhooks as computer_use_webhooks_router, computer_use_lead_scoring as computer_use_lead_scoring_router, computer_use_ad_orchestrator as computer_use_ad_orchestrator_router, computer_use_task_scheduler as computer_use_task_scheduler_router, sales_funnel as sales_funnel_router, onboarding as onboarding_router, missions as missions_router
from app.domains.business_context.api import router as business_context_router
from app.domains.credentials.api import router as credentials_router
from app.api.v1.mission_websocket import router as mission_ws_router
from app.api.v1.websocket import router as brain_ws_router
try:
    from app.api.v1 import upload
except ImportError:
    upload = None
try:
    from app.api.v1 import security as security_router
except ImportError:
    security_router = None
from app.domains.crm.router import router as crm_router
from app.domains.orders.router import router as orders_router
from app.domains.alerts.router import router as alerts_router
from app.domains.provisioning.router import router as provisioning_router
from app.domains.diagnostics.router import router as diagnostics_router
from app.domains.synthetic.router import router as synthetic_router
from app.domains.feature_flags.router import router as feature_flags_router
from app.domains.consumo.router import router as consumo_router
from app.domains.competitive.router import router as competitive_router, intelligence_router as competitive_intelligence_router
from app.domains.marketplace.router import router as marketplace_router
from app.domains.fomo.router import router as fomo_router
from app.domains.social_growth.router import router as social_growth_router
from app.domains.referrals.router import router as referrals_router
from app.domains.coupons.router import router as coupons_router
from app.domains.nps.router import router as nps_router
from app.domains.product_tours.router import router as tours_router
from app.domains.webhooks.router import router as webhooks_router
from app.domains.memory.router import router as memory_router
from app.domains.agents.router_outcomes import router as outcomes_router
from app.domains.agents.router_swarm import router as swarm_router
from app.domains.agents.router_scoring import router as scoring_router
from app.domains.agents.router_intelligence import router as intelligence_router
from app.domains.agents.router_reflection import router as reflection_router
from app.domains.agents.router_causal import router as causal_router
from app.domains.agents.router_ab import router as ab_router
from app.domains.agents.market_analyst.router import router as market_analyst_router
from app.domains.agents.financial_planner.router import router as financial_planner_router
from app.domains.agents.acquisition_strategist.router import router as acquisition_strategist_router
from app.domains.agents.landing_builder.router import router as landing_builder_router
from app.domains.agents.app_builder.router import router as app_builder_router
from app.domains.agents.crm_builder.router import router as crm_builder_router
from app.domains.agents.ad_copywriter.router import router as ad_copywriter_router
from app.domains.agents.investor_pitch.router import router as investor_pitch_router
from app.domains.agents.kpi_architect.router import router as kpi_architect_router
from app.domains.agents.customer_service.router import router as customer_service_router
from app.domains.agents.lead_qualifier.router import router as lead_qualifier_router
from app.domains.agents.auto_responder.router import router as auto_responder_router
from app.domains.training.router import router as training_router
from app.api.v1 import selfservice as selfservice_router
from app.api.v1 import admin as admin_router
from app.api.v1 import brain as brain_router
from app.api.v1 import trade_signals as trade_signals_router
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.core.semantic_cache import SemanticCacheEmbedding  # noqa: F401
from app.core.events import event_bus
from datetime import datetime, timezone
from app.core.event_handlers import register_event_handlers
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.security_logging import SecurityAuditMiddleware
from app.middleware.threat_intel import ThreatIntelMiddleware
from app.middleware.subscription_audit import SubscriptionAuditMiddleware
from app.middleware.audit_log import DataAccessAuditMiddleware
from app.middleware.cache_control import CacheControlMiddleware
from app.middleware.payload_limit import PayloadLimitMiddleware
from app.middleware.ip_blocklist import IPBlocklistMiddleware
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.csrf import CSRFMiddleware
from app.core.threat_intel import assess_client_risk, device_fingerprint
from app.core.cloudflare import get_cloudflare_info, validate_cloudflare_origin, is_cloudflare_ip
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.metrics import (
    SELLIA_LOGINS, SELLIA_FAILED_LOGINS, SELLIA_GEOFENCE_VIOLATIONS,
    SELLIA_NEW_DEVICES, SELLIA_RATE_LIMIT_HITS, SELLIA_REQUEST_DURATION,
    SELLIA_REQUESTS, SELLIA_ACTIVE_SESSIONS
)

settings = get_settings()
# WorkflowScheduler deshabilitado: Celery Beat maneja el scheduling ahora
# scheduler = WorkflowScheduler(check_interval=30)


_redis_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis_instance
    # Startup
    # WorkflowScheduler deshabilitado: Celery Beat maneja el scheduling ahora
    # await scheduler.start()

    # Inicializar Event Bus
    try:
        await event_bus.connect()
        register_event_handlers()
        await event_bus.start_listener()
    except Exception:
        pass

    # Inicializar WebSocket Manager para Computer Use (multi-worker)
    try:
        from app.domains.computer_use.ws_manager import ws_manager
        await ws_manager.start()
    except Exception:
        pass

    # Inicializar Redis para rate limiting
    try:
        _redis_instance = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(_redis_instance)
    except Exception:
        pass

    yield

    # Shutdown
    # await scheduler.stop()
    await event_bus.stop_listener()
    await event_bus.disconnect()
    from app.domains.computer_use.ws_manager import ws_manager
    await ws_manager.stop()
    if _redis_instance:
        await _redis_instance.close()


# Configurar OpenAPI condicionalmente
openapi_url = "/openapi.json" if settings.ENABLE_OPENAPI else None
docs_url = "/docs" if settings.ENABLE_OPENAPI else None
redoc_url = "/redoc" if settings.ENABLE_OPENAPI else None

app = FastAPI(
    title="SellIA - Vende mientras duermes",
    description="Sistema integral de agentes IA para automatización de ventas",
    version="0.2.0",
    lifespan=lifespan,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# Métricas Prometheus — instrumentación automática + endpoint /metrics
# En producción, /metrics requiere autenticación básica o IP allowlist
_METRICS_USERNAME = os.environ.get("METRICS_USERNAME", "")
_METRICS_PASSWORD = os.environ.get("METRICS_PASSWORD", "")

def _metrics_auth():
    import secrets
    from fastapi import Request, HTTPException, status
    async def check(request: Request):
        if settings.ENVIRONMENT != "production":
            return
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        import base64
        creds = base64.b64decode(auth[6:]).decode()
        user, pwd, *_ = creds.split(":", 1)
        if not secrets.compare_digest(user, _METRICS_USERNAME) or not secrets.compare_digest(pwd, _METRICS_PASSWORD):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return check

Instrumentator().instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False, dependencies=[Depends(_metrics_auth())]
)

# 0. Payload size limit (primero para rechazar bodies enormes antes de procesar)
app.add_middleware(PayloadLimitMiddleware, max_size_bytes=10 * 1024 * 1024)

# 0.5 IP Blocklist (bloquea IPs ya conocidas antes de procesar)
app.add_middleware(IPBlocklistMiddleware)

# 0.75 Idempotency keys (evita duplicados en operaciones críticas)
app.add_middleware(IdempotencyMiddleware)

# 1. Threat Intel (primero para analizar todo)
app.add_middleware(ThreatIntelMiddleware)

# 2. Logging de auditoría
app.add_middleware(SecurityAuditMiddleware)

# 3. Data access audit logging
app.add_middleware(DataAccessAuditMiddleware)

# 4. Headers de seguridad HTTP
app.add_middleware(SecurityHeadersMiddleware)

# 4.5 Cache-Control para endpoints sensibles (PII)
app.add_middleware(CacheControlMiddleware)

# 4. Subscription Audit (logueo de uso para evidencia)
app.add_middleware(SubscriptionAuditMiddleware)

# 4.6 CSRF protection (double-submit cookie) for cookie-based auth
if os.environ.get("CSRF_ENABLED", "false").lower() == "true":
    app.add_middleware(CSRFMiddleware)

# 5. CORS estricto
_cors_origins = []
if settings.FRONTEND_URL:
    _cors_origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()]
if settings.ENVIRONMENT == "development":
    _cors_origins.extend(["http://localhost:3000", "http://localhost:3001"])
if not _cors_origins:
    _cors_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-CSRF-Token"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(businesses.router, prefix="/api/v1/businesses", tags=["businesses"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
app.include_router(channels.router, prefix="/api/v1/businesses", tags=["channels"])
app.include_router(conversations.router, prefix="/api/v1/businesses", tags=["conversations"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(assistant_router.router, prefix="/api/v1/assistant", tags=["assistant"])
app.include_router(automations.router, prefix="/api/v1/automations", tags=["automations"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(crm_router, prefix="/api/v1", tags=["crm"])
app.include_router(orders_router, prefix="/api/v1", tags=["orders"])
app.include_router(alerts_router, prefix="/api/v1", tags=["alerts"])
app.include_router(provisioning_router, prefix="/api/v1", tags=["provisioning"])
app.include_router(diagnostics_router, prefix="/api/v1", tags=["diagnostics"])
app.include_router(synthetic_router, prefix="/api/v1", tags=["synthetic"])
app.include_router(feature_flags_router, prefix="/api/v1", tags=["feature-flags"])
app.include_router(consumo_router, prefix="/api/v1", tags=["consumo"])
app.include_router(competitive_router, prefix="/api/v1", tags=["competitive"])
app.include_router(competitive_intelligence_router, prefix="/api/v1", tags=["competitive"])
app.include_router(marketplace_router, prefix="/api/v1", tags=["marketplace"])
app.include_router(fomo_router, prefix="/api/v1", tags=["fomo"])
app.include_router(social_growth_router, prefix="/api/v1", tags=["social-growth"])
app.include_router(referrals_router, prefix="/api/v1", tags=["referrals"])
app.include_router(coupons_router, prefix="/api/v1", tags=["coupons"])
app.include_router(nps_router, prefix="/api/v1", tags=["feedback"])
app.include_router(tours_router, prefix="/api/v1", tags=["tours"])
app.include_router(webhooks_router, prefix="/api/v1", tags=["webhooks"])
app.include_router(memory_router, prefix="/api/v1", tags=["memory"])
app.include_router(outcomes_router, prefix="/api/v1", tags=["outcomes"])
app.include_router(swarm_router, prefix="/api/v1/swarm", tags=["swarm"])
app.include_router(intelligence_router, prefix="/api/v1", tags=["intelligence"])
app.include_router(scoring_router, prefix="/api/v1", tags=["deals"])
app.include_router(reflection_router, prefix="/api/v1", tags=["reflection"])
app.include_router(causal_router, prefix="/api/v1", tags=["causal"])
app.include_router(ab_router, prefix="/api/v1", tags=["ab-testing"])
app.include_router(brain_router.router, prefix="/api/v1", tags=["brain"])
app.include_router(market_analyst_router, prefix="/api/v1/agents", tags=["market-analyst"])
app.include_router(financial_planner_router, prefix="/api/v1/agents", tags=["financial-planner"])
app.include_router(acquisition_strategist_router, prefix="/api/v1/agents", tags=["acquisition-strategist"])
app.include_router(landing_builder_router, prefix="/api/v1/agents", tags=["landing-builder"])
app.include_router(app_builder_router, prefix="/api/v1/agents", tags=["app-builder"])
app.include_router(crm_builder_router, prefix="/api/v1/agents", tags=["crm-builder"])
app.include_router(ad_copywriter_router, prefix="/api/v1/agents", tags=["ad-copywriter"])
app.include_router(investor_pitch_router, prefix="/api/v1/agents", tags=["investor-pitch"])
app.include_router(kpi_architect_router, prefix="/api/v1/agents", tags=["kpi-architect"])
app.include_router(customer_service_router, prefix="/api/v1/agents", tags=["customer-service"])
app.include_router(lead_qualifier_router, prefix="/api/v1/agents", tags=["lead-qualifier"])
app.include_router(auto_responder_router, prefix="/api/v1/agents", tags=["auto-responder"])

from app.api.v1.social_content import router as social_content_router
app.include_router(social_content_router, prefix="/api/v1", tags=["social-content"])
app.include_router(selfservice_router.router, prefix="/api/v1", tags=["selfservice"])
app.include_router(admin_router.router, prefix="/api/v1", tags=["admin"])
app.include_router(missions_router.router, prefix="/api/v1", tags=["missions"])
app.include_router(business_context_router, prefix="/api/v1", tags=["business-context"])
app.include_router(credentials_router, prefix="/api/v1", tags=["credentials"])
app.include_router(mission_ws_router)
app.include_router(computer_use_router.router, prefix="/api/v1/computer-use", tags=["computer-use"])
app.include_router(computer_use_extended_router.router, prefix="/api/v1/computer-use", tags=["computer-use-extended"])
app.include_router(computer_use_brain_router.router, prefix="/api/v1/computer-use", tags=["computer-use-brain"])
app.include_router(computer_use_audit_log_router.router, prefix="/api/v1/computer-use", tags=["computer-use-audit"])
app.include_router(computer_use_lead_scoring_router.router, prefix="/api/v1/computer-use", tags=["lead-scoring"])
app.include_router(computer_use_ad_orchestrator_router.router, prefix="/api/v1/computer-use", tags=["ad-orchestrator"])
app.include_router(computer_use_task_scheduler_router.router, prefix="/api/v1/computer-use", tags=["task-scheduler"])
app.include_router(sales_funnel_router.router, prefix="/api/v1", tags=["sales-funnel"])
app.include_router(brain_ws_router.router, prefix="/api/v1", tags=["websocket"])
app.include_router(computer_use_webhooks_router.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(trade_signals_router.router, prefix="/api/v1/computer-use", tags=["copy-trade"])
app.include_router(onboarding_router.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(training_router, prefix="/api/v1", tags=["training"])
app.include_router(tracking.router, prefix="/api/v1", tags=["tracking"])
app.include_router(shipments.router, prefix="/api/v1/shipments", tags=["shipments"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
if upload:
    app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
if security_router:
    app.include_router(security_router.router, prefix="/api/v1/security", tags=["security"])

try:
    from app.domains.support.router import router as support_router
    app.include_router(support_router, prefix="/api/v1", tags=["support"])
except ImportError:
    pass

try:
    from app.domains.objectives.router import router as objectives_router
    app.include_router(objectives_router, prefix="/api/v1", tags=["objectives"])
except ImportError:
    pass
try:
    from app.domains.retention.router import router as retention_router
    app.include_router(retention_router, prefix="/api/v1", tags=["retention"])
except ImportError:
    pass
try:
    from app.domains.bi.router import router as bi_router
    app.include_router(bi_router, prefix="/api/v1", tags=["bi"])
except ImportError:
    pass
try:
    from app.domains.finance.router import router as finance_router
    app.include_router(finance_router, prefix="/api/v1", tags=["finance"])
except ImportError:
    pass
try:
    from app.domains.feedback.router import router as feedback_router
    app.include_router(feedback_router, prefix="/api/v1", tags=["feedback"])
except ImportError:
    pass
try:
    from app.domains.autopilot.router import router as autopilot_router
    app.include_router(autopilot_router, prefix="/api/v1", tags=["autopilot"])
except ImportError:
    pass
try:
    from app.domains.documents.router import router as documents_router
    app.include_router(documents_router, prefix="/api/v1", tags=["documents"])
except ImportError:
    pass
try:
    from app.domains.outreach.router import router as outreach_router
    app.include_router(outreach_router, prefix="/api/v1", tags=["outreach"])
except ImportError:
    pass
try:
    from app.domains.proactive.router import router as proactive_router
    app.include_router(proactive_router, prefix="/api/v1", tags=["proactive"])
except ImportError:
    pass
try:
    from app.domains.intelligence.router import router as intelligence_router
    app.include_router(intelligence_router, prefix="/api/v1", tags=["intelligence"])
except ImportError:
    pass
try:
    from app.domains.growth.router import router as growth_router
    app.include_router(growth_router, prefix="/api/v1", tags=["growth"])
except ImportError:
    pass
try:
    from app.domains.voice.router import router as voice_router
    app.include_router(voice_router, prefix="/api/v1", tags=["voice"])
except ImportError:
    pass
try:
    from app.domains.agents.music_agent.router import router as music_agent_router
    app.include_router(music_agent_router, prefix="/api/v1", tags=["music-agent"])
except ImportError:
    pass
try:
    from app.domains.agents.brand_visual.router import router as brand_visual_router
    app.include_router(brand_visual_router, prefix="/api/v1", tags=["brand-visual"])
except ImportError:
    pass
try:
    from app.domains.agents.viral_video.router import router as viral_video_router
    app.include_router(viral_video_router, prefix="/api/v1", tags=["viral-video"])
except ImportError:
    pass
try:
    from app.domains.gamification.router import router as gamification_router
    app.include_router(gamification_router, prefix="/api/v1", tags=["gamification"])
except ImportError:
    pass
try:
    from app.domains.social_sellers.router import router as social_sellers_router
    app.include_router(social_sellers_router, prefix="/api/v1", tags=["social-sellers"])
except ImportError:
    pass
try:
    from app.domains.gamification.ambassador_router import router as ambassador_router
    app.include_router(ambassador_router, prefix="/api/v1", tags=["ambassador"])
except ImportError:
    pass

try:
    from app.domains.simulation.router import router as simulation_router
    app.include_router(simulation_router, prefix="/api/v1", tags=["simulations"])
except ImportError:
    pass

try:
    from app.domains.voice.router import router as voice_router
    app.include_router(voice_router, prefix="/api/v1", tags=["voice"])
except ImportError:
    pass


from fastapi import Depends
from app.core.deps import get_current_user

@app.get("/api/ping", tags=["health"])
async def ping():
    return {"status": "ok"}


@app.get("/health", tags=["health"])
async def health_check():
    """Health check profundo: verifica DB, Redis y Celery worker."""
    from sqlalchemy import text
    import redis.asyncio as redis
    from app.tasks.celery_app import celery_app

    checks = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 1. Database
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        checks["status"] = "degraded"

    # 2. Redis
    try:
        r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await r.ping()
        await r.close()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
        checks["status"] = "degraded"

    # 3. Celery worker (inspect active workers)
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        inspect_result = await loop.run_in_executor(None, celery_app.control.inspect().active)
        if inspect_result:
            checks["celery"] = "ok"
        else:
            checks["celery"] = "warning"
            checks["status"] = "degraded"
    except Exception:
        checks["celery"] = "error"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "ok" else 503
    return JSONResponse(content=checks, status_code=status_code)


@app.get("/api/v1/auth/security-status", tags=["security"])
async def security_status(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint para que el frontend consulte el estado de seguridad del cliente.
    Detecta VPN, Tor, MITM, Cloudflare y da recomendaciones al usuario sobre su antivirus/VPN.
    """
    raw_ip = request.client.host if request.client else "unknown"
    client_ip = request.state.client_ip
    user_agent = request.headers.get("user-agent")
    headers = dict(request.headers)

    risk = assess_client_risk(
        ip=client_ip,
        headers=headers,
        user_agent=user_agent,
    )
    fingerprint = device_fingerprint(client_ip, user_agent, request.headers.get("accept-language"))
    cf_info = get_cloudflare_info(headers)
    cf_valid, cf_msg = validate_cloudflare_origin(raw_ip, headers)

    return JSONResponse(
        content={
            "secure_connection": request.url.scheme == "https",
            "risk_score": risk["score"],
            "is_vpn": risk["is_vpn"],
            "is_tor": risk["is_tor"],
            "mitm_detected": risk["mitm_detected"],
            "mitm_headers": risk["mitm_headers"],
            "malicious_ua": risk["malicious_ua"],
            "recommendations": risk["recommendations"],
            "device_fingerprint": fingerprint,
            "cloudflare": {
                "is_cloudflare": cf_info["is_cloudflare"],
                "cf_ray": cf_info["cf_ray"],
                "cf_country": cf_info["cf_country"],
                "cf_valid_origin": cf_valid,
                "cf_message": cf_msg,
                "is_high_risk_country": cf_info["is_high_risk_country"],
            },
            "tips": [
                "Asegurate de tener un antivirus actualizado y activo.",
                "Usa una VPN confiable solo cuando sea necesario; algunas VPN gratuitas interceptan trafico.",
                "Verifica que la URL comience con https:// y el candado este verde.",
                "Si tu antivirus detecta algo en este sitio, reportalo y no ignores la alerta.",
            ],
        }
    )


@app.get("/api/v1/auth/cloudflare-config", tags=["security"])
async def cloudflare_config(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint para verificar la configuración de Cloudflare.
    Devuelve los rangos IP de Cloudflare que deben estar en whitelist del firewall.
    """
    from app.core.cloudflare import CLOUDFLARE_IPV4_RANGES, CLOUDFLARE_IPV6_RANGES

    raw_ip = request.client.host if request.client else "unknown"
    headers = dict(request.headers)
    cf_valid, cf_msg = validate_cloudflare_origin(raw_ip, headers)

    return {
        "cloudflare_enabled": "cf-ray" in headers,
        "request_from_cloudflare": cf_valid,
        "message": cf_msg,
        "client_ip": request.state.client_ip,
        "cloudflare_ipv4_ranges": [str(r) for r in CLOUDFLARE_IPV4_RANGES],
        "cloudflare_ipv6_ranges": [str(r) for r in CLOUDFLARE_IPV6_RANGES],
        "instructions": [
            "1. Configura tu DNS para que apunte a Cloudflare",
            "2. Activa 'Always Use HTTPS' en el panel de Cloudflare",
            "3. Habilita 'Bot Fight Mode' o 'Super Bot Fight Mode'",
            "4. Configura 'Authenticated Origin Pulls' para validar certificados mTLS",
            "5. Agrega reglas de firewall en Cloudflare para bloquear paises de alto riesgo",
            "6. En el panel de Cloudflare, activa 'Under Attack Mode' si recibes DDoS",
        ],
    }
