"""Auto Responder — Process messages through SellIA Brain + send responses.

Pipeline:
1. Mensaje llega (desde webhook)
2. Detecta plataforma + etapa de venta
3. Consulta Brain por estrategia
4. Genera respuesta con SellIA
5. Calcula confianza
6. Si >80% → responde automático
7. Si <80% → pending_approval (supervisor revisa)
8. Registra en Audit Log (qué se hizo, por qué, resultado)

Integración con Scheduling:
- Si detecta intención agendar → usa SchedulingOrchestrator
- Maneja conversación de booking sin intervención manual
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.computer_use.services.webhook_receiver import IncomingMessage, MessageSource, MessageType
from app.domains.computer_use.services.sellia_brain_service import (
    get_brain_service,
    ActionContext,
    SalesStage,
    Platform,
)
from app.domains.computer_use.services.audit_log_service import AuditLogEntry, AuditLogService
from app.domains.computer_use.services.scheduling_orchestrator import SchedulingOrchestrator
from app.domains.computer_use.services.sales_closer import get_sales_closer_service
from app.domains.computer_use.integrations import (
    WhatsAppConnector,
    InstagramConnector,
    get_whatsapp_connector,
    get_instagram_connector,
)
from app.domains.computer_use.services.conversion_tracker import get_conversion_tracker
from app.domains.computer_use.services.platform_automation_engine import (
    get_platform_automation_engine,
    PlatformAutomationType,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Thresholds
CONFIDENCE_THRESHOLD_AUTO = 0.80  # >80% → auto-responder
CONFIDENCE_THRESHOLD_ESCALATE = 0.50  # <50% → escalate to human


class AutoResponderService:
    """Servicio para responder mensajes automáticamente."""

    def __init__(
        self,
        db: AsyncSession,
        scheduling_orchestrator: Optional[SchedulingOrchestrator] = None,
        closer_mode: str = "supervised",  # auto | supervised
    ):
        self.db = db
        self.brain_service = get_brain_service()
        self.audit_service = AuditLogService(db)
        self.scheduling_orchestrator = scheduling_orchestrator
        self.sales_closer = get_sales_closer_service(db)
        self.closer_mode = closer_mode  # Mode para sales closer

        # Real API connectors para enviar mensajes
        self.whatsapp_connector = (
            get_whatsapp_connector(
                business_account_id=settings.WHATSAPP_BUSINESS_ACCOUNT_ID,
                access_token=settings.WHATSAPP_ACCESS_TOKEN,
            ) if hasattr(settings, 'WHATSAPP_BUSINESS_ACCOUNT_ID') else None
        )
        self.instagram_connector = (
            get_instagram_connector(
                business_account_id=settings.INSTAGRAM_BUSINESS_ACCOUNT_ID,
                access_token=settings.INSTAGRAM_ACCESS_TOKEN,
            ) if hasattr(settings, 'INSTAGRAM_BUSINESS_ACCOUNT_ID') else None
        )

        # Payment tracking
        self.conversion_tracker = get_conversion_tracker(db)

        # Browser automation (fallback si APIs no disponibles)
        self.platform_automation = get_platform_automation_engine()

    async def process_message(
        self,
        user_id: str,
        message: IncomingMessage,
    ) -> Tuple[Optional[str], str, float]:
        """
        Procesa mensaje → genera respuesta.

        Retorna: (response_text, status, confidence)
        - response_text: si status=success o pending_approval
        - status: success | pending_approval | failed | escalated
        - confidence: score 0-1
        """
        try:
            # 0. SCHEDULING: Detectar si es request de agendar
            if self.scheduling_orchestrator:
                intent, scheduled_response, scheduling_state = await self.scheduling_orchestrator.process_message(
                    message.customer_id,
                    message.content,
                )

                # Si es scheduling intent → manejar especialmente
                if intent != self.scheduling_orchestrator.SchedulingIntent.SCHEDULE_REQUEST or scheduling_state:
                    # Registrar scheduling action en audit log
                    await self._log_scheduling_activity(
                        user_id=user_id,
                        message=message,
                        response=scheduled_response,
                        intent=intent.value,
                        state=scheduling_state,
                    )
                    return scheduled_response, "success", 0.95  # Scheduling es high-confidence

            # 1. Detectar plataforma
            platform = self._source_to_platform(message.source)
            if not platform:
                raise ValueError(f"Unknown source: {message.source}")

            # 2. Detectar etapa de venta
            stage = self._detect_stage(message)

            # 3. Construir contexto
            context = ActionContext(
                platform=platform,
                stage=stage,
                customer_profile={
                    "name": message.customer_name,
                    "id": message.customer_id,
                    "email": message.customer_email,
                },
                product_info={
                    "product_id": message.product_id,
                    "order_id": message.order_id,
                } if message.product_id or message.order_id else None,
                conversation_history=message.previous_messages or [],
            )

            # 4. Consultar Brain
            strategy = await self.brain_service.get_strategy(context)
            if not strategy:
                raise ValueError("No strategy found for context")

            # 5. Generar respuesta
            instruction = self._build_instruction(message, strategy)
            response_prompt = await self.brain_service.get_response_prompt(context, instruction)

            # 6. LLM genera respuesta (placeholder — usar vision agent o LLM provider)
            response_text = await self._generate_response(response_prompt, context)

            # 7. Detectar señales de compra
            signals = await self.brain_service.detect_sales_signals(message.content, context)

            # 7.5 SALES CLOSING: Evaluar si cerrar venta
            if signals.get("signal_found"):
                closing_msg, closing_status, closing_confidence = await self.sales_closer.evaluate_and_close(
                    user_id=user_id,
                    message=message,
                    conversation_history=context.conversation_history,
                    customer_profile=context.customer_profile,
                    product_info=strategy.metadata if strategy else {},
                    mode=self.closer_mode,
                )

                if closing_msg and closing_status != "not_ready_to_close":
                    response_text = closing_msg
                    confidence = closing_confidence
                    status = "success" if closing_status == "closing_attempt" else "pending_approval"

                    # GENERAR PAYMENT LINK si sale CERRADA
                    if closing_status == "closing_attempt" and status == "success":
                        checkout_success, checkout_url = await self.conversion_tracker.process_sale_to_payment(
                            user_id=user_id,
                            customer_id=message.customer_id,
                            customer_email=message.customer_email,
                            customer_name=message.customer_name,
                            product_info=strategy.metadata or {},
                            amount_cents=int((strategy.metadata.get("price", 0) if strategy.metadata else 0) * 100),
                        )

                        if checkout_success and checkout_url:
                            # Agregar link de pago al mensaje
                            response_text += f"\n\n💳 Confirma tu compra aquí: {checkout_url}"

                    await self._log_activity(
                        user_id=user_id,
                        message=message,
                        response=response_text,
                        strategy=strategy,
                        status=status,
                        confidence=confidence,
                        signals=signals,
                    )

                    return response_text, status, confidence

            # 8. Calcular confianza final
            confidence = self._calculate_confidence(
                strategy,
                signals,
                message,
            )

            # 9. Decidir acción
            if confidence >= CONFIDENCE_THRESHOLD_AUTO:
                status = "success"
                action_desc = "Auto-responder enviado"
            elif confidence >= CONFIDENCE_THRESHOLD_ESCALATE:
                status = "pending_approval"
                action_desc = "Pendiente aprobación del usuario"
            else:
                status = "escalated"
                action_desc = "Escalado a supervisor (confianza baja)"

            # 10. ENVIAR respuesta si status=success
            if status == "success" and response_text:
                send_success, send_msg_id = await self._send_response(
                    platform=platform,
                    recipient_id=message.customer_id,
                    response_text=response_text,
                    message=message,
                )
                if not send_success:
                    logger.warning(f"Failed to send response for {message.customer_id}")
                    status = "pending_approval"  # Retrograde a approval si falla envío

            # 11. Registrar en Audit Log
            await self._log_activity(
                user_id=user_id,
                message=message,
                response=response_text,
                strategy=strategy,
                status=status,
                confidence=confidence,
                signals=signals,
            )

            logger.info(
                f"Message processed: {message.source.value} | "
                f"stage={stage.value} | "
                f"status={status} | "
                f"confidence={confidence:.0%}"
            )

            return response_text, status, confidence

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._log_activity(
                user_id=user_id,
                message=message,
                response=None,
                strategy=None,
                status="failed",
                confidence=0.0,
                signals=None,
                error=str(e),
            )
            return None, "failed", 0.0

    # ── Private Methods ──────────────────────────────────────────────

    def _source_to_platform(self, source: MessageSource) -> Optional[Platform]:
        """Mapea MessageSource a Platform."""
        mapping = {
            MessageSource.WHATSAPP: Platform.WHATSAPP,
            MessageSource.INSTAGRAM_DM: Platform.INSTAGRAM,
            MessageSource.INSTAGRAM_COMMENT: Platform.INSTAGRAM,
            MessageSource.TIKTOK_COMMENT: Platform.TIKTOK,
            MessageSource.FACEBOOK_COMMENT: Platform.LINKEDIN,  # aproximado
            MessageSource.MERCADOLIBRE_MESSAGE: Platform.MERCADOLIBRE,
            MessageSource.AMAZON_MESSAGE: Platform.AMAZON,
            MessageSource.HOTMART_MESSAGE: Platform.WEBSITE,  # aproximado
        }
        return mapping.get(source)

    def _detect_stage(self, message: IncomingMessage) -> SalesStage:
        """Detecta etapa de venta basada en tipo de mensaje."""
        # Comments en productos → awareness/consideration
        if message.message_type == MessageType.COMMENT:
            return SalesStage.CONSIDERATION

        # Mensajes sobre órdenes → negotiation/closure
        if message.order_id:
            return SalesStage.NEGOTIATION

        # Default
        return SalesStage.AWARENESS

    def _build_instruction(
        self,
        message: IncomingMessage,
        strategy: Any,
    ) -> str:
        """Construye instrucción específica para el LLM."""
        base = f"Responde el siguiente mensaje de cliente de forma {strategy.strategy_name}.\n\n"
        base += f"Mensaje del cliente: {message.content}\n"
        base += f"Contexto: Cliente {message.customer_name}\n"

        if message.product_id:
            base += f"Sobre producto: {message.product_id}\n"

        if message.order_id:
            base += f"Sobre orden: {message.order_id}\n"

        base += f"\nResponde usando tácticas: {', '.join(strategy.tactics)}\n"
        base += "Sé auténtico, valora primero, pide permiso antes de vender."

        return base

    async def _generate_response(
        self,
        prompt: str,
        context: ActionContext,
    ) -> str:
        """Genera respuesta usando LLM (OpenAI/Anthropic/local)."""
        # TODO: llamar vision_agent.call_llm() o Anthropic SDK
        return f"Respuesta automática generada para {context.platform.value}"

    async def _send_response(
        self,
        platform: Platform,
        recipient_id: str,
        response_text: str,
        message: IncomingMessage,
    ) -> Tuple[bool, Optional[str]]:
        """Envía respuesta por WhatsApp/Instagram. Retorna (success, message_id)."""
        try:
            # Intentar API primero (más confiable)
            if platform == Platform.WHATSAPP and self.whatsapp_connector:
                return await self.whatsapp_connector.send_text_message(
                    recipient_id=recipient_id,
                    message=response_text,
                )
            elif platform == Platform.INSTAGRAM and self.instagram_connector:
                return await self.instagram_connector.send_text_message(
                    recipient_id=recipient_id,
                    message=response_text,
                )

            # Fallback: browser automation si API no disponible
            logger.info(f"API not available for {platform.value}, using browser automation")

            if platform == Platform.WHATSAPP:
                success, msg_id = await self.platform_automation.send_response(
                    platform=PlatformAutomationType.WHATSAPP_WEB,
                    recipient_identifier=message.customer_name or recipient_id,
                    response_text=response_text,
                )
                return success, msg_id

            elif platform == Platform.INSTAGRAM:
                success, msg_id = await self.platform_automation.send_response(
                    platform=PlatformAutomationType.INSTAGRAM_DM,
                    recipient_identifier=message.customer_name or recipient_id,
                    response_text=response_text,
                )
                return success, msg_id

            else:
                logger.warning(f"No handler for platform {platform.value}")
                return False, None

        except Exception as e:
            logger.error(f"Error sending response: {e}")
            return False, None

    def _calculate_confidence(
        self,
        strategy: Any,
        signals: Dict[str, Any],
        message: IncomingMessage,
    ) -> float:
        """Calcula score de confianza (0-1)."""
        base_confidence = strategy.confidence

        # Boost si hay señales de compra
        if signals.get("signal_found"):
            base_confidence = min(1.0, base_confidence + 0.15)

        # Penalty si contenido corto
        if len(message.content) < 10:
            base_confidence = max(0.0, base_confidence - 0.2)

        # Penalty si es pregunta compleja (múltiples preguntas)
        if message.content.count("?") > 2:
            base_confidence = max(0.0, base_confidence - 0.1)

        return base_confidence

    async def _log_activity(
        self,
        user_id: str,
        message: IncomingMessage,
        response: Optional[str],
        strategy: Any,
        status: str,
        confidence: float,
        signals: Optional[Dict[str, Any]],
        error: Optional[str] = None,
    ) -> None:
        """Registra actividad en Audit Log."""
        try:
            log_entry = AuditLogEntry(
                user_id=user_id,
                platform=message.source.value,
                action_type="message_response" if message.message_type == MessageType.DIRECT_MESSAGE else "comment_response",
            )

            log_entry.with_input(message.content)

            if strategy:
                log_entry.with_agent("auto_responder")
                log_entry.with_strategy(strategy.strategy_name, strategy.tactics)

            log_entry.with_confidence(confidence)

            if response:
                log_entry.with_output(response)

            if status == "success":
                log_entry.success()
            elif status == "pending_approval":
                log_entry.pending_approval()
            else:
                log_entry.failed(error or "Unknown error")

            log_entry.with_metadata({
                "customer_id": message.customer_id,
                "customer_name": message.customer_name,
                "message_id": message.message_id,
                "signals": signals,
            })

            await self.audit_service.log(log_entry)

        except Exception as e:
            logger.error(f"Error logging activity: {e}")

    async def _log_scheduling_activity(
        self,
        user_id: str,
        message: IncomingMessage,
        response: str,
        intent: str,
        state: Optional[Any],
    ) -> None:
        """Registra scheduling action en Audit Log."""
        try:
            log_entry = AuditLogEntry(
                user_id=user_id,
                platform=message.source.value,
                action_type="calendar_scheduling",
            )

            log_entry.with_input(message.content)
            log_entry.with_output(response)
            log_entry.with_agent("scheduling_orchestrator")
            log_entry.with_strategy(intent)
            log_entry.with_confidence(0.95)
            log_entry.success()

            metadata = {
                "customer_id": message.customer_id,
                "customer_name": message.customer_name,
                "intent": intent,
            }

            if state:
                metadata.update({
                    "proposed_slot": state.proposed_slot.to_dict() if state.proposed_slot else None,
                    "confirmed": state.confirmed,
                    "event_id": state.event_id,
                })

            log_entry.with_metadata(metadata)

            await self.audit_service.log(log_entry)

        except Exception as e:
            logger.error(f"Error logging scheduling activity: {e}")


def get_auto_responder_service(db: AsyncSession) -> AutoResponderService:
    return AutoResponderService(db)
