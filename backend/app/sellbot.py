"""
SellIA Sellbot - Minimalista, sin DB, sin Redis, sin dependencias complejas.
Endpoints:
- POST /api/v1/webhooks/whatsapp (Meta webhook)
- POST /api/v1/sequences/cold-email (Email generation)
- POST /api/v1/knowledge/ingest (PDF knowledge)
- GET /api/ping (Health check)
"""
import os
import logging
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SellIA Sellbot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def call_anthropic_api(system_prompt: str, user_message: str) -> str:
    """Llama a Claude API directamente."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

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
        return data["content"][0]["text"]

async def send_whatsapp_message(to: str, text: str, phone_number_id: str, token: str) -> dict:
    """Envía mensaje vía WhatsApp Graph API."""
    url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    async with httpx.AsyncClient() as client:
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
        return response.json()

# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
async def root():
    return RedirectResponse(url="/api/ping")

@app.get("/api/ping")
async def ping():
    """Health check."""
    return {"status": "ok", "service": "SellIA Sellbot"}

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
