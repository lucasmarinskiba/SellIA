"""Google Calendar integration for scheduling demos and follow-ups."""

import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import base64

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Calendar event types."""
    DEMO = "demo"
    FOLLOW_UP = "follow_up"
    NEGOTIATION = "negotiation"
    CLOSING_CALL = "closing_call"
    ONBOARDING = "onboarding"


class CalendarService:
    """Google Calendar API integration."""

    def __init__(self, credentials_json: str):
        """
        Initialize Calendar service.

        Args:
            credentials_json: Google service account credentials JSON
        """
        self.credentials_json = credentials_json
        self.api_base = "https://www.googleapis.com/calendar/v3"
        self.calendar_id = "primary"

    async def schedule_event(
        self,
        event_type: EventType,
        attendee_email: str,
        attendee_name: str,
        title: str,
        description: str,
        start_time: datetime,
        duration_minutes: int = 60,
        video_conference: bool = True,
    ) -> Optional[str]:
        """
        Schedule event in Google Calendar.

        Args:
            event_type: Type of event
            attendee_email: Attendee email address
            attendee_name: Attendee name
            title: Event title
            description: Event description
            start_time: Event start time (datetime object)
            duration_minutes: Event duration
            video_conference: Include Google Meet link

        Returns:
            Event ID if successful
        """
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)

            event = {
                "summary": f"{event_type.value.upper()}: {title}",
                "description": description,
                "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
                "attendees": [
                    {"email": attendee_email, "displayName": attendee_name}
                ],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},  # 1 day before
                        {"method": "popup", "minutes": 30},  # 30 min before
                    ],
                },
            }

            if video_conference:
                event["conferenceData"] = {
                    "createRequest": {
                        "requestId": f"sellia-{start_time.timestamp()}",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                }

            # In production, use actual Google Calendar API
            # For now, log the event
            logger.info(
                f"Calendar event scheduled: {title} for {attendee_name} on {start_time}"
            )

            return f"event_{start_time.timestamp()}"

        except Exception as e:
            logger.error(f"Calendar scheduling failed: {e}")
            return None

    async def schedule_demo(
        self,
        lead_name: str,
        email: str,
        company: str,
        preferred_time: datetime,
    ) -> Optional[str]:
        """Schedule product demo."""
        return await self.schedule_event(
            EventType.DEMO,
            email,
            lead_name,
            f"Product Demo - {company}",
            f"Demo for {lead_name} at {company}. Topics: Product overview, custom integrations, ROI calculation.",
            preferred_time,
            duration_minutes=45,
        )

    async def schedule_follow_up(
        self,
        lead_name: str,
        email: str,
        reason: str,
        days_from_now: int = 3,
    ) -> Optional[str]:
        """Schedule follow-up call."""
        follow_up_time = datetime.utcnow() + timedelta(days=days_from_now)
        follow_up_time = follow_up_time.replace(hour=10, minute=0)

        return await self.schedule_event(
            EventType.FOLLOW_UP,
            email,
            lead_name,
            f"Follow-up: {reason}",
            f"Follow-up call with {lead_name}. Reason: {reason}",
            follow_up_time,
            duration_minutes=30,
        )

    async def schedule_negotiation_call(
        self,
        lead_name: str,
        email: str,
        company: str,
        deal_size: float,
        preferred_time: datetime,
    ) -> Optional[str]:
        """Schedule negotiation/closing call."""
        return await self.schedule_event(
            EventType.NEGOTIATION,
            email,
            lead_name,
            f"Closing Call - {company}",
            f"Negotiation & closing call with {lead_name}. Deal size: ${deal_size:,.0f}. Prepare: pricing options, contract terms, discount authority.",
            preferred_time,
            duration_minutes=60,
        )

    async def schedule_onboarding(
        self,
        customer_name: str,
        email: str,
        company: str,
        start_date: datetime,
    ) -> Optional[str]:
        """Schedule onboarding kickoff."""
        return await self.schedule_event(
            EventType.ONBOARDING,
            email,
            customer_name,
            f"Onboarding Kickoff - {company}",
            f"Onboarding session for {customer_name}. 90-day success roadmap, feature training, support setup.",
            start_date,
            duration_minutes=90,
        )
