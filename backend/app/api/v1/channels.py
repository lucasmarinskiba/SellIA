from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Any
import hmac
from urllib.parse import urlencode

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import get_settings
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.channels.models import ChannelConnection, ChannelPlatform, ChannelStatus
from app.domains.channels.schemas import (
    ChannelConnectionCreate,
    ChannelConnectionUpdate,
    ChannelConnectionResponse,
    WebhookPayload,
)
from app.domains.subscriptions.services import check_subscription_limit, track_usage

router = APIRouter()
settings = get_settings()


async def _get_business_for_user(
    business_id: UUID, user: User, db: AsyncSession
) -> Business:
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == user.id,
            Business.is_active == True,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.post("/{business_id}/channels", response_model=ChannelConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    business_id: UUID,
    channel_in: ChannelConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)

    # Check channel limit
    limit_check = await check_subscription_limit(db, current_user.id, "channels", quantity=1)
    if not limit_check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Límite de canales alcanzado. Usados: {limit_check['used']}/{limit_check['limit']}"
        )

    channel = ChannelConnection(
        business_id=business_id,
        platform=channel_in.platform,
        name=channel_in.name,
        credentials=channel_in.credentials or {},
        settings=channel_in.settings or {},
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    await track_usage(db, current_user.id, "channels", quantity=1, business_id=business_id)
    return channel


@router.get("/{business_id}/channels", response_model=list[ChannelConnectionResponse])
async def list_channels(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id == business_id,
            ChannelConnection.is_active == True,
        )
    )
    return result.scalars().all()


@router.get("/{business_id}/channels/{channel_id}", response_model=ChannelConnectionResponse)
async def get_channel(
    business_id: UUID,
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.id == channel_id,
            ChannelConnection.business_id == business_id,
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    return channel


@router.put("/{business_id}/channels/{channel_id}", response_model=ChannelConnectionResponse)
async def update_channel(
    business_id: UUID,
    channel_id: UUID,
    channel_in: ChannelConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.id == channel_id,
            ChannelConnection.business_id == business_id,
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")

    update_data = channel_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)
    return channel


@router.delete("/{business_id}/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    business_id: UUID,
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.id == channel_id,
            ChannelConnection.business_id == business_id,
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")

    channel.is_active = False
    await db.commit()
    return None


@router.post("/{business_id}/channels/{channel_id}/test")
async def test_channel_connection(
    business_id: UUID,
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test channel credentials by validating them with the platform."""
    await _get_business_for_user(business_id, current_user, db)
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.id == channel_id,
            ChannelConnection.business_id == business_id,
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")

    try:
        from app.domains.channels.connectors import get_connector
        connector = get_connector(channel.platform, channel.credentials, channel.settings)
        is_valid = await connector.validate_credentials()
        if is_valid:
            channel.status = ChannelStatus.CONNECTED
            channel.status_message = None
            await db.commit()
            return {"status": "connected", "valid": True}
        else:
            channel.status = ChannelStatus.ERROR
            channel.status_message = "Credenciales inválidas"
            await db.commit()
            return {"status": "error", "valid": False, "detail": "Credenciales inválidas"}
    except Exception as e:
        channel.status = ChannelStatus.ERROR
        channel.status_message = str(e)[:255]
        await db.commit()
        return {"status": "error", "valid": False, "detail": str(e)}


# ========== OAuth Connection Flows ==========

@router.get("/{business_id}/channels/{platform}/auth-url")
async def get_oauth_url(
    business_id: UUID,
    platform: ChannelPlatform,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate OAuth authorization URL for supported platforms."""
    await _get_business_for_user(business_id, current_user, db)
    
    base_callback = settings.FRONTEND_URL or "http://localhost:3000"
    redirect_uri = f"{base_callback}/api/v1/channels/oauth/callback/{platform.value}"
    
    if platform == ChannelPlatform.MERCADOLIBRE:
        # Find existing channel to get client_id
        result = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.business_id == business_id,
                ChannelConnection.platform == ChannelPlatform.MERCADOLIBRE,
                ChannelConnection.is_active == True,
            )
        )
        channel = result.scalar_one_or_none()
        if not channel or not channel.credentials.get("client_id"):
            raise HTTPException(status_code=400, detail="Configure client_id en las credenciales del canal")
        
        client_id = channel.credentials["client_id"]
        auth_url = "https://auth.mercadolibre.com.ar/authorization"
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": str(channel.id),
        }
        return {"auth_url": f"{auth_url}?{urlencode(params)}"}
    
    elif platform in (ChannelPlatform.FACEBOOK_ADS, ChannelPlatform.INSTAGRAM, ChannelPlatform.MESSENGER, ChannelPlatform.WHATSAPP):
        result = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.business_id == business_id,
                ChannelConnection.platform == platform,
                ChannelConnection.is_active == True,
            )
        )
        channel = result.scalar_one_or_none()
        if not channel or not channel.credentials.get("app_id"):
            raise HTTPException(status_code=400, detail="Configure app_id en las credenciales del canal")
        
        app_id = channel.credentials["app_id"]
        scopes = "pages_messaging,pages_read_engagement,leads_retrieval"
        if platform == ChannelPlatform.WHATSAPP:
            scopes = "whatsapp_business_messaging,whatsapp_business_management"
        
        auth_url = "https://www.facebook.com/v18.0/dialog/oauth"
        params = {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": str(channel.id),
        }
        return {"auth_url": f"{auth_url}?{urlencode(params)}"}
    
    raise HTTPException(status_code=400, detail=f"OAuth no soportado para {platform.value}")


