"""MercadoLibre connector — Listar, vender, tracking automático."""

import aiohttp
import logging
from typing import Dict, List, Any
from .base_connector import BaseConnector, ConnectorType

logger = logging.getLogger(__name__)


class MercadoLibreConnector(BaseConnector):
    """MercadoLibre marketplace integration."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("mercadolibre", ConnectorType.MARKETPLACE, config)
        self.base_url = "https://api.mercadolibre.com"
        self.access_token = config.get("access_token")
        self.user_id = config.get("user_id")

    async def authenticate(self) -> bool:
        """Verifica acceso token."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/{self.user_id}"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        self.authenticated = True
                        logger.info("MercadoLibre authenticated")
                        return True
                    return False
        except Exception as e:
            logger.error(f"MercadoLibre auth failed: {str(e)}")
            return False

    async def list_products(self) -> List[Dict[str, Any]]:
        """Lista productos del vendedor."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/{self.user_id}/items/search"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("results", [])
                    return []
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}")
            return []

    async def create_listing(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Crea listing en MercadoLibre."""
        try:
            payload = {
                "title": product.get("name"),
                "category_id": product.get("category_id", "MLA1500"),  # Default: general
                "price": product.get("price"),
                "currency_id": "ARS",
                "available_quantity": product.get("stock", 1),
                "buying_mode": "buy_it_now",
                "listing_type_id": "gold_pro",
                "pictures": [
                    {"source": url} for url in product.get("images", [])
                ],
                "description": {
                    "plain_text": product.get("description", "")
                },
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/items"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        logger.info(f"Listing created: {data.get('id')}")
                        return {"status": "created", "listing_id": data.get("id")}
                    return {"status": "error", "message": "Failed to create listing"}
        except Exception as e:
            logger.error(f"Error creating listing: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def get_orders(self) -> List[Dict[str, Any]]:
        """Obtiene órdenes."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/users/{self.user_id}/orders/search"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with session.get(url, headers=headers, params={"sort": "date_desc"}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("results", [])
                    return []
        except Exception as e:
            logger.error(f"Error fetching orders: {str(e)}")
            return []

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Envía mensaje a comprador (vía MercadoLibre)."""
        # TODO: usar /messages API de MercadoLibre
        return {"status": "not_implemented"}

    async def create_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """MercadoLibre no tiene ads API expuesta fácilmente."""
        return {"status": "not_supported"}

    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de listings."""
        try:
            orders = await self.get_orders()
            products = await self.list_products()
            
            total_revenue = sum(o.get("total_amount", 0) for o in orders)
            
            return {
                "listings_active": len(products),
                "orders_completed": len(orders),
                "revenue": total_revenue,
                "platform": "mercadolibre",
            }
        except Exception as e:
            logger.error(f"Error fetching metrics: {str(e)}")
            return {}
