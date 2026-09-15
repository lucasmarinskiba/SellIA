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
from app.domains.platform_commerce import capabilities as platform_capabilities


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

    # Was a hand-written set including MERCADOLIBRE (whose connector has zero
    # catalog-pull code -- messages/webhooks only) and missing META_ADS/
    # BEACONS (which do have it). Derived by introspection now, same
    # single-source-of-truth principle as platform_commerce/capabilities.py:
    # a platform is here only if its connector class really defines
    # pull_catalog_items.
    @staticmethod
    def _pull_platforms() -> set:
        return {
            p for p in ChannelPlatform
            if platform_capabilities.can(p.value, "catalog_pull")
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
        """Pull products from external platform into local catalog.

        Was checking `hasattr(connector, "get_products")` -- no connector in
        this codebase has ever defined that method (the real one is
        `pull_catalog_items`, per platform_commerce/capabilities.py), so this
        always returned "no soporta importación" for every platform and the
        endpoint that calls this (POST /{business_id}/catalog/sync-pull) was
        completely dead despite being live and reachable.
        """
        try:
            channels = await self.get_connected_channels(business_id, {platform})
            if not channels:
                return CatalogSyncResult(platform.value, False, "No hay canal conectado para esta plataforma")

            channel = channels[0]
            connector = get_connector(platform, channel.credentials, channel.settings)

            if not hasattr(connector, "pull_catalog_items"):
                return CatalogSyncResult(platform.value, False, "Esta plataforma no soporta importación de productos")

            products = await connector.pull_catalog_items()
            created, updated = 0, 0

            for product in products:
                try:
                    external_id = self._external_id(product, platform)
                    existing = None
                    if external_id:
                        result = await self.db.execute(
                            select(CatalogItem).where(
                                CatalogItem.business_id == business_id,
                                CatalogItem.source_platform == platform.value,
                                CatalogItem.external_id == external_id,
                            )
                        )
                        existing = result.scalar_one_or_none()

                    fields = self._platform_product_fields(product, platform)
                    if existing:
                        for key, value in fields.items():
                            if key == "name":  # keep the seller's own rename if they changed it
                                continue
                            setattr(existing, key, value)
                        updated += 1
                    else:
                        item = CatalogItem(
                            business_id=business_id,
                            source_platform=platform.value,
                            external_id=external_id,
                            **fields,
                        )
                        self.db.add(item)
                        created += 1
                except Exception as e:
                    from app.core.logger import get_logger
                    get_logger(__name__).error(f"Error pulling product to catalog: {e}")
                    continue

            await self.db.commit()
            detail = f"{created} nuevo(s), {updated} actualizado(s)"
            if platform == ChannelPlatform.AMAZON and products:
                detail += ". Amazon no devuelve precio en este endpoint -- completalo a mano."
            return CatalogSyncResult(platform.value, True, detail, created + updated)
        except Exception as e:
            return CatalogSyncResult(platform.value, False, f"Error: {str(e)}")

    async def pull_all(self, business_id: UUID) -> list[CatalogSyncResult]:
        """Pull products from all platforms whose connector really supports it."""
        channels = await self.get_connected_channels(business_id, self._pull_platforms())
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

    def _external_id(self, product: dict[str, Any], platform: ChannelPlatform) -> str | None:
        """The platform's own id for this product -- what dedup keys on."""
        if platform == ChannelPlatform.SHOPIFY:
            p = product.get("product", product)
            pid = p.get("id")
            return str(pid) if pid is not None else None
        if platform == ChannelPlatform.AMAZON:
            return product.get("asin") or None
        if platform == ChannelPlatform.META_ADS:
            return product.get("id") or None
        if platform == ChannelPlatform.BEACONS:
            pid = product.get("id") or product.get("sku")
            return str(pid) if pid is not None else None
        return None

    def _platform_product_fields(self, product: dict[str, Any], platform: ChannelPlatform) -> dict[str, Any]:
        """CatalogItem constructor kwargs from a platform's raw product shape
        -- every connector's pull_catalog_items() returns that platform's own
        format verbatim, there is no normalized shape to rely on."""
        if platform == ChannelPlatform.SHOPIFY:
            p = product.get("product", product)
            variant = (p.get("variants") or [{}])[0]
            tags = p.get("tags", "")
            return dict(
                type="good",
                name=p.get("title", "Producto Shopify"),
                description=p.get("body_html", "") or "",
                category=p.get("product_type") or None,
                price=variant.get("price", "0") or "0",
                currency="USD",
                stock=variant.get("inventory_quantity", 0) or 0,
                is_available=p.get("status") == "active",
                extra_data={},
                images=[img.get("src", "") for img in (p.get("images") or [])],
                tags=tags.split(",") if isinstance(tags, str) and tags else (tags or []),
            )

        if platform == ChannelPlatform.AMAZON:
            attrs = product.get("attributes", {}) or {}
            summaries = (product.get("summaries") or [{}])[0]
            name = summaries.get("itemName") or (attrs.get("item_name", [{}])[0].get("value") if attrs.get("item_name") else None) or "Producto Amazon"
            price_list = attrs.get("list_price") or []
            price = price_list[0].get("value", "0") if price_list else "0"
            currency = price_list[0].get("currency", "USD") if price_list else "USD"
            return dict(
                type="good",
                name=name,
                description="\n".join(b.get("value", "") for b in attrs.get("bullet_point", [])),
                category=None,
                price=price,
                currency=currency,
                stock=0,
                is_available=True,
                extra_data={},
                images=[],
                tags=[],
            )

        if platform == ChannelPlatform.META_ADS:
            raw_price = product.get("price") or "0 USD"
            amount, _, currency = str(raw_price).partition(" ")
            return dict(
                type="good",
                name=product.get("name", "Producto Meta"),
                description=product.get("description", ""),
                category=None,
                price=amount or "0",
                currency=currency or "USD",
                stock=None,
                is_available=(product.get("availability") or "in stock") == "in stock",
                extra_data={},
                images=[product["image_url"]] if product.get("image_url") else [],
                tags=[],
            )

        if platform == ChannelPlatform.BEACONS:
            return dict(
                type="good",
                name=product.get("name", "Producto Beacons"),
                description=product.get("description", ""),
                category=None,
                price=product.get("price", "0") or "0",
                currency=product.get("currency", "USD"),
                stock=None,
                is_available=True,
                extra_data={},
                images=[product["image_url"]] if product.get("image_url") else [],
                tags=[],
            )

        return dict(
            type="good",
            name="Producto importado",
            description="",
            category=None,
            price=0,
            currency="USD",
            stock=None,
            is_available=True,
            extra_data={},
            images=[],
            tags=[],
        )
