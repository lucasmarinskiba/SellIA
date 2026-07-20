"""
Marketplace Service
"""

import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from app.domains.marketplace.models import MarketplaceItem, MarketplacePurchase, MarketplaceCategory


async def list_items(
    db: AsyncSession,
    category: Optional[MarketplaceCategory] = None,
    search: Optional[str] = None,
    featured_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> List[MarketplaceItem]:
    query = select(MarketplaceItem).where(MarketplaceItem.is_active == True, MarketplaceItem.is_approved == True)
    if category:
        query = query.where(MarketplaceItem.category == category)
    if featured_only:
        query = query.where(MarketplaceItem.is_featured == True)
    if search:
        query = query.where(
            and_(
                MarketplaceItem.name.ilike(f"%{search}%"),
                MarketplaceItem.description.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(desc(MarketplaceItem.is_featured), desc(MarketplaceItem.created_at))
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def get_item(db: AsyncSession, item_id: uuid.UUID) -> Optional[MarketplaceItem]:
    result = await db.execute(select(MarketplaceItem).where(MarketplaceItem.id == item_id))
    return result.scalar_one_or_none()


async def create_item(db: AsyncSession, vendor_id: uuid.UUID, data: dict) -> MarketplaceItem:
    item = MarketplaceItem(vendor_id=vendor_id, **data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def record_purchase(db: AsyncSession, buyer_id: uuid.UUID, item_id: uuid.UUID, price_paid: float) -> MarketplacePurchase:
    purchase = MarketplacePurchase(
        buyer_id=buyer_id,
        item_id=item_id,
        price_paid=price_paid,
    )
    db.add(purchase)

    # Update item stats
    item = await get_item(db, item_id)
    if item:
        item.purchase_count += 1
        if item.is_limited and item.stock_remaining:
            item.stock_remaining -= 1

    await db.commit()
    await db.refresh(purchase)
    return purchase


async def get_user_purchases(db: AsyncSession, user_id: uuid.UUID) -> List[MarketplacePurchase]:
    result = await db.execute(
        select(MarketplacePurchase)
        .where(MarketplacePurchase.buyer_id == user_id)
        .order_by(desc(MarketplacePurchase.created_at))
    )
    return result.scalars().all()
