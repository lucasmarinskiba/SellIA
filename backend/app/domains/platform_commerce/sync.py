"""Import real orders from the platforms whose connector can fetch them.

Only platforms that really implement an order call are attempted (see
capabilities.py). For the rest -- MercadoLibre and WooCommerce today -- this
says so rather than silently reporting zero sales, because "no pudimos traer tus
ventas de acá" and "no vendiste nada" are very different statements to put in
front of a seller.

Orders are keyed on (external_platform, external_id), so re-running the sync
updates rather than duplicates.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from . import capabilities

logger = get_logger(__name__)

DEFAULT_LOOKBACK_DAYS = 60


def _decimal(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _first(payload: dict[str, Any], *keys: str) -> Any:
    """Platform payloads disagree on field names for the same thing."""
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def normalize_order(platform: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Map a platform's order payload onto the fields Order actually has.

    Deliberately conservative: a field that cannot be found stays None, which
    the P&L then reports as unknown. Guessing a total from a partial payload
    would put a wrong number in a revenue figure.
    """
    total = _decimal(_first(raw, "total_amount", "OrderTotal", "total", "payment_total", "price"))
    if isinstance(total, Decimal) is False and isinstance(_first(raw, "OrderTotal"), dict):
        total = _decimal((_first(raw, "OrderTotal") or {}).get("Amount"))

    currency = _first(raw, "currency", "CurrencyCode", "currency_code")
    if currency is None and isinstance(_first(raw, "OrderTotal"), dict):
        currency = (_first(raw, "OrderTotal") or {}).get("CurrencyCode")

    external_id = _first(raw, "id", "order_id", "AmazonOrderId", "transaction", "order_sn")
    created_raw = _first(raw, "created_at", "PurchaseDate", "create_time", "order_date")

    created_at: Optional[datetime] = None
    if isinstance(created_raw, (int, float)):
        try:
            created_at = datetime.fromtimestamp(float(created_raw), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            created_at = None
    elif isinstance(created_raw, str):
        try:
            created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        except ValueError:
            created_at = None

    return {
        "external_id": str(external_id) if external_id is not None else None,
        "external_platform": platform,
        "total_amount": total,
        "currency": (str(currency)[:3].upper() if currency else None),
        "created_at": created_at,
        "status_raw": _first(raw, "status", "OrderStatus", "order_status"),
        "raw": raw,
    }


async def sync_platform_orders(
    db: AsyncSession,
    business_id: uuid.UUID,
    platform: str,
    credentials: dict[str, Any],
    settings: dict[str, Any],
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> dict[str, Any]:
    """Pull this platform's real orders into the Order table."""
    from app.domains.channels.connectors import get_connector
    from app.domains.channels.models import ChannelPlatform
    from app.domains.orders.models import Order, OrderStatus, PaymentStatus

    method_name = capabilities.order_method(platform)
    if method_name is None:
        return {
            "platform": platform,
            "supported": False,
            "reason": (
                f"El conector de {platform} todavía no puede traer órdenes: sólo maneja "
                "mensajes. Tus ventas de esta plataforma no se pueden importar automáticamente."
            ),
            "imported": 0,
            "updated": 0,
        }

    connector = get_connector(ChannelPlatform(platform), credentials, settings)
    method = getattr(connector, method_name)
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    try:
        # Each connector names its window parameter differently; try the ones
        # that exist and fall back to no argument.
        try:
            raw_orders = await method(since.strftime("%Y-%m-%dT%H:%M:%SZ"))
        except TypeError:
            raw_orders = await method()
    except Exception as e:  # noqa: BLE001 -- a platform error is a real result
        logger.warning("order sync failed for %s: %s", platform, str(e)[:200])
        return {
            "platform": platform,
            "supported": True,
            "ok": False,
            "reason": f"La plataforma rechazó la consulta: {str(e)[:160]}",
            "imported": 0,
            "updated": 0,
        }

    if not isinstance(raw_orders, list):
        raw_orders = []

    imported, updated, skipped = 0, 0, 0
    for raw in raw_orders:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        norm = normalize_order(platform, raw)
        if not norm["external_id"] or norm["total_amount"] is None:
            # Without an id we cannot dedupe, and without a total it is not a
            # sale we can put in a revenue figure.
            skipped += 1
            continue

        existing = await db.execute(
            select(Order).where(
                Order.external_platform == platform,
                Order.external_id == norm["external_id"],
                Order.business_id == business_id,
            )
        )
        order = existing.scalar_one_or_none()

        if order is None:
            order = Order(
                business_id=business_id,
                external_id=norm["external_id"],
                external_platform=platform,
                source_channel=platform,
                total_amount=norm["total_amount"],
                currency=norm["currency"] or "ARS",
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                items=[],
                extra_data={"synced_payload": norm["raw"]},
            )
            if norm["created_at"]:
                order.created_at = norm["created_at"]
            db.add(order)
            imported += 1
        else:
            order.total_amount = norm["total_amount"]
            if norm["currency"]:
                order.currency = norm["currency"]
            extra = dict(order.extra_data or {})
            extra["synced_payload"] = norm["raw"]
            order.extra_data = extra
            updated += 1

        # Paid/settled states differ per platform; only mark paid on words the
        # platforms really use, never by assumption.
        status_raw = str(norm["status_raw"] or "").lower()
        if any(word in status_raw for word in ("paid", "approved", "complete", "shipped", "delivered")):
            order.payment_status = PaymentStatus.COMPLETED
            if order.paid_at is None:
                order.paid_at = norm["created_at"] or datetime.now(timezone.utc)

    await db.commit()
    return {
        "platform": platform,
        "supported": True,
        "ok": True,
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "fetched": len(raw_orders),
    }


async def sync_all(db: AsyncSession, business_ids: list[uuid.UUID]) -> list[dict[str, Any]]:
    """Sync every connected platform that can report orders."""
    from app.domains.channels.models import ChannelConnection

    if not business_ids:
        return []

    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id.in_(business_ids),
            ChannelConnection.is_active.is_(True),
        )
    )
    results: list[dict[str, Any]] = []
    for channel in result.scalars().all():
        platform = channel.platform.value if hasattr(channel.platform, "value") else str(channel.platform)
        if not capabilities.can(platform, "orders"):
            continue
        try:
            results.append(await sync_platform_orders(
                db, channel.business_id, platform, channel.credentials or {}, channel.settings or {},
            ))
        except Exception as e:  # noqa: BLE001 -- one platform must not sink the sweep
            logger.warning("sync_all failed for %s: %s", platform, str(e)[:200])
            results.append({
                "platform": platform, "supported": True, "ok": False,
                "reason": str(e)[:160], "imported": 0, "updated": 0,
            })
    return results
