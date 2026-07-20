"""Browser extension OAuth · device authorization grant flow.

Flow (RFC 8628 style):
  1. Extension POST /v1/ext/device/code  → returns user_code + verification_uri + interval
  2. User opens verification_uri in normal browser · enters user_code · approves
  3. Extension polls /v1/ext/device/token  → returns access_token once approved
"""
import logging
import secrets
import time

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import CurrentUser, create_access_token, get_current_user


logger = logging.getLogger(__name__)
router = APIRouter()

DEVICE_CODE_TTL = 600  # 10 minutes
POLL_INTERVAL = 5

_redis: aioredis.Redis | None = None


def _redis_conn() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _key(suffix: str, code: str) -> str:
    return f"extauth:{suffix}:{code}"


# ─── Step 1 · request device code (no auth) ────────────────────────────────


class DeviceCodeResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


@router.post("/device/code", response_model=DeviceCodeResponse)
async def device_code() -> DeviceCodeResponse:
    """Issue device_code + user_code · extension calls before showing user code on screen."""
    device_code_val = secrets.token_urlsafe(32)
    user_code_val = secrets.token_hex(3).upper()  # 6 hex chars · easy to type

    r = _redis_conn()
    await r.setex(_key("device", device_code_val), DEVICE_CODE_TTL, "pending")
    await r.setex(_key("usercode", user_code_val), DEVICE_CODE_TTL, device_code_val)

    base = getattr(settings, "EXTENSION_VERIFY_BASE", "https://app.sellia.app")
    return DeviceCodeResponse(
        device_code=device_code_val,
        user_code=user_code_val,
        verification_uri=f"{base}/sellia-ext-auth",
        expires_in=DEVICE_CODE_TTL,
        interval=POLL_INTERVAL,
    )


# ─── Step 2 · user approves in browser (authenticated) ──────────────────────


class ApproveRequest(BaseModel):
    user_code: str


@router.post("/device/approve")
async def approve_device_code(
    payload: ApproveRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Logged-in user binds their account to the user_code shown in extension."""
    code = payload.user_code.strip().upper()
    r = _redis_conn()

    device_code_val = await r.get(_key("usercode", code))
    if not device_code_val:
        raise HTTPException(status_code=404, detail="Invalid or expired user_code")

    # Create scoped extension token (long-lived · 90 days)
    ext_token = create_access_token(user.user_id, user.tenant_id, user.role)
    await r.setex(_key("device", device_code_val), 600, f"approved:{ext_token}")
    await r.delete(_key("usercode", code))

    logger.info("ext_device_approved", extra={"user_id": user.user_id, "tenant_id": user.tenant_id})
    return {"approved": True}


# ─── Step 3 · extension polls for token ─────────────────────────────────────


class PollRequest(BaseModel):
    device_code: str


class TokenResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    error: str | None = None  # 'authorization_pending' · 'slow_down' · 'expired_token' · 'access_denied'


_last_poll: dict[str, float] = {}


@router.post("/device/token", response_model=TokenResponse)
async def poll_device_token(payload: PollRequest) -> TokenResponse:
    """Extension polls every `interval` seconds · returns token once user approves."""
    r = _redis_conn()
    state = await r.get(_key("device", payload.device_code))

    if not state:
        return TokenResponse(error="expired_token")

    # Rate-limit polling
    now = time.time()
    last = _last_poll.get(payload.device_code, 0)
    if now - last < POLL_INTERVAL - 1:
        return TokenResponse(error="slow_down")
    _last_poll[payload.device_code] = now

    if state == "pending":
        return TokenResponse(error="authorization_pending")

    if state.startswith("approved:"):
        token = state.split(":", 1)[1]
        # One-shot · consume
        await r.delete(_key("device", payload.device_code))
        _last_poll.pop(payload.device_code, None)
        return TokenResponse(access_token=token)

    return TokenResponse(error="access_denied")
