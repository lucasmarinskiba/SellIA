"""Orchestrator for location-based channel communications.

Coordinates proximity events → message template selection → channel delivery.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domains.analytics.offline_models import GeoProximityEvent
from app.domains.businesses.location_models import Location
from app.domains.businesses.localization import BusinessLocalizationService, LocalizationStrategy
from app.domains.channels.location_messaging import (
    LocationMessageTemplateService, MessageTemplate
)
from app.domains.proximity.proximity_engine import ProximityEngine, ProximityTriggerConfig

logger = logging.getLogger(__name__)


class LocationChannelOrchestrator:
    """Orchestrate location-based messaging across channels."""

    @staticmethod
    def build_message_for_location_proximity(
        proximity_event: GeoProximityEvent,
        location: Location,
        channel: str = "sms",
        business_model: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[dict]:
        """
        Build location-based message for proximity event.

        Args:
            proximity_event: GeoProximityEvent that triggered
            location: Location involved
            channel: 'sms', 'email', 'whatsapp'
            business_model: Localization model (if known)
            db: Database session

        Returns:
            Message dict with content + metadata, or None if no template
        """
        if not db:
            return None

        # Get strategy for this location
        business = db.query("Business").filter("Business.id" == location.business_id).first()
        if not business:
            return None

        strategy_name = BusinessLocalizationService.get_strategy_for_model(
            business.type,
            business.localization_model
        ).value

        # Find appropriate template
        template_key = LocationMessageTemplateService.get_default_template_for_strategy(
            strategy_name,
            location.type,
            channel
        )

        if not template_key:
            logger.warning(f"No template found for strategy {strategy_name}, location type {location.type}")
            return None

        # Build location context
        hours_str = LocationChannelOrchestrator._format_hours(location.hours_json)
        eta_minutes = ProximityEngine.estimate_eta_minutes(
            proximity_event.user_latitude,
            proximity_event.user_longitude,
            location
        )

        location_ctx = LocationMessageTemplateService.build_location_context(
            location_id=str(location.id),
            location_name=location.name,
            location_address=location.address,
            distance_km=proximity_event.distance_km,
            hours=hours_str,
            open_time="09:00",  # TODO: extract from location.hours_json
            close_time="18:00",
            maps_url=location.google_maps_url or f"https://maps.google.com/?q={location.latitude},{location.longitude}"
        )

        # Build visitor context
        visitor_ctx = LocationMessageTemplateService.build_visitor_context(
            visitor_name="Valued Customer",
            visitor_email=proximity_event.visitor_email or "",
            visitor_phone=proximity_event.visitor_phone or "",
        )

        # Build offer context (if applicable)
        offer_ctx = LocationMessageTemplateService.build_offer_context(
            offer_percentage=10,
            offer_type="discount",
            offer_expiry="today"
        )

        # Merge all contexts
        all_vars = {**location_ctx, **visitor_ctx, **offer_ctx}

        # Render template
        message_content = LocationMessageTemplateService.render_template(
            template_key,
            channel,
            all_vars
        )

        if not message_content:
            return None

        return {
            "channel": channel,
            "template": template_key.value,
            "content": message_content,
            "location_id": str(location.id),
            "proximity_event_id": str(proximity_event.id),
            "variables": all_vars,
        }

    @staticmethod
    def get_preferred_channel_for_strategy(strategy: str) -> list[str]:
        """Get preferred channels for given strategy."""
        channel_map = {
            "QR_INVITE": ["sms", "email"],  # Showroom: immediate SMS, follow-up email
            "FOOT_TRAFFIC": ["sms"],  # Retail: quick SMS with offer
            "TOUR_SCHEDULING": ["email"],  # B2B: detailed email invite
            "DEMO_BOOKING": ["email"],  # SaaS: professional email
            "SERVICE_DISPATCH": ["sms", "whatsapp"],  # Services: SMS + WhatsApp for updates
        }
        return channel_map.get(strategy, ["sms"])

    @staticmethod
    def build_trigger_check_message(
        business_id: UUID,
        location_id: UUID,
        user_name: str,
        distance_km: float,
        db: Optional[Session] = None
    ) -> dict:
        """Build summary message for "proximity check" trigger type."""
        location = db.query(Location).filter(Location.id == location_id).first() if db else None

        if not location:
            return {
                "status": "error",
                "message": "Location not found"
            }

        return {
            "status": "success",
            "trigger": "proximity_check_nearby",
            "user_name": user_name,
            "location_name": location.name,
            "location_address": location.address,
            "distance_km": distance_km,
            "message": f"📍 {user_name} is {distance_km:.1f}km from {location.name}. Send proximity invite?",
            "suggested_channels": ["sms", "email"],
            "suggested_template": MessageTemplate.SHOWROOM_NEARBY_SMS.value,
        }

    @staticmethod
    def _format_hours(hours_json: dict) -> str:
        """Format hours_json dict into readable string."""
        if not hours_json:
            return "Call for hours"

        days_open = []
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            day_hours = hours_json.get(day)
            if day_hours:
                days_open.append(f"{day.title()}: {day_hours.get('open', '')} - {day_hours.get('close', '')}")

        return "; ".join(days_open) if days_open else "Hours not specified"

    @staticmethod
    def route_message_to_channels(
        message: dict,
        channels: list[str],
        db: Optional[Session] = None
    ) -> list[dict]:
        """Route rendered message to multiple channels.

        Args:
            message: Built message dict
            channels: List of channels to send to (sms, email, whatsapp)
            db: Database session

        Returns:
            List of delivery results per channel
        """
        results = []

        for channel in channels:
            result = {
                "channel": channel,
                "location_id": message.get("location_id"),
                "proximity_event_id": message.get("proximity_event_id"),
                "status": "queued",
                "message_id": None
            }

            try:
                # In real implementation: get connector and send
                # connector = get_connector_for_channel(channel)
                # delivery = connector.send_message(...)

                logger.info(f"Queued {channel} message for location {message['location_id']}")
                result["status"] = "sent"

            except Exception as e:
                logger.error(f"Failed to send {channel} message: {e}")
                result["status"] = "failed"
                result["error"] = str(e)

            results.append(result)

        return results
