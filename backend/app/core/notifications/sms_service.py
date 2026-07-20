"""
SMS Notifications — Twilio integration.

Soporta:
1. Confirmación de orden
2. Notificación de envío + tracking
3. Confirmación de entrega
4. Alertas de pago
5. Reembolsos
"""

import logging
import os
from typing import Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class SMSProvider(Enum):
    """Proveedores de SMS soportados."""
    TWILIO = "twilio"
    AWS_SNS = "aws_sns"


class SMSTemplate(Enum):
    """Templates de SMS predefinidos."""
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPMENT_NOTIFICATION = "shipment_notification"
    DELIVERY_CONFIRMATION = "delivery_confirmation"
    PAYMENT_FAILED = "payment_failed"
    REFUND_NOTIFICATION = "refund_notification"
    TRACKING_UPDATE = "tracking_update"


@dataclass
class SMSMessage:
    """Estructura de mensaje SMS."""
    phone_number: str  # E164 format: +5491234567890
    content: str
    template_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class SMSTemplateEngine:
    """Motor de templates SMS."""

    def __init__(self):
        self.max_length = 160  # SMS standard
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[SMSTemplate, str]:
        """Carga templates predefinidas."""
        return {
            SMSTemplate.ORDER_CONFIRMATION: "🎉 Pedido confirmado #{order_id}. Recibirás actualización cuando se despache. Gracias por tu compra.",
            SMSTemplate.SHIPMENT_NOTIFICATION: "📦 Tu pedido #{order_id} ha sido despachado. Seguimiento: {tracking_number}. Ver: {tracking_url_short}",
            SMSTemplate.DELIVERY_CONFIRMATION: "✅ Entregado! Pedido #{order_id}. Deja reseña: {review_url_short}. Gracias!",
            SMSTemplate.PAYMENT_FAILED: "⚠️ Tu pago no fue procesado. Reintentar: {retry_url_short}. Si persiste el problema, contacta a tu banco.",
            SMSTemplate.REFUND_NOTIFICATION: "✅ Reembolso de ${refund_amount} aprobado para pedido #{order_id}. Llegará en 3-5 días.",
            SMSTemplate.TRACKING_UPDATE: "📍 Seguimiento #{tracking_number}: {status_text}. ETA: {estimated_delivery}",
        }

    def render(self, template: SMSTemplate, variables: Dict[str, Any]) -> str:
        """Renderiza template con variables."""
        content = self.templates.get(template)
        if not content:
            raise ValueError(f"Template {template.value} not found")

        # Simple string replacement
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            content = content.replace(placeholder, str(value))

        # Truncar si excede límite
        if len(content) > self.max_length:
            logger.warning(f"SMS truncated from {len(content)} to {self.max_length} chars")
            content = content[: self.max_length - 3] + "..."

        return content

    def is_valid_length(self, content: str) -> bool:
        """Valida longitud del SMS."""
        return len(content) <= self.max_length


