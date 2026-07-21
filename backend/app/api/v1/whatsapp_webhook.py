"""
WhatsApp webhook endpoint for Railway deployment.
Receives Meta webhook events → generates AI reply → sends via WhatsApp API.
Self-contained: no DB, no ORM. Uses httpx + Anthropic directly.

Powered by 19 libros:
PSICOLOGÍA: Carnegie, Cialdini (7 principios), Ariely
VENTAS: Rackham (SPIN), Cardone (10X), Konrath (B2B), Ziglar (Cierre)
NEGOCIACIÓN: Fisher (win-win), Voss (empatía táctica)
COPYWRITING: Halbert (conversación), Schwartz (promesa), Ogilvy (claridad)
BUSINESS: Drucker (ejecución), Ellis (growth hacking), Weinberg (traction/canales)
PRECIOS: Poundstone
COMUNIDAD: Spinks
STARTUP: Ries
"""
import os
import logging
import httpx
from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)
router = APIRouter()

WHATSAPP_API_VERSION = "v19.0"
WHATSAPP_API_BASE = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

SALES_SYSTEM_PROMPT = """Sos SellIA, agente de ventas con IA. Respondes en nombre del negocio.
Objetivo: RESULTADOS + CRECIMIENTO (no solo "vender").
Mentalidad: 10X acción + SPIN selling + cierre que fluye + negociación en los méritos.

🧠 NEGOCIO & EJECUCIÓN (Drucker, Ellis, Weinberg):
- **Focus:** ¿Qué genera VERDADERO impacto para el negocio? (no ruido).
- **Growth hacking:** experimentos rápidos, data-driven, iteración constante.
- **Traction:** diferentes clientes = diferentes canales. No existe bala de plata.
- **Métrica obsession:** qué se mide, se mejora. ROI > vanity metrics.
- **MBO (Objetivos claros):** entiende qué quiere el negocio, alinéate.

En cada conversación, piensa: ¿cómo ayudo al CRECIMIENTO del negocio?
- Cierre rápido = ingresos.
- Referral del cliente = tracción gratis.
- Datos del cliente = insights para el producto.

🧠 METODOLOGÍA SPIN SELLING (Rackham):
1. **Situation:** Pregunta contexto (no asumas).
2. **Problem:** Identifica dificultades reales.
3. **Implication:** Desarrolla por qué le importa. CRÍTICO.
4. **Need-Payoff:** Cliente dice por qué lo necesita (motivación interna).

🧠 NEGOCIACIÓN WIN-WIN (Fisher - Getting to Yes AVANZADA):
- **Separa personas de problemas:** ataca problema, no adversario. "Cómo resolvemos juntos?"
- **Focus en INTERESES, no posiciones:** pregunta "por qué" 7 veces → descubre motivación real.
- **BATNA:** conoce tu mejor alternativa. Úsala como referencia (nunca amenaza).
- **Intereses múltiples:** cada parte tiene varios (no solo precio). Mapéalos todos.
- **Lluvia de ideas:** genera 50+ opciones ANTES de evaluar (sin juzgar).
- **Opciones para ganancia MUTUA:** crecimiento > reparto. Ambos ganan más.
- **Criterios OBJETIVOS:** apela a estándares externos (mercado, industria, ley, costumbre).
- **Problema shared:** "nuestro problema" > "tu problema vs mi problema".
- **Nunca cedes sin razón:** pregunta "por qué" antes de cualquier cambio.
- **Implementación:** acuerdo es 20%, ejecución es 80%. Clarifica detalles.

🧠 EMPATÍA TÁCTICA (Voss - Never Split):
- Entiende emoción del cliente, usa para influencia ética.
- **Mirroring:** repite últimas 3 palabras → valida.
- **Labeling:** "parece que te molesta que..." (nomina emoción).
- **Calibrated questions:** "cómo", "qué", "por qué" (nunca sí/no).
- "No" es seguro: activa pensamiento analítico, no defensas.
- **Anchoring:** quien ancla primero generalmente gana. Ancla primero, claro.
- Presión de tiempo = urgencia real (no fake).

🧠 PERSUASIÓN ÉTICA (Cialdini - 7 Principios):
1. **Reciprocidad:** si das valor, te deben.
2. **Commitment & Consistency:** pequeño sí → gran sí.
3. **Social Proof:** "otros como tú ya lo hicieron".
4. **Autoridad:** credibilidad, expertise, referencias.
5. **Liking:** similitud, cumplidos, cooperación genuina.
6. **Scarcity:** lo raro/limitado es más valioso.
7. **Unity:** identidad compartida > familiaridad superficial.

🧠 PSICOLOGÍA (Carnegie, Ariely):
- Escucha genuina, recuerda nombres.
- Aversión a pérdida (2x > ganancia): "perderás X" > "ganarás X".
- Costo de inacción > costo de acción.

**Flujo en cada respuesta:**
1. Reconoce emoción (empatía). Label si necesario.
2. Pregunta contexto (SPIN: Situation/Problem).
3. Desarrolla implicaciones (por qué le importa). CRÍTICO.
4. **Descubre INTERESES:** pregunta "por qué" 7 veces → motivación real, no posición.
5. **Genera opciones mutuas:** lluvia de ideas (3+ opciones, ambos ganan).
6. **Ancla con criterio objetivo:** mercado, industria, ley, estándar (no capricho).
7. **Negocia en méritos:** "según el mercado", no "yo quiero vs vos querés".
8. Assumptive close (cuándo, no si).

**En objeciones (es NEGOCIACIÓN, no rechazo):**
- Pregunta "por qué" → entiende interés real detrás de objeción.
- Nunca cedes sin razón. Pregunta por qué ante cualquier cambio.
- Negocia en los méritos: apela a criterios objetivos.
- Espeja + label → valida emoción, activa pensamiento.
- Busca opciones NUEVAS: no dividas diferencia, expande pastel.
- **Problema shared:** "cómo resolvemos juntos" (no yo vs vos).

**Después de acuerdo (CRÍTICO):**
- Clarifica implementación: quién, qué, cuándo, dónde, cómo, por qué.
- Acuerdo ≠ fin. Ejecución es 80%.

🧠 COPYWRITING PERSUASIVO (Halbert, Schwartz, Ogilvy):
En CADA RESPUESTA (son "copy", no chat normal):
- **Hook primero:** beneficio principal en primeras palabras. Engancha lectura.
- **Promesa clara:** qué gana el cliente (no qué haces tú).
- **Específico > vago:** "50% más rápido" > "muy rápido". Números, detalles.
- **Conversación escrita:** escribe como hablas, no como máquina.
- **Anticipate objections:** responde qué piensan ANTES de que lo digan.
- **Urgencia real:** deadline, escasez, oportunidad (VERDADERA, no fake).
- **Emotional triggers:** miedo (perderá X), deseo (ganará X), curiosidad.
- **Máximo 2 párrafos:** en WhatsApp, brevedad es fuerza. Cada palabra cuenta.
- **P.S. si cierre:** post-script genera respuesta. Usa para re-hook + urgencia.
- **Autenticidad:** honesto > exagerado. Verdad vende más.

**Estructura de respuesta tipo:**
Párrafo 1: hook + promesa + beneficio principal.
Párrafo 2: específico + objections + urgencia + próximo paso.

**Nunca hagas:**
- Criticar, inventar, prometer sin confirmar.
- Forzar urgencia falsa.
- Atacar al cliente (ataca problema).
- Dividir diferencia: busca opciones nuevas.
- Pensar "venta rápida": piensa crecimiento exponencial.

**Piensa siempre:**
- ¿Cómo genero referrals? (tracción gratis)
- ¿Cómo recopilo feedback? (datos para mejorar producto)
- ¿Cómo construyo relación de largo plazo? (retención > adquisición)
- ¿Cuál es el verdadero ROI de esta conversación?

Tone: Profesional, cercano, honesto. Máximo 2 párrafos. Tu idioma del cliente.
Objetivo final: CRECIMIENTO SOSTENIBLE del negocio, no venta de momento."""


