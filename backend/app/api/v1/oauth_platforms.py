"""OAuth endpoints for platform integrations."""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.core.oauth_connectors import (
    MercadoLibreOAuth,
    AmazonSPAPI,
    HotmartOAuth,
    store_platform_credential,
    get_platform_credential,
)
from backend.app.core.config import get_settings

router = APIRouter(prefix="/oauth", tags=["oauth"])
settings = get_settings()


@router.get("/mercado-libre/auth-url")
async def mercado_libre_auth_url():
    """Get Mercado Libre authorization URL."""
    return {"auth_url": MercadoLibreOAuth.get_auth_url()}


@router.get("/mercado-libre/callback")
async def mercado_libre_callback(
    code: str = Query(...),
    seller_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Mercado Libre OAuth callback."""
    try:
        token_data = await MercadoLibreOAuth.exchange_code(code)
        seller_info = await MercadoLibreOAuth.get_seller_info(token_data["access_token"])

        cred = await store_platform_credential(
            db=db,
            seller_id=seller_id,
            platform="mercado_libre",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            seller_username=seller_info.get("nickname"),
            token_expiry_minutes=token_data.get("expires_in", 3600) // 60,
        )
        return {
            "status": "connected",
            "platform": "mercado_libre",
            "seller_username": cred.seller_username,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


@router.get("/amazon/auth-url")
async def amazon_auth_url():
    """Get Amazon SP-API authorization URL."""
    # Placeholder — actual Amazon LWA flow more complex
    return {
        "auth_url": f"https://sellercentral.amazon.com/apps/authorize/"
        f"?application_id={settings.AMAZON_CLIENT_ID}"
    }


@router.get("/amazon/callback")
async def amazon_callback(
    code: str = Query(...),
    seller_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Amazon SP-API callback."""
    try:
        token_data = await AmazonSPAPI.exchange_code(code)
        cred = await store_platform_credential(
            db=db,
            seller_id=seller_id,
            platform="amazon",
            access_token=token_data.get("access_token", ""),
            refresh_token=token_data.get("refresh_token"),
            token_expiry_minutes=token_data.get("expires_in", 3600) // 60,
        )
        return {"status": "connected", "platform": "amazon"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


@router.get("/hotmart/auth-url")
async def hotmart_auth_url():
    """Get Hotmart authorization URL."""
    return {"auth_url": HotmartOAuth.get_auth_url()}


@router.get("/hotmart/callback")
async def hotmart_callback(
    code: str = Query(...),
    seller_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Hotmart OAuth callback."""
    try:
        token_data = await HotmartOAuth.exchange_code(code)
        seller_info = await HotmartOAuth.get_seller_info(token_data["access_token"])

        cred = await store_platform_credential(
            db=db,
            seller_id=seller_id,
            platform="hotmart",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            seller_username=seller_info.get("name"),
            token_expiry_minutes=token_data.get("expires_in", 3600) // 60,
        )
        return {
            "status": "connected",
            "platform": "hotmart",
            "seller_username": cred.seller_username,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


@router.get("/platforms/status/{seller_id}")
async def get_platform_status(seller_id: str, db: AsyncSession = Depends(get_db)):
    """Get connection status for all platforms."""
    platforms = ["mercado_libre", "amazon", "hotmart"]
    status = {}

    for platform in platforms:
        cred = await get_platform_credential(db, seller_id, platform)
        status[platform] = {
            "connected": cred is not None,
            "seller_username": cred.seller_username if cred else None,
            "last_sync": cred.last_sync_at.isoformat() if cred and cred.last_sync_at else None,
        }

    return status


@router.post("/platforms/disconnect/{seller_id}/{platform}")
async def disconnect_platform(
    seller_id: str,
    platform: str,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect platform."""
    cred = await get_platform_credential(db, seller_id, platform)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    cred.is_active = False
    await db.commit()
    return {"status": "disconnected", "platform": platform}
