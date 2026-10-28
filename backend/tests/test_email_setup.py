"""Guided email connection: provider detection, code check, and the start/confirm/resend endpoints."""
# ruff: noqa: F811

import uuid

import pytest
from fastapi import HTTPException
from test_harvey import (  # noqa: F401
    ChannelConnection,
    ChannelPlatform,
    ChannelStatus,
    _Biz,
    db,
)

from app.api.v1 import email_channel
from app.domains.channels import email_setup
from app.domains.harvey import mailer

SECRET = "test-secret-key-32-chars-long-1234567890"


# ── pure helpers ──────────────────────────────────────────────────────────
def test_known_provider_is_detected_from_the_address():
    p = email_setup.detect_provider("Ventas@Gmail.com")
    assert (p.key, p.smtp_host, p.smtp_port, p.imap_host) == ("gmail", "smtp.gmail.com", 587, "imap.gmail.com")
    assert email_setup.detect_provider("a@hotmail.com").key == "outlook"


def test_unknown_domain_is_guessed():
    p = email_setup.detect_provider("hola@panaderiasol.com")
    assert p.guessed and p.smtp_host == "smtp.panaderiasol.com" and p.imap_host == "imap.panaderiasol.com"


def test_failure_message_is_specific_to_the_provider():
    gmail = email_setup.detect_provider("a@gmail.com")
    assert "contraseña de aplicación" in email_setup.explain_failure(gmail, "auth", "smtp.gmail.com")
    assert "smtp.x.com" in email_setup.explain_failure(email_setup.detect_provider("a@x.com"), "connect", "smtp.x.com")


def test_code_roundtrip_expiry_attempts_and_cooldown():
    stored = email_setup.pending_verification(SECRET, "ch1", "123456", now=1000)
    assert "123456" not in str(stored)
    assert email_setup.check_code(SECRET, "ch1", stored, " 123456 ", now=1001) == "ok"
    assert email_setup.check_code(SECRET, "ch1", stored, "000000", now=1001) == "wrong"
    assert email_setup.check_code(SECRET, "other", stored, "123456", now=1001) == "wrong"  # bound to the channel
    assert email_setup.check_code(SECRET, "ch1", stored, "123456", now=1000 + email_setup.CODE_TTL_SECONDS + 1) == "expired"
    assert email_setup.check_code(SECRET, "ch1", {**stored, "attempts": 5}, "123456", now=1001) == "locked"
    assert email_setup.check_code(SECRET, "ch1", None, "123456") == "none"
    assert not email_setup.can_resend(stored, now=1010)
    assert email_setup.can_resend(stored, now=1000 + email_setup.RESEND_COOLDOWN_SECONDS)


# ── endpoints ─────────────────────────────────────────────────────────────
class _User:
    id = uuid.uuid4()


@pytest.fixture
def wired(monkeypatch):
    sent = []

    async def ok_access(db, business_id, user, manage=False):
        return None

    async def limit(db, user_id, metric, quantity=1):
        return {"allowed": True, "used": 0, "limit": 5}

    async def track(*a, **k):
        return None

    async def login(account):
        return mailer.LoginCheck(True, "", "")

    async def send(account, msg):
        sent.append(msg)

    monkeypatch.setattr(email_channel, "require_business_access", ok_access)
    monkeypatch.setattr(email_channel, "check_subscription_limit", limit)
    monkeypatch.setattr(email_channel, "track_usage", track)
    monkeypatch.setattr(email_channel.mailer, "check_login", login)
    monkeypatch.setattr(email_channel.mailer, "send", send)
    monkeypatch.setattr(email_channel.settings, "SECRET_KEY", SECRET)
    return sent


def _code_from(sent) -> str:
    return sent[-1]["Subject"].rsplit(" ", 1)[-1]


@pytest.mark.asyncio
async def test_start_then_confirm_connects_the_channel(db, wired):
    biz = _Biz()
    out = await email_channel.start_email_connection(
        biz.id, email_channel.StartIn(email="Ventas@Gmail.com", password="app-pass"), db, _User()
    )
    ch = await db.get(ChannelConnection, out.channel_id)
    assert ch.status == ChannelStatus.PENDING and out.provider == "Gmail"
    assert wired[-1]["To"] == "ventas@gmail.com"
    assert await mailer.get_email_account(db, biz.id) is None  # not usable until confirmed

    with pytest.raises(HTTPException) as e:
        await email_channel.confirm_email_connection(biz.id, out.channel_id, email_channel.ConfirmIn(code="000000"), db, _User())
    assert e.value.status_code == 422 and "4 intentos" in e.value.detail

    res = await email_channel.confirm_email_connection(
        biz.id, out.channel_id, email_channel.ConfirmIn(code=_code_from(wired)), db, _User()
    )
    assert res.status == "connected"
    await db.refresh(ch)
    assert ch.status == ChannelStatus.CONNECTED and "email_verification" not in ch.settings
    assert (await mailer.get_email_account(db, biz.id)).from_address == "ventas@gmail.com"


@pytest.mark.asyncio
async def test_wrong_login_is_explained_and_nothing_is_stored(db, wired, monkeypatch):
    async def bad(account):
        return mailer.LoginCheck(False, "auth", "smtp.gmail.com")

    monkeypatch.setattr(email_channel.mailer, "check_login", bad)
    with pytest.raises(HTTPException) as e:
        await email_channel.start_email_connection(
            _Biz().id, email_channel.StartIn(email="a@gmail.com", password="x"), db, _User()
        )
    assert e.value.status_code == 422 and "contraseña de aplicación" in e.value.detail
    assert wired == []


@pytest.mark.asyncio
async def test_resend_has_a_cooldown_and_issues_a_new_code(db, wired):
    biz = _Biz()
    out = await email_channel.start_email_connection(
        biz.id, email_channel.StartIn(email="a@gmail.com", password="x"), db, _User()
    )
    with pytest.raises(HTTPException) as e:
        await email_channel.resend_email_code(biz.id, out.channel_id, db, _User())
    assert e.value.status_code == 429
    ch = await db.get(ChannelConnection, out.channel_id)
    ch.settings = {**ch.settings, "email_verification": {**ch.settings["email_verification"], "sent_at": 0}}
    await db.commit()
    await email_channel.resend_email_code(biz.id, out.channel_id, db, _User())
    assert len(wired) == 2


@pytest.mark.asyncio
async def test_other_business_cannot_confirm_my_channel(db, wired):
    biz = _Biz()
    out = await email_channel.start_email_connection(
        biz.id, email_channel.StartIn(email="a@gmail.com", password="x"), db, _User()
    )
    with pytest.raises(HTTPException) as e:
        await email_channel.confirm_email_connection(
            _Biz().id, out.channel_id, email_channel.ConfirmIn(code=_code_from(wired)), db, _User()
        )
    assert e.value.status_code == 404
