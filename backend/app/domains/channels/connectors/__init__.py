"""Channel connectors registry.

Single source of truth for mapping ChannelPlatform -> Connector class.
"""

from typing import Type
from app.domains.channels.models import ChannelPlatform
from app.domains.channels.connectors.base import BaseChannelConnector

from app.domains.channels.connectors.whatsapp import WhatsAppConnector
from app.domains.channels.connectors.email import EmailConnector
from app.domains.channels.connectors.instagram import InstagramConnector
from app.domains.channels.connectors.linkedin import LinkedInConnector
from app.domains.channels.connectors.telegram import TelegramConnector
from app.domains.channels.connectors.webchat import WebChatConnector
from app.domains.channels.connectors.messenger import MessengerConnector
from app.domains.channels.connectors.mercadolibre import MercadoLibreConnector
from app.domains.channels.connectors.facebook_ads import FacebookAdsConnector
from app.domains.channels.connectors.meta_ads import MetaAdsConnector
from app.domains.channels.connectors.google_ads import GoogleAdsConnector
from app.domains.channels.connectors.shopify import ShopifyConnector
from app.domains.channels.connectors.tiktok_ads import TikTokAdsConnector
from app.domains.channels.connectors.tiktok import TikTokConnector
from app.domains.channels.connectors.tiktok_shop import TikTokShopConnector
from app.domains.channels.connectors.amazon import AmazonSellerConnector
from app.domains.channels.connectors.beacons import BeaconsConnector
from app.domains.channels.connectors.twitter import XConnector
from app.domains.channels.connectors.threads import ThreadsConnector
from app.domains.channels.connectors.hotmart import HotmartConnector
from app.domains.channels.connectors.woocommerce import WooCommerceConnector
from app.domains.channels.connectors.etsy import EtsyConnector
from app.domains.channels.connectors.facebook_marketplace import FacebookMarketplaceConnector
from app.domains.channels.connectors.manychat import ManyChatConnector

CONNECTOR_REGISTRY: dict[ChannelPlatform, Type[BaseChannelConnector]] = {
    ChannelPlatform.WHATSAPP: WhatsAppConnector,
    ChannelPlatform.EMAIL: EmailConnector,
    ChannelPlatform.INSTAGRAM: InstagramConnector,
    ChannelPlatform.LINKEDIN: LinkedInConnector,
    ChannelPlatform.TELEGRAM: TelegramConnector,
    ChannelPlatform.WEBCHAT: WebChatConnector,
    ChannelPlatform.MESSENGER: MessengerConnector,
    ChannelPlatform.MERCADOLIBRE: MercadoLibreConnector,
    ChannelPlatform.FACEBOOK_ADS: FacebookAdsConnector,
    ChannelPlatform.META_ADS: MetaAdsConnector,
    ChannelPlatform.GOOGLE_ADS: GoogleAdsConnector,
    ChannelPlatform.SHOPIFY: ShopifyConnector,
    ChannelPlatform.TIKTOK_ADS: TikTokAdsConnector,
    ChannelPlatform.TIKTOK: TikTokConnector,
    ChannelPlatform.TIKTOK_SHOP: TikTokShopConnector,
    ChannelPlatform.AMAZON: AmazonSellerConnector,
    ChannelPlatform.BEACONS: BeaconsConnector,
    ChannelPlatform.TWITTER: XConnector,
    ChannelPlatform.THREADS: ThreadsConnector,
    ChannelPlatform.HOTMART: HotmartConnector,
    ChannelPlatform.WOOCOMMERCE: WooCommerceConnector,
    ChannelPlatform.ETSY: EtsyConnector,
    ChannelPlatform.FACEBOOK_MARKETPLACE: FacebookMarketplaceConnector,
    ChannelPlatform.MANYCHAT: ManyChatConnector,
}


def get_connector(platform: ChannelPlatform, credentials: dict, settings: dict) -> BaseChannelConnector:
    connector_class = CONNECTOR_REGISTRY.get(platform)
    if not connector_class:
        raise ValueError(f"Plataforma no soportada: {platform}")
    return connector_class(credentials, settings)
