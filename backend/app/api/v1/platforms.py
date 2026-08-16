"""Platform connection management endpoints."""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("/status")
async def get_platforms_status(user_id: str = Query(...)):
    """Get connection status for all platforms."""
    return {
        "user_id": user_id,
        "platforms": [
            {
                "id": "mercado-libre",
                "name": "Mercado Libre",
                "connected": False,
                "last_sync": None,
                "listings_count": 0,
                "orders_count": 0,
            },
            {
                "id": "amazon",
                "name": "Amazon",
                "connected": False,
                "last_sync": None,
                "listings_count": 0,
                "orders_count": 0,
            },
            {
                "id": "hotmart",
                "name": "Hotmart",
                "connected": False,
                "last_sync": None,
                "listings_count": 0,
                "orders_count": 0,
            },
        ]
    }


@router.get("/auth-url")
async def get_auth_url(platform: str = Query(...), user_id: str = Query(...)):
    """Get OAuth authorization URL for a platform."""
    auth_urls = {
        "mercado-libre": "https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://sellia-brain.vercel.app/api/v1/oauth/mercado-libre/callback",
        "amazon": "https://sellercentral.amazon.com/ap/signin",
        "hotmart": "https://app.hotmart.com/login",
    }
    return {
        "platform": platform,
        "auth_url": auth_urls.get(platform, ""),
        "message": f"Redirect to {platform} OAuth provider"
    }


@router.post("/disconnect")
async def disconnect_platform(platform: str = Query(...), user_id: str = Query(...)):
    """Disconnect a platform."""
    return {
        "platform": platform,
        "message": f"Disconnected from {platform}",
        "connected": False
    }


@router.get("/sync-now")
async def sync_platform(platform: str = Query(...), user_id: str = Query(...)):
    """Force sync for a specific platform."""
    return {
        "platform": platform,
        "status": "syncing",
        "message": "Platform sync initiated",
        "last_sync": "2025-01-15T10:30:00Z",
        "next_sync": "2025-01-15T10:35:00Z"
    }
