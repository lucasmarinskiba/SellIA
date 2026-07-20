"""WhatsApp Cloud API · Embedded Signup OAuth handler.

Meta's Embedded Signup flow:
  1. Frontend opens FB.login w/ config_id (WhatsApp Embedded Signup)
  2. User picks business account + phone number → Meta returns code
  3. Frontend POSTs code to this endpoint
  4. Backend exchanges code → system user access token + phone_number_id
  5. Persist to channels table → channel becomes live
"""
import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import settings
from app.core.security import CurrentUser, require_role
from app.db.models import Channel, ChannelKind
from app.db.session import get_session


logger = logging.getLogger(__name__)
router = APIRouter()


META_GRAPH_BASE = "https://graph.facebook.com/v21.0"


class ExchangeRequest(BaseModel):
    code: str
    waba_id: str  # WhatsApp Business Account ID
    phone_number_id: str


class ExchangeResponse(BaseModel):
    channel_id: str
    phone_number_id: str
    display_phone: str | None
    success: bool


@router.post("/exchange", response_model=ExchangeResponse)
async def exchange_code(
    payload: ExchangeRequest,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> ExchangeResponse:
    """Exchange Embedded Signup code → permanent system user access token.

    Requires Meta App env:
      - META_APP_ID
      - META_APP_SECRET
      - WhatsApp Cloud API permissions approved
    """
    app_id = getattr(settings, "META_APP_ID", None)
    app_secret = getattr(settings, "META_APP_SECRET", None) or settings.WA_APP_SECRET

    if not app_id or not app_secret:
        raise HTTPException(status_code=503, detail="Meta App not configured")

    # Step 1 · exchange code for access token
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.get(
            f"{META_GRAPH_BASE}/oauth/access_token",
            params={
                "client_id": app_id,
                "client_secret": app_secret,
                "code": payload.code,
            },
        )
        if token_resp.status_code != 200:
            logger.warning("wa_oauth_exchange_failed", extra={"body": token_resp.text})
            raise HTTPException(status_code=400, detail="Code exchange failed")

        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access_token in response")

        # Step 2 · subscribe app to WABA webhooks
        sub_resp = await client.post(
            f"{META_GRAPH_BASE}/{payload.waba_id}/subscribed_apps",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if sub_resp.status_code not in (200, 201):
            logger.warning("wa_webhook_subscribe_failed", extra={"body": sub_resp.text})

        # Step 3 · fetch phone number metadata
        meta_resp = await client.get(
            f"{META_GRAPH_BASE}/{payload.phone_number_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"fields": "display_phone_number,verified_name,quality_rating"},
        )
        meta = meta_resp.json() if meta_resp.status_code == 200 else {}

    # Persist channel
    async with get_session(tenant_id=user.tenant_id) as db:
        existing = await db.execute(
            select(Channel).where(
                Channel.external_id == payload.phone_number_id,
                Channel.kind == ChannelKind.WHATSAPP,
            )
        )
        ch = existing.scalar_one_or_none()
        if ch:
            ch.is_active = True
            ch.config = {
                "access_token": access_token,
                "waba_id": payload.waba_id,
                "display_phone": meta.get("display_phone_number"),
                "verified_name": meta.get("verified_name"),
            }
        else:
            ch = Channel(
                tenant_id=uuid.UUID(user.tenant_id),
                kind=ChannelKind.WHATSAPP,
                external_id=payload.phone_number_id,
                config={
                    "access_token": access_token,
                    "waba_id": payload.waba_id,
                    "display_phone": meta.get("display_phone_number"),
                    "verified_name": meta.get("verified_name"),
                },
                is_active=True,
            )
            db.add(ch)
        await db.flush()
        channel_id = str(ch.id)

    logger.info("wa_channel_connected", extra={"tenant_id": user.tenant_id, "phone_id": payload.phone_number_id})

    return ExchangeResponse(
        channel_id=channel_id,
        phone_number_id=payload.phone_number_id,
        display_phone=meta.get("display_phone_number"),
        success=True,
    )


class ChannelStatusResponse(BaseModel):
    is_active: bool
    display_phone: str | None
    verified_name: str | None
    quality_rating: str | None


@router.get("/status/{channel_id}", response_model=ChannelStatusResponse)
async def get_channel_status(
    channel_id: uuid.UUID,
    user: CurrentUser = Depends(require_role("owner", "admin", "manager")),
) -> ChannelStatusResponse:
    """Verify channel health · pings Meta for live quality rating."""
    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        ch = result.scalar_one_or_none()
        if not ch or ch.kind != ChannelKind.WHATSAPP:
            raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    cfg = ch.config or {}
    token = cfg.get("access_token")
    if not token:
        return ChannelStatusResponse(is_active=False, display_phone=None, verified_name=None, quality_rating=None)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{META_GRAPH_BASE}/{ch.external_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"fields": "display_phone_number,verified_name,quality_rating"},
        )
        data = r.json() if r.status_code == 200 else {}

    return ChannelStatusResponse(
        is_active=ch.is_active,
        display_phone=cfg.get("display_phone") or data.get("display_phone_number"),
        verified_name=cfg.get("verified_name") or data.get("verified_name"),
        quality_rating=data.get("quality_rating"),
    )
