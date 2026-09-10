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
    "answer_pending": {
        "label": "Contestar las consultas colgadas",
        "detail": (
            "Genera y envía con IA la respuesta a cada comprador que preguntó y todavía no "
            "recibió respuesta en esta plataforma."
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


async def pending_questions(
    db: AsyncSession, business_id: uuid.UUID, platform: str, limit: int = 25,
) -> list[dict[str, Any]]:
    """Buyers on this platform whose last message never got an answer.

    On a marketplace this is the most expensive thing a seller can leave open:
    a question on a listing is someone with their wallet already out.
    """
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )

    result = await db.execute(
        select(Conversation, ChannelConnection)
        .join(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(
            Conversation.business_id == business_id,
            Conversation.is_active.is_(True),
            ChannelConnection.is_active.is_(True),
        )
        .limit(300)
    )

    pending: list[dict[str, Any]] = []
    for conversation, channel in result.all():
        channel_platform = (
            channel.platform.value if hasattr(channel.platform, "value") else str(channel.platform)
        )
        if channel_platform != platform:
            continue

        messages = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
        )
        rows = list(messages.scalars().all())
        if not rows or rows[-1].direction != MessageDirection.INBOUND:
            continue  # answered, or nothing asked

        pending.append({
            "conversation_id": str(conversation.id),
            "name": conversation.lead_name or "comprador",
            "question": (rows[-1].content or "")[:300],
            "asked_at": rows[-1].created_at.isoformat() if rows[-1].created_at else None,
        })
        if len(pending) >= limit:
            break

    return pending


async def answer_pending(
    db: AsyncSession, business_id: uuid.UUID, platform: str,
) -> dict[str, Any]:
    """Have the AI answer every open question on this platform, for real.

    Each reply is generated by the same agent that powers the auto-reply and
    sent through the same outbound path, tagged generated_by="ai" so the
    conversation history keeps saying who actually wrote it.
    """
    from app.domains.agents.ai_reply import generate_ai_response
    from app.domains.channels.models import Conversation
    from app.domains.channels.services import send_outbound_message

    if not capabilities.can(platform, "messages"):
        raise ActionNotAvailable(f"El conector de {platform} no puede enviar mensajes.")

    open_questions = await pending_questions(db, business_id, platform)
    if not open_questions:
        raise ActionNotAvailable(
            f"No hay consultas sin responder en {platform} ahora mismo."
        )

    answered, failed = 0, 0
    last_error: str | None = None
    for item in open_questions:
        try:
            conversation = await db.get(Conversation, uuid.UUID(item["conversation_id"]))
            if conversation is None:
                continue
            reply = await generate_ai_response(
                db, conversation, "captador", business_id,
            )
            if not reply:
                failed += 1
                last_error = "la IA no devolvió respuesta (revisá el saldo del proveedor)"
                continue
            await send_outbound_message(
                db,
                conversation_id=conversation.id,
                content=reply,
                generated_by="ai",
            )
            answered += 1
        except Exception as e:  # noqa: BLE001 -- one buyer must not sink the batch
            logger.warning("answer_pending failed for %s: %s", item["conversation_id"], str(e)[:200])
            last_error = str(e)[:200]
            failed += 1

    if answered == 0:
        raise ActionNotAvailable(
            f"No se pudo responder ninguna de las {len(open_questions)} consultas"
            + (f": {last_error}" if last_error else ".")
        )

    return {
        "executed": True,
        "answered": answered,
        "failed": failed,
        "detail": (
            f"La IA respondió {answered} consulta(s) real(es) en {platform}."
            + (f" {failed} fallaron: {last_error}" if failed else "")
        ),
    }


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
