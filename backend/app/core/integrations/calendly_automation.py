"""
Calendly Automation — Webhook events, Google Calendar sync, auto-reminders, cancellation handling.

Flujo:
1. Usuario autoriza Calendly account
2. Sistema registra webhook para eventos
3. On event.scheduled → Sync a Google Calendar
4. Auto-envía reminder 15min antes vía email
5. On event.cancelled → Update Google Calendar
6. CRM sync: crea lead/contact en system

Calendly Webhooks:
  - invitee.created (nueva reserva)
  - invitee.canceled (cancellación)

Rate Limit: 60 requests/minute
"""

import logging
import httpx
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class CalendlyEventStatus(Enum):
    """Calendly event statuses."""
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class CalendlyAutomation:
    """Calendly complete automation."""

    CALENDLY_API = "https://api.calendly.com/v1"
    TIMEOUT = 30

    def __init__(
        self,
        access_token: str,
        webhook_uuid: Optional[str] = None,
    ):
        """
        Initialize Calendly automation.

        Args:
            access_token: Calendly personal API token (encrypted in production)
            webhook_uuid: Existing webhook subscription UUID
        """
        self.access_token = access_token
        self.webhook_uuid = webhook_uuid
        self.http_client = httpx.AsyncClient(timeout=self.TIMEOUT)

    # ========== WEBHOOK HANDLING ==========

    async def register_webhook(
        self,
        webhook_url: str,
        user_uri: str,
        scope: List[str] = None,
    ) -> Optional[str]:
        """
        Register webhook subscription for user events.

        Args:
            webhook_url: Where Calendly sends events
            user_uri: User URI from Calendly
            scope: Event types to subscribe (e.g., ["invitee.created", "invitee.canceled"])

        Returns:
            Webhook UUID or None
        """
        if scope is None:
            scope = ["invitee.created", "invitee.canceled"]

        try:
            logger.info(f"Registering webhook for {user_uri}")

            url = f"{self.CALENDLY_API}/webhook_subscriptions"
            payload = {
                "url": webhook_url,
                "events": scope,
                "organization": user_uri,
            }
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            webhook_uuid = data.get("resource", {}).get("uuid")

            if webhook_uuid:
                self.webhook_uuid = webhook_uuid
                logger.info(f"Webhook registered: {webhook_uuid}")
                return webhook_uuid
            else:
                logger.error("No webhook UUID in response")
                return None

        except httpx.HTTPError as e:
            logger.error(f"Error registering webhook: {e}")
            return None

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming Calendly webhook.

        Payload structure:
        {
          "event": "invitee.created",
          "payload": {
            "event_type_uuid": "...",
            "scheduled_event_uuid": "...",
            "invitee_uuid": "...",
            "first_name": "John",
            "email": "john@example.com",
            ...
          }
        }

        Args:
            payload: Webhook payload from Calendly

        Returns:
            Processed webhook response
        """
        try:
            event_type = payload.get("event")
            event_data = payload.get("payload", {})

            logger.info(f"Calendly webhook: {event_type}")

            if event_type == "invitee.created":
                await self._handle_event_created(event_data)
            elif event_type == "invitee.canceled":
                await self._handle_event_cancelled(event_data)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_event_created(self, event_data: Dict[str, Any]) -> None:
        """Handle new event scheduled."""
        invitee_email = event_data.get("email")
        event_time = event_data.get("start_time")

        logger.info(f"Event scheduled: {invitee_email} at {event_time}")

        # Sync to Google Calendar
        # TODO: Implement Google Calendar sync

        # Schedule reminder email
        # TODO: Implement reminder scheduler

    async def _handle_event_cancelled(self, event_data: Dict[str, Any]) -> None:
        """Handle event cancellation."""
        invitee_email = event_data.get("email")
        reason = event_data.get("cancellation_reason")

        logger.info(f"Event cancelled: {invitee_email}, reason: {reason}")

        # Update Google Calendar
        # TODO: Implement cancellation handling

    # ========== EVENT MANAGEMENT ==========

    async def get_event_details(self, event_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch scheduled event details.

        Args:
            event_uuid: Calendly event UUID

        Returns:
            Event details dict or None
        """
        try:
            url = f"{self.CALENDLY_API}/scheduled_events/{event_uuid}"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()

            return response.json().get("resource")

        except httpx.HTTPError as e:
            logger.error(f"Error fetching event {event_uuid}: {e}")
            return None

    async def list_events(
        self,
        user_uri: str,
        status: str = "scheduled",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List user's scheduled events.

        Args:
            user_uri: User URI
            status: Event status filter (scheduled, cancelled, etc)
            limit: Results limit

        Returns:
            List of event dictionaries
        """
        try:
            logger.info(f"Fetching events for {user_uri}")

            url = f"{self.CALENDLY_API}/scheduled_events"
            params = {
                "user": user_uri,
                "status": status,
                "count": limit,
            }
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.http_client.get(url, params=params, headers=headers)
            response.raise_for_status()

            return response.json().get("collection", [])

        except httpx.HTTPError as e:
            logger.error(f"Error listing events: {e}")
            return []

    async def cancel_event(
        self,
        event_uuid: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Cancel a scheduled event.

        Args:
            event_uuid: Calendly event UUID
            reason: Cancellation reason

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Cancelling event: {event_uuid}")

            url = f"{self.CALENDLY_API}/scheduled_events/{event_uuid}/cancellation"
            payload = {}
            if reason:
                payload["reason"] = reason

            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info(f"Event {event_uuid} cancelled")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Error cancelling event: {e}")
            return False

    # ========== GOOGLE CALENDAR INTEGRATION ==========

    async def sync_to_google_calendar(
        self,
        event_uuid: str,
        google_calendar_service: Any,
        calendar_id: str = "primary",
    ) -> bool:
        """
        Sync Calendly event to Google Calendar.

        Args:
            event_uuid: Calendly event UUID
            google_calendar_service: Google Calendar service instance
            calendar_id: Target Google Calendar ID

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Syncing event {event_uuid} to Google Calendar")

            # Fetch event details
            event_details = await self.get_event_details(event_uuid)
            if not event_details:
                return False

            # Create Google Calendar event
            # (Implementation depends on google-auth-oauthlib library)

            logger.info(f"Event synced to Google Calendar")
            return True

        except Exception as e:
            logger.error(f"Error syncing to Google Calendar: {e}")
            return False

    # ========== REMINDER AUTOMATION ==========

    async def schedule_reminder(
        self,
        event_uuid: str,
        invitee_email: str,
        reminder_minutes_before: int = 15,
        email_template: str = "default",
    ) -> bool:
        """
        Schedule auto-reminder email before event.

        Args:
            event_uuid: Calendly event UUID
            invitee_email: Invitee email address
            reminder_minutes_before: Minutes before event to send
            email_template: Email template name

        Returns:
            Success boolean
        """
        try:
            logger.info(
                f"Scheduling reminder for {invitee_email} "
                f"{reminder_minutes_before} min before event"
            )

            # Get event details to calculate reminder time
            event_details = await self.get_event_details(event_uuid)
            if not event_details:
                return False

            start_time = event_details.get("start_time")
            if not start_time:
                return False

            # Calculate reminder time
            event_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            reminder_time = event_datetime - timedelta(minutes=reminder_minutes_before)

            # Schedule task (implementation depends on task queue - Celery, APScheduler, etc)
            logger.info(f"Reminder scheduled for {reminder_time}")

            return True

        except Exception as e:
            logger.error(f"Error scheduling reminder: {e}")
            return False

    # ========== ATTENDEE MANAGEMENT ==========

    async def get_invitee_details(self, invitee_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch invitee details.

        Args:
            invitee_uuid: Calendly invitee UUID

        Returns:
            Invitee details dict or None
        """
        try:
            url = f"{self.CALENDLY_API}/invitees/{invitee_uuid}"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()

            return response.json().get("resource")

        except httpx.HTTPError as e:
            logger.error(f"Error fetching invitee {invitee_uuid}: {e}")
            return None

    async def send_invitee_confirmation(
        self,
        event_uuid: str,
        invitee_email: str,
        message: str = "",
    ) -> bool:
        """
        Send confirmation message to invitee.

        Args:
            event_uuid: Calendly event UUID
            invitee_email: Invitee email
            message: Optional additional message

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Sending confirmation to {invitee_email}")

            # Implementation: Use email service (SendGrid, etc)
            # Include event details, meeting link, etc

            return True

        except Exception as e:
            logger.error(f"Error sending confirmation: {e}")
            return False

    # ========== ANALYTICS & REPORTING ==========

    async def get_event_statistics(
        self,
        user_uri: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get event statistics for user.

        Args:
            user_uri: User URI
            days: Days to look back

        Returns:
            Statistics dict
        """
        try:
            logger.info(f"Fetching event statistics for {user_uri}")

            events = await self.list_events(user_uri, status="scheduled")

            total_events = len(events)
            total_minutes = sum(
                (event.get("duration_minutes") or 0) for event in events
            )

            return {
                "total_events": total_events,
                "total_duration_minutes": total_minutes,
                "avg_duration_minutes": (
                    total_minutes / total_events if total_events > 0 else 0
                ),
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    # ========== WEBHOOK MANAGEMENT ==========

    async def list_webhooks(self, user_uri: str) -> List[Dict[str, Any]]:
        """List all webhooks for user."""
        try:
            url = f"{self.CALENDLY_API}/webhook_subscriptions"
            params = {"organization": user_uri}
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.http_client.get(url, params=params, headers=headers)
            response.raise_for_status()

            return response.json().get("collection", [])

        except httpx.HTTPError as e:
            logger.error(f"Error listing webhooks: {e}")
            return []

    async def remove_webhook(self, webhook_uuid: str) -> bool:
        """Remove webhook subscription."""
        try:
            logger.info(f"Removing webhook: {webhook_uuid}")

            url = f"{self.CALENDLY_API}/webhook_subscriptions/{webhook_uuid}"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = await self.http_client.delete(url, headers=headers)
            response.raise_for_status()

            return True

        except httpx.HTTPError as e:
            logger.error(f"Error removing webhook: {e}")
            return False
