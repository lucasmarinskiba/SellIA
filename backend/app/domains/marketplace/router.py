"""
Marketplace Router
"""

from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.marketplace import service as marketplace_service
from app.domains.marketplace.models import MarketplaceCategory

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/items")
async def list_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: Optional[str] = None,
    search: Optional[str] = None,
    featured: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    cat = MarketplaceCategory(category) if category else None
    items = await marketplace_service.list_items(db, category=cat, search=search, featured_only=featured, limit=limit, offset=offset)
    return [
        {
            "id": i.id,
            "name": i.name,
            "slug": i.slug,
            "short_description": i.short_description,
            "category": i.category.value,
            "price_usd": float(i.price_usd),
            "compare_price_usd": float(i.compare_price_usd) if i.compare_price_usd else None,
            "thumbnail_url": i.thumbnail_url,
            "rating_avg": float(i.rating_avg),
            "rating_count": i.rating_count,
            "purchase_count": i.purchase_count,
            "is_limited": i.is_limited,
            "stock_remaining": i.stock_remaining,
            "offer_ends_at": i.offer_ends_at,
            "is_featured": i.is_featured,
        }
        for i in items
    ]


@router.get("/items/{item_id}")
async def get_item(item_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    item = await marketplace_service.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "category": item.category.value,
        "price_usd": float(item.price_usd),
        "compare_price_usd": float(item.compare_price_usd) if item.compare_price_usd else None,
        "thumbnail_url": item.thumbnail_url,
        "preview_urls": item.preview_urls,
        "demo_url": item.demo_url,
        "metadata": item.extra_data,
        "rating_avg": float(item.rating_avg),
        "rating_count": item.rating_count,
        "purchase_count": item.purchase_count,
        "is_limited": item.is_limited,
        "stock_remaining": item.stock_remaining,
        "offer_ends_at": item.offer_ends_at,
    }


@router.post("/items/{item_id}/purchase")
async def purchase_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    item = await marketplace_service.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.is_limited and item.stock_remaining is not None and item.stock_remaining <= 0:
        raise HTTPException(status_code=400, detail="Item out of stock")

    purchase = await marketplace_service.record_purchase(db, current_user.id, item_id, float(item.price_usd))
    return {"purchase_id": purchase.id, "status": purchase.status, "delivered_at": purchase.delivered_at}


@router.get("/my-purchases")
async def my_purchases(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    purchases = await marketplace_service.get_user_purchases(db, current_user.id)
    return [
        {
            "id": p.id,
            "item_name": p.item.name if p.item else None,
            "price_paid": float(p.price_paid),
            "status": p.status,
            "created_at": p.created_at,
        }
        for p in purchases
    ]
