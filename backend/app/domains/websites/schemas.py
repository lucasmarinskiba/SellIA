from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.domains.websites.models import WebsiteTemplate, WebsiteStatus


class DomainBase(BaseModel):
    subdomain: str = Field(..., min_length=3, max_length=63)
    custom_domain: Optional[str] = None


class DomainCreate(DomainBase):
    pass


class DomainUpdate(BaseModel):
    custom_domain: Optional[str] = None
    is_verified: Optional[bool] = None


class DomainResponse(DomainBase):
    id: UUID
    website_id: UUID
    is_primary: bool
    is_verified: bool
    dns_records: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebsiteBase(BaseModel):
    template: WebsiteTemplate = WebsiteTemplate.MODERN
    title: Optional[str] = None
    description: Optional[str] = None
    hero_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None


class WebsiteCreate(WebsiteBase):
    subdomain: str = Field(..., min_length=3, max_length=63)


class WebsiteUpdate(BaseModel):
    template: Optional[WebsiteTemplate] = None
    title: Optional[str] = None
    description: Optional[str] = None
    hero_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    og_image_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    pages: Optional[Dict[str, Any]] = None
    status: Optional[WebsiteStatus] = None


class WebsiteResponse(WebsiteBase):
    id: UUID
    business_id: UUID
    status: WebsiteStatus
    meta_title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    og_image_url: Optional[str]
    config: Dict[str, Any]
    pages: Dict[str, Any]
    domain: Optional[DomainResponse] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class OnboardingCompleteRequest(BaseModel):
    business_name: str
    business_description: Optional[str] = None
    website_template: WebsiteTemplate = WebsiteTemplate.MODERN
    subdomain: str = Field(..., min_length=3, max_length=63)
