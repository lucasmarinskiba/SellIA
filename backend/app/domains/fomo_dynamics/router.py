"""Phase X6: FOMO Dynamics API Endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.domains.fomo_dynamics.service import FOMODynamicsService
from app.domains.fomo_dynamics.models import FOMOStrategy


router = APIRouter(prefix="/api/v1/fomo-dynamics", tags=["fomo-dynamics"])


@router.post("/offers/create")
async def create_fomo_offer(
    business_id: str,
    product_id: str,
    strategy: FOMOStrategy,
    base_price: float,
    total_stock: Optional[int] = None,
    ends_at: Optional[datetime] = None,
    headline: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create psychology-driven FOMO offer with auto-optimization."""
    offer = await FOMODynamicsService.create_dynamic_offer(
        db, business_id, product_id, strategy, base_price, total_stock, ends_at, headline
    )
    return {
        "offer_id": offer.id,
        "strategy": offer.strategy,
        "price": offer.current_price,
        "headline": offer.headline,
        "urgency_badge": offer.urgency_badge,
    }


@router.post("/prices/update-dynamic")
async def update_dynamic_price(
    offer_id: str,
    purchases_count: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update price based on demand (scarcity psychology)."""
    new_price = await FOMODynamicsService.update_price_based_on_demand(db, offer_id, purchases_count)
    return {
        "offer_id": offer_id,
        "new_price": new_price,
        "message": "Price updated based on demand",
    }


@router.get("/badges/urgency/{offer_id}")
async def get_urgency_badge(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get psychological urgency badge for product."""
    badge = await FOMODynamicsService.get_urgency_badge(db, offer_id)
    if not badge:
        return {"badge": None, "message": "No urgency at this time"}

    return {
        "badge_type": badge.badge_type,
        "badge_text": badge.badge_text,
        "urgency_level": badge.urgency_level,
        "animate": badge.animate,
        "animation_type": badge.animation_type,
        "color": badge.badge_color,
    }


@router.post("/social-proof/update")
async def update_social_proof(
    offer_id: str,
    new_purchase: bool = False,
    viewer_increment: int = 1,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update real-time social proof signals."""
    proof = await FOMODynamicsService.update_social_proof(db, offer_id, new_purchase, viewer_increment)
    return {
        "today_sales": proof.today_sales,
        "recent_views": proof.recent_views,
        "social_message": f"{proof.today_sales} people bought this today",
        "is_bestseller": proof.is_bestseller,
        "sales_velocity": proof.sales_velocity,
    }


@router.get("/personalized/{user_id}/{product_id}")
async def get_personalized_fomo(
    business_id: UUID,
    user_id: str,
    product_id: UUID,
    browse_count: int = 1,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get personalized FOMO message based on user behavior."""
    fomo = await FOMODynamicsService.get_personalized_fomo(
        db, business_id, user_id, product_id, browse_count
    )
    return {
        "trigger_message": fomo.trigger_message,
        "trigger_type": fomo.trigger_type,
        "persuasion_angle": fomo.persuasion_angle,
        "conversion_probability": round(fomo.conversion_probability, 2),
        "browse_count": fomo.browse_count,
    }


@router.get("/conversion-probability")
async def get_conversion_probability(
    user_id: str,
    product_id: str,
    offer_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Calculate purchase probability based on FOMO signals."""
    probability = await FOMODynamicsService.calculate_conversion_probability(
        db, user_id, product_id, offer_id
    )
    return {
        "user_id": user_id,
        "product_id": product_id,
        "conversion_probability": round(probability, 2),
        "estimated_likelihood": "High" if probability > 0.65 else "Medium" if probability > 0.4 else "Low",
    }