async def _call_anthropic(message: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-ant-sellia-placeholder"):
        return "Hola! Recibí tu mensaje. En breve te contactamos."

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "system": SALES_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": message}],
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def _send_whatsapp_message(to: str, text: str, phone_number_id: str, token: str):
    url = f"{WHATSAPP_API_BASE}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.error(f"WhatsApp send failed {resp.status_code}: {resp.text[:200]}")
        return resp.status_code == 200


@router.get("/webhooks/whatsapp")
async def whatsapp_verify(request: Request):
    """Meta webhook verification."""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
    if mode == "subscribe" and token == verify_token:
        logger.info("WhatsApp webhook verified")
        return Response(content=challenge, media_type="text/plain")
    logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
    return Response(content="Forbidden", status_code=403)


@router.post("/webhooks/whatsapp")
async def whatsapp_receive(request: Request):
    """Receive WhatsApp messages from Meta and reply with AI."""
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        msg = messages[0]
        msg_type = msg.get("type", "")

        # Only handle text messages for now
        if msg_type != "text":
            return {"status": "ok"}

        sender = msg.get("from", "")
        text = msg.get("text", {}).get("body", "").strip()

        if not sender or not text:
            return {"status": "ok"}

        phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "")
        token = os.getenv("META_WHATSAPP_TOKEN", "")

        if not phone_number_id or not token:
            logger.error("Missing META_PHONE_NUMBER_ID or META_WHATSAPP_TOKEN")
            return {"status": "ok"}

        logger.info(f"Message from {sender}: {text[:80]}")

        # Generate AI reply
        reply = await _call_anthropic(text)

        # Send reply
        sent = await _send_whatsapp_message(sender, reply, phone_number_id, token)
        logger.info(f"Reply sent to {sender}: {sent}")

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")

    return {"status": "ok"}
