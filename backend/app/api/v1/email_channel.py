"""Guided email connection: /api/v1/businesses/{business_id}/channels/email/*

1. ``start``: address + password. The servers are detected from the address, both logins are tested, and a
   6-digit code is sent through that mailbox to itself. The channel exists but stays *pending*.
2. ``confirm``: the person types the code; only then is the channel connected (and usable by Harvey).
3. ``resend``: a new code (one per minute).
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logger import get_logger
from app.domains.channels import email_setup
from app.domains.channels.models import (
    ChannelConnection,
    ChannelPlatform,
    ChannelStatus,
)
from app.domains.harvey import mailer
from app.domains.harvey.gate import EMAIL_RE
from app.domains.subscriptions.services import check_subscription_limit, track_usage
from app.domains.users.models import User

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


class StartIn(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=300)
    # Only for a provider we could not detect ("Mi proveedor es otro").
    smtp_host: str | None = Field(None, max_length=255)
    smtp_port: int | None = Field(None, ge=1, le=65535)
    imap_host: str | None = Field(None, max_length=255)
    imap_port: int | None = Field(None, ge=1, le=65535)


class StartOut(BaseModel):
    channel_id: UUID
    email: str
    provider: str
    expires_in: int


class ConfirmIn(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class ConfirmOut(BaseModel):
    status: str
    email: str


def _http(code: int, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail=message)


async def _email_channel(db: AsyncSession, business_id: UUID, channel_id: UUID) -> ChannelConnection:
    channel = (
        await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.id == channel_id,
                ChannelConnection.business_id == business_id,
                ChannelConnection.platform == ChannelPlatform.EMAIL,
                ChannelConnection.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if channel is None:
        raise _http(404, "Canal de email no encontrado")
    return channel


async def _send_code(channel: ChannelConnection, account: mailer.EmailAccount) -> None:
    """Issue a new code and mail it through the person's own mailbox, to itself."""
    code = email_setup.new_code()
    msg = mailer.build_message(
        account,
        to_email=account.from_address,
        subject=f"Tu código de SellIA: {code}",
        body=(
            f"Tu código para conectar esta casilla a SellIA es {code}.\n\n"
            "Ingresalo en la pantalla de Canales. Vence en 15 minutos.\n"
            "Si no pediste esto, ignorá este mensaje: sin el código la casilla no se conecta."
        ),
        sender_name="SellIA",
    )
    try:
        await mailer.send(account, msg)
    except Exception as e:
        logger.warning("email channel: could not send the code (%s)", type(e).__name__)
        raise _http(422, "La casilla aceptó la contraseña pero no pudimos enviar el código. Probá de nuevo.") from e
    verification = email_setup.pending_verification(settings.SECRET_KEY, str(channel.id), code)
    channel.settings = {**(channel.settings or {}), "email_verification": verification}


def _account_from(channel: ChannelConnection) -> mailer.EmailAccount:
    account = mailer.account_from_credentials(channel.credentials or {})
    if account is None:
        raise _http(409, "La casilla no tiene datos de acceso guardados: empezá de nuevo")
    return account


