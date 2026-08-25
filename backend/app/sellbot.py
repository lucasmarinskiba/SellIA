"""
SellIA Sellbot - Email Delivery + PostgreSQL Persistence
Endpoints:
- POST /api/v1/webhooks/whatsapp (Meta webhook)
- POST /api/v1/webhooks/sendgrid (Email tracking)
- POST /api/v1/sequences/cold-email (Email generation)
- POST /api/v1/knowledge/ingest (PDF knowledge)
- GET /api/ping (Health check)
- /api/v1/leads/* (Lead management + scoring)
- /api/v1/workflows/* (Email automation)
- /api/v1/lead-sources/* (Prospecting)
"""
import os
import logging
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from collections import defaultdict
from datetime import datetime, timedelta

# Import routers
from app.api.v1 import leads as leads_module
from app.api.v1 import workflows as workflows_module
from app.api.v1 import lead_sources as lead_sources_module
from app.api.v1 import email_webhooks as email_webhooks_module
from app.api.v1 import progression as progression_module
from app.api.v1 import analytics as analytics_module
from app.api.v1 import attribution as attribution_module
from app.api.v1 import journeys as journeys_module
from app.api.v1 import compliance as compliance_module
from app.api.v1 import integrations as integrations_module
from app.api.v1 import sales_agents as sales_agents_module
from app.api.v1 import neural_networks as neural_networks_module
from app.api.v1 import sales_automation as sales_automation_module
from app.api.v1 import deal_intelligence as deal_intelligence_module
from app.api.v1 import sales_coaching as sales_coaching_module
from app.api.v1 import crm_collaboration as crm_collaboration_module
from app.api.v1 import sales_funnel_orchestration as sales_funnel_orchestration_module
from app.api.v1 import marketing_intelligence as marketing_intelligence_module
from app.api.v1 import accounting_intelligence as accounting_intelligence_module
from app.api.v1 import sales_operations as sales_operations_module

# Phase X6: FOMO Dynamics (Ultra-Potent Psychology Engine)
from app.domains.fomo_dynamics import router as fomo_dynamics_router

# Phase X7: Perception Engineering (Psychology-Driven Sales Agent)
from app.domains.perception_engineering import router as perception_engineering_router

# Phase X8: Auto-Marketing & Growth (SellIA Self-Promotion)
from app.domains.auto_marketing import router as auto_marketing_router

# Phase X9: AI User Intelligence (Deep Profiling)
from app.domains.user_intelligence import router as user_intelligence_router

# Phase X10: FOMO Generation (Personalized Scarcity)
from app.domains.fomo_generation import router as fomo_generation_router

# Phase X11: Loyalty & Retention (VIP Program)
from app.domains.loyalty_engine import router as loyalty_engine_router

# Phase X12: Conversion & Attraction (Multi-touch Closing)
from app.domains.conversion_engine import router as conversion_engine_router

# Acquisition Orchestrator (X9→X10→X12→X11 Integration)
from app.domains.acquisition_orchestrator import router as acquisition_orchestrator_router

# Instagram Automation (@sell_.ia + FeedIA synergy)
from app.domains.instagram_automation import router as instagram_automation_router

# Feedback Loop (Conversion data → X9 improvements)
from app.domains.feedback_loop import router as feedback_loop_router

# FOMO Intelligence (Escasez real / Prueba social / Exclusividad / Transparencia)
from app.domains.fomo_intelligence import router as fomo_intelligence_router

# ARCA Compliance (CUIT, Monotributo, INCOTERMS, NCM — datos reales)
from app.domains.arca_compliance import router as arca_compliance_router

# Business model: se importa explícito porque ChannelConnection.business usa
# relationship("Business") (string) - SQLAlchemy necesita la clase ya cargada
# en el registry antes de configurar mappers, y ningún import previo la traía.
from app.domains.businesses.models import Business

# Location model: Phase 5A location profiles — must be imported before SQLAlchemy mapper config
from app.domains.businesses.location_models import Location

# Nota: api.v1.channels ya se registra en app.main (_try_include, prefix
# /api/v1/businesses) — no duplicar acá.

# Platforms Integration (TikTok Shop real; resto queda como TODO histórico)
from app.api.v1.platforms_integration import router as platforms_integration_router

from app.domains.performance_optimization.models import PerformanceMetrics, SlowQuery, IndexRecommendation, CacheStrategy, QueryOptimization
from app.domains.channel_integration.models import GoogleBusinessProfileConnection, GoogleMapsLocation, LocationMessage, LocationMessageExecution, LocationReview
from app.domains.ai_content_generation.models import ContentTemplate, GeneratedContent, ContentPerformance, BulkContentGeneration, ContentVariant