class SMSService:
    """Servicio de notificaciones por SMS."""

    def __init__(self, provider: SMSProvider = SMSProvider.TWILIO):
        self.provider = provider
        self.template_engine = SMSTemplateEngine()
        self._init_provider()

    def _init_provider(self) -> None:
        """Inicializa proveedor de SMS."""
        if self.provider == SMSProvider.TWILIO:
            self._init_twilio()
        elif self.provider == SMSProvider.AWS_SNS:
            self._init_sns()

    def _init_twilio(self) -> None:
        """Inicializa Twilio."""
        try:
            from twilio.rest import Client

            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")

            if not account_sid or not auth_token:
                raise ValueError("TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN requeridos")

            self.twilio_client = Client(account_sid, auth_token)
            logger.info(f"Twilio initialized. From: {self.twilio_phone}")

        except ImportError:
            logger.error("twilio package not installed")
            self.twilio_client = None

    def _init_sns(self) -> None:
        """Inicializa AWS SNS."""
        try:
            import boto3

            self.sns_client = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))
            logger.info("AWS SNS initialized")

        except ImportError:
            logger.error("boto3 package not installed")
            self.sns_client = None

    async def send_order_confirmation(
        self,
        phone_number: str,
        order_id: str,
    ) -> Dict[str, Any]:
        """Envía confirmación de orden por SMS."""

        variables = {
            "order_id": order_id,
        }

        content = self.template_engine.render(SMSTemplate.ORDER_CONFIRMATION, variables)

        message = SMSMessage(
            phone_number=phone_number,
            content=content,
            metadata={"order_id": order_id, "type": "order_confirmation"},
        )

        return await self.send(message)

    async def send_shipment_notification(
        self,
        phone_number: str,
        order_id: str,
        tracking_number: str,
        tracking_url: str = None,
    ) -> Dict[str, Any]:
        """Envía notificación de envío por SMS."""

        tracking_url_short = self._shorten_url(tracking_url or f"https://track.sellia.ai/{tracking_number}")

        variables = {
            "order_id": order_id,
            "tracking_number": tracking_number,
            "tracking_url_short": tracking_url_short,
        }

        content = self.template_engine.render(SMSTemplate.SHIPMENT_NOTIFICATION, variables)

        message = SMSMessage(
            phone_number=phone_number,
            content=content,
            metadata={"order_id": order_id, "tracking_number": tracking_number, "type": "shipment"},
        )

        return await self.send(message)

    async def send_delivery_confirmation(
        self,
        phone_number: str,
        order_id: str,
        review_url: str = None,
    ) -> Dict[str, Any]:
        """Envía confirmación de entrega por SMS."""

        review_url_short = self._shorten_url(review_url or f"https://review.sellia.ai/{order_id}")

        variables = {
            "order_id": order_id,
            "review_url_short": review_url_short,
        }

        content = self.template_engine.render(SMSTemplate.DELIVERY_CONFIRMATION, variables)

        message = SMSMessage(
            phone_number=phone_number,
            content=content,
            metadata={"order_id": order_id, "type": "delivery"},
        )

        return await self.send(message)

    async def send_payment_failed_alert(
        self,
        phone_number: str,
        order_id: str,
        retry_url: str = None,
    ) -> Dict[str, Any]:
        """Envía alerta de pago rechazado por SMS."""

        retry_url_short = self._shorten_url(retry_url or f"https://checkout.sellia.ai/{order_id}")

        variables = {
            "retry_url_short": retry_url_short,
        }

        content = self.template_engine.render(SMSTemplate.PAYMENT_FAILED, variables)

        message = SMSMessage(
            phone_number=phone_number,
            content=content,
            metadata={"order_id": order_id, "type": "payment_failed"},
        )

        return await self.send(message)

    async def send_refund_notification(
        self,
        phone_number: str,
        order_id: str,
        refund_amount: float,
    ) -> Dict[str, Any]:
        """Envía notificación de reembolso por SMS."""

        variables = {
            "order_id": order_id,
            "refund_amount": f"{refund_amount:.2f}",
        }

        content = self.template_engine.render(SMSTemplate.REFUND_NOTIFICATION, variables)

        message = SMSMessage(
            phone_number=phone_number,
            content=content,
            metadata={"order_id": order_id, "type": "refund", "amount": str(refund_amount)},
        )

        return await self.send(message)

    async def send_tracking_update(
        self,
        phone_number: str,
        tracking_number: str,
        status_text: str,
        estimated_delivery: str,
    ) -> Dict[str, Any]:
        """Envía actualización de seguimiento."""

        variables = {
            "tracking_number": tracking_number,
            "status_text": status_text,
            "estimated_delivery": estimated_delivery,
        }

        content = self.template_engine.render(SMSTemplate.TRACKING_UPDATE, variables)

        message = SMSMessage(
            phone_number=phone_number,
            content=content,
            metadata={"tracking_number": tracking_number, "type": "tracking_update"},
        )

        return await self.send(message)

    async def send(self, message: SMSMessage) -> Dict[str, Any]:
        """Envía SMS genérico."""

        # Validar longitud
        if not self.template_engine.is_valid_length(message.content):
            logger.warning(f"SMS content too long: {len(message.content)} chars")

        logger.info(f"Sending SMS to {message.phone_number}: {message.content[:50]}...")

        try:
            if self.provider == SMSProvider.TWILIO:
                return await self._send_twilio(message)
            elif self.provider == SMSProvider.AWS_SNS:
                return await self._send_sns(message)

        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_twilio(self, message: SMSMessage) -> Dict[str, Any]:
        """Envía via Twilio."""
        if not self.twilio_client:
            return {"status": "error", "error": "Twilio not configured"}

        try:
            msg = self.twilio_client.messages.create(
                body=message.content,
                from_=self.twilio_phone,
                to=message.phone_number,
            )

            return {
                "status": "success",
                "message_id": msg.sid,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Twilio error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_sns(self, message: SMSMessage) -> Dict[str, Any]:
        """Envía via AWS SNS."""
        if not self.sns_client:
            return {"status": "error", "error": "AWS SNS not configured"}

        try:
            response = self.sns_client.publish(
                PhoneNumber=message.phone_number,
                Message=message.content,
                MessageAttributes={
                    "AWS.SNS.SMS.SenderID": {
                        "DataType": "String",
                        "StringValue": "SellIA",
                    },
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    },
                },
            )

            return {
                "status": "success",
                "message_id": response.get("MessageId"),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"AWS SNS error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _shorten_url(self, url: str) -> str:
        """Acorta URL para SMS (implementación simplificada)."""
        if len(url) > 30:
            # En producción, usar TinyURL o similar
            return url[:27] + "..."
        return url
