import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="ARS", nullable=False)
    stock = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    extra_data = Column(JSONB, default=dict, nullable=False)
    images = Column(JSONB, default=list, nullable=False)
    tags = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="catalog_items")