# Database
from app.db import init_db, close_db, get_db

# Scheduler
from app.core.scheduler import get_scheduler
from app.core.task_processor import init_processor, start_processor, stop_processor, get_processor_stats

# Progression
from app.services.progression_service import init_progression_service

scheduler = None
processor = None
progression_service = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# STARTUP/SHUTDOWN
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global scheduler, processor, progression_service
    logger.info("🚀 SellIA Sellbot starting...")

    await init_db()
    logger.info("✅ Database initialized")

    # Migrate schema for 2FA columns
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(32)"))
            await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_2fa_enabled BOOLEAN DEFAULT false"))
            await db.commit()
        logger.info("✅ 2FA schema migrated")
    except Exception as e:
        logger.warning(f"2FA schema migration: {str(e)[:80]}")

    # Load Phase 33 seed data if needed (async-compatible)
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import os
        from app.db.seed_phase_33 import seed_phase_33

        # Get sync engine from DATABASE_URL
        db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://").replace("postgresql://", "postgresql+psycopg2://")
        if db_url:
            sync_engine = create_engine(db_url, connect_args={"connect_timeout": 5})
            SessionLocal = sessionmaker(bind=sync_engine)
            db = SessionLocal()
            try:
                result = seed_phase_33(db)
                if result["status"] == "success":
                    logger.info(f"✅ Phase 33 seed loaded: {result['products_created']} products, {result['listings_created']} listings, ${result['total_gmv_monthly']:,}/mo GMV")
                elif result["status"] == "skipped":
                    logger.debug(f"Phase 33 seed: {result['reason']}")
                else:
                    logger.warning(f"Phase 33 seed error: {result.get('error', 'unknown')}")
            finally:
                db.close()
    except Exception as e:
        logger.debug(f"Phase 33 seed unavailable: {e}")

    scheduler = await get_scheduler()
    logger.info("✅ Redis scheduler connected")

    if scheduler and scheduler.redis:
        try:
            from fastapi_limiter import FastAPILimiter
            await FastAPILimiter.init(scheduler.redis)
            logger.info("✅ FastAPILimiter initialized")
        except Exception as e:
            logger.warning(f"FastAPILimiter init skipped: {e}")
    else:
        logger.warning("⚠️ Redis unavailable — rate-limited endpoints (auth) will fail")

    processor = await init_processor(scheduler)
    logger.info("✅ Task processor initialized")

    progression_service = await init_progression_service(scheduler)
    logger.info("✅ Progression service initialized")

    # Start processor in background
    try:
        asyncio.create_task(start_processor())
        logger.info("✅ Task processor started")
    except Exception as e:
        logger.warning(f"Processor background start warning: {e}")

    yield

    # Shutdown
    logger.info("🛑 SellIA Sellbot shutting down...")
    await stop_processor()
    await close_db()
    if scheduler:
        await scheduler.close()
    logger.info("✅ All services closed")

app = FastAPI(
    title="SellIA Sellbot",
    version="1.0.0",
    lifespan=lifespan
)

allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://sellia-brain.vercel.app").split(",")]

# Rate limiter (simple in-memory)
class RateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.rpm = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        # Clean old requests
        self.requests[ip] = [t for t in self.requests[ip] if t > minute_ago]
        if len(self.requests[ip]) >= self.rpm:
            return False
        self.requests[ip].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=100)

# Logging middleware (structured)
@app.middleware("http")
async def log_request(request: Request, call_next):
    import time
    from app.middleware.threat_intel import get_client_ip
    start_time = time.time()
    client_ip = get_client_ip(request)
    request.state.client_ip = client_ip

    # Rate limit check
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded: {client_ip} {request.method} {request.url.path}")
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

    response = await call_next(request)
    process_time = time.time() - start_time

    # Structured log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "client_ip": client_ip,
        "process_time_ms": round(process_time * 1000, 2)
    }
    logger.info(f"API | {log_entry}")

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Registrar routers
# v1 routes (current stable) — each wrapped so a single broken router
# (missing dependency, bad import) can never take the whole app down.
def _register(router_module, name: str) -> None:
    try:
        app.include_router(router_module.router)
        logger.info(f"✅ {name} router registered")
    except Exception as e:
        logger.error(f"❌ Failed to register {name} router: {e}", exc_info=True)

