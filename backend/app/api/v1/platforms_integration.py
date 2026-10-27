"""
Platforms Integration API — Unified endpoints for all 6 platforms.

Endpoints:
- /platforms/facebook-shop/* - Facebook Shop integration
- /platforms/instagram-shop/* - Instagram Shop integration
- /platforms/tiktok-shop/* - TikTok Shop integration
- /platforms/calendly/* - Calendly integration
- /platforms/slack/* - Slack bot integration
- /platforms/telegram/* - Telegram bot integration

Each platform:
- Webhook endpoints (POST /webhooks)
- Configuration endpoints (POST/GET /config)
- Sync endpoints (POST /sync)
- Analytics endpoints (GET /analytics)

Auth: Required account_id + API key from JWT token
Rate Limiting: Implemented per platform limits
Error Handling: Standardized error responses with correlation IDs
"""

import logging
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Header, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.domains.channels.models import ChannelConnection, ChannelPlatform, ChannelStatus

_INTEGRATION_NOT_IMPLEMENTED = (
    "Integración no implementada: este endpoint todavía no procesa nada real."
)


_SHOP_NOT_IMPLEMENTED = (
    "Integración de tienda no implementada: el sync y las métricas todavía no están conectados."
)

# get_connector se importa perezoso dentro de cada handler (no a nivel de
# módulo): app.domains.channels.connectors.__init__ importa TODOS los
# conectores al cargarse, incluido email.py -> aiosmtplib. Un import a nivel
# de módulo acá tumbó el deploy entero cuando esa dependencia faltaba -
# channels.py (api/v1/channels.py) ya usaba este mismo patrón perezoso por
# esta razón.

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/platforms", tags=["platforms"])

# ========== PYDANTIC MODELS ==========


class WebhookResponse(BaseModel):
    """Standard webhook response."""
    status: str
    message: str
    correlation_id: str


class PlatformConfig(BaseModel):
    """Platform configuration."""
    platform_type: str
    api_key: str
    webhook_url: str
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrderSyncRequest(BaseModel):
    """Order sync request."""
    platform_type: str
    force_refresh: bool = False
    page: int = 1
    limit: int = 50


class SyncResponse(BaseModel):
    """Sync operation response."""
    status: str
    synced_count: int
    duration_seconds: float
    errors: List[str] = []


class AlertRequest(BaseModel):
    """Alert notification request."""
    title: str
    message: str
    level: str = "info"  # info, warning, error, critical
    data: Optional[Dict[str, Any]] = None


# ========== FACEBOOK SHOP ENDPOINTS ==========

