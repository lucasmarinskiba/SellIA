import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class BusinessType(str, enum.Enum):
    SERVICES = "services"
    GOODS = "goods"
    DIGITAL = "digital"
    MIXED = "mixed"


class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(BusinessType), nullable=False, default=BusinessType.SERVICES)
    description = Column(Text, nullable=True)
    config = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="businesses")
    catalog_items = relationship("CatalogItem", back_populates="business", cascade="all, delete-orphan")
    channels = relationship("ChannelConnection", back_populates="business", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="business", cascade="all, delete-orphan")


# Config por defecto según tipo de negocio
DEFAULT_SERVICE_CONFIG = {
    "modalities": ["home_office", "on_site", "hybrid"],
    "coverage_zones": [],
    "availability": {
        "monday": {"start": "09:00", "end": "18:00"},
        "tuesday": {"start": "09:00", "end": "18:00"},
        "wednesday": {"start": "09:00", "end": "18:00"},
        "thursday": {"start": "09:00", "end": "18:00"},
        "friday": {"start": "09:00", "end": "18:00"},
        "saturday": None,
        "sunday": None,
    },
    "appointment_duration_minutes": 60,
    "buffer_minutes_between": 15,
}

DEFAULT_GOODS_CONFIG = {
    "delivery_methods": ["shipping", "pickup", "meetup"],
    "pickup_locations": [],
    "shipping_providers": ["andreani", "dhl", "mercado_envios", "oca", "correo_argentino"],
    "shipping_zones": [],
    "free_shipping_threshold": None,
}

DEFAULT_DIGITAL_CONFIG = {
    "delivery_method": "direct_download",
    "download_expiry_hours": 72,
    "max_downloads": 3,
}

DEFAULT_CONFIGS = {
    BusinessType.SERVICES: DEFAULT_SERVICE_CONFIG,
    BusinessType.GOODS: DEFAULT_GOODS_CONFIG,
    BusinessType.DIGITAL: DEFAULT_DIGITAL_CONFIG,
    BusinessType.MIXED: {
        **DEFAULT_SERVICE_CONFIG,
        **DEFAULT_GOODS_CONFIG,
        **DEFAULT_DIGITAL_CONFIG,
    },
}
