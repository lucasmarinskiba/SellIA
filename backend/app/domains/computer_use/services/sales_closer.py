"""Sales Closer Service — Autonomous closing pipeline.

Integra ClosingStrategist en AutoResponder.

Pipeline:
1. Detecta momento de cierre
2. Selecciona técnica (basada en buyer personality)
3. Genera cierre personalizado
4. Si objeción → maneja
5. Si acepta → confirma venta + next steps
6. Registra en Audit Log
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.computer_use.services.closing_strategist import (
    ClosingStrategist,
    BuyerPersonality,
    ClosingTechnique,
)
from app.domains.computer_use.services.audit_log_service import AuditLogEntry, AuditLogService
from app.domains.computer_use.services.webhook_receiver import IncomingMessage

logger = logging.getLogger(__name__)


class SalesCloserService:
    """Servicio para cerrar ventas automáticamente."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.strategist = ClosingStrategist()
        self.audit_service = AuditLogService(db)

    async def evaluate_and_close(
        self,
        user_id: str,
        message: IncomingMessage,
        conversation_history: List[Dict[str, str]],
        customer_profile: Dict[str, Any],
        product_info: Dict[str, Any],
        mode: str = "supervised",  # auto | supervised
    ) -> Tuple[Optional[str], str, float]:
        """
        Evalúa si cerrar y ejecuta cierre.

        Retorna: (closing_message, status, confidence)
        - status: closing_attempt | closed_won | closed_lost | objection_handled | needs_approval
        - confidence: score 0-1
        """
        try:
            # 1. Detectar si es momento de cerrar
            is_closing_moment, signals = await self.strategist.detect_closing_moment(
                conversation_history,
                customer_profile,
            )

            if not is_closing_moment:
                return None, "not_ready_to_close", 0.0

            # 2. Calcular readiness score
            readiness = await self.strategist.score_close_readiness(
                conversation_history,
                customer_profile,
                signals,
            )

            logger.info(f"Close readiness: {readiness:.0%} | signals: {len(signals)}")

            # 3. Detectar buyer personality (heurística)
            buyer_personality = self._infer_personality(message.content, conversation_history)

            # 4. Seleccionar técnica de cierre
            technique = await self.strategist.select_closing_technique(
                buyer_personality=buyer_personality,
                signals=signals,
                product_type=product_info.get("type"),
            )

            # 5. Detectar si es objeción → manejar
            if self._is_objection(message.content):
                objection_response = await self.strategist.handle_objection(
                    message.content,
                    product_info,
                )

                status = "objection_handled"
                confidence = 0.7

                await self._log_sales_activity(
                    user_id=user_id,
                    message=message,
                    response=objection_response,
                    technique=technique,
                    status=status,
                    confidence=confidence,
                    readiness=readiness,
                )

                return objection_response, status, confidence

            # 6. Generar mensaje de cierre
            closing_message = await self.strategist.generate_closing_message(
                technique=technique,
                customer_name=customer_profile.get("name", ""),
                product_info=product_info,
                offer_deadline=product_info.get("offer_deadline"),
                objections=conversation_history[-1].get("objections") if conversation_history else None,
            )

            # 7. Decisión basada en readiness + mode
            if mode == "auto" and readiness >= 0.75:
                # Auto-close
                status = "closing_attempt"
                confidence = readiness
                action = "sent"

            elif mode == "supervised" and readiness >= 0.75:
                # Pending approval for supervised mode
                status = "needs_approval"
                confidence = readiness
                action = "pending_approval"

            else:
                # Not ready
                status = "not_ready_to_close"
                confidence = readiness
                action = "skipped"

            # 8. Log activity
            await self._log_sales_activity(
                user_id=user_id,
                message=message,
                response=closing_message if action != "skipped" else None,
                technique=technique,
                status=status,
                confidence=confidence,
                readiness=readiness,
                buyer_personality=buyer_personality.value,
            )

            logger.info(
                f"Sales close: {status} | "
                f"technique={technique.value} | "
                f"readiness={readiness:.0%} | "
                f"mode={mode}"
            )

            if action == "skipped":
                return None, status, confidence

            return closing_message, status, confidence

        except Exception as e:
            logger.error(f"Error in sales closer: {e}")
            return None, "failed", 0.0

    async def handle_sale_confirmation(
        self,
        user_id: str,
        customer_id: str,
        customer_name: str,
        product_info: Dict[str, Any],
        amount: float,
    ) -> Tuple[str, str]:
        """
        Maneja confirmación de venta.

        Retorna: (confirmation_message, order_reference)
        """
        order_reference = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        confirmation = f"""
🎉 ¡VENTA CERRADA! 🎉

Referencia: {order_reference}

Producto: {product_info.get('name', 'Purchase')}
Monto: ${amount:.2f}

Próximos pasos:
1. Recibirás confirmación en tu email
2. {product_info.get('next_step_1', 'Acceso inmediato a tu compra')}
3. {product_info.get('next_step_2', 'Soporte 24/7 disponible')}

¡Gracias por confiar en nosotros!

Team
"""

        logger.info(f"Sale confirmed: {order_reference} | {customer_name} | ${amount}")

        return confirmation, order_reference

    # ── Private Methods ──────────────────────────────────────────

    def _infer_personality(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
    ) -> BuyerPersonality:
        """Infiere personalidad del comprador basada en conversación."""
        msg_lower = message.lower()
        full_conv = " ".join([m.get("content", "").lower() for m in conversation_history])

        # ANALYTICAL: preguntas técnicas, datos, ROI
        if any(word in full_conv for word in ["como", "cuál es", "detalles", "proceso", "specifics", "how does"]):
            return BuyerPersonality.ANALYTICAL

        # DRIVER: urgencia, resultados, dinero
        if any(word in full_conv for word in ["rápido", "ahora", "cuando", "resultados", "profit", "immediately"]):
            return BuyerPersonality.DRIVER

        # EXPRESSIVE: emocional, historias, relaciones
        if any(word in full_conv for word in ["siento", "creo", "pienso", "feel", "think", "love"]):
            return BuyerPersonality.EXPRESSIVE

        # AMIABLE: consenso, armonía, preocupación
        if any(word in full_conv for word in ["acuerdo", "juntos", "equipo", "todos", "team", "together"]):
            return BuyerPersonality.AMIABLE

        # Default
        return BuyerPersonality.DRIVER

    def _is_objection(self, message: str) -> bool:
        """Detecta si mensaje contiene objeción."""
        objection_keywords = [
            "pero", "sin embargo", "aunque", "no estoy", "preocupación",
            "caro", "expensive", "tiempo", "seguro", "sure",
            "however", "concerned", "hesitant", "worried",
        ]

        return any(keyword in message.lower() for keyword in objection_keywords)

    async def _log_sales_activity(
        self,
        user_id: str,
        message: IncomingMessage,
        response: Optional[str],
        technique: ClosingTechnique,
        status: str,
        confidence: float,
        readiness: float,
        buyer_personality: Optional[str] = None,
    ) -> None:
        """Registra actividad de cierre en Audit Log."""
        try:
            log_entry = AuditLogEntry(
                user_id=user_id,
                platform=message.source.value,
                action_type="sale_closing_attempt",
            )

            log_entry.with_input(message.content)

            if response:
                log_entry.with_output(response)

            log_entry.with_agent("sales_closer")
            log_entry.with_strategy(technique.value)
            log_entry.with_confidence(confidence)

            if status in ("closing_attempt", "needs_approval"):
                log_entry.success() if status == "closing_attempt" else log_entry.pending_approval()
            elif status == "objection_handled":
                log_entry.success()
            else:
                log_entry.failed("Not ready to close")

            log_entry.with_metadata({
                "customer_id": message.customer_id,
                "customer_name": message.customer_name,
                "technique": technique.value,
                "readiness_score": readiness,
                "buyer_personality": buyer_personality,
                "status": status,
            })

            await self.audit_service.log(log_entry)

        except Exception as e:
            logger.error(f"Error logging sales activity: {e}")


def get_sales_closer_service(db: AsyncSession) -> SalesCloserService:
    return SalesCloserService(db)