@router.post("/{business_id}/channels/email/start", response_model=StartOut, status_code=status.HTTP_201_CREATED)
async def start_email_connection(
    business_id: UUID,
    body: StartIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    address = body.email.strip().lower()
    if not EMAIL_RE.match(address):
        raise _http(422, "Ese email no parece válido. Revisá cómo está escrito.")

    provider = email_setup.detect_provider(address)
    smtp_host = (body.smtp_host or provider.smtp_host).strip()
    smtp_port = body.smtp_port or provider.smtp_port
    imap_host = (body.imap_host or (provider.imap_host if not body.smtp_host else mailer.derive_imap_host(smtp_host))).strip()
    credentials: dict[str, Any] = {
        "smtp_host": smtp_host, "smtp_port": smtp_port, "smtp_user": address, "smtp_password": body.password,
        "from_address": address, "imap_host": imap_host, "imap_port": body.imap_port or provider.imap_port,
    }
    account = mailer.account_from_credentials(credentials)
    assert account is not None  # user and password are present

    check = await mailer.check_login(account)
    if not check.ok:
        raise _http(422, email_setup.explain_failure(provider, check.kind, check.host or smtp_host))

    existing = (
        await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.business_id == business_id,
                ChannelConnection.platform == ChannelPlatform.EMAIL,
                ChannelConnection.is_active.is_(True),
            )
        )
    ).scalars().all()
    channel = next((c for c in existing if (c.credentials or {}).get("smtp_user", "").lower() == address), None)
    if channel is None:
        limit = await check_subscription_limit(db, current_user.id, "channels", quantity=1)
        if not limit["allowed"]:
            raise _http(403, f"Límite de canales alcanzado. Usados: {limit['used']}/{limit['limit']}")
        channel = ChannelConnection(
            business_id=business_id, platform=ChannelPlatform.EMAIL, name="Email", credentials=credentials,
            settings={"account": {"name": address, "detail": provider.name}}, status=ChannelStatus.PENDING,
        )
        db.add(channel)
        await db.flush()
        created = True
    else:
        channel.credentials = credentials
        channel.status = ChannelStatus.PENDING  # a changed password is confirmed again
        created = False

    try:
        await _send_code(channel, account)
    except HTTPException:
        await db.rollback()
        raise
    await db.commit()
    if created:
        try:
            await track_usage(db, current_user.id, "channels", quantity=1, business_id=business_id)
        except Exception:  # noqa: BLE001 - usage tracking must never break the connection
            pass
    return StartOut(channel_id=channel.id, email=address, provider=provider.name, expires_in=email_setup.CODE_TTL_SECONDS)


@router.post("/{business_id}/channels/{channel_id}/email/confirm", response_model=ConfirmOut)
async def confirm_email_connection(
    business_id: UUID,
    channel_id: UUID,
    body: ConfirmIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    channel = await _email_channel(db, business_id, channel_id)
    stored = (channel.settings or {}).get("email_verification")
    result = email_setup.check_code(settings.SECRET_KEY, str(channel.id), stored, body.code)
    address = (channel.credentials or {}).get("smtp_user", "")

    if result == "ok":
        rest = {k: v for k, v in (channel.settings or {}).items() if k != "email_verification"}
        channel.settings = rest
        channel.status = ChannelStatus.CONNECTED
        channel.status_message = None
        await db.commit()
        return ConfirmOut(status="connected", email=address)

    if result == "wrong":
        channel.settings = {**(channel.settings or {}), "email_verification": {**stored, "attempts": int(stored.get("attempts", 0)) + 1}}
        await db.commit()
        left = email_setup.MAX_CODE_ATTEMPTS - int(stored.get("attempts", 0)) - 1
        raise _http(422, f"Ese código no es correcto. Te quedan {max(left, 0)} intentos." if left > 0 else "Ese código no es correcto. Pedí uno nuevo.")
    if result == "locked":
        raise _http(429, "Demasiados intentos. Pedí un código nuevo.")
    if result == "expired":
        raise _http(410, "El código venció. Pedí uno nuevo.")
    raise _http(409, "No hay un código pendiente. Pedí uno nuevo.")


@router.post("/{business_id}/channels/{channel_id}/email/resend", response_model=StartOut)
async def resend_email_code(
    business_id: UUID,
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    channel = await _email_channel(db, business_id, channel_id)
    if not email_setup.can_resend((channel.settings or {}).get("email_verification")):
        raise _http(429, "Esperá un minuto antes de pedir otro código.")
    account = _account_from(channel)
    await _send_code(channel, account)
    await db.commit()
    return StartOut(
        channel_id=channel.id,
        email=account.from_address,
        provider=((channel.settings or {}).get("account") or {}).get("detail", ""),
        expires_in=email_setup.CODE_TTL_SECONDS,
    )


__all__ = ["router", "time"]