_register(leads_module, "leads")
_register(workflows_module, "workflows")
_register(lead_sources_module, "lead_sources")
_register(email_webhooks_module, "email_webhooks")
_register(progression_module, "progression")
_register(analytics_module, "analytics")
_register(attribution_module, "attribution")
_register(journeys_module, "journeys")
_register(compliance_module, "compliance")
_register(integrations_module, "integrations")
_register(sales_agents_module, "sales_agents")
_register(neural_networks_module, "neural_networks")
_register(sales_automation_module, "sales_automation")
_register(deal_intelligence_module, "deal_intelligence")
_register(sales_coaching_module, "sales_coaching")
_register(crm_collaboration_module, "crm_collaboration")
_register(sales_funnel_orchestration_module, "sales_funnel_orchestration")
_register(marketing_intelligence_module, "marketing_intelligence")
_register(accounting_intelligence_module, "accounting_intelligence")
_register(sales_operations_module, "sales_operations")

# Domain routers (Phase 2-5: Backend Intelligence)
def _register_domain_router(router_obj, name: str) -> None:
    try:
        app.include_router(router_obj)
        logger.info(f"✅ {name} router registered")
    except Exception as e:
        logger.error(f"❌ Failed to register {name} router: {e}", exc_info=True)

# Phase X6: FOMO Dynamics (Ultra-Potent Psychology Engine)
_register_domain_router(fomo_dynamics_router, "fomo_dynamics")

# Phase X7: Perception Engineering (Psychology-Driven Sales Agent)
_register_domain_router(perception_engineering_router, "perception_engineering")

# Phase X8: Auto-Marketing & Growth (SellIA Self-Promotion)
_register_domain_router(auto_marketing_router, "auto_marketing")

# Phase X9: AI User Intelligence (Deep Profiling)
_register_domain_router(user_intelligence_router, "user_intelligence")

# Phase X10: FOMO Generation (Personalized Scarcity)
_register_domain_router(fomo_generation_router, "fomo_generation")

# Phase X11: Loyalty & Retention (VIP Program)
_register_domain_router(loyalty_engine_router, "loyalty_engine")

# Phase X12: Conversion & Attraction (Multi-touch Closing)
_register_domain_router(conversion_engine_router, "conversion_engine")

# Acquisition Orchestrator (X9→X10→X12→X11 Integration)
_register_domain_router(acquisition_orchestrator_router, "acquisition_orchestrator")

# Instagram Automation (@sell_.ia + FeedIA synergy)
_register_domain_router(instagram_automation_router, "instagram_automation")

# Feedback Loop (Conversion data → X9 improvements)
_register_domain_router(feedback_loop_router, "feedback_loop")

# FOMO Intelligence (Escasez real / Prueba social / Exclusividad / Transparencia)
_register_domain_router(fomo_intelligence_router, "fomo_intelligence")

# ARCA Compliance (CUIT, Monotributo, INCOTERMS, NCM — datos reales)
_register_domain_router(arca_compliance_router, "arca_compliance")

# Platforms Integration (TikTok Shop real; resto queda como TODO histórico)
_register_domain_router(platforms_integration_router, "platforms_integration")

# Legacy redirect (v1 is default)
@app.get("/api/version", tags=["system"])
async def get_version():
    return {
        "version": "1.0.0",
        "status": "stable",
        "deprecation": None,
        "next_version": "2.0.0 (planned Q3 2024)"
    }

