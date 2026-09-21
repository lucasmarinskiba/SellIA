"""Mercado Libre order notifications -> FOMO conversion events.

Why this is built the way it is
-------------------------------
A Mercado Libre notification carries only `{topic, resource, user_id, ...}`; ML's
own guidance is to validate the origin and never act on the payload alone. The
documented signature scheme people associate with `x-signature` belongs to
Mercado PAGO, not to Mercado Libre notifications, so there is no HMAC to check
here. Instead the request is authenticated in layers:

1. Callback token: the channel's unguessable `webhook_token` (the same
   convention channels/webhook uses), compared in constant time and bound to the
   `business_id` in the URL. A wrong token, wrong business, inactive or
   non-Mercado-Libre channel all fail identically (401) — no enumeration.
2. Payload sanity: `resource` must be exactly `/orders/<digits>` (the only URL we
   will ever fetch, so the payload cannot steer requests elsewhere), and
   `user_id` must equal the channel's own seller id.
3. Confirmation with ML itself: the order is re-fetched with the seller's own
   token. It must exist, belong to that seller and be `paid`. A forged
   notification cannot pass this without a real paid order.

The origin-IP allowlist ML documents is deliberately not enforced: behind the
platform proxy the TCP peer is not the sender, and a spoofable X-Forwarded-For
would give false confidence while a wrong allowlist would silently drop real
sales. The token + confirmation carry the security instead.

Ingestion is idempotent (ML retries, and `orders_v2` fires on every change to an
order — shipping, delivery — while the status stays `paid`). The check-then-insert
is not atomic, so two truly simultaneous deliveries of the same order could both
insert; that is accepted rather than adding a schema change.
"""

import hmac
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.channels.models import ChannelConnection, ChannelPlatform
from app.domains.seo_config.fomo_models import ConversionEvent
from app.domains.seo_config.fomo_service import FOMAConversionService
from app.domains.seo_config.models import PublicationLink

logger = get_logger(__name__)

ML_API = "https://api.mercadolibre.com"
PLATFORM_NAME = "mercado-libre"
ORDER_TOPICS = frozenset({"orders_v2", "orders"})
_ORDER_RESOURCE_RE = re.compile(r"^/orders/(\d+)$")
DEDUPE_WINDOW = timedelta(days=90)


class NotificationRejected(Exception):
    """The notification must be refused; carries the HTTP status to answer with."""

    def __init__(self, status_code: int, reason: str):
        super().__init__(reason)
        self.status_code = status_code
        self.reason = reason


class MercadoLibreUnavailable(Exception):
    """Mercado Libre could not be reached/verified right now (not a verdict on the order)."""


@dataclass(frozen=True)
class OrderNotification:
    order_id: str
    seller_id: str


async def authenticate_channel(
    db: AsyncSession, business_id: UUID, token: str | None
) -> ChannelConnection | None:
    """Return the channel iff `token` is the webhook token of an active Mercado Libre
    channel of this business. Constant-time compare; None on any mismatch."""
    if not token:
        return None
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id == business_id,
            ChannelConnection.platform == ChannelPlatform.MERCADOLIBRE,
            ChannelConnection.is_active.is_(True),
        )
    )
    supplied = token.encode("utf-8")
    match = None
    for channel in result.scalars().all():
        # No early return: every candidate is compared so timing doesn't reveal which matched.
        if hmac.compare_digest(channel.webhook_token.encode("utf-8"), supplied):
            match = channel
    return match


def parse_notification(payload: Any, channel: ChannelConnection) -> OrderNotification | None:
    """Validate an already-authenticated notification.

    Returns None for topics that are not order notifications (questions, messages,
    items...) — acknowledged and ignored, since they are not conversions.
    Raises NotificationRejected for malformed or mismatched payloads.
    """
    if not isinstance(payload, dict):
        raise NotificationRejected(400, "Payload inválido")

    if payload.get("topic") not in ORDER_TOPICS:
        return None

    match = _ORDER_RESOURCE_RE.match(str(payload.get("resource", "")))
    if not match:
        raise NotificationRejected(400, "Recurso inválido")

    channel_seller = str((channel.credentials or {}).get("seller_id") or "")
    if not channel_seller or str(payload.get("user_id")) != channel_seller:
        raise NotificationRejected(403, "La notificación no corresponde al vendedor de este canal")

    return OrderNotification(order_id=match.group(1), seller_id=channel_seller)


def extract_paid_items(order: dict[str, Any], seller_id: str) -> list[dict[str, Any]]:
    """Items of a verified, paid order belonging to `seller_id`; [] otherwise.

    Raises NotificationRejected(403) if the order belongs to a different seller.
    """
    if str((order.get("seller") or {}).get("id")) != seller_id:
        raise NotificationRejected(403, "La orden no pertenece al vendedor del canal")
    if order.get("status") != "paid":
        return []

    items = []
    for line in order.get("order_items") or []:
        item_id = (line.get("item") or {}).get("id")
        if not item_id:
            continue
        try:
            value = float(line.get("unit_price") or 0) * float(line.get("quantity") or 1)
        except (TypeError, ValueError):
            value = 0.0
        items.append({"item_id": str(item_id), "value": value})
    return items


async def _refresh_channel_token(db: AsyncSession, channel: ChannelConnection) -> bool:
    """Refresh the seller's access token once and persist it. False if it can't be done."""
    refresh_token = (channel.credentials or {}).get("refresh_token")
    if not refresh_token:
        return False
    from app.core.oauth_connectors import MercadoLibreOAuth

    try:
        data = await MercadoLibreOAuth.refresh_token(refresh_token)
    except Exception as e:
        logger.warning(f"ML token refresh failed for channel {channel.id}: {str(e)[:100]}")
        return False
    if not data.get("access_token"):
        return False
    channel.credentials["access_token"] = data["access_token"]
    if data.get("refresh_token"):
        channel.credentials["refresh_token"] = data["refresh_token"]
    await db.commit()
    return True


