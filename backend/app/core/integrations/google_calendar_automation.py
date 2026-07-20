"""
Google Calendar Automation — Scheduling, conflict detection, delivery tracking.

Usuario ingresa:
- GOOGLE_CALENDAR_API_KEY
- GOOGLE_CALENDAR_ID

Sistema:
- Crea eventos desde WhatsApp (ej: "mañana 15hs")
- Detecta conflictos (no double-book)
- Sincroniza entregas con llamadas
- Bloquea horarios si usuario de viaje
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class GoogleCalendarAutomation:
    """Google Calendar automation + conflict detection."""

    CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3"

    def __init__(self, api_key: str, calendar_id: str):
        self.api_key = api_key
        self.calendar_id = calendar_id
        self.http_client = httpx.AsyncClient(timeout=30)

    # ========== EVENT CREATION ==========

    async def create_event(
        self,
        title: str,
        description: str,
        start_time: datetime,
        duration_minutes: int = 30,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Crea evento en Google Calendar.

        Con conflict detection automático.
        """

        logger.info(f"Creating calendar event: {title}")

        # Detectar conflictos
        conflict_check = await self._check_conflicts(start_time, duration_minutes)

        if conflict_check["has_conflict"]:
            logger.warning(f"Conflict detected: {conflict_check['conflicts']}")

            # Buscar slot disponible
            alternative_time = await self._find_available_slot(start_time, duration_minutes)

            if alternative_time:
                logger.info(f"Proposing alternative: {alternative_time}")
                return {
                    "status": "conflict",
                    "conflict_with": conflict_check["conflicts"],
                    "suggested_time": alternative_time.isoformat(),
                    "action": "ask_user",
                }

            else:
                return {
                    "status": "no_available_slots",
                    "requested_time": start_time.isoformat(),
                }

        # Sin conflictos, crear evento
        end_time = start_time + timedelta(minutes=duration_minutes)

        event_body = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Argentina/Buenos_Aires",  # TODO: user timezone
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Argentina/Buenos_Aires",
            },
            "attendees": [{"email": email} for email in (attendees or [])],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "notification", "minutes": 10},  # Reminder 10 min antes
                ],
            },
        }

        try:
            response = await self.http_client.post(
                f"{self.CALENDAR_API_URL}/calendars/{self.calendar_id}/events",
                json=event_body,
                params={"key": self.api_key},
            )

            if response.status_code in [200, 201]:
                event = response.json()
                logger.info(f"Event created: {event['id']}")

                return {
                    "status": "success",
                    "event_id": event["id"],
                    "event_link": event.get("htmlLink"),
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                }
            else:
                logger.error(f"Create event failed: {response.status_code}")
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Create event failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ========== CONFLICT DETECTION ==========

    async def _check_conflicts(
        self,
        start_time: datetime,
        duration_minutes: int,
    ) -> Dict[str, Any]:
        """Detecta conflictos en el calendario."""

        logger.info(f"Checking conflicts for {start_time}")

        end_time = start_time + timedelta(minutes=duration_minutes)

        try:
            response = await self.http_client.get(
                f"{self.CALENDAR_API_URL}/calendars/{self.calendar_id}/events",
                params={
                    "key": self.api_key,
                    "timeMin": start_time.isoformat(),
                    "timeMax": end_time.isoformat(),
                    "singleEvents": True,
                    "maxResults": 10,
                },
            )

            if response.status_code == 200:
                events = response.json().get("items", [])

                if events:
                    logger.warning(f"Found {len(events)} conflicts")
                    return {
                        "has_conflict": True,
                        "conflicts": [
                            {
                                "title": e.get("summary"),
                                "start": e.get("start", {}).get("dateTime"),
                                "end": e.get("end", {}).get("dateTime"),
                            }
                            for e in events
                        ],
                    }
                else:
                    return {"has_conflict": False}
            else:
                logger.error(f"Conflict check failed: {response.status_code}")
                return {"has_conflict": False, "warning": "Could not verify conflicts"}

        except Exception as e:
            logger.error(f"Conflict check failed: {str(e)}")
            return {"has_conflict": False, "warning": str(e)}

    async def _find_available_slot(
        self,
        preferred_time: datetime,
        duration_minutes: int,
    ) -> Optional[datetime]:
        """Busca primer slot disponible después de preferred_time."""

        logger.info("Finding available slot")

        for days_ahead in range(7):  # Check próximos 7 días
            for hour in [9, 10, 11, 14, 15, 16, 17]:  # Horarios de negocio
                candidate_time = preferred_time.replace(hour=hour, minute=0)
                candidate_time += timedelta(days=days_ahead)

                conflict_check = await self._check_conflicts(candidate_time, duration_minutes)

                if not conflict_check["has_conflict"]:
                    logger.info(f"Available slot found: {candidate_time}")
                    return candidate_time

        logger.warning("No available slot found")
        return None

    # ========== DELIVERY SCHEDULING ==========

    async def block_delivery_time(
        self,
        delivery_date: datetime,
        duration_hours: int,
        reason: str = "Entrega",
    ) -> Dict[str, Any]:
        """Bloquea horario de entrega en calendario (no agendar llamadas)."""

        logger.info(f"Blocking delivery slot: {delivery_date}")

        return await self.create_event(
            title=f"📦 {reason}",
            description=f"No agendar llamadas. {reason} en progreso.",
            start_time=delivery_date,
            duration_minutes=duration_hours * 60,
        )

    # ========== TRAVEL MODE ==========

    async def set_travel_mode(
        self,
        start_date: datetime,
        end_date: datetime,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Bloquea período completo (usuario de viaje)."""

        logger.info(f"Setting travel mode: {start_date} to {end_date}")

        # Crear bloque de disponibilidad
        return await self.create_event(
            title="✈️ TRAVEL MODE - No agendar",
            description=f"Usuario no disponible. {notes}",
            start_time=start_date,
            duration_minutes=int((end_date - start_date).total_seconds() / 60),
        )

    # ========== AVAILABILITY CHECK ==========

    async def get_available_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 30,
    ) -> Dict[str, Any]:
        """Retorna slots disponibles para agendar (próximos N días)."""

        logger.info(f"Getting available slots between {start_date} and {end_date}")

        available_slots = []

        current = start_date

        while current < end_date:
            for hour in [9, 10, 11, 14, 15, 16, 17]:
                candidate_time = current.replace(hour=hour, minute=0)

                conflict_check = await self._check_conflicts(candidate_time, duration_minutes)

                if not conflict_check["has_conflict"]:
                    available_slots.append(candidate_time)

            current += timedelta(days=1)

        logger.info(f"Found {len(available_slots)} available slots")

        return {
            "status": "success",
            "available_slots": [s.isoformat() for s in available_slots[:10]],  # Primeros 10
            "total_found": len(available_slots),
        }

    async def close(self):
        """Cierra conexión HTTP."""
        await self.http_client.aclose()
