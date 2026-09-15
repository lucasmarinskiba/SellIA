import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, Integer, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class CatalogItemType(str, enum.Enum):
    SERVICE = "service"
    GOOD = "good"
    DIGITAL = "digital"


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(CatalogItemType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Real rubro (ej. "Servicios jurídicos", "Reparación de PC",
    # "Videojuegos"), separado de `type` (solo service/good/digital, muy
    # genérico) y de `tags` (JSONB libre sin estructura) -- antes el form de
    # creación metía esto como único elemento de `tags`, sin campo propio.
    category = Column(String(120), nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="ARS", nullable=False)
    stock = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    # Set only on items auto-imported from a connected platform (see
    # platform_commerce/selling.py's import_catalog). The unique constraint
    # below (business_id, source_platform, external_id) is what makes a
    # re-sync update the existing row instead of creating a duplicate --
    # Postgres allows multiple NULLs through a unique constraint, so
    # manually-created items (both NULL) are unaffected.
    source_platform = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True)
    # MutableDict/MutableList.as_mutable: without them, an in-place edit like
    # `item.extra_data["key"] = ...` never marks the column dirty, so the
    # UPDATE can silently omit it.
    extra_data = Column(MutableDict.as_mutable(JSONB), default=dict, nullable=False)
    images = Column(MutableList.as_mutable(JSONB), default=list, nullable=False)
    tags = Column(MutableList.as_mutable(JSONB), default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="catalog_items")

    __table_args__ = (
        UniqueConstraint("business_id", "source_platform", "external_id", name="uq_catalog_item_external"),
    )