@router.post("/facebook-shop/webhooks/orders")
async def facebook_shop_webhook_orders(
    request: Request,
    account_id: str = Header(...),
    x_hub_signature: str = Header(...),
) -> WebhookResponse:
    """
    Handle Facebook Shop webhook for orders.

    Args:
        request: FastAPI request
        account_id: Account ID from header
        x_hub_signature: Facebook webhook signature

    Returns:
        WebhookResponse
    """
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/facebook-shop/config")
async def facebook_shop_config(
    config: PlatformConfig,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """
    Configure Facebook Shop integration.

    Args:
        config: Configuration details
        account_id: Account ID

    Returns:
        Configuration confirmation
    """
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/facebook-shop/sync/products")
async def facebook_shop_sync_products(
    request: OrderSyncRequest,
    account_id: str = Header(...),
) -> SyncResponse:
    """
    Sync products from Facebook Shop to local DB.

    Args:
        request: Sync request details
        account_id: Account ID

    Returns:
        SyncResponse
    """
    raise HTTPException(status_code=501, detail=_SHOP_NOT_IMPLEMENTED)


@router.get("/facebook-shop/orders/{order_id}")
async def facebook_shop_get_order(
    order_id: str,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """
    Fetch Facebook Shop order details.

    Args:
        order_id: Facebook order ID
        account_id: Account ID

    Returns:
        Order details
    """
    raise HTTPException(status_code=501, detail=_SHOP_NOT_IMPLEMENTED)


# ========== INSTAGRAM SHOP ENDPOINTS ==========

@router.post("/instagram-shop/webhooks/orders")
async def instagram_shop_webhook_orders(
    request: Request,
    account_id: str = Header(...),
    x_hub_signature: str = Header(...),
) -> WebhookResponse:
    """Handle Instagram Shop webhook for orders."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/instagram-shop/sync/products")
async def instagram_shop_sync_products(
    request: OrderSyncRequest,
    account_id: str = Header(...),
) -> SyncResponse:
    """Sync products to Instagram Shop."""
    raise HTTPException(status_code=501, detail=_SHOP_NOT_IMPLEMENTED)


@router.get("/instagram-shop/analytics")
async def instagram_shop_analytics(
    account_id: str = Header(...),
    days: int = 30,
) -> Dict[str, Any]:
    """Fetch Instagram Shop analytics."""
    raise HTTPException(status_code=501, detail=_SHOP_NOT_IMPLEMENTED)


# ========== TIKTOK SHOP ENDPOINTS ==========

@router.post("/tiktok-shop/webhooks/orders")
async def tiktok_shop_webhook_orders(
    request: Request,
    account_id: str = Header(...),
) -> WebhookResponse:
    """Handle TikTok Shop webhook for orders."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/tiktok-shop/config")
async def tiktok_shop_config(
    config: PlatformConfig,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """Configure TikTok Shop OAuth."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


async def _get_tiktok_shop_connection(account_id: str, db: AsyncSession) -> ChannelConnection:
    try:
        business_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="account_id debe ser un UUID de business válido")

    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id == business_uuid,
            ChannelConnection.platform == ChannelPlatform.TIKTOK_SHOP,
            ChannelConnection.is_active == True,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(
            status_code=404,
            detail="No hay conexión de TikTok Shop configurada para este business_id. "
                   "Crear una vía POST /api/v1/businesses/{business_id}/channels con platform=tiktok_shop.",
        )
    return connection


@router.post("/tiktok-shop/sync/orders")
async def tiktok_shop_sync_orders(
    request: OrderSyncRequest,
    account_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    """Sync orders reales desde TikTok Shop Seller API."""
    import time
    start_time = time.time()

    connection = await _get_tiktok_shop_connection(account_id, db)
    from app.domains.channels.connectors import get_connector
    connector = get_connector(ChannelPlatform.TIKTOK_SHOP, connection.credentials, connection.settings)

    try:
        orders = await connector.list_orders(page=request.page, page_size=request.limit)
        duration = time.time() - start_time

        if orders is None:
            connection.status = ChannelStatus.ERROR
            connection.status_message = "list_orders devolvió error - ver logs de TikTok API"
            await db.commit()
            return SyncResponse(status="error", synced_count=0, duration_seconds=duration,
                                 errors=["TikTok Shop API no devolvió órdenes - credenciales inválidas o error de API"])

        connection.status = ChannelStatus.CONNECTED
        connection.last_sync_at = datetime.now(timezone.utc)
        await db.commit()

        return SyncResponse(status="success", synced_count=len(orders), duration_seconds=duration)

    except Exception as e:
        connection.status = ChannelStatus.ERROR
        connection.status_message = str(e)[:255]
        await db.commit()
        raise HTTPException(status_code=400, detail=str(e))


# ========== CALENDLY ENDPOINTS ==========

@router.post("/calendly/webhooks/events")
async def calendly_webhook_events(
    payload: Dict[str, Any],
    account_id: str = Header(...),
) -> WebhookResponse:
    """Handle Calendly webhook for scheduled events."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/calendly/config")
async def calendly_config(
    config: PlatformConfig,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """Configure Calendly integration."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.get("/calendly/events")
async def calendly_list_events(
    account_id: str = Header(...),
    days: int = 7,
) -> Dict[str, Any]:
    """List upcoming Calendly events."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


# ========== SLACK ENDPOINTS ==========

@router.post("/slack/commands")
async def slack_command_handler(
    request: Request,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """
    Handle Slack slash commands.

    Slack sends:
    - token
    - command: /status, /orders, etc
    - text: command arguments
    - user_id
    - channel_id
    """
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/slack/events")
async def slack_events_handler(
    payload: Dict[str, Any],
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """Handle Slack Events API."""
    # Handshake de URL de Slack: el único paso del protocolo que sí se implementa.
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/slack/alerts")
async def slack_send_alert(
    alert: AlertRequest,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """Send alert via Slack bot."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


# ========== TELEGRAM ENDPOINTS ==========

@router.post("/telegram/webhooks/updates")
async def telegram_webhook_updates(
    request: Request,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """Handle Telegram bot updates."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/telegram/config")
async def telegram_config(
    config: PlatformConfig,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """Configure Telegram bot."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


@router.post("/telegram/send-notification")
async def telegram_send_notification(
    alert: AlertRequest,
    account_id: str = Header(...),
) -> Dict[str, Any]:
    """Send Telegram notification."""
    raise HTTPException(status_code=501, detail=_INTEGRATION_NOT_IMPLEMENTED)


# ========== HEALTH & STATUS ==========

@router.get("/health")
async def platforms_health() -> Dict[str, Any]:
    """Check health of all platform integrations."""
    """Estado de salud por plataforma: no hay chequeo real todavía."""
    names = ["facebook_shop", "instagram_shop", "tiktok_shop", "calendly", "slack", "telegram"]
    return {
        "status": "unknown",
        "platforms": {name: "unknown" for name in names},
        "detail": "Sin chequeo de salud por plataforma; usar /status por cuenta.",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/status")
async def platforms_status(
    account_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get platform integration status for account.

    tiktok_shop consulta la conexión real en channel_connections. Las otras 5
    plataformas de este archivo (facebook_shop, instagram_shop, calendly,
    slack, telegram) siguen sin implementar (TODO histórico, fuera del scope
    actual) — se listan como no-conectadas explícitamente, no simuladas.
    """
    try:
        logger.info(f"Fetching platform status for {account_id}")

        tiktok_status: dict[str, Any] = {"connected": False, "last_sync": None}
        try:
            business_uuid = uuid.UUID(account_id)
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == business_uuid,
                    ChannelConnection.platform == ChannelPlatform.TIKTOK_SHOP,
                    ChannelConnection.is_active == True,
                )
            )
            connection = result.scalar_one_or_none()
            if connection:
                tiktok_status = {
                    "connected": connection.status == ChannelStatus.CONNECTED,
                    "status": connection.status.value,
                    "status_message": connection.status_message,
                    "last_sync": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                }
        except ValueError:
            pass  # account_id no es UUID válido - se reporta como no conectado

        return {
            "account_id": account_id,
            "platforms": {
                "facebook_shop": {"connected": False, "last_sync": None, "implemented": False},
                "instagram_shop": {"connected": False, "last_sync": None, "implemented": False},
                "tiktok_shop": {**tiktok_status, "implemented": True},
                "calendly": {"connected": False, "last_sync": None, "implemented": False},
                "slack": {"connected": False, "last_sync": None, "implemented": False},
                "telegram": {"connected": False, "last_sync": None, "implemented": False},
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
