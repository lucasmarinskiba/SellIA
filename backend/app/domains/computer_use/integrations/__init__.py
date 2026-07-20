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

from .google_calendar_connector import GoogleCalendarConnector, get_google_calendar_connector
from .calendly_connector import CalendlyConnector, get_calendly_connector
from .whatsapp_connector import WhatsAppConnector, get_whatsapp_connector
from .instagram_connector import InstagramConnector, get_instagram_connector
from .stripe_connector import StripeConnector, get_stripe_connector
from .meta_ads_connector import MetaAdsConnector, get_meta_ads_connector
from .google_ads_connector import GoogleAdsConnector, get_google_ads_connector

__all__ = [
    "GoogleCalendarConnector",
    "get_google_calendar_connector",
    "CalendlyConnector",
    "get_calendly_connector",
    "WhatsAppConnector",
    "get_whatsapp_connector",
    "InstagramConnector",
    "get_instagram_connector",
    "StripeConnector",
    "get_stripe_connector",
    "MetaAdsConnector",
    "get_meta_ads_connector",
    "GoogleAdsConnector",
    "get_google_ads_connector",
]
