"""Calendly API Connector — Real booking integration.

Alternativa a Google Calendar para scheduling.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
import httpx

logger = logging.getLogger(__name__)


class CalendlyConnector:
    """Conector real de Calendly API."""

    BASE_URL = "https://api.calendly.com"

    def __init__(self, access_token: str):
        """access_token: Personal access token from Calendly"""
        self.access_token = access_token
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )

    async def get_availability(
        self,
        event_type_id: str,
        date: str,  # YYYY-MM-DD
    ) -> List[Dict[str, Any]]:
        """Obtiene slots disponibles."""
        try:
            url = f"{self.BASE_URL}/event_type_availability"

            params = {
                "event_type": event_type_id,
                "date": date,
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            result = response.json()

            return result.get("data", {}).get("available_periods", [])

        except Exception as e:
            logger.error(f"Error getting availability: {e}")
            return []

    async def create_event(
        self,
        event_type_id: str,
        start_time: str,  # ISO format
        invitee_email: str,
        invitee_name: str,
    ) -> Tuple[bool, Optional[str]]:
        """Crea evento en Calendly."""
        try:
            url = f"{self.BASE_URL}/scheduled_events"

            data = {
                "event_type": event_type_id,
                "start_time": start_time,
                "invitee": {
                    "email": invitee_email,
                    "name": invitee_name,
                },
            }

            response = await self.client.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            event_id = result.get("data", {}).get("id")

            logger.info(f"Calendly event created: {event_id}")

            return True, event_id

        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return False, None

    async def close(self):
        await self.client.aclose()


def get_calendly_connector(access_token: str) -> CalendlyConnector:
    return CalendlyConnector(access_token)
