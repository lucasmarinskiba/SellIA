"""Platform Script Registry — maps domains to platform script classes."""

from .amazon import AmazonScript
from .base import PlatformScript
from .facebook_business import FacebookBusinessScript
from .facebook_messenger import FacebookMessengerScript
from .google_ads import GoogleAdsScript
from .google_business import GoogleBusinessScript
from .hotmart import HotmartScript
from .instagram import InstagramScript
from .mercadolibre import MercadoLibreScript
from .shopify import ShopifyScript
from .tiktok import TikTokScript
from .whatsapp_web import WhatsAppWebScript

PLATFORM_REGISTRY: dict[str, type[PlatformScript]] = {
    "web.whatsapp.com": WhatsAppWebScript,
    "whatsapp.com": WhatsAppWebScript,
    "messenger.com": FacebookMessengerScript,
    "instagram.com": InstagramScript,
    "business.facebook.com": FacebookBusinessScript,
    "facebook.com": FacebookBusinessScript,
    "ads.google.com": GoogleAdsScript,
    "adwords.google.com": GoogleAdsScript,
    "tiktok.com": TikTokScript,
    "seller.tiktok.com": TikTokScript,
    "business.tiktok.com": TikTokScript,
    "myshopify.com": ShopifyScript,
    "shopify.com": ShopifyScript,
    "mercadolibre.com": MercadoLibreScript,
    "mercadolibre.com.ar": MercadoLibreScript,
    "mercadolibre.com.br": MercadoLibreScript,
    "mercadolibre.com.mx": MercadoLibreScript,
    "amazon.com": AmazonScript,
    "sellercentral.amazon.com": AmazonScript,
    "vendorcentral.amazon.com": AmazonScript,
    "hotmart.com": HotmartScript,
    "app.hotmart.com": HotmartScript,
    "business.google.com": GoogleBusinessScript,
    "search.google.com": GoogleBusinessScript,
}


def get_script_for_domain(domain: str) -> PlatformScript | None:
    """Get an instance of the appropriate platform script for a domain."""
    # Try exact match first
    if domain in PLATFORM_REGISTRY:
        return PLATFORM_REGISTRY[domain]()

    # Try partial match (e.g. "admin.shopify.com" matches "shopify.com")
    for registered_domain, script_class in PLATFORM_REGISTRY.items():
        if registered_domain in domain or domain.endswith(registered_domain):
            return script_class()

    return None


def get_script_for_task(platform: str, action_type: str) -> PlatformScript | None:
    """Get script by platform name (from playbook steps)."""
    platform_map = {
        "whatsapp": WhatsAppWebScript,
        "whatsapp_web": WhatsAppWebScript,
        "messenger": FacebookMessengerScript,
        "facebook_messenger": FacebookMessengerScript,
        "instagram": InstagramScript,
        "facebook": FacebookBusinessScript,
        "meta_ads": FacebookBusinessScript,
        "google_ads": GoogleAdsScript,
        "google": GoogleBusinessScript,
        "tiktok": TikTokScript,
        "tiktok_ads": TikTokScript,
        "tiktok_shop": TikTokScript,
        "shopify": ShopifyScript,
        "mercadolibre": MercadoLibreScript,
        "amazon": AmazonScript,
        "hotmart": HotmartScript,
    }
    script_class = platform_map.get(platform.lower())
    if script_class:
        return script_class()
    return None
