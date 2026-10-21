"""Landing Page Builder Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LandingVariant(BaseModel):
    variant_name: str
    headline: str
    subheadline: str
    cta_text: str
    color_scheme: dict[str, str] = {}  # {primary: "#...", secondary: "#..."}
    conversion_rate: float | None = None


class LandingPageJobBase(BaseModel):
    product_id: UUID | None = None
    style: str = "modern"


class LandingPageJobCreate(LandingPageJobBase):
    pass


class LandingPageJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    status: str
    product_id: UUID | None = None
    template_used: str | None = None
    generated_code_url: str | None = None
    preview_url: str | None = None
    variants: list[dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime


class LandingPageCodeOut(BaseModel):
    job_id: UUID
    files: dict[str, str] = {}
    variants: list[dict[str, Any]] = []


class LandingPageZipOut(BaseModel):
    job_id: UUID
    download_url: str
