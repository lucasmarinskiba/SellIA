"""Listings management endpoints."""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("")
async def create_listing(
    user_id: str = Query(...),
    name: str = Query(...),
    description: str = Query(...),
    price: float = Query(...),
    stock: int = Query(...),
    platform: str = Query(...),
    sku: str = Query(None),
    category: str = Query(None),
):
    """Create a new listing."""
    return {
        "user_id": user_id,
        "listing_id": "LST-NEW-001",
        "name": name,
        "price": price,
        "stock": stock,
        "platform": platform,
        "message": "Listing created successfully",
        "status": "active"
    }


@router.get("")
async def get_listings(
    user_id: str = Query(...),
    platform: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    stock_status: str = Query(None),
    search: str = Query(None),
    skip: int = 0,
    limit: int = 10,
):
    """Get listings with advanced filtering."""
    listings = [
        {"id": "LST-001", "product": "iPhone 15 Pro", "platform": "Mercado Libre", "price": 999, "stock": 12, "views": 1234, "rating": 4.8, "status": "active"},
        {"id": "LST-002", "product": "AirPods Pro", "platform": "Amazon", "price": 249, "stock": 45, "views": 856, "rating": 4.6, "status": "active"},
        {"id": "LST-003", "product": "MacBook Air M3", "platform": "Hotmart", "price": 1299, "stock": 5, "views": 432, "rating": 4.9, "status": "active"},
        {"id": "LST-004", "product": "iPad Pro 12.9\"", "platform": "Mercado Libre", "price": 799, "stock": 0, "views": 567, "rating": 4.7, "status": "out_of_stock"},
    ]

    # Apply filters
    filtered = listings
    if platform:
        filtered = [l for l in filtered if l["platform"].lower() == platform.lower()]
    if min_price is not None:
        filtered = [l for l in filtered if l["price"] >= min_price]
    if max_price is not None:
        filtered = [l for l in filtered if l["price"] <= max_price]
    if stock_status == "in_stock":
        filtered = [l for l in filtered if l["stock"] > 0]
    elif stock_status == "out_of_stock":
        filtered = [l for l in filtered if l["stock"] == 0]
    if search:
        filtered = [l for l in filtered if search.lower() in l["product"].lower()]

    return {
        "user_id": user_id,
        "total": len(filtered),
        "filters_applied": {
            "platform": platform,
            "min_price": min_price,
            "max_price": max_price,
            "stock_status": stock_status,
            "search": search,
        },
        "listings": filtered[skip : skip + limit]
    }


@router.put("/{listing_id}")
async def update_listing(listing_id: str, user_id: str = Query(...), price: float = Query(None), stock: int = Query(None)):
    """Update listing details."""
    return {
        "listing_id": listing_id,
        "message": "Listing updated successfully",
        "updated_fields": {"price": price, "stock": stock}
    }


@router.delete("/{listing_id}")
async def delete_listing(listing_id: str, user_id: str = Query(...)):
    """Delete a listing."""
    return {
        "listing_id": listing_id,
        "message": "Listing deleted successfully",
        "status": "deleted"
    }
