"""Service for detecting business localization model and generating offline strategies.

Classifies businesses as ONLINE_ONLY, HYBRID_LIGHT, HYBRID_HEAVY, or OFFLINE_FIRST
based on business type, location count, and configuration.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domains.businesses.models import Business, BusinessType, LocalizationModel
from app.domains.businesses.location_models import Location, LocationType

logger = logging.getLogger(__name__)


class LocalizationStrategy(Enum):
    """Offline-to-online strategy per business model."""
    NONE = "none"  # ONLINE_ONLY: no offline strategy
    QR_INVITE = "qr_invite"  # E-commerce+showroom: QR codes → visit invites
    FOOT_TRAFFIC = "foot_traffic"  # Retail: walk-by detection → offers
    TOUR_SCHEDULING = "tour_scheduling"  # B2B: factory/office tours
    DEMO_BOOKING = "demo_booking"  # SaaS: office demo appointments
    SERVICE_DISPATCH = "service_dispatch"  # Services: send technician on-site


class LocationalizationHint(Enum):
    """Signals that indicate business needs offline strategy."""
    HAS_PHYSICAL_LOCATION = "has_physical_location"
    CONFIG_PICKUP_LOCATIONS = "config_pickup_locations"  # GOODS model with pickups
    SERVICE_MODALITIES = "service_modalities"  # SERVICES with on_site/hybrid
    MULTIPLE_LOCATIONS = "multiple_locations"
    DELIVERY_CONFIG = "delivery_config"


class BusinessLocalizationService:
    """Detects business localization model and manages offline strategies."""

    @staticmethod
    def detect_model(
        business: Business,
        locations: List[Location] | None = None,
        db: Session | None = None
    ) -> LocalizationModel:
        """
        Auto-detect localization model based on business type, config, and locations.

        Strategy:
        1. If no locations: ONLINE_ONLY
        2. If 1 location + (showroom/office/center): HYBRID_LIGHT
        3. If 1-2 locations + high foot-traffic config: HYBRID_HEAVY
        4. If 3+ locations OR flagship office: OFFLINE_FIRST
        """
        if not locations:
            # Fetch from DB if needed
            if db:
                locations = db.query(Location).filter(
                    Location.business_id == business.id,
                    Location.is_active == True
                ).all()
            else:
                locations = []

        location_count = len(locations)

        # No physical locations → online only
        if location_count == 0:
            return LocalizationModel.ONLINE_ONLY

        # Analyze location types
        location_types = {loc.type for loc in locations}
        has_showroom = LocationType.SHOWROOM in location_types
        has_office = LocationType.OFFICE in location_types
        has_service_center = LocationType.SERVICE_CENTER in location_types
        has_factory = LocationType.FACTORY in location_types

        # Analyze business config
        config = business.config or {}
        has_pickup_locations = len(config.get("pickup_locations", [])) > 0
        delivery_methods = config.get("delivery_methods", [])
        has_pickup_delivery = "pickup" in delivery_methods or "meetup" in delivery_methods

        # Score: weight indicators toward offline-first
        signals = []

        # Location-based signals
        if location_count >= 3:
            signals.append(LocationalizationHint.MULTIPLE_LOCATIONS)
        if has_factory:
            signals.append(LocationalizationHint.HAS_PHYSICAL_LOCATION)
        if has_pickup_locations or has_pickup_delivery:
            signals.append(LocationalizationHint.CONFIG_PICKUP_LOCATIONS)

        # Config-based signals
        if business.type == BusinessType.SERVICES:
            modalities = config.get("modalities", [])
            if "on_site" in modalities or "hybrid" in modalities:
                signals.append(LocationalizationHint.SERVICE_MODALITIES)

        # Classify based on signals
        signal_count = len(signals)

        if signal_count == 0:
            return LocalizationModel.ONLINE_ONLY
        elif signal_count == 1:
            if has_factory or has_service_center:
                return LocalizationModel.HYBRID_HEAVY
            return LocalizationModel.HYBRID_LIGHT
        elif signal_count == 2:
            return LocalizationModel.HYBRID_HEAVY
        else:  # signal_count >= 3
            return LocalizationModel.OFFLINE_FIRST

    @staticmethod
    def get_strategy_for_model(
        business_type: BusinessType,
        localization_model: LocalizationModel
    ) -> LocalizationStrategy:
        """Get recommended offline strategy based on business type + localization model."""

        if localization_model == LocalizationModel.ONLINE_ONLY:
            return LocalizationStrategy.NONE

        # E-commerce + showroom
        if business_type == BusinessType.GOODS:
            if localization_model in (LocalizationModel.HYBRID_LIGHT, LocalizationModel.HYBRID_HEAVY):
                return LocalizationStrategy.QR_INVITE
            return LocalizationStrategy.FOOT_TRAFFIC

        # Services (plumber, hairdresser, etc.)
        if business_type == BusinessType.SERVICES:
            return LocalizationStrategy.SERVICE_DISPATCH

        # Digital-only: no offline strategy
        if business_type == BusinessType.DIGITAL:
            return LocalizationStrategy.NONE

        # Mixed: lean on GOODS behavior
        if business_type == BusinessType.MIXED:
            if localization_model == LocalizationModel.OFFLINE_FIRST:
                return LocalizationStrategy.FOOT_TRAFFIC
            return LocalizationStrategy.QR_INVITE

        # Fallback
        return LocalizationStrategy.NONE

    @staticmethod
    def automation_triggers_for_strategy(
        strategy: LocalizationStrategy
    ) -> List[str]:
        """Get list of automation trigger names that should be enabled per strategy."""

        triggers_map = {
            LocalizationStrategy.NONE: [],
            LocalizationStrategy.QR_INVITE: [
                "proximity_check_nearby",
                "qr_scanned_at_location",
                "send_visit_invite_sms",
                "send_visit_invite_email",
            ],
            LocalizationStrategy.FOOT_TRAFFIC: [
                "location_visit_detected",
                "send_special_offer_sms",
                "track_dwell_time",
            ],
            LocalizationStrategy.TOUR_SCHEDULING: [
                "qualified_lead_nearby",
                "send_tour_invite",
                "schedule_tour_appointment",
            ],
            LocalizationStrategy.DEMO_BOOKING: [
                "trial_user_nearby",
                "send_demo_offer",
                "schedule_demo_meeting",
            ],
            LocalizationStrategy.SERVICE_DISPATCH: [
                "service_inquiry_received",
                "calculate_service_radius",
                "dispatch_technician",
                "send_eta_to_customer",
            ],
        }

        return triggers_map.get(strategy, [])

    @staticmethod
    def create_location_config_template(
        location_type: LocationType,
        business_type: BusinessType
    ) -> Dict[str, any]:
        """Create default configuration template for new location based on type + business."""

        base_config = {
            "proximity_trigger_radius_km": 5.0,  # Trigger invite when user is within 5km
            "foot_traffic_dwell_threshold_minutes": 15,
            "enable_qr_codes": True,
            "enable_manual_checkin": True,
        }

        # Location-specific configs
        if location_type == LocationType.SHOWROOM:
            base_config.update({
                "dwell_threshold_minutes": 10,
                "offer_demo": True,
                "offer_tour": True,
                "collect_contact_info": True,
            })
        elif location_type == LocationType.RETAIL_STORE:
            base_config.update({
                "dwell_threshold_minutes": 5,
                "offer_special_price": True,
                "track_category_browsing": True,
                "impulse_offer": True,
            })
        elif location_type == LocationType.FACTORY:
            base_config.update({
                "dwell_threshold_minutes": 30,
                "require_appointment": True,
                "offer_tour": True,
                "collect_business_info": True,
            })
        elif location_type == LocationType.OFFICE:
            base_config.update({
                "dwell_threshold_minutes": 20,
                "require_appointment": True,
                "offer_demo": True,
                "collect_company_info": True,
            })
        elif location_type == LocationType.SERVICE_CENTER:
            base_config.update({
                "dwell_threshold_minutes": 15,
                "enable_booking": True,
                "offer_consultation": True,
            })

        # Business-specific configs
        if business_type == BusinessType.SERVICES:
            base_config["enable_appointment_booking"] = True
            base_config["show_available_slots"] = True
        elif business_type == BusinessType.GOODS:
            base_config["enable_qr_checkout"] = True
            base_config["enable_cart_pickup"] = True

        return base_config

    @staticmethod
    def should_enable_proximity_triggers(localization_model: LocalizationModel) -> bool:
        """Check if proximity-based marketing should be active."""
        return localization_model != LocalizationModel.ONLINE_ONLY

    @staticmethod
    def get_success_metrics(localization_model: LocalizationModel) -> Dict[str, str]:
        """Get KPIs to track for this localization model."""

        metrics = {
            LocalizationModel.ONLINE_ONLY: {
                "conversion_rate": "Online funnel only",
                "avg_order_value": "Pure online",
            },
            LocalizationModel.HYBRID_LIGHT: {
                "foot_traffic_monthly": "Location visits per month",
                "visit_to_purchase": "% of visitors who purchase",
                "online_to_visit_rate": "% of online leads who visit",
                "dwell_time": "Avg time spent in location",
            },
            LocalizationModel.HYBRID_HEAVY: {
                "foot_traffic_weekly": "Location visits per week",
                "visit_to_purchase": "% of visitors who purchase",
                "demo_conversion": "% of demos that convert to deals",
                "appointment_show_rate": "% of booked appointments attended",
            },
            LocalizationModel.OFFLINE_FIRST: {
                "walk_in_conversion": "% of walk-ins that purchase",
                "repeat_visit_rate": "% of customers with repeat visits",
                "local_market_share": "Estimated local market penetration",
                "referral_rate": "% of sales from local referrals",
            },
        }

        return metrics.get(localization_model, {})
