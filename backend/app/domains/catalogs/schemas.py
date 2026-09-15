from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any
from decimal import Decimal

from app.domains.catalogs.models import CatalogItemType


class CatalogItemBase(BaseModel):
    type: CatalogItemType
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=120)
    price: Decimal = Field(..., ge=0)
    currency: str = "ARS"
    stock: int | None = Field(None, ge=0)
    is_available: bool = True
    tags: list[str] = []


class CatalogItemCreate(CatalogItemBase):
    extra_data: dict[str, Any] | None = None
    images: list[str] = []


class CatalogItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=120)
    price: Decimal | None = Field(None, ge=0)
    currency: str | None = None
    stock: int | None = Field(None, ge=0)
    is_available: bool | None = None
    extra_data: dict[str, Any] | None = None
    images: list[str] | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class CatalogItemResponse(CatalogItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    source_platform: str | None = None
    external_id: str | None = None
    listing_url: str | None = None
    extra_data: dict[str, Any]
    images: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
