"""Location-based messaging templates for proximity automations.

Templates for SMS, WhatsApp, Email when user is near a location.
Customizable per business model, location type, funnel stage.
"""

from enum import Enum
from typing import Optional
from uuid import UUID

from app.domains.businesses.location_models import LocationType
from app.domains.proximity.proximity_engine import ProximityTriggerConfig


class MessageTemplate(Enum):
    """Predefined location-based message templates."""

    # E-Commerce + Showroom (QR_INVITE strategy)
    SHOWROOM_NEARBY_SMS = "showroom_nearby_sms"
    SHOWROOM_NEARBY_EMAIL = "showroom_nearby_email"
    SHOWROOM_QR_CHECKOUT = "showroom_qr_checkout"

    # Retail (FOOT_TRAFFIC strategy)
    WALK_BY_OFFER_SMS = "walk_by_offer_sms"
    IMPULSE_OFFER_SMS = "impulse_offer_sms"
    PEAK_HOUR_OFFER = "peak_hour_offer"

    # B2B (TOUR_SCHEDULING strategy)
    FACTORY_TOUR_EMAIL = "factory_tour_email"
    TOUR_CONFIRMATION = "tour_confirmation"
    POST_TOUR_FOLLOW_UP = "post_tour_follow_up"

    # SaaS (DEMO_BOOKING strategy)
    OFFICE_DEMO_EMAIL = "office_demo_email"
    DEMO_CONFIRMATION = "demo_confirmation"
    POST_DEMO_PROPOSAL = "post_demo_proposal"

    # Services (SERVICE_DISPATCH strategy)
    SERVICE_AVAILABLE = "service_available"
    TECHNICIAN_ETA = "technician_eta"
    SERVICE_COMPLETE = "service_complete"


