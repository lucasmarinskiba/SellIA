"""Selling actions per platform, offered only where the connector can do them.

The AI agents that sell are the ones this codebase already has: the auto-reply
that answers a buyer's question through the unified conversation pipeline (which
is what a MercadoLibre question or an Amazon buyer message becomes), and the
catalog push that puts products on the platforms whose connector implements it.

Each action is advertised per platform strictly from capabilities.py, so a
platform never shows a button for something its connector cannot do -- the
matrix and the buttons come from the same introspection.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from . import capabilities, sync

logger = get_logger(__name__)


class ActionNotAvailable(Exception):
    """This platform's connector cannot do this."""


#: action -> (label, what it does, required capability, whether it reaches buyers)
ACTIONS: dict[str, dict[str, Any]] = {
    "answer_buyers": {
        "label": "Que la IA conteste a los compradores",
        "detail": (
            "Las preguntas que entran por esta plataforma reciben una primera respuesta "
            "automática en segundos, con el contexto de tu negocio."
        ),
        "capability": "messages",
        "touches_customers": True,
    },
    "sync_orders": {
        "label": "Traer mis ventas",
        "detail": "Importa las órdenes reales para calcular facturación y margen.",
        "capability": "orders",
        "touches_customers": False,
    },
    "publish_catalog": {
        "label": "Publicar mi catálogo",
        "detail": "Sube tus productos de SellIA a esta plataforma.",
        "capability": "catalog_push",
        "touches_customers": True,
    },
}


def actions_for(platform: str) -> list[dict[str, Any]]:
    """The actions really available on this platform."""
    return [
        {
            "key": key,
            "label": spec["label"],
            "detail": spec["detail"],
            "available": capabilities.can(platform, spec["capability"]),
            "touches_customers": spec["touches_customers"],
        }
        for key, spec in ACTIONS.items()
    ]


async def answer_buyers(db: AsyncSession, business_id: uuid.UUID) -> dict[str, Any]:
    """Turn on the real AI auto-reply. Shares the implementation with the
    authority builder so both screens cannot drift into different behaviour."""
    from app.domains.authority.automations import enable_auto_reply

    return await enable_auto_reply(db, business_id)


async def sync_orders(
    db: AsyncSession, business_id: uuid.UUID, platform: str,
) -> dict[str, Any]:
    from app.domains.channels.models import ChannelConnection

    if not capabilities.can(platform, "orders"):
        raise ActionNotAvailable(
            f"El conector de {platform} todavía no puede traer órdenes."
        )

    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id == business_id,
            ChannelConnection.is_active.is_(True),
        )
    )
    channel = next(
        (
            c for c in result.scalars().all()
            if (c.platform.value if hasattr(c.platform, "value") else str(c.platform)) == platform
        ),
        None,
    )
    if channel is None:
        raise ActionNotAvailable(f"No tenés {platform} conectado.")

    return await sync.sync_platform_orders(
        db, business_id, platform, channel.credentials or {}, channel.settings or {},
    )


async def publish_catalog(
    db: AsyncSession, business_id: uuid.UUID, platform: str,
) -> dict[str, Any]:
    """Push the account's real products to the platform.

    Reports per-product outcomes from what the platform actually answered: a
    push that the platform rejected is a failure, not a published listing.
    """
    from app.domains.channels.connectors import get_connector
    from app.domains.channels.models import ChannelConnection, ChannelPlatform

    if not capabilities.can(platform, "catalog_push"):
        raise ActionNotAvailable(
            f"El conector de {platform} no puede publicar productos todavía."
        )

    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id == business_id,
            ChannelConnection.is_active.is_(True),
        )
    )
    channel = next(
        (
            c for c in result.scalars().all()
            if (c.platform.value if hasattr(c.platform, "value") else str(c.platform)) == platform
        ),
        None,
    )
    if channel is None:
        raise ActionNotAvailable(f"No tenés {platform} conectado.")

    try:
        from app.domains.products.models import Product

        products_result = await db.execute(
            select(Product).where(Product.business_id == business_id).limit(50)
        )
        products = list(products_result.scalars().all())
    except Exception as e:  # noqa: BLE001
        logger.warning("publish_catalog: products unavailable: %s", str(e)[:200])
        await db.rollback()
        products = []

    if not products:
        raise ActionNotAvailable(
            "No tenés productos cargados en SellIA todavía, así que no hay nada que publicar."
        )

    connector = get_connector(ChannelPlatform(platform), channel.credentials or {}, channel.settings or {})
    pushed, failed = 0, 0
    last_error: str | None = None

    for product in products:
        try:
            if hasattr(connector, "push_catalog_item"):
                await connector.push_catalog_item(product)
            else:
                await connector.sync_products_to_tiktok([{  # type: ignore[attr-defined]
                    "id": str(product.id),
                    "name": product.name,
                    "price": float(product.price or 0),
                }])
            pushed += 1
        except Exception as e:  # noqa: BLE001 -- one product must not sink the batch
            logger.warning("publish_catalog: %s failed: %s", product.id, str(e)[:200])
            last_error = str(e)[:200]
            failed += 1

    if pushed == 0:
        raise ActionNotAvailable(
            f"La plataforma rechazó los {failed} productos"
            + (f": {last_error}" if last_error else ".")
            + " Revisá las credenciales del canal."
        )

    return {
        "executed": True,
        "pushed": pushed,
        "failed": failed,
        "detail": (
            f"{pushed} producto(s) enviados a {platform}."
            + (f" {failed} fallaron: {last_error}" if failed else "")
        ),
    }