# ============================================================
# SALES SYSTEM PROMPT - 34 libros integrados
# ============================================================
SALES_SYSTEM_PROMPT = """Eres SellIA, un agente de ventas de IA con maestría en 34 libros de psicología de ventas, negocios y marketing.

### MARCOS DE REFERENCIA INTEGRADOS:

**PROSPECTING & COLD OUTREACH:**
- Efti (Cold Email): subject lines con curiosidad, personalización profunda, valor primero, social proof, CTA simple
- LinkedIn B2B (Konrath): decision makers, pain points, multi-threading, account-based selling

**SALES METHODOLOGY:**
- SPIN Selling (Rackham): Situation, Problem, Implication, Need-Payoff questions
- 10X Mindset (Cardone): Audacia, volumen, presión positiva, cierre agresivo pero ético
- Closing (Ziglar): 7 técnicas de cierre, manejar objeciones con empatía

**PSYCHOLOGY & INFLUENCE:**
- 7 Principios Cialdini: Reciprocidad, Compromiso, Prueba Social, Autoridad, Simpatía, Escasez, Urgencia
- Pre-suasión (Cialdini): Framing antes de pitch
- Irracionalidad (Ariely): Anclaje, relatividad, costo hundido
- Empatía (Carnegie): Escuchar, validar, conexión humana

**POSITIONING & DIFERENCIACIÓN:**
- Purple Cow (Godin): Ser notable, diferente, memorable
- Monopoly (Thiel): Crear categoría única, defensible
- Expert Secrets (Brunson): Posicionarse como authority, storytelling

**OFFER DESIGN & PRICING:**
- Offer Design (Hormozi): Value equation, stack, bonuses, urgency real
- Pricing Psychology (Poundstone): Anclajes, decoys, paquetes
- Direct Response (Kennedy): ROI focus, 80/20 rule, metricas

**FUNNELS & CONVERSION:**
- Funnel Hacking (Brunson): Squeeze page, sales page, order form, thank you page
- A/B Testing: Headlines, copy, calls to action
- Conversion Optimization (Saleh): Scarcity, social proof, testimonials

**RETENTION & EXPANSION:**
- NPS & Retention (Reichheld): Proactive engagement, loyalty loops
- Tiny Habits (Fogg): Behavior change, sticky features
- Customer Success (Mehta): Health scores, proactive outreach, upsell sequences

**NEGOTIATION:**
- Getting to Yes (Fisher): Win-win, BATNA, options generation
- Never Split the Difference (Voss): Mirroring, labels, tactical empathy

### TU COMPORTAMIENTO:

1. **Prospecting**: Busca pain points, propón soluciones claras, crea urgencia real
2. **Sales**: SPIN questions → descubre need → presenta offer con ROI visible
3. **Objeciones**: Reframe, social proof, alternative close, urgencia limitada
4. **Retention**: Onboarding rápido, health score check-in, cross-sell/upsell
5. **Analytics**: Pensa en métricas (conversion, CAC, LTV, churn), 80/20

### TONO:
- Audaz pero profesional
- Directo sin ser grosero
- ROI-focused
- Data-driven cuando sea posible
- Empatico pero orientado a resultados
"""

# ============================================================
# MODELOS
# ============================================================
class LeadProfile(BaseModel):
    name: str
    email: str
    company: str
    title: str
    pain_point: str
    industry: str

class EmailSequenceRequest(BaseModel):
    lead: LeadProfile
    offer: str
    sender_name: str = "SellIA"
    sender_email: str

class KnowledgeIngestRequest(BaseModel):
    content: str
    source: str

# ============================================================
# FUNCIONES CORE
# ============================================================
async def call_anthropic_api(system_prompt: str, user_message: str, retries: int = 3) -> str:
    """Llama a Claude API con retry logic."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    last_error = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 2048,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_message}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                if not data.get("content") or not isinstance(data["content"], list) or len(data["content"]) == 0:
                    raise ValueError(f"Invalid Anthropic response structure: {data}")
                return data["content"][0]["text"]
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:  # Retry only 5xx errors
                last_error = e
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            raise HTTPException(status_code=e.response.status_code, detail=str(e))

    raise HTTPException(status_code=503, detail=f"Anthropic API unavailable after {retries} attempts: {last_error}")

async def send_whatsapp_message(to: str, text: str, phone_number_id: str, token: str) -> dict:
    """Envía mensaje vía WhatsApp Graph API."""
    url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params={"access_token": token},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"body": text},
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error(f"WhatsApp API timeout for {to}")
        raise
    except httpx.HTTPError as e:
        logger.error(f"WhatsApp API error for {to}: {e}")
        raise

# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
async def root():
    return RedirectResponse(url="/api/ping")

@app.get("/api/ping")
async def ping():
    """Simple health check."""
    return {"status": "ok", "service": "SellIA Sellbot", "timestamp": datetime.now().isoformat()}

@app.get("/api/health", tags=["system"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency status."""
    try:
        # Check database
        await db.execute(select(1))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "failed"

    # Check Redis
    try:
        if processor and processor.scheduler and processor.scheduler.redis:
            await processor.scheduler.redis.ping()
            redis_status = "ok"
        else:
            redis_status = "fallback"  # In-memory mode
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "failed"

    # Check processor
    try:
        processor_running = processor and processor.running
        processor_status = "ok" if processor_running else "stopped"
    except Exception as e:
        logger.error(f"Processor health check failed: {e}")
        processor_status = "failed"

    overall = "ok" if db_status == "ok" and processor_status == "ok" else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "redis": redis_status,
            "processor": processor_status,
            "scheduler": "ok" if scheduler else "not_initialized"
        },
        "uptime_seconds": 0  # TODO: track from startup
    }

