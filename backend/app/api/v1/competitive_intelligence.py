"""Competitive intelligence API — competitor tracking + market analysis."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.competitive.competitive_service import CompetitiveIntelligenceService

router = APIRouter(prefix="/api/v1", tags=["competitive-intelligence"])


class AddCompetitorRequest(BaseModel):
    name: str
    competitor_type: str
    website: str | None = None
    primary_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    threat_level: str | None = "medium"


class LogPricingRequest(BaseModel):
    competitor_id: UUID
    product_name: str
    base_price: Decimal
    discounted_price: Decimal | None = None
    in_stock: bool = True
    source: str = "website"
    date: str | None = None


class AddOfferingRequest(BaseModel):
    competitor_id: UUID
    offering_type: str
    offering_name: str
    category: str | None = None
    description: str | None = None
    features: list[str] | None = None
    our_has_equivalent: bool = False
    competitive_advantage: str | None = None


@router.post("/businesses/{business_id}/competitors")
def add_competitor(
    business_id: UUID,
    request: AddCompetitorRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Add competitor to tracking."""
    return CompetitiveIntelligenceService.add_competitor(
        business_id=business_id,
        name=request.name,
        competitor_type=request.competitor_type,
        website=request.website,
        primary_address=request.primary_address,
        latitude=request.latitude,
        longitude=request.longitude,
        threat_level=request.threat_level,
        db=db,
    )


@router.post("/competitors/pricing")
def log_competitor_pricing(
    business_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    request: LogPricingRequest = None,
):
    """Log competitor product pricing."""
    return CompetitiveIntelligenceService.log_competitor_pricing(
        competitor_id=request.competitor_id,
        business_id=business_id,
        product_name=request.product_name,
        base_price=request.base_price,
        date=request.date,
        discounted_price=request.discounted_price,
        in_stock=request.in_stock,
        source=request.source,
        db=db,
    )


@router.post("/competitors/offering")
def add_competitor_offering(
    business_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    request: AddOfferingRequest = None,
):
    """Log competitor product/service offering."""
    return CompetitiveIntelligenceService.add_competitor_offering(
        competitor_id=request.competitor_id,
        business_id=business_id,
        offering_type=request.offering_type,
        offering_name=request.offering_name,
        category=request.category,
        description=request.description,
        features=request.features,
        our_has_equivalent=request.our_has_equivalent,
        competitive_advantage=request.competitive_advantage,
        db=db,
    )


@router.get("/businesses/{business_id}/competitive-position")
def get_competitive_position(
    business_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
):
    """Get competitive position summary."""
    return CompetitiveIntelligenceService.get_competitive_position(
        business_id=business_id, date=date, db=db
    )


@router.get("/businesses/{business_id}/price-benchmark")
def get_price_benchmark(
    business_id: UUID,
    product_name: Annotated[str, Query()],
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    """Get price benchmarking for product."""
    return CompetitiveIntelligenceService.get_price_benchmarking(
        business_id=business_id, product_name=product_name, days=days, db=db
    )


@router.get("/businesses/{business_id}/offering-gaps")
def get_offering_gaps(
    business_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """Identify feature/offering gaps vs competitors."""
    return CompetitiveIntelligenceService.get_offering_gaps(
        business_id=business_id, db=db
    )


@router.get("/businesses/{business_id}/competitors")
def get_competitors(
    business_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    threat_level: Annotated[
        str | None, Query(description="low, medium, high, critical")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Get list of tracked competitors."""
    return CompetitiveIntelligenceService.get_competitor_list(
        business_id=business_id, threat_level=threat_level, limit=limit, db=db
    )