async def fetch_order(db: AsyncSession, channel: ChannelConnection, order_id: str) -> dict[str, Any] | None:
    """Fetch the order from ML with the seller's token.

    None -> ML says it isn't there / isn't ours (404/403): nothing to record.
    MercadoLibreUnavailable -> could not verify (network, 5xx, dead token).
    """
    url = f"{ML_API}/orders/{order_id}"
    for attempt in (1, 2):
        token = (channel.credentials or {}).get("access_token")
        if not token:
            raise MercadoLibreUnavailable("el canal no tiene access_token")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        except httpx.HTTPError as e:
            raise MercadoLibreUnavailable(str(e)[:100]) from e

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (404, 403):
            return None
        if resp.status_code == 401 and attempt == 1 and await _refresh_channel_token(db, channel):
            continue
        raise MercadoLibreUnavailable(f"ML devolvió {resp.status_code}")
    raise MercadoLibreUnavailable("no se pudo verificar la orden")


_ITEM_ID_RE = re.compile(r"^([A-Za-z]{2,4})(\d+)$")


def url_matches_item(url: str, item_id: str) -> bool:
    """Does a publication URL point at this Mercado Libre item?

    The API id is `MLA1234567890` but listing permalinks read
    `.../MLA-1234567890-title-_JM` (hyphen) while catalog pages use
    `.../p/MLA1234567890`, so both spellings must match. Boundaries stop
    `MLA111` from matching inside `MLA-1111` or `XMLA111`.
    """
    match = _ITEM_ID_RE.match(item_id)
    if not match:
        return item_id in url
    prefix, digits = match.groups()
    return re.search(rf"(?<![A-Za-z0-9]){prefix}-?{digits}(?!\d)", url, re.IGNORECASE) is not None


async def _find_link(db: AsyncSession, business_id: UUID, item_id: str) -> PublicationLink | None:
    match = _ITEM_ID_RE.match(item_id)
    needle = match.group(2) if match else item_id  # the digits are spelled the same in every URL form
    result = await db.execute(
        select(PublicationLink)
        .where(
            PublicationLink.business_id == business_id,
            PublicationLink.url.contains(needle, autoescape=True),
        )
        .limit(50)
    )
    return next((link for link in result.scalars().all() if url_matches_item(link.url, item_id)), None)


async def _already_recorded(db: AsyncSession, business_id: UUID, link_id: UUID, order_id: str, item_id: str) -> bool:
    cutoff = datetime.now(timezone.utc) - DEDUPE_WINDOW
    result = await db.execute(
        select(ConversionEvent.raw_event_data).where(
            ConversionEvent.business_id == business_id,
            ConversionEvent.link_id == link_id,
            ConversionEvent.platform_name == PLATFORM_NAME,
            ConversionEvent.external_listing_id == item_id,
            ConversionEvent.created_at >= cutoff,
        )
    )
    return any((raw or {}).get("order_id") == order_id for (raw,) in result.all())


async def process_order_notification(db: AsyncSession, channel_id: UUID, order_id: str) -> dict[str, Any]:
    """Confirm the order with Mercado Libre and log one conversion per tracked item.

    Only items that map to one of the business's PublicationLinks count: a
    conversion event is defined per link, and an order for something the business
    isn't tracking is not a FOMO conversion.
    """
    channel = await db.get(ChannelConnection, channel_id)
    if not channel or not channel.is_active:
        return {"status": "ignored", "reason": "canal inactivo o inexistente"}

    seller_id = str((channel.credentials or {}).get("seller_id") or "")
    business_id = channel.business_id

    order = await fetch_order(db, channel, order_id)
    if order is None:
        return {"status": "ignored", "reason": "Mercado Libre no reconoce la orden para este vendedor"}

    items = extract_paid_items(order, seller_id)
    if not items:
        return {"status": "ignored", "reason": f"orden en estado '{order.get('status')}', no pagada"}

    recorded = 0
    service = FOMAConversionService(db)
    for item in items:
        link = await _find_link(db, business_id, item["item_id"])
        if not link:
            continue
        if await _already_recorded(db, business_id, link.id, order_id, item["item_id"]):
            continue
        await service.log_conversion(
            business_id=business_id,
            link_id=link.id,
            platform_name=PLATFORM_NAME,
            conversion_type="purchase",
            conversion_value=item["value"],
            external_listing_id=item["item_id"],
            raw_event_data={"source": "mercado-libre", "order_id": order_id, "verified": True},
        )
        recorded += 1

    return {"status": "recorded" if recorded else "ignored", "conversions": recorded}


async def run_order_notification(channel_id: UUID, order_id: str) -> None:
    """Background entry point: own DB session (the request's is closed by then).

    The 200 was already returned to ML, so a failure here can't trigger an ML
    retry — it is logged with the order id so the loss is traceable.
    """
    from app.core.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            outcome = await process_order_notification(db, channel_id, order_id)
        logger.info(f"ML order {order_id} processed: {outcome}")
    except NotificationRejected as e:
        logger.warning(f"ML order {order_id} rejected after verification: {e.reason}")
    except MercadoLibreUnavailable as e:
        logger.warning(f"ML order {order_id} could not be verified, conversion NOT recorded: {e}")
    except Exception as e:  # noqa: BLE001 -- a background task must never raise
        logger.error(f"ML order {order_id} processing failed: {str(e)[:200]}")
