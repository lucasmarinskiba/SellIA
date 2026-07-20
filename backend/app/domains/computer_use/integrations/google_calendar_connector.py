"""Google Calendar Connector — Real API integration.

Usa google-auth + google-api-client para operaciones reales.
OAuth2 flow para usuarios.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from google.auth.oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.api_core.exceptions import GoogleAPIError
from google.calendar import v3

logger = logging.getLogger(__name__)


class GoogleCalendarConnector:
    """Conector real de Google Calendar API."""

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob",
    ):
        """
        Inicializa connector.

        client_id, client_secret: from Google Cloud Console
        redirect_uri: donde redirige después de OAuth2
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self, state: str = "") -> str:
        """
        Genera URL para iniciar OAuth2 flow.

        Retorna: URL que usuario debe visitar.
        """
        flow = Flow.from_client_config(
            client_config={
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
        )

        flow.redirect_uri = self.redirect_uri
        auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")

        return auth_url

    def get_credentials_from_code(
        self,
        auth_code: str,
    ) -> Tuple[bool, Optional[Credentials]]:
        """
        Intercambia auth code por credenciales.

        Retorna: (success, credentials)
        """
        try:
            flow = Flow.from_client_config(
                client_config={
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=self.SCOPES,
            )

            flow.redirect_uri = self.redirect_uri
            credentials = flow.fetch_token(code=auth_code)

            return True, credentials

        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            return False, None

    async def get_available_slots(
        self,
        credentials: Dict[str, Any],
        date: datetime,
        duration_minutes: int = 60,
        working_hours: Tuple[int, int] = (9, 18),
    ) -> List[Dict[str, Any]]:
        """
        Obtiene slots disponibles para fecha.

        Usa Google Calendar API para leer eventos existentes.
        """
        try:
            # Crear servicio de calendar
            creds = Credentials.from_authorized_user_info(credentials)
            service = v3.build("calendar", "v3", credentials=creds)

            # Definir timeframe
            start_time = datetime.combine(date.date(), (working_hours[0], 0))
            end_time = datetime.combine(date.date(), (working_hours[1], 0))

            # Obtener eventos del día
            events_result = service.events().list(
                calendarId="primary",
                timeMin=start_time.isoformat() + "Z",
                timeMax=end_time.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = events_result.get("items", [])

            # Calcular slots libres
            busy_times = [(
                datetime.fromisoformat(e["start"].get("dateTime", "").replace("Z", "")),
                datetime.fromisoformat(e["end"].get("dateTime", "").replace("Z", "")),
            ) for e in events if "dateTime" in e["start"]]

            slots = []
            current = start_time

            while current + timedelta(minutes=duration_minutes) <= end_time:
                # Verificar si slot está libre
                is_free = True
                for busy_start, busy_end in busy_times:
                    if current < busy_end and current + timedelta(minutes=duration_minutes) > busy_start:
                        is_free = False
                        break

                if is_free:
                    slots.append({
                        "start": current.isoformat(),
                        "end": (current + timedelta(minutes=duration_minutes)).isoformat(),
                        "duration_minutes": duration_minutes,
                    })

                current += timedelta(minutes=30)

            logger.info(f"Found {len(slots)} available slots for {date.date()}")

            return slots

        except GoogleAPIError as e:
            logger.error(f"Google Calendar API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []

    async def create_event(
        self,
        credentials: Dict[str, Any],
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        attendee_email: Optional[str] = None,
        meeting_url: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Crea evento en Google Calendar.

        Retorna: (success, event_id)
        """
        try:
            creds = Credentials.from_authorized_user_info(credentials)
            service = v3.build("calendar", "v3", credentials=creds)

            event = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start.isoformat(),
                    "timeZone": "America/New_York",  # TODO: obtener timezone del usuario
                },
                "end": {
                    "dateTime": end.isoformat(),
                    "timeZone": "America/New_York",
                },
            }

            # Agregar attendee si se proporciona
            if attendee_email:
                event["attendees"] = [{"email": attendee_email}]

            # Agregar videoconferencia si se solicita
            if meeting_url:
                event["conferenceData"] = {
                    "entryPoints": [{"entryPointType": "video", "uri": meeting_url}]
                }

            event_result = service.events().insert(
                calendarId="primary",
                body=event,
                conferenceDataVersion=1,
                sendNotifications=True,
            ).execute()

            event_id = event_result.get("id")

            logger.info(f"Event created: {event_id} | {title}")

            return True, event_id

        except GoogleAPIError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return False, None

    async def delete_event(
        self,
        credentials: Dict[str, Any],
        event_id: str,
    ) -> bool:
        """Elimina evento de Google Calendar."""
        try:
            creds = Credentials.from_authorized_user_info(credentials)
            service = v3.build("calendar", "v3", credentials=creds)

            service.events().delete(calendarId="primary", eventId=event_id).execute()

            logger.info(f"Event deleted: {event_id}")

            return True

        except GoogleAPIError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False


def get_google_calendar_connector(
    client_id: str,
    client_secret: str,
    redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob",
) -> GoogleCalendarConnector:
    """Factory para obtener connector."""
    return GoogleCalendarConnector(client_id, client_secret, redirect_uri)
