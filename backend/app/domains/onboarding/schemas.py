"""Onboarding Mágico — Schemas"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScrapedProduct(BaseModel):
    name: str
    description: str | None = None
    price: Decimal | None = None
    currency: str = "ARS"
    category: str | None = None


class BusinessDiscovery(BaseModel):
    name: str
    description: str | None = None
    type: str = "services"  # services, goods, digital, mixed
    tone_of_voice: str | None = None
    brand_colors: list[str] = []
    target_audience: str | None = None
    products: list[ScrapedProduct] = []
    suggested_agents: list[dict[str, Any]] = []
    suggested_workflows: list[dict[str, Any]] = []


class OnboardingAnalyzeRequest(BaseModel):
    source: str = Field(..., description="Instagram handle (@cafe) o URL completa")


class OnboardingAnalyzeResponse(BaseModel):
    raw_text: str
    discovery: BusinessDiscovery


class OnboardingCreateRequest(BaseModel):
    discovery: BusinessDiscovery
    source: str


class OnboardingCreateResponse(BaseModel):
    business_id: UUID
    catalog_items_count: int
    agents_count: int
    workflows_count: int
    message: str
