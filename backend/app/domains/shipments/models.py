"""Shipments & Logistics Models

Gestión de envíos, tracking y conectores de carriers.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class CarrierType(str, enum.Enum):
    """Carriers soportados."""
    ANDREANI = "andreani"
    CORREO_ARGENTINO = "correo_argentino"
    OCA = "oca"
    MERCADO_ENVIOS = "mercado_envios"
    DHL = "dhl"
    FEDEX = "fedex"
    UPS = "ups"
    STARKEN = "starken"
    SERVIENTREGA = "servientrega"
    LOCAL = "local"
    OTHER = "other"


class ShipmentStatus(str, enum.Enum):
    """Estados de un envío."""
    PENDING = "pending"              # Creado, sin etiqueta
    LABEL_CREATED = "label_created"  # Etiqueta generada
    PICKED_UP = "picked_up"          # Retirado por carrier
    IN_TRANSIT = "in_transit"        # En tránsito
    OUT_FOR_DELIVERY = "out_for_delivery"  # En reparto
    DELIVERED = "delivered"          # Entregado
    EXCEPTION = "exception"          # Problema (devolución, daño, etc.)
    RETURNED = "returned"            # Devuelto
    CANCELLED = "cancelled"          # Cancelado


class ServiceType(str, enum.Enum):
    """Tipo de servicio de envío."""
    STANDARD = "standard"
    EXPRESS = "express"
    SAME_DAY = "same_day"
    OVERNIGHT = "overnight"
    INTERNATIONAL = "international"
    ECONOMY = "economy"


class ShipmentConfig(Base):
    """Configuración de un carrier para un negocio."""
    __tablename__ = "shipment_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier = Column(Enum(CarrierType), nullable=False)
    label = Column(String(100), nullable=True)  # Nombre personalizado ej: "Mi Andreani"
    credentials = Column(JSONB, default=dict, nullable=False)  # API keys, usuario, contraseña, cuenta
    is_test_mode = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    default_service_type = Column(Enum(ServiceType), nullable=True)
    default_from_address = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Shipment(Base):
    """Un envío asociado a una orden."""
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    config_id = Column(UUID(as_uuid=True), ForeignKey("shipment_configs.id", ondelete="SET NULL"), nullable=True)

    # Carrier info
    carrier = Column(Enum(CarrierType), nullable=False)
    service_type = Column(Enum(ServiceType), default=ServiceType.STANDARD, nullable=False)

    # Status
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING, nullable=False, index=True)

    # Tracking
    tracking_number = Column(String(100), nullable=True, index=True)
    tracking_url = Column(Text, nullable=True)

    # Label
    label_url = Column(Text, nullable=True)
    label_data = Column(Text, nullable=True)  # PDF en base64

    # Addresses
    from_address = Column(JSONB, default=dict, nullable=False)
    # { "name": "...", "company": "...", "street": "...", "city": "...", 
    #   "state": "...", "zip": "...", "country": "AR", "phone": "...", "email": "..." }
    to_address = Column(JSONB, default=dict, nullable=False)

    # Package details
    package = Column(JSONB, default=dict, nullable=False)
    # { "weight_kg": 1.5, "length_cm": 20, "width_cm": 15, "height_cm": 10,
    #   "items": [{"name": "...", "qty": 1, "sku": "..." }], "description": "..." }

    # Costs
    shipping_cost = Column(Numeric(14, 2), nullable=True)
    insurance_amount = Column(Numeric(14, 2), nullable=True)
    declared_value = Column(Numeric(14, 2), nullable=True)

    # Dates
    estimated_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)

    # Notifications
    customer_notified_at = Column(DateTime(timezone=True), nullable=True)
    notification_channel = Column(String(50), nullable=True)  # whatsapp, email, sms

    # Carrier raw response for debugging
    carrier_response = Column(JSONB, default=dict, nullable=False)
    last_tracking_check_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ShipmentTrackingEvent(Base):
    """Evento de tracking recibido del carrier."""
    __tablename__ = "shipment_tracking_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)

    event_code = Column(String(50), nullable=True)
    event_description = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    carrier_status = Column(String(100), nullable=True)

    event_at = Column(DateTime(timezone=True), nullable=False)  # Fecha que reporta el carrier
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
