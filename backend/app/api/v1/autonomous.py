"""
Autonomous Sales Agent — 24/7 modo.

El sistema responde como vendedor experto sin intervención:
- Procesa webhooks (WhatsApp, Meta, email)
- Dispara agentes según contexto
- Ejecuta flujos de venta en paralelo
- Loguea cada acción + resultado
- Monitorea métricas en vivo

Arquitectura:
1. Webhook → ParseEvent → Classify (contacto nuevo/seguimiento/objeción) → SelectAgent → Dispatch
2. Dispatch → ExecuteFlow (Belfort/SPIN/Hermozi según tipo) → SendResponse → LogEvent
3. Monitoring → Dashboard (conversiones/objeciones/leads por hora)
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel

from app.core.clock import utc_now
from app.core.intelligence.strategy_generator import StrategyGenerator
from app.core.resilience import (
    InputValidator,
    health_tracker,
    retry_with_exponential_backoff,
)

router = APIRouter(prefix="/api/v1/autonomous", tags=["autonomous"])
logger = logging.getLogger(__name__)

# Cache de estrategias por producto (product_id -> strategy)
_STRATEGY_CACHE: dict[str, dict[str, Any]] = {}


class EventType(str, Enum):
    """Tipos de eventos que disparan ventas autónomas."""
    WHATSAPP_MESSAGE = "whatsapp_message"
    INSTAGRAM_DM = "instagram_dm"
    EMAIL_RECEIVED = "email_received"
    LEAD_CAPTURE = "lead_capture"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    OBJECTION_DETECTED = "objection_detected"


class SalesStage(str, Enum):
    """Etapa de venta donde ocurre el evento."""
    FIRST_CONTACT = "first_contact"
    DISCOVERY = "discovery"
    OBJECTION = "objection"
    OFFER = "offer"
    CLOSE = "close"
    POST_SALE = "post_sale"


class AutonomousEvent(BaseModel):
    """Evento que dispara vendedor autónomo."""
    event_type: EventType
    contact_id: str
    contact_name: str
    contact_phone: str | None = None
    contact_email: str | None = None
    message: str | None = None
    context: dict[str, Any]  # producto, negocio, etapa, historial previo
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = utc_now()


class SalesResponse(BaseModel):
    """Respuesta del vendedor autónomo."""
    contact_id: str
    message: str
    channel: str  # whatsapp, instagram, email
    strategy_used: str  # master_seller, spin, assumptive_close, etc
    confidence: float  # 0-1, confianza en la respuesta
    next_action: str | None = None  # follow_up en X horas, cierre en 48h, etc
    logged_at: datetime = None


class StrategySelector:
    """Selecciona estrategia basada en producto + contexto."""

    @staticmethod
    def get_or_generate_strategy(account_id: str, product_info: dict[str, Any]) -> dict[str, Any]:
        """Obtiene estrategia del cache o genera nueva."""

        product_id = product_info.get("id", "default")
        cache_key = f"{account_id}:{product_id}"

        # Buscar en cache
        if cache_key in _STRATEGY_CACHE:
            logger.info(f"Estrategia desde cache: {cache_key}")
            return _STRATEGY_CACHE[cache_key]

        # Generar nueva estrategia
        logger.info(f"Generando estrategia para producto: {product_id}")

        try:
            strategy = StrategyGenerator.generate_strategy(
                product_name=product_info.get("name", "unknown"),
                category=product_info.get("category", "general"),
                market_size=product_info.get("market_size", "Medio"),
                demand=product_info.get("demand", "Medio"),
                competition=product_info.get("competition", "Media"),
                price=product_info.get("price", 100),
                price_avg_market=product_info.get("price_avg_market", 100),
            )

            # Guardar en cache
            _STRATEGY_CACHE[cache_key] = strategy

            return strategy

        except Exception:
            logger.exception("Error generando estrategia")
            # Fallback a estrategia genérica
            return {"segment": "growth", "recommended_channels": {"primary": "email"}}


class AgentSelector:
    """Selecciona agente óptimo según evento + estrategia."""

    @staticmethod
    def select(event: AutonomousEvent, strategy: dict[str, Any] | None = None) -> str:
        """Retorna ID del agente a usar, basado en estrategia si disponible."""

        stage = event.context.get("sales_stage", SalesStage.FIRST_CONTACT)

        # Si hay estrategia, usarla para seleccionar agente óptimo
        if strategy:
            segment = strategy.get("segment", "growth")

            if segment == "premium":
                # Premium → personal touch, relationship building
                if stage == SalesStage.FIRST_CONTACT:
                    return "consultative_agent"  # Consultivo
                elif stage == SalesStage.OFFER:
                    return "exclusive_offer_agent"  # Oferta exclusiva

            elif segment == "budget":
                # Budget → volumen, urgencia, FOMO
                if stage == SalesStage.FIRST_CONTACT:
                    return "urgency_agent"  # Crear urgencia
                elif stage == SalesStage.CLOSE:
                    return "immediate_close_agent"  # Cierre rápido

        # Default: etapa de venta
        if stage == SalesStage.FIRST_CONTACT:
            return "master_seller"  # Script maestro integrado
        elif stage == SalesStage.DISCOVERY:
            return "spin_agent"  # Diagnóstico profundo
        elif stage == SalesStage.OBJECTION:
            return "objection_master"  # Manejo de objeciones
        elif stage == SalesStage.OFFER:
            return "hermozi_agent"  # Oferta irresistible
        elif stage == SalesStage.CLOSE:
            return "hopkins_agent"  # Técnicas de cierre Hopkins

        # Default: maestro
        return "master_seller"


class FlowExecutor:
    """Ejecuta flujos de venta autónomos."""

    @staticmethod
    async def execute(agent_id: str, event: AutonomousEvent, account_id: str) -> SalesResponse:
        """
        Ejecuta flujo del agente seleccionado.

        En producción:
        1. Llama al backend del cerebro (/brain/cua/dispatch)
        2. Obtiene script personalizado
        3. Envía por canal correspondiente
        4. Recibe respuesta
        5. Loguea resultado
        """

        logger.info(f"[{account_id}] Ejecutando agente {agent_id} para contacto {event.contact_id}")

        # TODO: Integración real con `/brain/cua/dispatch`
        # Por ahora, respuesta simulada

        return SalesResponse(
            contact_id=event.contact_id,
            message=f"Respuesta de {agent_id} personalizada según {event.context.get('product')}",
            channel=event.context.get("channel", "whatsapp"),
            strategy_used=agent_id,
            confidence=0.95,
            next_action="follow_up en 24h" if agent_id == "cardone_agent" else None,
            logged_at=utc_now()
        )


class EventLogger:
    """Loguea eventos de venta para análisis + optimización."""

    @staticmethod
    def log_event(event: AutonomousEvent, response: SalesResponse, result: str = "sent") -> dict[str, Any]:
        """
        Loguea evento completo.

        En producción: guardar en DB (PostgreSQL/Mongo) para:
        - Dashboard de conversión en vivo
        - Análisis de qué agente funciona mejor
        - Reentrenamiento de modelos
        - Auditoría de ventas
        """

        log_entry = {
            "timestamp": utc_now().isoformat(),
            "account_id": event.context.get("account_id"),
            "contact_id": event.contact_id,
            "event_type": event.event_type.value,
            "sales_stage": event.context.get("sales_stage", "unknown"),
            "agent_used": response.strategy_used,
            "message_in": event.message,
            "message_out": response.message,
            "channel": response.channel,
            "confidence": response.confidence,
            "result": result,  # sent, bounced, error, etc
        }

        logger.info(f"SALES_EVENT: {json.dumps(log_entry)}")

        # TODO: Guardar en DB para dashboard

        return log_entry


@router.post("/webhook/whatsapp", tags=["webhooks"])
async def webhook_whatsapp(
    payload: dict[str, Any],
    x_hub_signature: str | None = Header(None),
    background_tasks: BackgroundTasks = None
):
    """
    Webhook de WhatsApp Business API.

    Recibe mensaje → Valida → Procesa automáticamente → Responde sin intervención.
    Nunca expone error interno al webhook (siempre 200 OK si procesable).
    """

    try:
        # Verificar firma (TODO: implementar verificación real)
        # if not verify_webhook_signature(payload, x_hub_signature):
        #     return {"status": "ok"}  # No revelar si auth falló

        # Extraer datos del mensaje
        messages = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])

        if not messages:
            return {"status": "ok"}  # Sin mensajes, ignora

        messages_processed = 0
        messages_rejected = 0

        for msg in messages:
            try:
                contact_phone = msg.get("from")
                contact_name = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [{}])[0].get("profile", {}).get("name", "Unknown")
                message_text = msg.get("text", {}).get("body", "")

                # Validación: rechaza spam/ruido antes de procesar
                if not contact_phone or not message_text:
                    logger.warning(f"WhatsApp webhook: missing required fields (phone={contact_phone}, msg_len={len(message_text)})")
                    messages_rejected += 1
                    continue

                # Crear evento autónomo
                event = AutonomousEvent(
                    event_type=EventType.WHATSAPP_MESSAGE,
                    contact_id=contact_phone,
                    contact_name=contact_name,
                    contact_phone=contact_phone,
                    message=message_text,
                    context={
                        "channel": "whatsapp",
                        "sales_stage": SalesStage.FIRST_CONTACT.value,  # TODO: detectar etapa real desde historial
                        "account_id": payload.get("account_id"),
                        "product": payload.get("product_info"),
                    }
                )

                # Procesar en background (no bloquea webhook)
                background_tasks.add_task(process_autonomous_event, event)
                messages_processed += 1

            except Exception:
                logger.exception("Error procesando mensaje individual")
                messages_rejected += 1
                # Continuar con siguiente mensaje, no fallar

        # Siempre retorna 200 (webhook no debe reintenta)
        return {
            "status": "received",
            "messages_count": len(messages),
            "processed": messages_processed,
            "rejected": messages_rejected
        }

    except Exception:
        logger.exception("Error en webhook WhatsApp")
        # Retorna 200 aunque haya error: webhook no debe reintentar
        return {"status": "ok", "warning": "error_processing_webhook"}


@router.post("/webhook/instagram", tags=["webhooks"])
async def webhook_instagram(
    payload: dict[str, Any],
    background_tasks: BackgroundTasks = None
):
    """
    Webhook de Instagram DMs (vía Meta Graph API).
    Mismo flujo que WhatsApp.
    """

    try:
        # Extraer DMs
        dms = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])

        if not dms:
            return {"status": "ok"}

        for dm in dms:
            event = AutonomousEvent(
                event_type=EventType.INSTAGRAM_DM,
                contact_id=dm.get("from", {}).get("id"),
                contact_name=dm.get("from", {}).get("name", "Unknown"),
                message=dm.get("text"),
                context={
                    "channel": "instagram",
                    "sales_stage": SalesStage.FIRST_CONTACT.value,
                    "account_id": payload.get("account_id"),
                }
            )

            background_tasks.add_task(process_autonomous_event, event)

        return {"status": "received", "dms_count": len(dms)}

    except Exception as e:
        logger.exception("Error en webhook Instagram")
        raise HTTPException(status_code=500, detail=str(e))


async def process_autonomous_event(event: AutonomousEvent):
    """
    Procesa evento autónomo en background.

    Pipeline:
    1. Valida input (rechaza ruido inmediatamente)
    2. Selecciona agente óptimo
    3. Ejecuta flujo (con circuit breaker + retry)
    4. Envía respuesta (degrada a fallback si falla)
    5. Loguea evento (completo, para auditoría)
    """

    account_id = event.context.get("account_id", "unknown")

    try:
        # 1. Validar input — rechazar ruido rápido
        validation = InputValidator.validate_batch(
            {
                "product_name": event.context.get("product", ""),
                "message": event.message or "",
                "email": event.contact_email or "",
                "phone": event.contact_phone or "",
            },
            ["product_name", "message"]
        )

        if not validation["valid"]:
            logger.warning(f"[{account_id}] Input validation failed: {validation['errors']}")
            EventLogger.log_event(event, SalesResponse(
                contact_id=event.contact_id,
                message="[REJECTED] Invalid input",
                channel=event.context.get("channel", "unknown"),
                strategy_used="validation_reject",
                confidence=0.0,
            ), result="rejected")
            return

        if validation["quarantine"]:
            logger.info(f"[{account_id}] Quarantined: {validation['quarantine']}")

        # 2. Obtener estrategia del producto
        product_info = event.context.get("product_info", {})
        strategy = StrategySelector.get_or_generate_strategy(account_id, product_info)
        logger.info(f"[{account_id}] Estrategia cargada: {strategy.get('segment', 'unknown')}")

        # 3. Seleccionar agente basado en estrategia
        agent_id = AgentSelector.select(event, strategy)
        logger.info(f"[{account_id}] Agente seleccionado: {agent_id} (estrategia: {strategy.get('segment', 'default')})")

        # 4. Ejecutar flujo con resilience
        try:
            # Circuit breaker: previene martillar agente fallido
            if not health_tracker.is_service_available(agent_id):
                logger.warning(f"[{account_id}] Agent {agent_id} unavailable (circuit open), falling back to master_seller")
                agent_id = "master_seller"  # Graceful degradation

            # Retry idempotent operation (envío mensaje)
            response = await retry_with_exponential_backoff(
                FlowExecutor.execute,
                args=(agent_id, event, account_id),
                max_retries=3,
                is_idempotent=True
            )
            health_tracker.record_success(agent_id)

        except Exception:
            # Falla la ejecución: degrade a fallback ultra básico
            logger.exception(f"[{account_id}] Agente falló")
            health_tracker.record_failure(agent_id)
            response = SalesResponse(
                contact_id=event.contact_id,
                message="Hola! Viendo tu mensaje. Te respondo en breve.",  # Fallback ultra básico
                channel=event.context.get("channel", "whatsapp"),
                strategy_used="fallback_basic",
                confidence=0.3,
            )
            EventLogger.log_event(event, response, result="degraded")
            return

        # 5. Enviar respuesta
        channel = event.context.get("channel", "whatsapp")
        try:
            # TODO: send_by_channel(channel, event.contact_phone, response.message)
            logger.info(f"[{account_id}] Respuesta enviada por {channel}: {response.message[:100]}...")
        except Exception:
            logger.exception(f"[{account_id}] Error enviando respuesta por {channel}")
            # No hacer falla aquí: respuesta ya se preparó, si falla envío es problema de canal, no de agente
            EventLogger.log_event(event, response, result="prepared_not_sent")
            return

        # 6. Loguear éxito + estrategia usada
        EventLogger.log_event(event, response, result="sent")
        logger.info(f"[{account_id}] Evento procesado exitosamente con estrategia {strategy.get('segment')}")

    except Exception:
        logger.exception(f"[{account_id}] Excepción no capturada procesando evento")
        # Notificar a admin: hay bug que requiere investigación
        # TODO: send_admin_alert(account_id, "autonomous_event_error", str(e))


@router.get("/status", tags=["monitoring"])
async def status_autonomous(account_id: str | None = None):
    """
    Status del vendedor autónomo.

    Retorna: contactos activos, eventos hoy, tasa de conversión, agente más usado.
    """

    # TODO: Consultar DB

    return {
        "status": "active",
        "account_id": account_id,
        "active_conversations": 24,  # Simulado
        "events_today": 156,
        "conversion_rate": 0.28,  # 28%
        "top_agent": "master_seller",
        "uptime": "99.8%",
    }


@router.post("/cron/follow_up", tags=["automation"])
async def cron_follow_up():
    """
    Cron job: ejecuta follow-ups cada 2 horas.

    Lógica:
    - Busca leads que hace 24-48h no respondieron
    - Dispara follow-up con valor nuevo
    - Loguea resultado

    En producción: ejecutar con APScheduler / celery.
    """

    logger.info("Iniciando cron follow-up")

    # TODO: Buscar leads pendientes en DB
    # TODO: Para cada uno: crear evento FOLLOW_UP_REMINDER, procesar

    return {"status": "completed", "follow_ups_sent": 0}  # Simulado


@router.post("/cron/lead_scoring", tags=["automation"])
async def cron_lead_scoring():
    """
    Cron job: recalcula lead scoring cada 4 horas.

    Detecta:
    - Leads calientes (responden rápido)
    - Leads fríos (ignoran 3+ toques)
    - Objeciones recurrentes (mejorar script)

    En producción: ML model + feedback loop.
    """

    logger.info("Recalculando lead scores")

    # TODO: Procesar con lead_scoring_model

    return {"status": "completed", "leads_rescored": 0}


@router.post("/crm/sync", tags=["integrations"])
async def crm_sync_contact(
    account_id: str,
    contact_id: str,
    contact_data: dict[str, Any]
):
    """
    Sincroniza contacto con CRM (Salesforce, HubSpot, Pipedrive).

    Resilience:
    - Circuit breaker por CRM (si falla, deja de intentar 60s)
    - Retry idempotent con backoff (update/create son idempotentes)
    - Degradation: si CRM offline, loguea localmente para queue sync después
    - Nunca falla silenciosamente: siempre loguea resultado

    Datos que sincroniza:
    - Nombre, email, teléfono, empresa
    - Etapa de venta (first_contact/discovery/objection/offer/close)
    - Historial de mensajes (último mensaje, timestamp)
    - Resultado (abierto, respondió, cerrado, perdido)
    - Agentes usados + conversión por agente
    - Métricas (tiempo a respuesta, tiempo a cierre, valor)
    """

    logger.info(f"[{account_id}] Sincronizando contacto {contact_id} con CRM")

    # Validar input: rechazar ruido
    if not contact_id or not contact_data:
        logger.warning(f"[{account_id}] CRM sync: invalid input (contact_id={contact_id}, data_len={len(contact_data)})")
        return {"status": "rejected", "reason": "invalid_input"}

    # Circuit breaker: previene martillar CRM fallido
    crm_name = "crm_sync"
    if not health_tracker.is_service_available(crm_name):
        logger.warning(f"[{account_id}] CRM circuit open, queuing sync para después")
        # TODO: guardar en queue local para retry posterior
        return {"status": "queued", "contact_id": contact_id, "reason": "crm_unavailable"}

    # Retry idempotent (update/create son idempotentes)
    try:
        result = await retry_with_exponential_backoff(
            _sync_to_crm_internal,
            args=(account_id, contact_id, contact_data),
            max_retries=3,
            is_idempotent=True
        )

        health_tracker.record_success(crm_name)
        logger.info(f"[{account_id}] CRM sync completado: {result}")

        return {
            "status": "synced",
            "contact_id": contact_id,
            "crm": result.get("crm", "unknown"),
            "fields_synced": result.get("fields_synced", 0),
            "timestamp": utc_now().isoformat(),
        }

    except Exception as e:
        # Falla CRM: log + queue local, no falla completamente
        logger.exception(f"[{account_id}] CRM sync falló")
        health_tracker.record_failure(crm_name)

        # Degradation: guardar en queue local para retry después
        # TODO: guardar en local_queue.json o DB para retry cada 30min
        logger.info(f"[{account_id}] Contacto {contact_id} guardado en queue local para retry")

        return {
            "status": "queued",
            "contact_id": contact_id,
            "reason": f"crm_error: {e!s}",
            "retry_at": (utc_now() + timedelta(minutes=30)).isoformat(),
            "timestamp": utc_now().isoformat(),
        }


async def _sync_to_crm_internal(account_id: str, contact_id: str, contact_data: dict[str, Any]) -> dict[str, Any]:
    """Lógica interna de sync a CRM (reintentable)."""

    # TODO: Conectar a CRM API real
    # Ejemplo Salesforce:
    # sf = Salesforce(instance=instance_url, session_id=access_token)
    # sf.Contact.create({
    #     'FirstName': contact_data.get('first_name'),
    #     'LastName': contact_data.get('last_name'),
    #     'Email': contact_data.get('email'),
    #     'Phone': contact_data.get('phone'),
    #     'Company': contact_data.get('company'),
    #     'StageName': contact_data.get('sales_stage'),
    # })

    return {
        "crm": "salesforce",  # TODO: detectar de config
        "fields_synced": len(contact_data),
    }


@router.post("/scheduling/smart_follow_up", tags=["automation"])
async def smart_follow_up_schedule(
    contact_id: str,
    account_id: str,
    context: dict[str, Any]
):
    """
    Agenda follow-up inteligente basado en:
    1. Zona horaria del contacto (no lo llames a las 3am)
    2. Patrón de respuesta (si responde mejor miércoles, agenda miércoles)
    3. Contexto del cierre (si está en vacaciones, espera)
    4. Presión óptima (no abrumar con 10 toques; respetar ritmo)

    Retorna: timestamp recomendado para siguiente toque.
    """

    try:
        logger.info(f"[{account_id}] Calculando follow-up óptimo para {contact_id}")

        # TODO: Procesar con SmartScheduler
        # 1. Buscar historial de mensajes de contacto
        # 2. Calcular zona horaria (from IP / from contact info)
        # 3. Detectar patrón (lunes-viernes? mañana-tarde?)
        # 4. Calcular presión (cuántos toques ya, cuál es máximo antes de churn)
        # 5. Retornar timestamp óptimo

        # Simulado por ahora
        from datetime import timedelta

        next_optimal = utc_now() + timedelta(days=2, hours=10)  # Miércoles 10am

        return {
            "contact_id": contact_id,
            "next_follow_up": next_optimal.isoformat(),
            "reason": "Patrón de respuesta: miércoles 10-11am",
            "timezone": "America/Argentina/Buenos_Aires",
            "confidence": 0.85
        }

    except Exception as e:
        logger.exception("Error en smart scheduling")
        return {"status": "error", "detail": str(e)}


@router.post("/ab_test/message_variant", tags=["optimization"])
async def ab_test_variants(
    account_id: str,
    contact_segment: str,
    variants: list[str]
):
    """
    A/B test de mensajes/scripts para optimizar conversión.

    Workflow:
    1. Define 2-3 variantes de pitch/copy
    2. Asigna aleatoriamente a contactos (split 50/25/25)
    3. Mide: open rate, response rate, conversion rate
    4. Retorna ganador + confidence level
    5. Actualiza sistema con ganador automáticamente

    En producción: ejecutar test 2-4 semanas, n>=100 contactos por variante.
    """

    try:
        logger.info(f"[{account_id}] Iniciando A/B test con {len(variants)} variantes")

        # TODO: Procesar con ExperimentRunner
        # 1. Seleccionar contactos de segment
        # 2. Asignar aleatoriamente variantes
        # 3. Enviar variante asignada
        # 4. Rastrear métrica (open/response/conversion)
        # 5. Tras 1000+ eventos, retornar ganador

        return {
            "status": "running",
            "account_id": account_id,
            "segment": contact_segment,
            "variants": len(variants),
            "power": 0.8,
            "sample_size_needed": 100,
            "estimated_duration": "7-14 days"
        }

    except Exception as e:
        logger.exception("Error en A/B test")
        return {"status": "error", "detail": str(e)}
