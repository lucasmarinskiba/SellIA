"""Shipments Services

Lógica de negocio para crear, rastrear y gestionar envíos.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_value, encrypt_value
from app.core.events import emit_event
from app.domains.channels.services import send_outbound_message
from app.domains.orders.models import Order, OrderStatus
from app.domains.shipments.connectors import get_carrier_metadata, get_connector
from app.domains.shipments.models import (
    Shipment,
    ShipmentConfig,
    ShipmentStatus,
    ShipmentTrackingEvent,
)

logger = logging.getLogger(__name__)

# ============================================================
# SHIPMENT CONFIG
# ============================================================


async def list_shipment_configs(
    db: AsyncSession, business_id: uuid.UUID
) -> list[ShipmentConfig]:
    result = await db.execute(
        select(ShipmentConfig)
        .where(ShipmentConfig.business_id == business_id)
        .order_by(ShipmentConfig.created_at)
    )
    return result.scalars().all()


async def get_shipment_config(
    db: AsyncSession, config_id: uuid.UUID
) -> ShipmentConfig | None:
    return await db.get(ShipmentConfig, config_id)


async def create_shipment_config(
    db: AsyncSession, business_id: uuid.UUID, data: dict[str, Any]
) -> ShipmentConfig:
    # Encrypt sensitive credentials
    creds = data.get("credentials", {})
    encrypted_creds = {}
    for key, value in creds.items():
        if key in ("password", "api_key", "secret", "token", "private_key") and value:
            encrypted_creds[key] = encrypt_value(str(value))
        else:
            encrypted_creds[key] = value

    config = ShipmentConfig(
        business_id=business_id,
        carrier=data["carrier"],
        label=data.get("label"),
        credentials=encrypted_creds,
        is_test_mode=data.get("is_test_mode", False),
        is_active=data.get("is_active", True),
        default_service_type=data.get("default_service_type"),
        default_from_address=data.get("default_from_address", {}),
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def update_shipment_config(
    db: AsyncSession, config: ShipmentConfig, data: dict[str, Any]
) -> ShipmentConfig:
    if "credentials" in data:
        creds = data["credentials"]
        encrypted_creds = {}
        for key, value in creds.items():
            if (
                key in ("password", "api_key", "secret", "token", "private_key")
                and value
            ):
                encrypted_creds[key] = encrypt_value(str(value))
            else:
                encrypted_creds[key] = value
        config.credentials = encrypted_creds

    for field in [
        "label",
        "is_test_mode",
        "is_active",
        "default_service_type",
        "default_from_address",
    ]:
        if field in data:
            setattr(config, field, data[field])

    await db.commit()
    await db.refresh(config)
    return config


async def delete_shipment_config(db: AsyncSession, config: ShipmentConfig):
    await db.delete(config)
    await db.commit()


async def test_shipment_config(
    db: AsyncSession, config: ShipmentConfig
) -> dict[str, Any]:
    """Test a carrier connection by creating a dummy shipment and checking tracking."""
    try:
        connector = _get_connector_from_config(config)
        # Test with dummy data
        test_result = await connector.get_tracking("TEST123")
        return {
            "success": True,
            "message": f"Conexión exitosa con {config.carrier.value}",
            "details": test_result,
        }
    except Exception as e:
        logger.exception("test_shipment_config: error inesperado")
        return {"success": False, "message": f"Error de conexión: {e!s}"}


def _get_connector_from_config(config: ShipmentConfig):
    """Get connector instance from a ShipmentConfig, decrypting credentials."""
    creds = dict(config.credentials)
    for key in ("password", "api_key", "secret", "token", "private_key"):
        if creds.get(key):
            try:
                creds[key] = decrypt_value(creds[key])
            except Exception:
                logger.exception("_get_connector_from_config: error inesperado")
                # Assume plain text
    return get_connector(config.carrier.value, creds, config.is_test_mode)


# ============================================================
# SHIPMENTS
# ============================================================


async def list_shipments(
    db: AsyncSession,
    business_id: uuid.UUID,
    status: str | None = None,
    carrier: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Shipment], int]:
    query = select(Shipment).where(
        Shipment.business_id == business_id, Shipment.is_active == True
    )

    if status:
        query = query.where(Shipment.status == status)
    if carrier:
        query = query.where(Shipment.carrier == carrier)
    if search:
        query = query.where(
            (Shipment.tracking_number.ilike(f"%{search}%"))
            | (Shipment.notes.ilike(f"%{search}%"))
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    query = query.order_by(desc(Shipment.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_shipment(db: AsyncSession, shipment_id: uuid.UUID) -> Shipment | None:
    return await db.get(Shipment, shipment_id)


async def get_shipment_with_events(
    db: AsyncSession, shipment_id: uuid.UUID
) -> Shipment | None:
    shipment = await db.get(Shipment, shipment_id)
    if not shipment:
        return None
    # Load tracking events
    result = await db.execute(
        select(ShipmentTrackingEvent)
        .where(ShipmentTrackingEvent.shipment_id == shipment_id)
        .order_by(desc(ShipmentTrackingEvent.event_at))
    )
    shipment.tracking_events = result.scalars().all()
    return shipment


async def create_shipment(
    db: AsyncSession, business_id: uuid.UUID, data: dict[str, Any]
) -> Shipment:
    """Create a shipment, optionally generating label with carrier and notifying customer."""
    order_id = data["order_id"]
    order = await db.get(Order, order_id)
    if not order:
        raise ValueError("Orden no encontrada")

    # Resolve config
    config_id = data.get("config_id")
    config = None
    if config_id:
        config = await db.get(ShipmentConfig, config_id)

    carrier = data["carrier"]
    service_type = data.get("service_type", "standard")

    # Build addresses
    from_addr = data.get("from_address") or (
        config.default_from_address if config else {}
    )
    to_addr = data.get("to_address") or order.shipping_address or {}

    # Build package from order items if not provided
    package = data.get("package", {})
    if not package.get("items") and order.items:
        package["items"] = [
            {
                "name": item.get("name", ""),
                "qty": item.get("qty", 1),
                "sku": item.get("sku"),
            }
            for item in order.items
        ]

    # Create shipment record
    shipment = Shipment(
        business_id=business_id,
        order_id=order_id,
        config_id=config_id,
        carrier=carrier,
        service_type=service_type,
        from_address=from_addr,
        to_address=to_addr,
        package=package,
        shipping_cost=data.get("shipping_cost"),
        insurance_amount=data.get("insurance_amount"),
        declared_value=data.get("declared_value") or float(order.total_amount),
        estimated_delivery_date=data.get("estimated_delivery_date"),
        notes=data.get("notes"),
    )
    db.add(shipment)
    await db.flush()

    # Generate label if requested and config exists
    if data.get("auto_generate_label") and config:
        try:
            connector = _get_connector_from_config(config)
            result = await connector.create_shipment(
                from_address=from_addr,
                to_address=to_addr,
                package=package,
                service_type=service_type,
                reference=str(order.order_number or order_id),
            )
            shipment.tracking_number = result.get("tracking_number")
            shipment.tracking_url = result.get("tracking_url")
            shipment.label_url = result.get("label_url")
            shipment.label_data = result.get("label_data")
            shipment.carrier_response = result.get("carrier_response", {})
            if result.get("status"):
                shipment.status = result["status"]

            # Save initial tracking events if any
            for ev in result.get("events", []):
                event = ShipmentTrackingEvent(
                    shipment_id=shipment.id,
                    event_code=ev.get("event_code"),
                    event_description=ev.get("event_description"),
                    location=ev.get("location"),
                    event_at=(
                        datetime.fromisoformat(ev["event_at"])
                        if isinstance(ev.get("event_at"), str)
                        else datetime.now(UTC)
                    ),
                )
                db.add(event)

            # Update order with shipping info
            order.shipping_provider = carrier
            order.tracking_number = shipment.tracking_number
            if (
                shipment.status
                in (
                    ShipmentStatus.LABEL_CREATED,
                    ShipmentStatus.PICKED_UP,
                    ShipmentStatus.IN_TRANSIT,
                )
                and order.status == OrderStatus.PAID
            ):
                order.status = OrderStatus.SHIPPED
                order.shipped_at = datetime.now(UTC)

        except Exception as e:
            logger.exception("create_shipment: error inesperado")
            shipment.notes = (
                f"{shipment.notes or ''}\nError al generar etiqueta: {e!s}".strip()
            )
            shipment.status = ShipmentStatus.EXCEPTION

    await db.commit()
    await db.refresh(shipment)

    # Notify customer if requested
    if data.get("notify_customer"):
        await notify_customer(db, shipment, channel=data.get("notification_channel"))

    # Emit event
    await emit_event(
        "shipment_created",
        {
            "shipment_id": str(shipment.id),
            "order_id": str(order_id),
            "business_id": str(business_id),
            "carrier": carrier,
            "tracking_number": shipment.tracking_number,
        },
    )

    return shipment


async def update_shipment(
    db: AsyncSession, shipment: Shipment, data: dict[str, Any]
) -> Shipment:
    for field in [
        "tracking_number",
        "tracking_url",
        "status",
        "label_url",
        "label_data",
        "shipping_cost",
        "estimated_delivery_date",
        "actual_delivery_date",
        "notes",
        "is_active",
    ]:
        if field in data and data[field] is not None:
            setattr(shipment, field, data[field])

    # If status changed to delivered, update order too
    if data.get("status") == ShipmentStatus.DELIVERED.value:
        order = await db.get(Order, shipment.order_id)
        if order and order.status != OrderStatus.DELIVERED:
            order.status = OrderStatus.DELIVERED
            order.delivered_at = datetime.now(UTC)
            await emit_event(
                "order_delivered",
                {
                    "order_id": str(order.id),
                    "shipment_id": str(shipment.id),
                },
            )

    # If status changed to picked_up
    if data.get("status") == ShipmentStatus.PICKED_UP.value:
        shipment.picked_up_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(shipment)
    return shipment


async def refresh_tracking(db: AsyncSession, shipment: Shipment) -> dict[str, Any]:
    """Fetch latest tracking from carrier and update events."""
    if not shipment.tracking_number:
        return {
            "success": False,
            "message": "Sin número de tracking",
            "new_events_count": 0,
            "current_status": shipment.status.value,
        }

    config = None
    if shipment.config_id:
        config = await db.get(ShipmentConfig, shipment.config_id)

    try:
        if config:
            connector = _get_connector_from_config(config)
        else:
            connector = get_connector(shipment.carrier.value, {}, True)

        result = await connector.get_tracking(shipment.tracking_number)

        new_events = 0
        for ev_data in result.get("events", []):
            # Check if event already exists
            event_at = None
            if isinstance(ev_data.get("event_at"), str):
                event_at = datetime.fromisoformat(ev_data["event_at"])
            event_at = event_at or datetime.now(UTC)

            existing = await db.execute(
                select(ShipmentTrackingEvent).where(
                    ShipmentTrackingEvent.shipment_id == shipment.id,
                    ShipmentTrackingEvent.event_description
                    == ev_data.get("event_description"),
                    ShipmentTrackingEvent.event_at == event_at,
                )
            )
            if existing.scalar_one_or_none():
                continue

            event = ShipmentTrackingEvent(
                shipment_id=shipment.id,
                event_code=ev_data.get("event_code"),
                event_description=ev_data.get("event_description"),
                location=ev_data.get("location"),
                carrier_status=result.get("status"),
                event_at=event_at,
            )
            db.add(event)
            new_events += 1

        # Update shipment status from carrier
        raw_status = result.get("status")
        if raw_status:
            if isinstance(raw_status, str):
                try:
                    shipment.status = ShipmentStatus(raw_status)
                except ValueError:
                    pass
            else:
                shipment.status = raw_status

        shipment.last_tracking_check_at = datetime.now(UTC)

        if (
            shipment.status == ShipmentStatus.DELIVERED
            and not shipment.actual_delivery_date
        ):
            shipment.actual_delivery_date = datetime.now(UTC)
            order = await db.get(Order, shipment.order_id)
            if order and order.status != OrderStatus.DELIVERED:
                order.status = OrderStatus.DELIVERED
                order.delivered_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(shipment)

        return {
            "success": True,
            "new_events_count": new_events,
            "current_status": shipment.status.value,
            "message": f"Tracking actualizado. {new_events} eventos nuevos.",
        }

    except Exception as e:
        logger.exception("refresh_tracking: error inesperado")
        return {
            "success": False,
            "message": f"Error: {e!s}",
            "new_events_count": 0,
            "current_status": shipment.status.value,
        }


async def notify_customer(
    db: AsyncSession, shipment: Shipment, channel: str | None = None
) -> dict[str, Any]:
    """Send shipping notification to customer via their preferred channel."""
    order = await db.get(Order, shipment.order_id)
    if not order:
        return {"success": False, "message": "Orden no encontrada"}

    # Determine channel
    if not channel:
        # Try to infer from conversation or customer data
        channel = "email" if order.customer_email else "whatsapp"

    # Build message
    tracking_url = shipment.tracking_url or ""
    tracking_text = (
        f"\n📦 Tracking: {shipment.tracking_number}" if shipment.tracking_number else ""
    )
    url_text = f"\n🔗 Seguir envío: {tracking_url}" if tracking_url else ""

    message = (
        f"¡Hola {order.customer_name or ''}! 👋\n\n"
        f"Tu pedido #{order.order_number} ha sido enviado.{tracking_text}{url_text}\n\n"
        f"Carrier: {shipment.carrier.value}\n"
        f"Estado: {shipment.status.value}\n"
    )

    if shipment.estimated_delivery_date:
        message += f"Llegada estimada: {shipment.estimated_delivery_date.strftime('%d/%m/%Y')}\n"

    # Send via available channel
    try:
        if channel == "email" and order.customer_email:
            # TODO: Use email channel if available
            pass
        elif channel in ("whatsapp", "sms", "telegram") and order.customer_phone:
            # Try to find active channel connection
            from app.domains.channels.models import ChannelConnection, ChannelPlatform

            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == shipment.business_id,
                    ChannelConnection.platform == ChannelPlatform.WHATSAPP,
                    ChannelConnection.is_active == True,
                )
            )
            conn = result.scalar_one_or_none()
            if conn:
                await send_outbound_message(
                    db=db,
                    channel_id=conn.id,
                    recipient=order.customer_phone,
                    content=message,
                )

        shipment.customer_notified_at = datetime.now(UTC)
        shipment.notification_channel = channel
        await db.commit()

        return {
            "success": True,
            "channel": channel,
            "message": "Notificación enviada al cliente",
        }
    except Exception as e:
        logger.exception("notify_customer: error inesperado")
        return {
            "success": False,
            "channel": channel,
            "message": f"Error al notificar: {e!s}",
        }


async def cancel_shipment(db: AsyncSession, shipment: Shipment) -> bool:
    """Cancel a shipment. Attempts carrier cancellation if possible."""
    if shipment.config_id:
        config = await db.get(ShipmentConfig, shipment.config_id)
        if config and shipment.tracking_number:
            try:
                connector = _get_connector_from_config(config)
                await connector.cancel_shipment(shipment.tracking_number)
            except Exception:
                logger.exception("cancel_shipment: error inesperado")
                # Continue with local cancellation

    shipment.status = ShipmentStatus.CANCELLED
    shipment.is_active = False
    await db.commit()
    return True


async def get_carriers_info() -> list[dict[str, Any]]:
    return get_carrier_metadata()