@router.get("/oauth/callback/{platform}")
async def oauth_callback(
    platform: ChannelPlatform,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """OAuth callback handler for supported platforms."""
    import httpx
    
    try:
        channel_id = UUID(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="State inválido")
    
    result = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.id == channel_id,
            ChannelConnection.platform == platform,
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    
    base_callback = settings.FRONTEND_URL or "http://localhost:3000"
    redirect_uri = f"{base_callback}/api/v1/channels/oauth/callback/{platform.value}"
    
    if platform == ChannelPlatform.MERCADOLIBRE:
        client_id = channel.credentials.get("client_id")
        client_secret = channel.credentials.get("client_secret")
        if not client_id or not client_secret:
            raise HTTPException(status_code=400, detail="Faltan client_id o client_secret")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mercadolibre.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Error de OAuth: {response.text}")
            
            data = response.json()
            channel.credentials["access_token"] = data.get("access_token")
            channel.credentials["refresh_token"] = data.get("refresh_token")
            channel.credentials["seller_id"] = str(data.get("user_id", ""))
            channel.status = ChannelStatus.CONNECTED
            await db.commit()
            return {"status": "connected", "platform": platform.value}
    
    elif platform in (ChannelPlatform.FACEBOOK_ADS, ChannelPlatform.INSTAGRAM, ChannelPlatform.MESSENGER, ChannelPlatform.WHATSAPP):
        app_id = channel.credentials.get("app_id")
        app_secret = channel.credentials.get("app_secret")
        if not app_id or not app_secret:
            raise HTTPException(status_code=400, detail="Faltan app_id o app_secret")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Error de OAuth: {response.text}")
            
            data = response.json()
            channel.credentials["access_token"] = data.get("access_token")
            channel.status = ChannelStatus.CONNECTED
            await db.commit()
            return {"status": "connected", "platform": platform.value}
    
    raise HTTPException(status_code=400, detail=f"OAuth no soportado para {platform.value}")


# ========== Webhook Verification (GET) ==========

@router.get("/webhook/{platform}", status_code=status.HTTP_200_OK)
async def verify_webhook(
    platform: ChannelPlatform,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    token: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Verify webhook subscription (used by WhatsApp Business API, Meta, etc.)."""
    # Si hay token, verificar por token directo (Telegram, Webchat)
    if token:
        result = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.webhook_token == token,
                ChannelConnection.platform == platform,
                ChannelConnection.is_active == True,
            )
        )
        channel = result.scalar_one_or_none()
        if channel:
            return {"status": "ok"}
        raise HTTPException(status_code=403, detail="Token de webhook inválido")

    if platform == ChannelPlatform.WHATSAPP:
        if hub_mode == "subscribe" and hub_verify_token and hub_challenge:
            # Find channel with matching verify token
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.WHATSAPP,
                    ChannelConnection.is_active == True,
                )
            )
            channels = result.scalars().all()
            for ch in channels:
                settings = ch.settings or {}
                expected_token = settings.get("verify_token", ch.credentials.get("verify_token", ""))
                if expected_token and hmac.compare_digest(hub_verify_token, expected_token):
                    return int(hub_challenge)
        raise HTTPException(status_code=403, detail="Verificación de webhook fallida")

    # Generic verification for other platforms
    return {"status": "ok"}


# ========== Webhook Reception (POST) ==========

@router.post("/webhook/{platform}", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(
    platform: ChannelPlatform,
    request: Request,
    token: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Receive incoming webhook from any platform.
    
    Requiere ?token=xxx para identificar el canal, excepto para plataformas
    que usan verificación por firma (WhatsApp) donde el canal se identifica
    por el ID contenido en el payload.
    """
    raw_body = await request.body()
    raw_json = await request.json() if raw_body else {}

    channel: ChannelConnection | None = None

    # Estrategia 1: Buscar por webhook_token (método preferido)
    if token:
        result = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.webhook_token == token,
                ChannelConnection.platform == platform,
                ChannelConnection.is_active == True,
            )
        )
        channel = result.scalar_one_or_none()
        if not channel:
            raise HTTPException(status_code=401, detail="Token de webhook inválido")

    # Estrategia 2: Para WhatsApp, identificar por phone_number_id + verificar firma
    elif platform == ChannelPlatform.WHATSAPP:
        # Extraer phone_number_id del payload
        phone_number_id = None
        try:
            entry = raw_json.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")
        except Exception:
            pass

        if phone_number_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.WHATSAPP,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"phone_number_id": phone_number_id}),
                )
            )
            channel = result.scalar_one_or_none()

        # Verificar firma si hay app_secret configurado
        if channel:
            signature = request.headers.get("X-Hub-Signature-256", "")
            app_secret = channel.credentials.get("app_secret", channel.settings.get("app_secret", ""))
            if app_secret and signature:
                import hmac
                import hashlib
                expected = "sha256=" + hmac.new(
                    app_secret.encode(), raw_body, hashlib.sha256
                ).hexdigest()
                if not hmac.compare_digest(expected, signature):
                    raise HTTPException(status_code=401, detail="Firma de webhook inválida")
        else:
            # Fallback: buscar en todos los canales de WhatsApp y verificar firma
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.WHATSAPP,
                    ChannelConnection.is_active == True,
                )
            )
            channels = result.scalars().all()
            verified = False
            signature = request.headers.get("X-Hub-Signature-256", "")
            for ch in channels:
                app_secret = ch.credentials.get("app_secret", ch.settings.get("app_secret", ""))
                if app_secret and signature:
                    import hmac
                    import hashlib
                    expected = "sha256=" + hmac.new(
                        app_secret.encode(), raw_body, hashlib.sha256
                    ).hexdigest()
                    if hmac.compare_digest(expected, signature):
                        channel = ch
                        verified = True
                        break
            has_secret = any(
                (ch.credentials.get("app_secret") or ch.settings.get("app_secret"))
                for ch in channels
            )
            if has_secret and not verified:
                raise HTTPException(status_code=401, detail="Firma de webhook inválida")

    # Estrategia 3: Para Instagram/Messenger, identificar por page_id/instagram_account_id
    elif platform in (ChannelPlatform.INSTAGRAM, ChannelPlatform.MESSENGER):
        page_id = None
        try:
            entry = raw_json.get("entry", [{}])[0]
            page_id = entry.get("id")
        except Exception:
            pass

        if page_id:
            # Buscar por page_id o instagram_account_id en credentials
            from sqlalchemy import or_
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == platform,
                    ChannelConnection.is_active == True,
                    or_(
                        ChannelConnection.credentials.contains({"page_id": page_id}),
                        ChannelConnection.credentials.contains({"instagram_account_id": page_id}),
                    ),
                )
            )
            channel = result.scalar_one_or_none()

    # Estrategia 4: Para Telegram, identificar por bot_token en settings/credentials
    elif platform == ChannelPlatform.TELEGRAM:
        bot_token = None
        try:
            # Telegram no incluye bot_token en el webhook payload
            # Se debe usar ?token=xxx o verificar por webhook_secret
            pass
        except Exception:
            pass

    # Estrategia 5: Para MercadoLibre, identificar por seller_id (user_id en notificación)
    elif platform == ChannelPlatform.MERCADOLIBRE:
        seller_id = raw_json.get("user_id")
        if seller_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.MERCADOLIBRE,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"seller_id": str(seller_id)}),
                )
            )
            channel = result.scalar_one_or_none()

    # Estrategia 6: Para Facebook Ads, identificar por page_id
    elif platform == ChannelPlatform.FACEBOOK_ADS:
        page_id = None
        try:
            entry = raw_json.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            page_id = value.get("page_id") or entry.get("id")
        except Exception:
            pass

        if page_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.FACEBOOK_ADS,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"page_id": str(page_id)}),
                )
            )
            channel = result.scalar_one_or_none()

    # Estrategia 7: Para Shopify, identificar por shop_domain header + verificar HMAC
    elif platform == ChannelPlatform.SHOPIFY:
        shop_domain = request.headers.get("X-Shopify-Shop-Domain")
        if shop_domain:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.SHOPIFY,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"shop_domain": shop_domain}),
                )
            )
            channel = result.scalar_one_or_none()

        if channel:
            hmac_header = request.headers.get("X-Shopify-Hmac-SHA256", "")
            webhook_secret = channel.credentials.get("webhook_secret")
            if webhook_secret and hmac_header:
                import hmac
                import hashlib
                digest = hmac.new(
                    webhook_secret.encode("utf-8"),
                    raw_body,
                    hashlib.sha256,
                ).hexdigest()
                if not hmac.compare_digest(digest, hmac_header):
                    raise HTTPException(status_code=401, detail="Firma de webhook inválida")

        # Also inject the topic into the payload for parsing
        topic = request.headers.get("X-Shopify-Topic", "")
        if raw_json:
            raw_json["_topic"] = topic

    # Estrategia 8: Para Amazon, identificar por seller_id
    elif platform == ChannelPlatform.AMAZON:
        seller_id = raw_json.get("SellerId") or raw_json.get("seller_id")
        if seller_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.AMAZON,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"seller_id": str(seller_id)}),
                )
            )
            channel = result.scalar_one_or_none()

    # Estrategia 9: Para Beacons, identificar por creator_id
    elif platform == ChannelPlatform.BEACONS:
        creator_id = raw_json.get("data", {}).get("creator_id")
        if creator_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.BEACONS,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"creator_id": str(creator_id)}),
                )
            )
            channel = result.scalar_one_or_none()

    # Estrategia 10: Para Meta Ads, identificar por page_id (mismo que Facebook Ads)
    elif platform == ChannelPlatform.META_ADS:
        page_id = None
        try:
            entry = raw_json.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            page_id = value.get("page_id") or entry.get("id")
        except Exception:
            pass

        if page_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.META_ADS,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"page_id": str(page_id)}),
                )
            )
            channel = result.scalar_one_or_none()

    # Estrategia 11: Para Google Ads, identificar por customer_id o campaign_id
    elif platform == ChannelPlatform.GOOGLE_ADS:
        customer_id = raw_json.get("customer_id")
        campaign_id = raw_json.get("campaign_id")
        lookup_id = customer_id or campaign_id
        if lookup_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.GOOGLE_ADS,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"customer_id": str(lookup_id)}),
                )
            )
            channel = result.scalar_one_or_none()

    # Estrategia 12: Para TikTok Ads, identificar por advertiser_id
    elif platform == ChannelPlatform.TIKTOK_ADS:
        advertiser_id = raw_json.get("advertiser_id")
        if advertiser_id:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.platform == ChannelPlatform.TIKTOK_ADS,
                    ChannelConnection.is_active == True,
                    ChannelConnection.credentials.contains({"advertiser_id": str(advertiser_id)}),
                )
            )
            channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado para este webhook")

    # Parse payload using connector
    try:
        from app.domains.channels.connectors import CONNECTOR_REGISTRY

        payload = None
        connector_class = CONNECTOR_REGISTRY.get(platform)
        if connector_class and raw_json:
            connector = connector_class(channel.credentials, channel.settings)
            if hasattr(connector, "parse_webhook"):
                payload = await connector.parse_webhook(raw_json)

        if not payload:
            # Fallback: try to construct generic payload
            payload = WebhookPayload(
                platform=platform,
                external_id=raw_json.get("from") or raw_json.get("sender", {}).get("id") or "unknown",
                sender_name=raw_json.get("sender", {}).get("name"),
                content=raw_json.get("text") or raw_json.get("message", ""),
                content_type="text",
                extra_data=raw_json,
            )
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Webhook parse error for {platform}: {e}")
        raise HTTPException(status_code=400, detail="Payload inválido")

    from app.domains.channels.services import process_incoming_message
    await process_incoming_message(db, channel, payload)
    return {"status": "accepted"}
