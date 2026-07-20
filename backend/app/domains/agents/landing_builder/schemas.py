"""Landing Page Builder Schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LandingVariant(BaseModel):
    variant_name: str
    headline: str
    subheadline: str
    cta_text: str
    color_scheme: Dict[str, str] = {}  # {primary: "#...", secondary: "#..."}
    conversion_rate: Optional[float] = None


class LandingPageJobBase(BaseModel):
    product_id: Optional[UUID] = None
    style: str = "modern"


class LandingPageJobCreate(LandingPageJobBase):
    pass


class LandingPageJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    status: str
    product_id: Optional[UUID] = None
    template_used: Optional[str] = None
    generated_code_url: Optional[str] = None
    preview_url: Optional[str] = None
    variants: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime


class LandingPageCodeOut(BaseModel):
    job_id: UUID
    files: Dict[str, str] = {}
    variants: List[Dict[str, Any]] = []


class LandingPageZipOut(BaseModel):
    job_id: UUID
    download_url: str
