"""Calendar Integration Service — Google Calendar + Calendly sync.

Conecta sistemas de calendario para agendar citas sin conflictos.
Soporta: Google Calendar, Calendly.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CalendarProvider(str, Enum):
    """Proveedores de calendario soportados."""

    GOOGLE_CALENDAR = "google_calendar"
    CALENDLY = "calendly"


@dataclass
class TimeSlot:
    """Slot de tiempo disponible."""

    start: datetime
    end: datetime
    provider: CalendarProvider
    is_available: bool = True

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_minutes": self.duration_minutes,
            "provider": self.provider.value,
        }


@dataclass
class CalendarEvent:
    """Evento de calendario."""

    title: str
    description: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    duration_minutes: int = 60
    organizer_email: str | None = None
    attendee_email: str | None = None
    attendee_name: str | None = None
    meeting_url: str | None = None  # Zoom/Meet link
    provider: CalendarProvider = CalendarProvider.GOOGLE_CALENDAR
    event_id: str | None = None  # ID en plataforma
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "duration_minutes": self.duration_minutes,
            "organizer_email": self.organizer_email,
            "attendee_email": self.attendee_email,
            "attendee_name": self.attendee_name,
            "meeting_url": self.meeting_url,
            "provider": self.provider.value,
            "event_id": self.event_id,
        }


class GoogleCalendarClient:
    """Cliente para Google Calendar API (placeholder)."""

    def __init__(self, credentials_dict: dict[str, Any]):
        """
        Inicializa cliente con credenciales.

        credentials_dict: token dict desde Google OAuth2.
        """
        self.credentials = credentials_dict
        self.calendar_id = credentials_dict.get("calendar_id", "primary")

    async def get_availability(
        self,
        date: datetime,
        duration_minutes: int = 60,
        working_hours: tuple[time, time] = (time(9, 0), time(18, 0)),
    ) -> list[TimeSlot]:
        """
        Obtiene slots disponibles para fecha.

        Considera:
        - Eventos existentes
        - Horario de trabajo
        - Duración requerida
        """
        # TODO: Usar google.calendar.v3 API
        # Placeholder: retorna slots cada hora entre 9am-6pm
        slots = []

        start = datetime.combine(date.date(), working_hours[0])
        end = datetime.combine(date.date(), working_hours[1])

        current = start
        while current + timedelta(minutes=duration_minutes) <= end:
            slots.append(
                TimeSlot(
                    start=current,
                    end=current + timedelta(minutes=duration_minutes),
                    provider=CalendarProvider.GOOGLE_CALENDAR,
                    is_available=True,
                )
            )
            current += timedelta(minutes=30)

        return slots

    async def create_event(self, event: CalendarEvent) -> tuple[bool, str | None]:
        """
        Crea evento en Google Calendar.

        Retorna: (success, event_id)
        """
        # TODO: Usar google.calendar.v3 API
        logger.info(f"Creating Google Calendar event: {event.title} at {event.start}")
        return True, "event_id_placeholder"

    async def delete_event(self, event_id: str) -> bool:
        """Elimina evento."""
        logger.info(f"Deleting Google Calendar event: {event_id}")
        return True


class CalendlyClient:
    """Cliente para Calendly API (placeholder)."""

    def __init__(self, api_token: str):
        """Inicializa con token de Calendly."""
        self.api_token = api_token
        self.base_url = "https://api.calendly.com"

    async def get_availability(
        self,
        date: datetime,
        duration_minutes: int = 60,
    ) -> list[TimeSlot]:
        """Obtiene slots disponibles de evento tipo en Calendly."""
        # TODO: Llamar Calendly API v2 /availability_schedules
        slots = []

        start = datetime.combine(date.date(), time(9, 0))
        end = datetime.combine(date.date(), time(18, 0))

        current = start
        while current + timedelta(minutes=duration_minutes) <= end:
            slots.append(
                TimeSlot(
                    start=current,
                    end=current + timedelta(minutes=duration_minutes),
                    provider=CalendarProvider.CALENDLY,
                    is_available=True,
                )
            )
            current += timedelta(minutes=30)

        return slots

    async def create_event(self, event: CalendarEvent) -> tuple[bool, str | None]:
        """Crea evento en Calendly."""
        logger.info(f"Creating Calendly event: {event.title} at {event.start}")
        return True, "event_id_placeholder"


class CalendarIntegrationService:
    """Servicio centralizado de calendario."""

    def __init__(
        self,
        google_credentials: dict[str, Any] | None = None,
        calendly_token: str | None = None,
    ):
        self.google_client = (
            GoogleCalendarClient(google_credentials) if google_credentials else None
        )
        self.calendly_client = (
            CalendlyClient(calendly_token) if calendly_token else None
        )

    async def get_available_slots(
        self,
        date: datetime,
        duration_minutes: int = 60,
        provider: CalendarProvider | None = None,
    ) -> list[TimeSlot]:
        """Obtiene slots disponibles (unifica múltiples calendarios)."""
        all_slots = []

        if provider in (None, CalendarProvider.GOOGLE_CALENDAR) and self.google_client:
            slots = await self.google_client.get_availability(date, duration_minutes)
            all_slots.extend(slots)

        if provider in (None, CalendarProvider.CALENDLY) and self.calendly_client:
            slots = await self.calendly_client.get_availability(date, duration_minutes)
            all_slots.extend(slots)

        # Remover duplicados + ordenar
        unique_slots = {}
        for slot in all_slots:
            key = f"{slot.start}|{slot.end}"
            if key not in unique_slots:
                unique_slots[key] = slot

        return sorted(unique_slots.values(), key=lambda s: s.start)

    async def create_event(
        self,
        event: CalendarEvent,
    ) -> tuple[bool, str | None]:
        """Crea evento en calendario seleccionado."""
        if event.provider == CalendarProvider.GOOGLE_CALENDAR:
            if not self.google_client:
                logger.error("Google Calendar client not configured")
                return False, None
            return await self.google_client.create_event(event)

        elif event.provider == CalendarProvider.CALENDLY:
            if not self.calendly_client:
                logger.error("Calendly client not configured")
                return False, None
            return await self.calendly_client.create_event(event)

        return False, None

    async def check_conflicts(
        self,
        event: CalendarEvent,
    ) -> tuple[bool, list[str] | None]:
        """
        Verifica si hay conflictos.

        Retorna: (has_conflict, conflicting_event_ids)
        """
        # TODO: Comparar con eventos existentes
        return False, None


def get_calendar_service(
    google_credentials: dict[str, Any] | None = None,
    calendly_token: str | None = None,
) -> CalendarIntegrationService:
    """Factory para obtener servicio calendar."""
    return CalendarIntegrationService(google_credentials, calendly_token)
