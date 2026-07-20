"""
WhatsApp Automation — Dual mode (API + Computer Use) + Calendar scheduling + Bots.

Modo 1: WhatsApp Business API (WABA)
- Usuario ingresa API token + phone
- Sistema recibe webhooks (incoming messages)

Modo 2: WhatsApp Web + Computer Use
- App en ordenador usuario
- Sistema controla via CV (lee, responde)
- Gratis, sin API limits

Respuestas:
- Bots prediseñados (FAQ engine)
- Computer Use + CV (dynamic responses)

Scheduling:
- Extrae "podemos mañana 15hs?"
- Agrega Google Calendar
- Evita conflictos
"""

import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import re

logger = logging.getLogger(__name__)


class WhatsAppAutomation:
    """WhatsApp Automation — mensajes + scheduling + routing."""

    WABA_API_URL = "https://graph.instagram.com/v18.0"

    def __init__(
        self,
        mode: str = "api",  # "api" o "computer_use"
        waba_token: Optional[str] = None,
        waba_phone_id: Optional[str] = None,
        computer_vision_engine: Optional[Any] = None,
        calendar_service: Optional[Any] = None,
    ):
        self.mode = mode  # API or Computer Use
        self.waba_token = waba_token
        self.waba_phone_id = waba_phone_id
        self.cv = computer_vision_engine
        self.calendar = calendar_service
        self.http_client = httpx.AsyncClient(timeout=30)
        self.bots_config = {}

    # ========== WEBHOOK HANDLING (API MODE) ==========

    async def handle_incoming_message(self, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa mensaje incoming desde WhatsApp Business API.

        Webhook payload estructura:
        {
          "entry": [{
            "messaging": [{
              "sender": {"id": "..."},
              "message": {"text": "..."}
            }]
          }]
        }
        """

        logger.info("Processing incoming WhatsApp message")

        try:
            # Extraer mensaje
            sender_id = webhook_payload["entry"][0]["messaging"][0]["sender"]["id"]
            message_text = webhook_payload["entry"][0]["messaging"][0]["message"]["text"]
            timestamp = webhook_payload["entry"][0]["messaging"][0]["timestamp"]

            logger.info(f"Message from {sender_id}: {message_text}")

            # Detectar tipo de mensaje
            message_type = self._classify_message(message_text)

            # Procesar según tipo
            if message_type == "urgency":
                # Ruta a humano
                logger.warning(f"Urgency detected from {sender_id}")
                return await self._route_to_human(sender_id, message_text)

            elif message_type == "scheduling":
                # Extraer fecha/hora, agendar
                logger.info(f"Scheduling request detected")
                return await self._handle_scheduling_request(sender_id, message_text)

            else:
                # Responder con bot o CV
                return await self._generate_response(sender_id, message_text)

        except Exception as e:
            logger.error(f"Handle message failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _classify_message(self, text: str) -> str:
        """Clasifica tipo de mensaje (urgency, scheduling, etc)."""

        text_lower = text.lower()

        urgency_keywords = ["urgente", "problema", "no funciona", "reclamar", "abogado", "chargeback", "fraude"]
        if any(keyword in text_lower for keyword in urgency_keywords):
            return "urgency"

        scheduling_keywords = ["mañana", "hoy", "hora", "podemos", "disponible", "cuando", "qué hora", "meeting", "llamada"]
        if any(keyword in text_lower for keyword in scheduling_keywords):
            return "scheduling"

        return "standard"

    async def _route_to_human(self, sender_id: str, message: str) -> Dict[str, Any]:
        """Ruta mensaje urgente a humano."""

        logger.warning(f"Routing to human: {sender_id}")

        # TODO: Notificar usuario (email, SMS, in-app alert)
        # TODO: Guardar en DB como "pending_human_review"

        return {
            "status": "routed_to_human",
            "sender_id": sender_id,
            "reason": "urgency_detected",
            "message": message,
        }

    async def _handle_scheduling_request(self, sender_id: str, message: str) -> Dict[str, Any]:
        """Extrae fecha/hora del mensaje, agendando en Google Calendar."""

        logger.info(f"Scheduling request: {message}")

        # Extraer fecha/hora con regex
        time_match = re.search(r"(\d{1,2}):(\d{2})", message)
        date_match = re.search(r"(mañana|hoy|próximo|siguiente|día|lunes|martes|miércoles|jueves|viernes|sábado|domingo)", message, re.IGNORECASE)

        if not (time_match and date_match):
            # Pedir clarificación
            response = await self._send_message(
                sender_id,
                "Para agendar, porfa indicá: fecha (ej: mañana, lunes) y hora (ej: 15:30). Ejemplo: 'Mañana a las 3pm'",
            )
            return {"status": "clarification_requested"}

        hour = int(time_match.group(1))
        minute = int(time_match.group(2))

        # Calcular fecha (simplificado)
        if "hoy" in message.lower():
            scheduled_date = datetime.now()
        elif "mañana" in message.lower():
            scheduled_date = datetime.now() + timedelta(days=1)
        else:
            scheduled_date = datetime.now() + timedelta(days=3)  # Default: 3 días

        scheduled_datetime = scheduled_date.replace(hour=hour, minute=minute)

        # Agregar a Google Calendar
        if self.calendar:
            calendar_result = await self.calendar.create_event(
                title=f"Call with {sender_id}",
                description=f"WhatsApp call scheduled from: {message}",
                start_time=scheduled_datetime,
                duration_minutes=30,
            )

            if calendar_result["status"] == "success":
                # Confirmar al usuario
                response = await self._send_message(
                    sender_id,
                    f"✅ Agendado! Nos vemos {scheduled_datetime.strftime('%A a las %H:%M')}. Te enviaré link de llamada 10 min antes.",
                )

                return {
                    "status": "scheduled",
                    "sender_id": sender_id,
                    "datetime": scheduled_datetime.isoformat(),
                    "calendar_event": calendar_result.get("event_id"),
                }
            else:
                response = await self._send_message(
                    sender_id,
                    "⚠️ Error al agendar. Intenta de nuevo o contacta soporte.",
                )
                return {"status": "scheduling_error"}

        return {"status": "error", "reason": "calendar_service_not_configured"}

    async def _generate_response(self, sender_id: str, message: str) -> Dict[str, Any]:
        """Genera respuesta (bot o Computer Use)."""

        logger.info(f"Generating response for: {message}")

        # Opción 1: Bot prediseñado
        bot_response = self._check_bot_response(message)

        if bot_response:
            logger.info("Using bot response")
            result = await self._send_message(sender_id, bot_response)
            return {"status": "bot_response", "response": bot_response}

        # Opción 2: Computer Use + CV (si disponible)
        if self.cv and self.mode == "computer_use":
            logger.info("Using Computer Use + CV")
            cv_response = await self.cv.suggest_next_action(
                screenshot=None,  # TODO: screenshot from WhatsApp Web
                goal=f"Respond to WhatsApp: {message}",
            )

            if cv_response["status"] == "success":
                response_text = cv_response.get("suggestion", {}).get("next_action", "No entiendo, podés reformular?")
                result = await self._send_message(sender_id, response_text)
                return {"status": "cv_response", "response": response_text}

        # Fallback: respuesta genérica
        default_response = "Gracias por tu mensaje! En breve nos ponemos en contacto. Si es urgente, escribí 'urgente'."
        result = await self._send_message(sender_id, default_response)

        return {"status": "default_response", "response": default_response}

    def _check_bot_response(self, message: str) -> Optional[str]:
        """Busca bot response prediseñado para el mensaje."""

        message_lower = message.lower()

        # Bots globales (default)
        default_bots = {
            "hola": "¡Hola! 👋 Cómo estás? Te ayudo con lo que necesites.",
            "precio": "Consulta nuestro catálogo en https://tienda.com. ¿Algo específico que buscas?",
            "envío": "Enviamos en 24-48hs a todo el país. Costo depende de tu zona. ¿Dónde estás?",
            "garantía": "Todos nuestros productos tienen garantía de 1 año. Cualquier problema, nosotros nos hacemos cargo.",
            "pago": "Aceptamos todos los métodos: transferencia, Mercado Pago, tarjeta. ¿Cuál preferís?",
            "gracias": "¡De nada! Cualquier cosa, acá estamos. 😊",
        }

        # Buscar match
        for keyword, response in default_bots.items():
            if keyword in message_lower:
                return response

        # TODO: Cargar bots personalizados del usuario (stored en DB)

        return None

    async def _send_message(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """Envía mensaje via WhatsApp API o Computer Use."""

        if self.mode == "api":
            return await self._send_via_api(recipient_id, text)
        else:
            return await self._send_via_computer_use(recipient_id, text)

    async def _send_via_api(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """Envía via WhatsApp Business API."""

        logger.info(f"Sending via API to {recipient_id}")

        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient_id,
                "type": "text",
                "text": {"preview_url": True, "body": text},
            }

            response = await self.http_client.post(
                f"{self.WABA_API_URL}/{self.waba_phone_id}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {self.waba_token}"},
            )

            if response.status_code == 200:
                logger.info(f"Message sent to {recipient_id}")
                return {"status": "success", "message_id": response.json().get("messages", [{}])[0].get("id")}
            else:
                logger.error(f"Send failed: {response.status_code}")
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Send via API failed: {str(e)}")
            return {"status": "error"}

    async def _send_via_computer_use(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """Envía via Computer Use (WhatsApp Web)."""

        logger.info(f"Sending via Computer Use to {recipient_id}")

        # TODO: Computer Use workflow
        # 1. Screenshot de WhatsApp Web
        # 2. CV detecta chat con recipient_id
        # 3. Clickea, escribe mensaje
        # 4. Envía

        return {"status": "scheduled_for_computer_use", "recipient": recipient_id, "text": text}

    async def close(self):
        """Cierra conexión HTTP."""
        await self.http_client.aclose()


class WhatsAppBotBuilder:
    """Builder para crear bots personalizados sin code."""

    def __init__(self):
        self.bots: Dict[str, Dict[str, str]] = {}

    def add_bot(self, bot_name: str, patterns: List[str], response: str) -> None:
        """Agrega bot prediseñado."""

        self.bots[bot_name] = {
            "patterns": patterns,
            "response": response,
        }

        logger.info(f"Bot added: {bot_name}")

    def get_response(self, message: str) -> Optional[str]:
        """Obtiene respuesta si hay match."""

        message_lower = message.lower()

        for bot_name, config in self.bots.items():
            for pattern in config["patterns"]:
                if pattern.lower() in message_lower:
                    return config["response"]

        return None

    def export_config(self) -> Dict[str, Any]:
        """Exporta configuración de bots."""
        return self.bots

    def import_config(self, config: Dict[str, Any]) -> None:
        """Importa configuración de bots."""
        self.bots = config
        logger.info(f"Imported {len(self.bots)} bots")
