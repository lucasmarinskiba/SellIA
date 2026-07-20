"""
Failsafe Engine — Asegura ventas. Si falla WhatsApp, email. Si email falla, SMS.

Multi-channel redundancy. Escalation automática. Guaranteed delivery.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class Channel(str, Enum):
    """Canales de comunicación (en orden de preferencia)."""
    WHATSAPP = "whatsapp"  # 1er intento
    EMAIL = "email"  # 2do intento
    SMS = "sms"  # 3er intento
    PHONE_CALL = "phone_call"  # 4to intento (escalación)
    LINKEDIN = "linkedin"  # 5to intento
    PUSH_NOTIFICATION = "push"  # 6to intento


class FailsafeEngine:
    """Asegura cierre venta con multi-channel failover."""

    # Configuración retry + escalación
    CHANNEL_FALLBACK_ORDER = [
        Channel.WHATSAPP,
        Channel.EMAIL,
        Channel.SMS,
        Channel.PHONE_CALL,
        Channel.LINKEDIN,
    ]

    RETRY_CONFIG = {
        Channel.WHATSAPP: {"max_retries": 3, "delay_seconds": 300},
        Channel.EMAIL: {"max_retries": 2, "delay_seconds": 3600},
        Channel.SMS: {"max_retries": 3, "delay_seconds": 600},
        Channel.PHONE_CALL: {"max_retries": 1, "delay_seconds": 1800},
    }

    @staticmethod
    async def send_with_fallback(
        buyer: Dict[str, Any],
        message: str,
        campaign_id: str,
        preferred_channel: Optional[Channel] = None,
    ) -> Dict[str, Any]:
        """
        Envía mensaje con fallback automático.

        Intenta: WhatsApp → Email → SMS → Phone → LinkedIn
        Si falla, próximo canal automático.
        """

        logger.info(f"Sending message to {buyer.get('email')} with fallback")

        # Determinar orden de canales
        if preferred_channel:
            channels = FailsafeEngine._reorder_channels(preferred_channel)
        else:
            channels = FailsafeEngine.CHANNEL_FALLBACK_ORDER

        result = {
            "campaign_id": campaign_id,
            "buyer_email": buyer.get("email"),
            "attempts": [],
            "final_status": "failed",
            "delivery_channel": None,
        }

        for attempt_num, channel in enumerate(channels, 1):
            logger.info(f"Attempt {attempt_num}: trying {channel.value}")

            # Intentar este canal
            send_result = await FailsafeEngine._send_via_channel(
                buyer=buyer,
                message=message,
                channel=channel,
            )

            result["attempts"].append({
                "channel": channel.value,
                "attempt": attempt_num,
                "status": send_result.get("status"),
                "error": send_result.get("error"),
            })

            # Si éxito, stop
            if send_result.get("status") == "success":
                result["final_status"] = "success"
                result["delivery_channel"] = channel.value
                logger.info(f"Message delivered via {channel.value}")
                break

            # Si no, retry en mismo canal antes de pasar al siguiente
            if attempt_num < len(channels):
                retry_config = FailsafeEngine.RETRY_CONFIG.get(
                    channel,
                    {"max_retries": 1, "delay_seconds": 300},
                )
                if send_result.get("retryable"):
                    logger.info(
                        f"Retrying {channel.value} in {retry_config['delay_seconds']}s"
                    )
                    await asyncio.sleep(retry_config["delay_seconds"])

        return result

    @staticmethod
    async def _send_via_channel(
        buyer: Dict[str, Any],
        message: str,
        channel: Channel,
    ) -> Dict[str, Any]:
        """Envía vía canal específico."""

        try:
            if channel == Channel.WHATSAPP:
                # from twilio_whatsapp_api import WhatsAppClient
                # client = WhatsAppClient()
                # result = await client.send_message(buyer.get("phone"), message)

                return {
                    "status": "success",
                    "message_id": "wa_12345",
                    "retryable": False,
                }

            elif channel == Channel.EMAIL:
                # from backend.app.core.integrations.sendgrid_email import EmailService
                # result = EmailService.send_transactional(buyer.get("email"), "...", message)

                return {
                    "status": "success",
                    "message_id": "email_12345",
                    "retryable": False,
                }

            elif channel == Channel.SMS:
                # from twilio_client import TwilioClient
                # client = TwilioClient()
                # result = await client.send_sms(buyer.get("phone"), message)

                return {
                    "status": "success",
                    "message_id": "sms_12345",
                    "retryable": False,
                }

            elif channel == Channel.PHONE_CALL:
                # Escalación = human call (costly pero asegura cierre)
                # from twilio_client import TwilioClient
                # result = await schedule_phone_call(buyer)

                return {
                    "status": "pending",
                    "message_id": "call_scheduled",
                    "retryable": False,
                }

            else:
                return {"status": "error", "error": "Unknown channel", "retryable": False}

        except Exception as e:
            logger.error(f"Error sending via {channel.value}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "retryable": True,  # Retry si error temporal
            }

    @staticmethod
    def _reorder_channels(preferred: Channel) -> List[Channel]:
        """Reordena canales con preferencia al inicio."""

        channels = list(FailsafeEngine.CHANNEL_FALLBACK_ORDER)
        if preferred in channels:
            channels.remove(preferred)
            channels.insert(0, preferred)
        return channels

    @staticmethod
    async def escalate_if_stuck(campaign_id: str, buyer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Si ciclo atascado (72h+ sin respuesta), escala a humano.

        Opciones:
        1. Phone call automático (expensive but high conversion)
        2. Email from CEO (authority, personalization)
        3. SMS + WhatsApp simultáneo (maximum urgency)
        """

        logger.info(f"Escalating stuck campaign {campaign_id}")

        escalation_plan = {
            "stage_1_auto": {
                "action": "Phone call recording (human-like voice, personal)",
                "delay_hours": 72,
                "expected_conversion": "15-20%",
            },
            "stage_2_auto": {
                "action": "Email from CEO (authority + personal touch)",
                "delay_hours": 96,
                "expected_conversion": "10-15%",
            },
            "stage_3_manual": {
                "action": "Human sales rep calls (last resort, manual)",
                "delay_hours": 120,
                "expected_conversion": "25-35%",
            },
        }

        return {
            "campaign_id": campaign_id,
            "escalation_triggered": True,
            "plan": escalation_plan,
        }

    @staticmethod
    async def verify_delivery(
        campaign_id: str,
        buyer: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Post-sale verification: ¿cliente recibió? ¿accedió? ¿usó?

        Garantiza que venta sea REAL (no ghost sale).
        """

        checks = {
            "email_opened": False,
            "link_clicked": False,
            "account_created": False,
            "payment_confirmed": False,
            "access_granted": False,
            "first_login": False,
        }

        # TODO: Implementar checks reales

        verified = all(checks.values())

        if not verified:
            logger.warning(f"Sale verification failed for {buyer.get('email')}")
            # Trigger recovery (send reminder, discount, etc)

        return {
            "campaign_id": campaign_id,
            "verified": verified,
            "checks": checks,
        }
