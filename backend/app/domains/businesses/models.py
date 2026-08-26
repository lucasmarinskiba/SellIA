import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum

if TYPE_CHECKING:
    from app.domains.users.models import User
    from app.domains.catalogs.models import CatalogItem
    from app.domains.channels.models import ChannelConnection
    from app.domains.websites.models import Website
    from app.domains.crm.models import Conversation


class LocalizationModel(str, enum.Enum):
    """Business model classification for online/offline mix."""
    ONLINE_ONLY = "online_only"
    HYBRID_LIGHT = "hybrid_light"
    HYBRID_HEAVY = "hybrid_heavy"
    OFFLINE_FIRST = "offline_first"


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
    description = Column(Text, nullable=True)
    config = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    locations = relationship("Location", back_populates="business", cascade="all, delete-orphan")

    # user/catalog_items/website/channels/conversations habilitados: las 5
    # clases target (User, CatalogItem, Website, ChannelConnection,
    # Conversation) ya están confirmadas en el registry de SQLAlchemy
    # (verificado con Base.registry._class_registry tras importar app.main).
    user = relationship("User", back_populates="businesses")
    catalog_items = relationship("CatalogItem", back_populates="business", cascade="all, delete-orphan")
    website = relationship("Website", back_populates="business", uselist=False, cascade="all, delete-orphan")
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
