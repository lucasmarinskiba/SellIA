"""
Refund Automation — Auto-process disputes, chargebacks, quality complaints.

Flujo:
1. Buyer reclama (WhatsApp, Mercado Libre, direct)
2. Sistema detecta urgencia
3. Valida claim (foto, descripción, etc)
4. Propone solución (refund, replacement, store credit)
5. Si buyer acepta: procesa automático
6. Si no: escala a humano
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class DisputeReason(Enum):
    """Categorías de reclamo."""
    PRODUCT_DAMAGED = "producto_dañado"
    PRODUCT_DIFFERENT = "producto_diferente"
    NOT_ARRIVED = "no_llegó"
    QUALITY_ISSUE = "problema_calidad"
    FRAUD = "fraude"
    WRONG_ADDRESS = "dirección_incorrecta"


class RefundStrategy(Enum):
    """Estrategias de resolución."""
    FULL_REFUND = "full_refund"
    PARTIAL_REFUND = "partial_refund"
    REPLACEMENT = "replacement"
    STORE_CREDIT = "store_credit"
    ESCALATE = "escalate_to_human"


class RefundAutomation:
    """Automatización de refunds y disputes."""

    def __init__(self, stripe_service, mercadolibre_service):
        self.stripe = stripe_service
        self.ml = mercadolibre_service

    # ========== DISPUTE DETECTION ==========

    async def analyze_dispute(
        self,
        order_id: str,
        buyer_message: str,
        photos: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analiza reclamo. Detecta categoría + confianza + estrategia recomendada.
        """

        logger.info(f"Analyzing dispute for order {order_id}")

        reason = self._classify_reason(buyer_message)
        confidence = self._estimate_confidence(buyer_message, photos)

        # Determinar estrategia automática
        strategy = self._recommend_strategy(reason, confidence)

        logger.info(f"Dispute: {reason.value}, confidence: {confidence:.1%}, strategy: {strategy.value}")

        return {
            "status": "analyzed",
            "order_id": order_id,
            "reason": reason.value,
            "confidence": confidence,
            "strategy": strategy.value,
            "auto_process": strategy != RefundStrategy.ESCALATE,
            "recommendation": self._get_resolution_text(reason, strategy),
        }

    def _classify_reason(self, message: str) -> DisputeReason:
        """Detecta categoría de reclamo por keywords."""

        message_lower = message.lower()

        keywords = {
            DisputeReason.PRODUCT_DAMAGED: ["dañado", "roto", "quebrado", "defecto"],
            DisputeReason.PRODUCT_DIFFERENT: ["no es igual", "diferente", "no es lo que", "no corresponde"],
            DisputeReason.NOT_ARRIVED: ["no llegó", "no recibí", "desapareció", "tracking"],
            DisputeReason.QUALITY_ISSUE: ["mala calidad", "bajo calidad", "no funciona", "falla"],
            DisputeReason.WRONG_ADDRESS: ["dirección incorrecta", "envío equivocado", "otro destino"],
        }

        for reason, kws in keywords.items():
            if any(kw in message_lower for kw in kws):
                return reason

        return DisputeReason.FRAUD  # Default fallback (rare)

    def _estimate_confidence(self, message: str, photos: Optional[List[str]]) -> float:
        """Estima confianza en reclamo (0-1)."""

        confidence = 0.5

        # Mensaje detallado (+0.2)
        if len(message) > 100:
            confidence += 0.2

        # Fotos de evidencia (+0.3)
        if photos and len(photos) > 0:
            confidence += 0.3

        # Reclamo reciente (+0.1)
        confidence += 0.1

        return min(confidence, 1.0)

    def _recommend_strategy(self, reason: DisputeReason, confidence: float) -> RefundStrategy:
        """Recomienda estrategia de resolución."""

        # Alta confianza → refund automático
        if confidence >= 0.8:
            if reason == DisputeReason.NOT_ARRIVED:
                return RefundStrategy.FULL_REFUND
            elif reason == DisputeReason.PRODUCT_DAMAGED:
                return RefundStrategy.REPLACEMENT
            else:
                return RefundStrategy.PARTIAL_REFUND

        # Confianza media → ofrecer opciones
        elif confidence >= 0.5:
            if reason == DisputeReason.PRODUCT_DAMAGED:
                return RefundStrategy.REPLACEMENT
            else:
                return RefundStrategy.PARTIAL_REFUND

        # Baja confianza → escalación
        else:
            return RefundStrategy.ESCALATE

    def _get_resolution_text(self, reason: DisputeReason, strategy: RefundStrategy) -> str:
        """Texto de oferta de resolución."""

        offers = {
            (DisputeReason.PRODUCT_DAMAGED, RefundStrategy.REPLACEMENT): "Enviaremos producto nuevo sin cargo. El dañado lo retiramos.",
            (DisputeReason.PRODUCT_DAMAGED, RefundStrategy.PARTIAL_REFUND): "Ofrecemos 50% de refund + puedes quedarte con el producto.",
            (DisputeReason.NOT_ARRIVED, RefundStrategy.FULL_REFUND): "Reembolso 100%. Lamentamos el inconveniente.",
            (DisputeReason.PRODUCT_DIFFERENT, RefundStrategy.PARTIAL_REFUND): "Refund 70%. Te pedimos disculpas.",
        }

        return offers.get(
            (reason, strategy),
            "Nos gustaría resolver esto. ¿Cómo podemos ayudarte?",
        )

    # ========== AUTO-REFUND ==========

    async def process_refund(
        self,
        order_id: str,
        payment_method: str,  # stripe, mercadolibre, etc
        amount: float,
        reason: str,
    ) -> Dict[str, Any]:
        """Procesa refund automáticamente."""

        logger.info(f"Processing refund for order {order_id}: ${amount}")

        try:
            if payment_method == "stripe":
                result = await self.stripe.process_refund(order_id, reason)
            elif payment_method == "mercadolibre":
                result = await self.ml.process_refund(order_id, amount, reason)
            else:
                return {"status": "error", "error": f"Unknown payment method: {payment_method}"}

            if result["status"] == "success":
                # Notificar buyer
                await self._notify_buyer_refund(order_id, amount, reason)
                return result
            else:
                logger.error(f"Refund processing failed: {result}")
                return result

        except Exception as e:
            logger.error(f"Refund error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _notify_buyer_refund(self, order_id: str, amount: float, reason: str) -> None:
        """Notifica buyer vía WhatsApp."""

        message = f"✅ Refund procesado: ${amount}. Retornarán en 3-5 días hábiles. Motivo: {reason}."

        # TODO: WhatsApp notification integration
        logger.info(f"Refund notification sent for {order_id}")

    # ========== CHARGEBACK HANDLING ==========

    async def handle_chargeback(
        self,
        order_id: str,
        chargeback_amount: float,
        reason_code: str,
    ) -> Dict[str, Any]:
        """Maneja chargeback automático."""

        logger.warning(f"Chargeback received for {order_id}: ${chargeback_amount} ({reason_code})")

        # Estrategia: responder a chargeback con evidencia
        evidence = await self._gather_evidence(order_id)

        if evidence:
            logger.info(f"Submitting chargeback evidence for {order_id}")
            return {
                "status": "evidence_submitted",
                "order_id": order_id,
                "evidence": evidence,
            }
        else:
            # Sin evidencia: concede chargeback
            logger.warning(f"No evidence for {order_id}. Chargeback accepted.")
            return {"status": "chargeback_accepted"}

    async def _gather_evidence(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Reúne evidencia de transacción válida."""

        # TODO: Obtener del DB: confirmación de pago, shipping evidence, tracking, etc

        return {
            "payment_confirmation": "https://...",
            "shipping_label": "https://...",
            "tracking_number": "1234567890",
            "delivery_confirmation": "https://...",
        }

    # ========== FRAUD DETECTION ==========

    async def detect_fraud(
        self,
        order_id: str,
        amount: float,
        buyer_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detecta posible fraude en reclamo."""

        logger.info(f"Checking for fraud signals in {order_id}")

        risk_score = 0.0

        # Señales de riesgo
        if amount > 500:
            risk_score += 0.2  # Montos altos

        if buyer_info.get("account_age_days", 0) < 7:
            risk_score += 0.25  # Cuenta nueva

        if buyer_info.get("previous_disputes", 0) > 3:
            risk_score += 0.3  # Historial de reclamos

        if buyer_info.get("chargeback_rate", 0) > 0.1:
            risk_score += 0.25  # Alto chargeback rate

        is_fraud = risk_score > 0.5

        logger.info(f"Fraud risk score: {risk_score:.2f}, fraud: {is_fraud}")

        return {
            "status": "analyzed",
            "risk_score": risk_score,
            "is_fraud": is_fraud,
            "action": "escalate_to_human" if is_fraud else "process_auto",
        }