class LocationMessageTemplateService:
    """Generate and manage location-based messages."""

    # SMS Templates (160 chars max per SMS)
    SMS_TEMPLATES = {
        MessageTemplate.SHOWROOM_NEARBY_SMS: (
            "🏢 {business_name} showroom está a {distance}km de ti! "
            "Visita hoy y obtén 10% off. {location_name}\n"
            "📍 {maps_url}"
        ),
        MessageTemplate.WALK_BY_OFFER_SMS: (
            "¡{business_name} te espera! Descuento especial hoy: {offer}. "
            "Abierto {open_time}-{close_time}\n"
            "📍 {location_address}"
        ),
        MessageTemplate.IMPULSE_OFFER_SMS: (
            "⚡ Oferta limitada en {location_name}! {offer} solo hoy. "
            "Escanea el QR en tienda.\n"
            "⏰ Hasta las {close_time}"
        ),
        MessageTemplate.FACTORY_TOUR_EMAIL: (
            "Hola {visitor_name},\n\n"
            "Te invitamos a conocer nuestras instalaciones de {business_name}. "
            "Tour guiado: cómo fabricamos, capacidad, volúmenes.\n\n"
            "📅 Disponibilidad: {available_dates}\n"
            "📍 Ubicación: {location_address}\n\n"
            "Confirmá tu visita: {booking_link}"
        ),
        MessageTemplate.OFFICE_DEMO_EMAIL: (
            "Hola {visitor_name},\n\n"
            "Vimos que estás usando {product_name} intensamente. "
            "¿Te gustaría una demostración personalizada en nuestra oficina?\n\n"
            "📍 {location_address}\n"
            "⏰ {available_slots}\n\n"
            "Reservar: {booking_link}"
        ),
        MessageTemplate.SERVICE_AVAILABLE: (
            "¡Servicio disponible en tu zona! {service_name} de {business_name}.\n"
            "📍 {distance}km de distancia\n"
            "🚗 ETA {eta_minutes}min\n"
            "Reservar: {booking_link}"
        ),
    }

    # Email Templates (full format)
    EMAIL_TEMPLATES = {
        MessageTemplate.SHOWROOM_NEARBY_EMAIL: {
            "subject": "¡{business_name} showroom a {distance}km! Visitá hoy",
            "body": (
                "<h2>¡Hola {visitor_name}!</h2>\n"
                "<p>Notamos que estás cerca de nuestro showroom en {location_name}.</p>\n\n"
                "<p><strong>📍 Ubicación:</strong> {location_address}</p>\n"
                "<p><strong>⏰ Horarios:</strong> {hours}</p>\n"
                "<p><strong>🎁 Oferta especial:</strong> 10% off en tu primera visita</p>\n\n"
                "<p><a href='{maps_url}'>Ver en Google Maps</a></p>\n"
                "<p><a href='{booking_link}'>Reservar visita guiada</a></p>"
            )
        },
        MessageTemplate.POST_TOUR_FOLLOW_UP: {
            "subject": "Propuesta personalizada post-visita",
            "body": (
                "<h2>Gracias por visitar {location_name}!</h2>\n"
                "<p>Nos gustó mucho conocerte en el tour del {visit_date}.</p>\n\n"
                "<p>Basado en tu interés en <strong>{customer_interest}</strong>, "
                "preparamos una propuesta personalizada:</p>\n\n"
                "<ul>"
                "<li>Volumen: {estimated_volume} unidades/mes</li>"
                "<li>Precio: {quoted_price}</li>"
                "<li>Timeline: {delivery_timeline}</li>"
                "</ul>\n\n"
                "<p><a href='{proposal_link}'>Ver propuesta completa</a></p>"
            )
        },
        MessageTemplate.POST_DEMO_PROPOSAL: {
            "subject": "Tu plan personalizado para {product_name}",
            "body": (
                "<h2>Propuesta de implementación</h2>\n"
                "<p>Basado en la demostración del {demo_date}, armamos un plan "
                "customizado para {customer_name}:</p>\n\n"
                "<ul>"
                "<li>Módulos: {selected_modules}</li>"
                "<li>Usuarios: {user_count}</li>"
                "<li>Inversión: {pricing}</li>"
                "<li>Go-live: {implementation_timeline}</li>"
                "</ul>\n\n"
                "<p><a href='{proposal_link}'>Revisar propuesta</a></p>"
            )
        }
    }

    @staticmethod
    def get_template(
        template_key: MessageTemplate,
        channel: str = "sms"
    ) -> Optional[str]:
        """Get message template for given type and channel."""
        if channel == "sms":
            return LocationMessageTemplateService.SMS_TEMPLATES.get(template_key)
        elif channel in ("email", "whatsapp"):
            template_data = LocationMessageTemplateService.EMAIL_TEMPLATES.get(template_key)
            if template_data:
                return template_data.get("body")
        return None

    @staticmethod
    def render_template(
        template_key: MessageTemplate,
        channel: str = "sms",
        variables: Optional[dict[str, str]] = None
    ) -> Optional[str]:
        """Render message template with variables substituted.

        Args:
            template_key: MessageTemplate enum value
            channel: 'sms', 'email', 'whatsapp'
            variables: Dict of {placeholder: value}. E.g., {"business_name": "TechCorp"}

        Returns:
            Rendered message with variables substituted
        """
        template = LocationMessageTemplateService.get_template(template_key, channel)

        if not template:
            return None

        if not variables:
            variables = {}

        # Simple template rendering: replace {key} with value
        rendered = template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    @staticmethod
    def get_default_template_for_strategy(
        strategy: str,
        location_type: LocationType,
        channel: str = "sms"
    ) -> Optional[MessageTemplate]:
        """Recommend template based on localization strategy + location type."""

        mapping = {
            # E-Commerce + Showroom
            ("QR_INVITE", LocationType.SHOWROOM): MessageTemplate.SHOWROOM_NEARBY_SMS,

            # Retail
            ("FOOT_TRAFFIC", LocationType.RETAIL_STORE): MessageTemplate.WALK_BY_OFFER_SMS,

            # B2B
            ("TOUR_SCHEDULING", LocationType.FACTORY): MessageTemplate.FACTORY_TOUR_EMAIL,
            ("TOUR_SCHEDULING", LocationType.OFFICE): MessageTemplate.FACTORY_TOUR_EMAIL,

            # SaaS
            ("DEMO_BOOKING", LocationType.OFFICE): MessageTemplate.OFFICE_DEMO_EMAIL,

            # Services
            ("SERVICE_DISPATCH", LocationType.SERVICE_CENTER): MessageTemplate.SERVICE_AVAILABLE,
        }

        return mapping.get((strategy, location_type))

    @staticmethod
    def get_template_variables_required(template_key: MessageTemplate) -> list[str]:
        """Get list of required variables for template (extracted from {placeholders})."""
        template = LocationMessageTemplateService.SMS_TEMPLATES.get(template_key) or ""

        import re
        placeholders = re.findall(r'\{(\w+)\}', template)

        return list(set(placeholders))

    @staticmethod
    def build_location_context(
        location_id: str,
        location_name: str,
        location_address: str,
        distance_km: float,
        hours: str,
        open_time: str,
        close_time: str,
        maps_url: str
    ) -> dict[str, str]:
        """Build context variables for location-based template."""
        return {
            "location_id": location_id,
            "location_name": location_name,
            "location_address": location_address,
            "distance": f"{distance_km:.1f}",
            "hours": hours,
            "open_time": open_time,
            "close_time": close_time,
            "maps_url": maps_url,
        }

    @staticmethod
    def build_visitor_context(
        visitor_name: str,
        visitor_email: str,
        visitor_phone: str,
        customer_stage: str = "lead"  # lead, prospect, qualified, customer
    ) -> dict[str, str]:
        """Build context variables for visitor/customer."""
        return {
            "visitor_name": visitor_name or "Valued Customer",
            "visitor_email": visitor_email or "",
            "visitor_phone": visitor_phone or "",
            "customer_stage": customer_stage,
        }

    @staticmethod
    def build_offer_context(
        offer_percentage: int = 10,
        offer_type: str = "discount",  # discount, free_shipping, bundled
        offer_expiry: str = "today"
    ) -> dict[str, str]:
        """Build offer-specific variables."""
        if offer_type == "discount":
            offer_text = f"{offer_percentage}% off"
        elif offer_type == "free_shipping":
            offer_text = "Free shipping"
        else:
            offer_text = "Special bundle"

        return {
            "offer": offer_text,
            "offer_percentage": str(offer_percentage),
            "offer_type": offer_type,
            "offer_expiry": offer_expiry,
        }
