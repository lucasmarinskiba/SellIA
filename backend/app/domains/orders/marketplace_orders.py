"""Órdenes de Mercado Libre en la tabla de órdenes.

Las notificaciones de ML no traen la orden completa y pueden perderse, así que la
fuente de verdad es la búsqueda de órdenes del vendedor (que sí trae el detalle).
Corre periódicamente y es idempotente: la clave es (negocio, plataforma, id de ML).

Cambios de estado de órdenes más viejas que la ventana de búsqueda no se ven
hasta que la orden vuelve a aparecer. Por eso la ventana se solapa con la última
corrida en vez de empezar exactamente en ella.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Awaitable, Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.channels.connectors.mercadolibre import (
    MercadoLibreAPIError,
    MercadoLibreAuthError,
    MercadoLibreConnector,
    refresh_credentials,
)
from app.domains.channels.models import ChannelConnection, ChannelPlatform
from app.domains.orders.models import Order, OrderStatus, PaymentStatus
from app.domains.orders.services import EcommerceWebhookProcessor

logger = logging.getLogger(__name__)

PLATFORM = "mercadolibre"
PAGE_SIZE = 50
MAX_PAGES = 20
FIRST_RUN_LOOKBACK = timedelta(days=1)
OVERLAP = timedelta(hours=2)


def order_fields(order: dict[str, Any]) -> dict[str, Any]:
    """Campos de Order a partir de una orden de Mercado Libre."""
    order_id = str(order["id"])
    status = EcommerceWebhookProcessor._map_ml_status(order.get("status", "pending"))
    buyer = order.get("buyer") or {}
    return {
        "external_id": order_id,
        "external_platform": PLATFORM,
        "order_number": order_id,
        "total_amount": Decimal(str(order.get("total_amount", "0"))),
        "currency": order.get("currency_id") or "ARS",
        "status": status,
        "payment_status": (
            PaymentStatus.COMPLETED
            if status == OrderStatus.PAID
            else PaymentStatus.PENDING
        ),
        "customer_name": buyer.get("nickname") or "",
        "customer_email": buyer.get("email"),
        "items": [
            {
                "name": (line.get("item") or {}).get("title", ""),
                "qty": line.get("quantity", 1),
                "price": str(line.get("unit_price", "0")),
                "sku": (line.get("item") or {}).get("seller_sku") or "",
            }
            for line in order.get("order_items", [])
        ],
        "source_channel": PLATFORM,
    }


async def upsert_order(
    db: AsyncSession, business_id: UUID, order: dict[str, Any]
) -> Order:
    """Crea o actualiza la Order de una orden de ML. No hace commit: lo hace quien llama."""
    fields = order_fields(order)
    result = await db.execute(
        select(Order).where(
            Order.business_id == business_id,
            Order.external_platform == PLATFORM,
            Order.external_id == fields["external_id"],
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = Order(business_id=business_id, **fields)
        db.add(row)
        return row

    for key in (
        "status",
        "payment_status",
        "total_amount",
        "currency",
        "items",
        "customer_name",
        "customer_email",
    ):
        setattr(row, key, fields[key])
    return row


async def _with_token_refresh(
    channel: ChannelConnection,
    call: Callable[[MercadoLibreConnector], Awaitable[Any]],
) -> Any:
    """Ejecuta la llamada; si ML rechaza el token, lo renueva una vez y reintenta."""
    try:
        return await call(MercadoLibreConnector(channel.credentials, channel.settings))
    except MercadoLibreAuthError:
        new_credentials = await refresh_credentials(channel.credentials)
        if new_credentials is None:
            raise
        channel.credentials = new_credentials
        return await call(MercadoLibreConnector(new_credentials, channel.settings))


async def _fetch_orders(
    channel: ChannelConnection, since: datetime
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    for page_number in range(MAX_PAGES):
        offset = page_number * PAGE_SIZE

        async def call(
            connector: MercadoLibreConnector, offset: int = offset
        ) -> list[dict[str, Any]]:
            return await connector.list_orders(since, limit=PAGE_SIZE, offset=offset)

        page = await _with_token_refresh(channel, call)
        orders.extend(page)
        if len(page) < PAGE_SIZE:
            break
    return orders


async def reconcile_mercadolibre_orders(
    db: AsyncSession, now: datetime | None = None
) -> dict[str, int]:
    """Trae las órdenes nuevas o cambiadas de cada canal de Mercado Libre activo."""
    now = now or datetime.now(timezone.utc)
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.platform == ChannelPlatform.MERCADOLIBRE,
            ChannelConnection.is_active == True,
        )
    )
    summary = {"channels": 0, "orders": 0, "failed_channels": 0}

    for channel in result.scalars().all():
        summary["channels"] += 1
        since = (
            (channel.last_sync_at - OVERLAP)
            if channel.last_sync_at
            else (now - FIRST_RUN_LOOKBACK)
        )
        try:
            orders = await _fetch_orders(channel, since)
        except (MercadoLibreAuthError, MercadoLibreAPIError, ValueError) as e:
            summary["failed_channels"] += 1
            logger.warning(
                f"Mercado Libre sync failed for channel {channel.id}: {str(e)[:200]}"
            )
            await db.commit()  # conserva un token renovado aunque la búsqueda haya fallado después
            continue

        for order in orders:
            await upsert_order(db, channel.business_id, order)
        summary["orders"] += len(orders)
        channel.last_sync_at = now
        await db.commit()

    return summary
