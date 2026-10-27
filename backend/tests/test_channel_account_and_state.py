"""Channel connections: signed OAuth state, masked credentials, and which account a channel belongs to."""

import os
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from app.domains.channels import account as channel_account
from app.domains.channels.models import ChannelPlatform, ChannelStatus
from app.domains.channels.oauth_state import sign_state, verify_state
from app.domains.channels.schemas import ChannelConnectionResponse

SECRET = "server-secret-for-tests"
CHANNEL, USER = uuid.uuid4(), uuid.uuid4()


# ── signed state ──────────────────────────────────────────────────────────
def test_state_round_trip_returns_the_channel_and_the_user_who_started_it():
    state = sign_state(SECRET, CHANNEL, USER, now=1_000)
    assert verify_state(SECRET, state, now=1_100) == (CHANNEL, USER)


def test_state_cannot_be_finished_by_someone_who_only_knows_the_channel_id():
    for forged in (str(CHANNEL), f"{CHANNEL}.{USER}.9999999999.{'0' * 64}", ""):
        with pytest.raises(ValueError):
            verify_state(SECRET, forged, now=1_000)


def test_state_is_bound_to_the_user_channel_and_secret():
    state = sign_state(SECRET, CHANNEL, USER, now=1_000)
    channel, user, expires, signature = state.split(".")
    other = uuid.uuid4()
    for tampered in (
        f"{other}.{user}.{expires}.{signature}",
        f"{channel}.{other}.{expires}.{signature}",
        f"{channel}.{user}.{int(expires) + 3600}.{signature}",
    ):
        with pytest.raises(ValueError):
            verify_state(SECRET, tampered, now=1_100)
    with pytest.raises(ValueError):
        verify_state("another-secret", state, now=1_100)


def test_state_expires():
    state = sign_state(SECRET, CHANNEL, USER, ttl=60, now=1_000)
    verify_state(SECRET, state, now=1_059)
    with pytest.raises(ValueError, match="vencido"):
        verify_state(SECRET, state, now=1_100)


# ── masked credentials ────────────────────────────────────────────────────
def test_credentials_are_reported_as_present_never_with_their_value():
    masked = channel_account.mask_credentials({"access_token": "APP_USR-secret", "seller_id": "123", "empty": "", "none": None})
    assert masked == {"access_token": channel_account.MASK, "seller_id": channel_account.MASK}
    assert "secret" not in str(masked)


def test_writing_back_the_masked_values_keeps_the_stored_secrets():
    stored = {"smtp_user": "a@b.com", "smtp_password": "real-password"}
    incoming = {"smtp_user": "new@b.com", "smtp_password": channel_account.MASK, "imap_host": "imap.b.com"}
    assert channel_account.restore_masked(incoming, stored) == {
        "smtp_user": "new@b.com",
        "smtp_password": "real-password",
        "imap_host": "imap.b.com",
    }
    assert channel_account.restore_masked({"smtp_password": "changed"}, stored) == {"smtp_password": "changed"}


# ── account identity ──────────────────────────────────────────────────────
def test_manual_channels_say_which_account_they_point_at():
    email = channel_account.account_from_credentials(
        "email", {"smtp_user": "ventas@mi-negocio.com", "smtp_host": "smtp.gmail.com", "smtp_password": "x"}
    )
    assert email == {"name": "ventas@mi-negocio.com", "detail": "smtp.gmail.com"}
    assert "x" not in str(email.values())
    assert channel_account.account_from_credentials("shopify", {"shop_domain": "mitienda.myshopify.com"}) == {
        "name": "mitienda.myshopify.com"
    }
    assert channel_account.account_from_credentials("telegram", {"bot_token": "1:abc"}) is None


def test_public_account_only_exposes_known_fields():
    assert channel_account.public_account({"account": {"id": 7, "name": "TIENDA_X", "token": "leak"}}) == {
        "id": "7",
        "name": "TIENDA_X",
    }
    assert channel_account.public_account({}) is None
    assert channel_account.public_account({"account": "nope"}) is None


def _channel(**overrides):
    base = dict(
        id=uuid.uuid4(), business_id=uuid.uuid4(), platform=ChannelPlatform.MERCADOLIBRE, name="Mercado Libre",
        credentials={"access_token": "APP_USR-secret", "refresh_token": "TG-secret", "seller_id": "999"},
        settings={"account": {"id": "999", "name": "TIENDA_X"}}, status=ChannelStatus.CONNECTED, status_message=None,
        webhook_url=None, webhook_token="wh", last_sync_at=None, is_active=True,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_api_response_hides_secrets_and_shows_the_account():
    data = ChannelConnectionResponse.model_validate(_channel(), from_attributes=True).model_dump(mode="json")
    assert data["account"] == {"id": "999", "name": "TIENDA_X"}
    assert set(data["credentials"]) == {"access_token", "refresh_token", "seller_id"}
    assert "APP_USR-secret" not in str(data) and "TG-secret" not in str(data)


def test_api_response_for_a_channel_without_identity():
    data = ChannelConnectionResponse.model_validate(
        _channel(settings={}, credentials={}), from_attributes=True
    ).model_dump(mode="json")
    assert data["account"] is None and data["credentials"] == {}


# ── callback rejects states it did not issue (no DB needed: it never gets that far) ──
@pytest.mark.asyncio
@pytest.mark.parametrize("state", [str(uuid.uuid4()), "garbage", f"{uuid.uuid4()}.{uuid.uuid4()}.9999999999.{'a' * 64}"])
async def test_oauth_callback_ignores_unsigned_or_forged_state(state):
    import httpx
    from fastapi import FastAPI

    from app.api.v1 import channels as channels_api
    from app.core.database import get_db

    class _NoDb:
        async def execute(self, *args, **kwargs):
            raise AssertionError("an invalid state must be rejected before touching the database")

    async def no_db():
        yield _NoDb()

    app = FastAPI()
    app.include_router(channels_api.router)
    app.dependency_overrides[get_db] = no_db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as client:
        for platform in ("mercadolibre", "instagram"):
            resp = await client.get(f"/oauth/callback/{platform}", params={"code": "c", "state": state}, follow_redirects=False)
            assert resp.status_code in (302, 307) and resp.headers["location"].endswith("/dashboard/canales?connect_error=state")
