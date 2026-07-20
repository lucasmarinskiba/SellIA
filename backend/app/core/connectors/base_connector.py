"""
Base connector architecture — Pluggable integrations.

Cada plataforma = connector independiente. Mismo interface.
Fácil agregar: MercadoLibre, Shopify, Meta Ads, WhatsApp, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConnectorType(str, Enum):
    """Tipo connector."""
    MARKETPLACE = "marketplace"  # MercadoLibre, Amazon, Shopify
    ADS = "ads"  # Facebook/Meta Ads, Google Ads
    MESSAGING = "messaging"  # WhatsApp, Twilio, Email
    SHIPPING = "shipping"  # OCA, Andreani, tracking
    SOCIAL = "social"  # Instagram, TikTok, LinkedIn
    SERVICES = "services"  # Calendly, Zoom, etc
    CRM = "crm"  # Salesforce, HubSpot


class BaseConnector(ABC):
    """Base class para todos los connectors."""

    def __init__(self, name: str, connector_type: ConnectorType, config: Dict[str, Any]):
        self.name = name
        self.connector_type = connector_type
        self.config = config
        self.authenticated = False

    @abstractmethod
    async def authenticate(self) -> bool:
        """Autentica con la plataforma."""
        pass

    @abstractmethod
    async def list_products(self) -> List[Dict[str, Any]]:
        """Lista productos/anuncios/items."""
        pass

    @abstractmethod
    async def create_listing(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Crea listing/anuncio en plataforma."""
        pass

    @abstractmethod
    async def get_orders(self) -> List[Dict[str, Any]]:
        """Obtiene órdenes."""
        pass

    @abstractmethod
    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Envía mensaje (WhatsApp, SMS, email, etc)."""
        pass

    @abstractmethod
    async def create_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Crea campaña ads."""
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas (impressions, clicks, conversiones, etc)."""
        pass

    async def sync_inventory(self, inventory: Dict[str, int]) -> bool:
        """Sincroniza inventario a plataforma."""
        pass

    def is_ready(self) -> bool:
        """¿Connector está listo para usar?"""
        return self.authenticated


class ConnectorRegistry:
    """Registro de connectors disponibles."""

    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector):
        """Registra connector."""
        self.connectors[connector.name] = connector
        logger.info(f"Connector registered: {connector.name}")

    async def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Obtiene connector por nombre."""
        return self.connectors.get(name)

    async def authenticate_all(self) -> Dict[str, bool]:
        """Autentica todos los connectors."""
        results = {}
        for name, connector in self.connectors.items():
            try:
                success = await connector.authenticate()
                results[name] = success
                logger.info(f"{name}: {'✅' if success else '❌'}")
            except Exception as e:
                logger.error(f"{name} auth failed: {str(e)}")
                results[name] = False
        return results

    async def sync_product_across_platforms(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Publica producto en todos los connectors habilitados."""
        results = {}
        for name, connector in self.connectors.items():
            if connector.connector_type == ConnectorType.MARKETPLACE:
                try:
                    result = await connector.create_listing(product)
                    results[name] = result
                    logger.info(f"Product listed on {name}: {result.get('listing_id')}")
                except Exception as e:
                    logger.error(f"Error listing on {name}: {str(e)}")
                    results[name] = {"status": "error", "error": str(e)}
        return results

    async def broadcast_message(self, recipients: List[str], message: str) -> Dict[str, Any]:
        """Envía mensaje por todos los canales (WhatsApp, SMS, email)."""
        results = {}
        for name, connector in self.connectors.items():
            if connector.connector_type == ConnectorType.MESSAGING:
                try:
                    for recipient in recipients:
                        result = await connector.send_message(recipient, message)
                        results[f"{name}_{recipient}"] = result
                except Exception as e:
                    logger.error(f"Error sending via {name}: {str(e)}")
        return results

    async def get_unified_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas consolidadas de todas las plataformas."""
        unified = {
            "total_impressions": 0,
            "total_clicks": 0,
            "total_conversions": 0,
            "total_revenue": 0,
            "by_platform": {},
        }

        for name, connector in self.connectors.items():
            try:
                metrics = await connector.get_metrics()
                unified["by_platform"][name] = metrics
                unified["total_impressions"] += metrics.get("impressions", 0)
                unified["total_clicks"] += metrics.get("clicks", 0)
                unified["total_conversions"] += metrics.get("conversions", 0)
                unified["total_revenue"] += metrics.get("revenue", 0)
            except Exception as e:
                logger.error(f"Error fetching metrics from {name}: {str(e)}")

        return unified
