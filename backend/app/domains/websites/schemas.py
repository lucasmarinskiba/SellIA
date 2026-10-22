from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.websites.models import WebsiteStatus, WebsiteTemplate


class DomainBase(BaseModel):
    subdomain: str = Field(..., min_length=3, max_length=63)
    custom_domain: str | None = None


class DomainCreate(DomainBase):
    pass


class DomainUpdate(BaseModel):
    custom_domain: str | None = None
    is_verified: bool | None = None


class DomainResponse(DomainBase):
    id: UUID
    website_id: UUID
    is_primary: bool
    is_verified: bool
    dns_records: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebsiteBase(BaseModel):
    template: WebsiteTemplate = WebsiteTemplate.MODERN
    title: str | None = None
    description: str | None = None
    hero_image_url: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None


class WebsiteCreate(WebsiteBase):
    subdomain: str = Field(..., min_length=3, max_length=63)


class WebsiteUpdate(BaseModel):
    template: WebsiteTemplate | None = None
    title: str | None = None
    description: str | None = None
    hero_image_url: str | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    og_image_url: str | None = None
    config: dict[str, Any] | None = None
    pages: dict[str, Any] | None = None
    status: WebsiteStatus | None = None


class WebsiteResponse(WebsiteBase):
    id: UUID
    business_id: UUID
    status: WebsiteStatus
    meta_title: str | None
    meta_description: str | None
    meta_keywords: str | None
    og_image_url: str | None
    config: dict[str, Any]
    pages: dict[str, Any]
    domain: DomainResponse | None = None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    class Config:
        from_attributes = True


class OnboardingCompleteRequest(BaseModel):
    business_name: str
    business_description: str | None = None
    website_template: WebsiteTemplate = WebsiteTemplate.MODERN
    subdomain: str = Field(..., min_length=3, max_length=63)
