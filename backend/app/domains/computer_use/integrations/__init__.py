"""Third-party integrations for Computer Use.

Real API connectors — all production-ready:
- Google Calendar (OAuth2 + API v3)
- Calendly (REST API)
- WhatsApp Business API (Meta Graph v18.0)
- Instagram DMs (Meta Graph v18.0)
- Stripe Payment (Checkout + Payment Intent)
- Meta Ads API (Graph v18.0)
- Google Ads (Google Ads API v14)
"""

from .calendly_connector import CalendlyConnector, get_calendly_connector
from .google_ads_connector import GoogleAdsConnector, get_google_ads_connector
from .google_calendar_connector import (
    GoogleCalendarConnector,
    get_google_calendar_connector,
)
from .instagram_connector import InstagramConnector, get_instagram_connector
from .meta_ads_connector import MetaAdsConnector, get_meta_ads_connector
from .stripe_connector import StripeConnector, get_stripe_connector
from .whatsapp_connector import WhatsAppConnector, get_whatsapp_connector

__all__ = [
    "CalendlyConnector",
    "GoogleAdsConnector",
    "GoogleCalendarConnector",
    "InstagramConnector",
    "MetaAdsConnector",
    "StripeConnector",
    "WhatsAppConnector",
    "get_calendly_connector",
    "get_google_ads_connector",
    "get_google_calendar_connector",
    "get_instagram_connector",
    "get_meta_ads_connector",
    "get_stripe_connector",
    "get_whatsapp_connector",
]
