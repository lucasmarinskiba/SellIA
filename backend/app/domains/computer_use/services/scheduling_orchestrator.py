"""Scheduling Orchestrator — Smart calendar booking from messages.

Detecta intención de agendar en mensaje → extrae info → propone slots
→ confirma → crea evento → notifica.

Conversación fluida vía WhatsApp/DM.
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from app.domains.computer_use.services.calendar_integration import (
    CalendarIntegrationService,
    CalendarEvent,
    CalendarProvider,
    TimeSlot,
)

logger = logging.getLogger(__name__)


class SchedulingIntent(str, Enum):
    """Intención detectada en mensaje."""
    SCHEDULE_REQUEST = "schedule_request"  # "Quiero agendar una cita"
    PROVIDE_DATE = "provide_date"  # "Martes"
    PROVIDE_TIME = "provide_time"  # "3pm"
    CONFIRM = "confirm"  # "Perfecto", "Sí"
    CANCEL = "cancel"  # "Cancelar", "No puedo"


class SchedulingState:
    """Estado de conversación de scheduling."""

    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.requested_at = datetime.utcnow()
        self.preferred_date: Optional[datetime] = None
        self.preferred_time: Optional[str] = None
        self.duration_minutes: int = 60
        self.available_slots: List[TimeSlot] = []
        self.proposed_slot: Optional[TimeSlot] = None
        self.confirmed: bool = False
        self.event_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "requested_at": self.requested_at.isoformat(),
            "preferred_date": self.preferred_date.isoformat() if self.preferred_date else None,
            "preferred_time": self.preferred_time,
            "duration_minutes": self.duration_minutes,
            "proposed_slot": self.proposed_slot.to_dict() if self.proposed_slot else None,
            "confirmed": self.confirmed,
            "event_id": self.event_id,
        }


class SchedulingOrchestrator:
    """Orquestador de scheduling vía mensajes."""

    # Keywords para detectar intención
    SCHEDULE_KEYWORDS = {
        "es": ["agendar", "cita", "horario", "fecha", "hora", "reunión", "llamada", "reservar"],
        "en": ["schedule", "appointment", "time", "date", "meeting", "call", "book"],
    }

    CONFIRM_KEYWORDS = {
        "es": ["sí", "si", "perfecto", "ok", "dale", "excelente", "genial", "confirmo"],
        "en": ["yes", "ok", "perfect", "great", "confirm", "sounds good"],
    }

    CANCEL_KEYWORDS = {
        "es": ["cancelar", "no puedo", "no", "después", "otro día"],
        "en": ["cancel", "no", "can't", "later", "another day"],
    }

    def __init__(self, calendar_service: CalendarIntegrationService):
        self.calendar_service = calendar_service
        self.states: Dict[str, SchedulingState] = {}  # customer_id → state

    async def process_message(
        self,
        customer_id: str,
        message: str,
    ) -> Tuple[SchedulingIntent, str, Optional[SchedulingState]]:
        """
        Procesa mensaje en contexto de scheduling.

        Retorna: (intent, response, state)
        """
        intent = self._detect_intent(message)
        state = self.states.get(customer_id)

        logger.info(f"Scheduling message: {customer_id} | intent={intent.value}")

        if intent == SchedulingIntent.SCHEDULE_REQUEST:
            # Nuevo request de agendar
            state = SchedulingState(customer_id)
            self.states[customer_id] = state

            response = "¡Claro! ¿Qué día te vendría bien para la reunión?"
            return intent, response, state

        elif intent == SchedulingIntent.PROVIDE_DATE:
            if not state:
                state = SchedulingState(customer_id)
                self.states[customer_id] = state

            # Parsear fecha
            date = self._parse_date(message)
            if date:
                state.preferred_date = date

                # Obtener slots disponibles
                slots = await self.calendar_service.get_available_slots(date)

                if slots:
                    state.available_slots = slots
                    slot_options = self._format_slot_options(slots)
                    response = f"Perfecto. Tengo disponibles estos horarios:\n{slot_options}\n\n¿Cuál te viene bien?"
                else:
                    response = "Lo siento, no tengo disponibilidad ese día. ¿Otro día?"

                return intent, response, state

        elif intent == SchedulingIntent.PROVIDE_TIME:
            if not state or not state.available_slots:
                response = "Disculpa, necesitamos empezar desde el principio. ¿Cuándo quieres agendar?"
                return intent, response, state

            # Parsear hora + encontrar slot
            time_str = self._parse_time(message)
            slot = self._find_matching_slot(state.available_slots, time_str)

            if slot:
                state.proposed_slot = slot
                response = f"Excelente. Confirmamos la cita para {self._format_datetime(slot.start)}. ¿Te parece bien?"
                return intent, response, state
            else:
                response = "No encontré ese horario. ¿Cuál prefieres?"
                return intent, response, state

        elif intent == SchedulingIntent.CONFIRM:
            if not state or not state.proposed_slot:
                response = "No hay cita pendiente de confirmar."
                return intent, response, state

            # Crear evento
            success, event_id = await self._create_event(state)

            if success:
                state.confirmed = True
                state.event_id = event_id
                response = f"¡Listo! Tu cita está confirmada para {self._format_datetime(state.proposed_slot.start)}.\n\nTe enviaremos un link de reunión."
                # Limpiar state después de tiempo
                return intent, response, state
            else:
                response = "Hubo un error al agendar. ¿Intentamos de nuevo?"
                return intent, response, state

        elif intent == SchedulingIntent.CANCEL:
            if customer_id in self.states:
                del self.states[customer_id]
            response = "Entendido. Si necesitas agendar en otro momento, avísame."
            return intent, response, None

        return SchedulingIntent.SCHEDULE_REQUEST, "¿En qué puedo ayudarte?", state

    # ── Private Methods ──────────────────────────────────────────

    def _detect_intent(self, message: str) -> SchedulingIntent:
        """Detecta intención en mensaje."""
        msg_lower = message.lower()

        if any(kw in msg_lower for kw in self.SCHEDULE_KEYWORDS.get("es", []) + self.SCHEDULE_KEYWORDS.get("en", [])):
            return SchedulingIntent.SCHEDULE_REQUEST

        if any(kw in msg_lower for kw in self.CONFIRM_KEYWORDS.get("es", []) + self.CONFIRM_KEYWORDS.get("en", [])):
            return SchedulingIntent.CONFIRM

        if any(kw in msg_lower for kw in self.CANCEL_KEYWORDS.get("es", []) + self.CANCEL_KEYWORDS.get("en", [])):
            return SchedulingIntent.CANCEL

        # Heurística: si es solo palabra corta = probablemente hora
        if re.match(r"^\d{1,2}(:?[0-5][0-9])?\s*(am|pm|a\.m\.|p\.m\.)?$", msg_lower.strip()):
            return SchedulingIntent.PROVIDE_TIME

        # Palabras de día/fecha
        if any(day in msg_lower for day in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo", "monday", "tuesday", "wednesday"]):
            return SchedulingIntent.PROVIDE_DATE

        return SchedulingIntent.SCHEDULE_REQUEST

    def _parse_date(self, message: str) -> Optional[datetime]:
        """Parsea fecha del mensaje."""
        msg_lower = message.lower()
        today = datetime.utcnow().date()

        days_map = {
            "lunes": 0,
            "martes": 1,
            "miércoles": 2,
            "jueves": 3,
            "viernes": 4,
            "sábado": 5,
            "domingo": 6,
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        for day_name, day_num in days_map.items():
            if day_name in msg_lower:
                today_day = today.weekday()
                days_ahead = day_num - today_day
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                return datetime.combine(target_date, datetime.min.time())

        # Si dice "mañana"
        if "mañana" in msg_lower or "tomorrow" in msg_lower:
            return datetime.combine(today + timedelta(days=1), datetime.min.time())

        # Si dice "hoy"
        if "hoy" in msg_lower or "today" in msg_lower:
            return datetime.combine(today, datetime.min.time())

        return None

    def _parse_time(self, message: str) -> Optional[str]:
        """Extrae hora del mensaje."""
        # Match: 10am, 3:30pm, 14:00, etc
        match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?", message.lower())
        if match:
            hour = match.group(1)
            minute = match.group(2) or "00"
            ampm = match.group(3) or ""

            return f"{hour}:{minute}{ampm}".strip()

        return None

    def _find_matching_slot(self, slots: List[TimeSlot], time_str: str) -> Optional[TimeSlot]:
        """Encuentra slot que match con hora proporcionada."""
        # Parse time_str to hour:minute format
        time_parts = re.match(r"(\d{1,2}):(\d{2})", time_str)
        if not time_parts:
            return None

        target_hour = int(time_parts.group(1))
        target_minute = int(time_parts.group(2))

        # Buscar slot más cercano
        for slot in slots:
            if slot.start.hour == target_hour and slot.start.minute <= target_minute:
                return slot

        # Si no hay match exacto, retornar primer slot disponible
        return slots[0] if slots else None

    def _format_slot_options(self, slots: List[TimeSlot]) -> str:
        """Formatea opciones de slot para mostrar."""
        options = []
        for i, slot in enumerate(slots[:5], 1):  # Max 5 opciones
            time_str = self._format_time(slot.start)
            options.append(f"{i}. {time_str}")

        return "\n".join(options)

    def _format_time(self, dt: datetime) -> str:
        """Formatea datetime a hora legible."""
        return dt.strftime("%I:%M %p").lower().replace(" ", "")

    def _format_datetime(self, dt: datetime) -> str:
        """Formatea datetime completo."""
        day_names = {
            0: "lunes",
            1: "martes",
            2: "miércoles",
            3: "jueves",
            4: "viernes",
            5: "sábado",
            6: "domingo",
        }
        day_name = day_names.get(dt.weekday(), "")
        time_str = self._format_time(dt)

        return f"{day_name} {dt.day} de {dt.strftime('%B')} a las {time_str}"

    async def _create_event(self, state: SchedulingState) -> Tuple[bool, Optional[str]]:
        """Crea evento en calendario."""
        if not state.proposed_slot:
            return False, None

        event = CalendarEvent(
            title="Cita de ventas",
            description=f"Cita agendada vía mensajes",
            start=state.proposed_slot.start,
            end=state.proposed_slot.end,
            attendee_name=state.customer_id,
            provider=state.proposed_slot.provider,
        )

        return await self.calendar_service.create_event(event)


def get_scheduling_orchestrator(
    calendar_service: CalendarIntegrationService,
) -> SchedulingOrchestrator:
    return SchedulingOrchestrator(calendar_service)
