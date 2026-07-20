"""Catalog Sync Service.

Synchronizes catalog items between SellIA and external platforms
(Shopify, MercadoLibre, Amazon, Meta, TikTok).
"""

import asyncio
from typing import Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.catalogs.models import CatalogItem
from app.domains.channels.models import ChannelConnection, ChannelPlatform
from app.domains.channels.connectors import get_connector


class CatalogSyncResult:
    def __init__(self, platform: str, success: bool, message: str, items_synced: int = 0):
        self.platform = platform
        self.success = success
        self.message = message
        self.items_synced = items_synced
        self.synced_at = datetime.now(timezone.utc)


class CatalogSyncService:
    """Service for syncing catalog items across connected platforms."""

    # Platforms that support catalog/product push
    PUSH_PLATFORMS = {
        ChannelPlatform.SHOPIFY,
        ChannelPlatform.MERCADOLIBRE,
        ChannelPlatform.AMAZON,
        ChannelPlatform.META_ADS,
        ChannelPlatform.TIKTOK_ADS,
    }

    # Platforms that support catalog/product pull
    PULL_PLATFORMS = {
        ChannelPlatform.SHOPIFY,
        ChannelPlatform.MERCADOLIBRE,
        ChannelPlatform.AMAZON,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_catalog_items(self, business_id: UUID) -> list[CatalogItem]:
        """Get all active catalog items for a business."""
        result = await self.db.execute(
            select(CatalogItem).where(
                CatalogItem.business_id == business_id,
                CatalogItem.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def get_connected_channels(self, business_id: UUID, platforms: Optional[set] = None) -> list[ChannelConnection]:
        """Get active connected channels for a business, optionally filtered by platform."""
        query = select(ChannelConnection).where(
            ChannelConnection.business_id == business_id,
            ChannelConnection.status == "connected",
            ChannelConnection.is_active == True,
        )
        if platforms:
            query = query.where(ChannelConnection.platform.in_(platforms))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def push_to_platform(self, business_id: UUID, platform: ChannelPlatform) -> CatalogSyncResult:
        """Push local catalog items to a specific platform."""
        try:
            channels = await self.get_connected_channels(business_id, {platform})
            if not channels:
                return CatalogSyncResult(platform.value, False, "No hay canal conectado para esta plataforma")

            channel = channels[0]
            items = await self.get_catalog_items(business_id)
            if not items:
                return CatalogSyncResult(platform.value, True, "No hay items en el catálogo para sincronizar", 0)

            connector = get_connector(platform, channel.credentials, channel.settings)
            items_synced = 0

            for item in items:
                try:
                    product_data = self._item_to_platform_format(item, platform)
                    if hasattr(connector, "create_product"):
                        await connector.create_product(product_data)
                        items_synced += 1
                except Exception as e:
                    from app.core.logger import get_logger
                    get_logger(__name__).error(f"Error pushing {item.id} to {platform.value}: {e}")
                    continue

            return CatalogSyncResult(
                platform.value,
                True,
                f"Sincronización completada",
                items_synced,
            )
        except Exception as e:
            return CatalogSyncResult(platform.value, False, f"Error: {str(e)}")

    async def push_all(self, business_id: UUID) -> list[CatalogSyncResult]:
        """Push local catalog to all supported platforms."""
        channels = await self.get_connected_channels(business_id, self.PUSH_PLATFORMS)
        if not channels:
            return []

        platforms = {ch.platform for ch in channels}
        results = []
        for platform in platforms:
            result = await self.push_to_platform(business_id, platform)
            results.append(result)
        return results

    async def pull_from_platform(self, business_id: UUID, platform: ChannelPlatform) -> CatalogSyncResult:
        """Pull products from external platform into local catalog."""
        try:
            channels = await self.get_connected_channels(business_id, {platform})
            if not channels:
                return CatalogSyncResult(platform.value, False, "No hay canal conectado para esta plataforma")

            channel = channels[0]
            connector = get_connector(platform, channel.credentials, channel.settings)

            if not hasattr(connector, "get_products"):
                return CatalogSyncResult(platform.value, False, "Esta plataforma no soporta importación de productos")

            products = await connector.get_products()
            items_synced = 0

            for product in products:
                try:
                    item = self._platform_product_to_item(product, platform, business_id)
                    self.db.add(item)
                    items_synced += 1
                except Exception as e:
                    from app.core.logger import get_logger
                    get_logger(__name__).error(f"Error pulling product to catalog: {e}")
                    continue

            await self.db.commit()
            return CatalogSyncResult(platform.value, True, f"Importación completada", items_synced)
        except Exception as e:
            return CatalogSyncResult(platform.value, False, f"Error: {str(e)}")

    async def pull_all(self, business_id: UUID) -> list[CatalogSyncResult]:
        """Pull products from all supported platforms."""
        channels = await self.get_connected_channels(business_id, self.PULL_PLATFORMS)
        if not channels:
            return []

        platforms = {ch.platform for ch in channels}
        results = []
        for platform in platforms:
            result = await self.pull_from_platform(business_id, platform)
            results.append(result)
        return results

    def _item_to_platform_format(self, item: CatalogItem, platform: ChannelPlatform) -> dict[str, Any]:
        """Convert a CatalogItem to platform-specific product format."""
        base = {
            "title": item.name,
            "description": item.description or "",
            "price": str(item.price),
            "currency": item.currency,
            "sku": str(item.id),
            "images": item.images if item.images else [],
            "tags": item.tags if item.tags else [],
            "status": "active" if item.is_available else "draft",
        }

        if platform == ChannelPlatform.SHOPIFY:
            return {
                "product": {
                    "title": base["title"],
                    "body_html": base["description"],
                    "variants": [{"price": base["price"], "sku": base["sku"]}],
                    "images": [{"src": img} for img in base["images"][:10]],
                    "tags": ",".join(base["tags"]),
                    "status": base["status"],
                }
            }

        elif platform == ChannelPlatform.MERCADOLIBRE:
            return {
                "title": base["title"][:60],
                "category_id": item.extra_data.get("ml_category_id", "MLA3530"),
                "price": float(item.price),
                "currency_id": item.currency,
                "available_quantity": item.stock or 1,
                "buying_mode": "buy_it_now",
                "condition": "new",
                "listing_type_id": "gold_special",
                "description": {"plain_text": base["description"]},
                "pictures": [{"source": img} for img in base["images"][:10]],
            }

        elif platform == ChannelPlatform.AMAZON:
            return {
                "productType": item.extra_data.get("amazon_product_type", "HOME"),
                "requirements": "LISTING",
                "attributes": {
                    "item_name": [{"value": base["title"]}],
                    "brand": [{"value": item.extra_data.get("brand", "Generic")}],
                    "bullet_point": [{"value": b} for b in base["description"].split("\n")[:5] if b],
                    "list_price": [{"currency": item.currency, "value": str(item.price)}],
                    "merchant_suggested_asin": [{"value": base["sku"]}],
                },
            }

        elif platform == ChannelPlatform.META_ADS:
            return {
                "name": base["title"],
                "description": base["description"],
                "price": base["price"],
                "currency": base["currency"],
                "image_url": base["images"][0] if base["images"] else None,
                "url": item.extra_data.get("product_url", ""),
            }

        elif platform == ChannelPlatform.TIKTOK_ADS:
            return {
                "product_name": base["title"],
                "description": base["description"],
                "price": float(item.price),
                "currency": item.currency,
                "main_image": {"url": base["images"][0]} if base["images"] else None,
                "category_id": item.extra_data.get("tiktok_category_id", ""),
            }

        return base

    def _platform_product_to_item(self, product: dict[str, Any], platform: ChannelPlatform, business_id: UUID) -> CatalogItem:
        """Convert a platform product to CatalogItem."""
        if platform == ChannelPlatform.SHOPIFY:
            p = product.get("product", product)
            variant = p.get("variants", [{}])[0]
            return CatalogItem(
                business_id=business_id,
                type="good",
                name=p.get("title", "Producto Shopify"),
                description=p.get("body_html", ""),
                price=variant.get("price", "0"),
                currency="USD",
                stock=variant.get("inventory_quantity", 0),
                is_available=p.get("status") == "active",
                extra_data={"shopify_id": str(p.get("id", "")), "source_platform": "shopify"},
                images=[img.get("src", "") for img in p.get("images", [])],
                tags=p.get("tags", ",").split(",") if isinstance(p.get("tags"), str) else p.get("tags", []),
            )

        elif platform == ChannelPlatform.MERCADOLIBRE:
            return CatalogItem(
                business_id=business_id,
                type="good",
                name=product.get("title", "Producto ML"),
                description=product.get("description", {}).get("plain_text", ""),
                price=product.get("price", 0),
                currency=product.get("currency_id", "ARS"),
                stock=product.get("available_quantity", 0),
                is_available=product.get("status") == "active",
                extra_data={"ml_id": product.get("id", ""), "source_platform": "mercadolibre"},
                images=[pic.get("url", "") for pic in product.get("pictures", [])],
                tags=[],
            )

        elif platform == ChannelPlatform.AMAZON:
            attrs = product.get("attributes", {})
            name = attrs.get("item_name", [{}])[0].get("value", "Producto Amazon")
            price_data = attrs.get("list_price", [{}])[0]
            return CatalogItem(
                business_id=business_id,
                type="good",
                name=name,
                description="\n".join([b.get("value", "") for b in attrs.get("bullet_point", [])]),
                price=price_data.get("value", "0"),
                currency=price_data.get("currency", "USD"),
                stock=0,
                is_available=True,
                extra_data={"asin": product.get("asin", ""), "source_platform": "amazon"},
                images=[],
                tags=[],
            )

        return CatalogItem(
            business_id=business_id,
            type="good",
            name="Producto importado",
            description="",
            price=0,
            currency="USD",
            stock=0,
            is_available=True,
            extra_data={"source_platform": platform.value},
            images=[],
            tags=[],
        )
