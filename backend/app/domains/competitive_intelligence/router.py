"""Phase 4: Competitive Intelligence Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.competitive_intelligence.service import CompetitiveIntelligenceService

router = APIRouter(prefix="/api/v1/competitive-intelligence", tags=["competitive-intelligence"])


@router.post("/track-competitor")
async def track_competitor(
    business_id: UUID,
    competitor_name: str,
    industry: str,
    market_segment: str | None = None,
    price_point: float | None = None,
    strength_areas: list[str] | None = None,
    weakness_areas: list[str] | None = None,
    feature_set: list[str] | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Register or update competitor profile."""
    result = await CompetitiveIntelligenceService.track_competitor(
        db, business_id, competitor_name, industry, market_segment, price_point, strength_areas, weakness_areas, feature_set
    )
    return result


@router.post("/analyze-price")
async def analyze_price(
    business_id: UUID,
    product_id: UUID,
    current_price: float,
    competitor_prices: list[float] | None = None,
    target_margin: float = 0.4,
    market_position: str = "competitive",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recommend optimal price based on competitive analysis."""
    result = await CompetitiveIntelligenceService.analyze_price_positioning(
        db, business_id, product_id, current_price, competitor_prices, target_margin, market_position
    )
    return result


@router.get("/landscape")
async def get_landscape(
    business_id: UUID,
    market_segment: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Analyze competitive landscape."""
    result = await CompetitiveIntelligenceService.get_competitive_landscape(
        db, business_id, market_segment
    )
    return result


@router.get("/opportunities")
async def find_opportunities(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Identify market opportunities and threats."""
    result = await CompetitiveIntelligenceService.identify_market_opportunities(db, business_id)
    return result


@router.post("/add-feed")
async def add_feed(
    business_id: UUID,
    feed_type: str,
    competitor_name: str,
    event_title: str,
    event_description: str | None = None,
    threat_level: str = "medium",
    source_url: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Log competitive intelligence event."""
    result = await CompetitiveIntelligenceService.add_intelligence_feed(
        db, business_id, feed_type, competitor_name, event_title, event_description, threat_level, source_url
    )
    return result


@router.get("/dashboard")
async def get_dashboard(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get competitive intelligence dashboard."""
    result = await CompetitiveIntelligenceService.get_intelligence_dashboard(db, business_id)
    return result