@app.get("/api/queue/dlq", tags=["monitoring"])
async def get_dead_letter_queue():
    """Get tasks that failed permanently (DLQ)."""
    try:
        if not scheduler or not scheduler.redis:
            return {"status": "not_available", "dlq_size": 0}

        dlq_size = await scheduler.redis.llen("sellia:dead-letter")
        dlq_tasks = await scheduler.redis.lrange("sellia:dead-letter", 0, 10)  # Last 10

        return {
            "status": "ok",
            "dlq_size": dlq_size,
            "recent_tasks": [json.loads(t) if isinstance(t, str) else t for t in dlq_tasks],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"DLQ query failed: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/api/v1/queue/stats")
async def queue_stats():
    """Get email queue statistics."""
    try:
        stats = await get_processor_stats()
        return {
            "status": "ok",
            "queue": stats
        }
    except Exception as e:
        logger.error(f"Queue stats error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/api/v1/queue/peek")
async def queue_peek(count: int = 5):
    """Peek at queue (non-destructive)."""
    global scheduler
    if not scheduler:
        return {"status": "error", "detail": "Scheduler not initialized"}

    try:
        tasks = await scheduler.peek_queue(count)
        return {
            "status": "ok",
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        logger.error(f"Queue peek error: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/api/v1/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """Meta WhatsApp webhook - recibe y responde mensajes."""
    try:
        body = await request.json()

        # Meta verifica webhook con GET
        if request.method == "GET":
            token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
            verify_token = request.query_params.get("hub.verify_token", "")
            if verify_token == token:
                return int(request.query_params.get("hub.challenge", 0))
            return JSONResponse({"error": "Invalid token"}, status_code=403)

        # Procesa mensaje entrante
        messages = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
        if not messages:
            return JSONResponse({"status": "ok"})

        message = messages[0]
        from_number = message.get("from")
        message_text = message.get("text", {}).get("body", "")

        if not message_text:
            return JSONResponse({"status": "ok"})

        # Genera respuesta con IA
        response_text = await call_anthropic_api(
            system_prompt=SALES_SYSTEM_PROMPT,
            user_message=f"Cliente: {message_text}\n\nResponde como agente de ventas SellIA.",
        )

        # Envía respuesta
        phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "")
        token = os.getenv("META_WHATSAPP_TOKEN", "")
        if phone_number_id and token:
            await send_whatsapp_message(from_number, response_text, phone_number_id, token)

        return JSONResponse({"status": "ok", "response_sent": True})
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

@app.post("/api/v1/sequences/cold-email")
async def generate_cold_email_sequence(req: EmailSequenceRequest):
    """Genera secuencia de 5 emails (Efti + Kennedy frameworks)."""
    try:
        prompt = f"""Genera una secuencia de 5 emails de prospecting para:

LEAD:
- Nombre: {req.lead.name}
- Email: {req.lead.email}
- Empresa: {req.lead.company}
- Título: {req.lead.title}
- Pain point: {req.lead.pain_point}
- Industria: {req.lead.industry}

OFFER: {req.offer}

Usa Efti (cold email) + Kennedy (80/20 ROI).
Retorna JSON array: [{"day": 1, "subject": "...", "body": "..."}, ...]
SOLO JSON, sin markdown."""

        response_json = await call_anthropic_api(
            system_prompt="Eres un copywriter experto. Devuelve SOLO JSON válido.",
            user_message=prompt,
        )

        emails = json.loads(response_json)
        return {
            "sequence_id": f"seq_{req.lead.email}",
            "lead": req.lead,
            "emails": emails,
            "status": "generated",
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse email sequence JSON")
    except Exception as e:
        logger.error(f"Email sequence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/knowledge/ingest")
async def ingest_knowledge(req: KnowledgeIngestRequest):
    """Ingesta PDFs/conocimientos para mejorar system prompt (v1: solo logging)."""
    try:
        # v1: Solo registra. v2: Mejorar system prompt dinámicamente
        logger.info(f"Knowledge ingested from {req.source}: {len(req.content)} chars")
        return {
            "status": "ingested",
            "source": req.source,
            "size": len(req.content),
            "message": "Knowledge received. System will be enhanced in v2.",
        }
    except Exception as e:
        logger.error(f"Knowledge ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
