"""Webhook token rotation that the business owner decides.

Rotating a channel's ``webhook_token`` invalidates the webhook URL configured on the external
platform (WhatsApp, ManyChat, ...): messages stop arriving until someone pastes the new URL
there. The scheduled task therefore no longer rotates anything by itself. For each token that
is more than 90 days old it leaves a *proposal* the owner can read and answer:

* a ``Recommendation`` (``context_data.kind == ROTATION_KIND``) that is ``pending`` until the
  owner applies it (the token is rotated) or dismisses it (the token is kept and the question
  comes back after another 90 days), and
* an ``Alert`` so it shows up in the notifications, with the consequences spelled out.

No schema change: the proposal reuses ``Recommendation`` (type CUSTOM, action WAIT) and the
rotation is audited in ``secret_rotation_logs`` like before.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.alerts.factory import build_alert
from app.domains.alerts.models import (
    Recommendation,
    RecommendationActionType,
    RecommendationStatus,
    RecommendationType,
)
from app.domains.channels.models import ChannelConnection
from app.domains.security.models import SecretRotationLog

ROTATION_KIND = "webhook_token_rotation"
ROTATION_ALERT_KIND = "webhook_token_rotation_proposed"
#: A token is proposed for rotation after this long, and is not proposed again for this long
#: after a proposal (whatever the owner answered).
ROTATION_INTERVAL = timedelta(days=90)


def is_rotation_proposal(rec: Recommendation) -> bool:
    return (
        isinstance(rec.context_data, dict)
        and rec.context_data.get("kind") == ROTATION_KIND
    )


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:16]


async def _already_proposed(
    db: AsyncSession, channel_id: uuid.UUID, now: datetime
) -> bool:
    """A pending proposal, or any proposal made in the last 90 days (dismissing postpones)."""
    result = await db.execute(
        select(Recommendation.id)
        .where(
            Recommendation.context_data["kind"].astext == ROTATION_KIND,
            Recommendation.context_data["channel_id"].astext == str(channel_id),
        )
        .where(
            (Recommendation.status == RecommendationStatus.PENDING)
            | (Recommendation.created_at >= now - ROTATION_INTERVAL)
        )
        .limit(1)
    )
    return result.first() is not None


async def propose_rotation(
    db: AsyncSession, channel: ChannelConnection, now: datetime | None = None
) -> bool:
    """Leave the owner a proposal to rotate ``channel``'s token. False if one is already open.

    The caller commits.
    """
    now = now or datetime.now(UTC)
    if await _already_proposed(db, channel.id, now):
        return False

    platform = getattr(channel.platform, "value", channel.platform)
    title = f"Renovar el token del webhook de «{channel.name}» ({platform})"
    body = (
        f"El token del webhook del canal «{channel.name}» ({platform}) lleva más de 90 días sin renovarse. "
        "Renovarlo es una buena práctica de seguridad, pero cambia la URL del webhook: apenas lo aceptes, "
        f"la URL anterior deja de funcionar y vas a tener que pegar la nueva en {platform}; "
        "hasta entonces no llegarán mensajes de ese canal.\n\n"
        "• Aceptar: se genera un token nuevo y vas a ver la URL nueva en la configuración del canal.\n"
        "• Rechazar: no se cambia nada y te lo volvemos a proponer en 90 días.\n"
        "No se renueva nada sin tu respuesta."
    )
    db.add(
        Recommendation(
            business_id=channel.business_id,
            type=RecommendationType.CUSTOM,
            title=title,
            description=body,
            priority=2,
            context_data={
                "kind": ROTATION_KIND,
                "channel_id": str(channel.id),
                "platform": platform,
            },
            action_type=RecommendationActionType.WAIT,
            action_payload={},
        )
    )
    db.add(
        build_alert(
            channel.business_id,
            title,
            body,
            kind=ROTATION_ALERT_KIND,
            level="info",
            dedupe_key=str(channel.id),
            created_at=now,
        )
    )
    return True


class RotationNotPossible(Exception):
    """The channel is gone or inactive: there is nothing to rotate."""


async def apply_rotation(
    db: AsyncSession, rec: Recommendation, user_id: uuid.UUID | None
) -> None:
    """The owner accepted ``rec``: rotate the channel's token and mark it applied. Caller commits."""
    channel_id = uuid.UUID(str(rec.context_data["channel_id"]))
    channel = (
        await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.id == channel_id,
                ChannelConnection.business_id == rec.business_id,
                ChannelConnection.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if channel is None:
        raise RotationNotPossible("El canal ya no existe o está inactivo.")

    old_token = channel.webhook_token or ""
    new_token = secrets.token_urlsafe(32)
    channel.webhook_token = new_token
    db.add(
        SecretRotationLog(
            business_id=channel.business_id,
            secret_type="webhook_token",
            target_id=str(channel.id),
            old_value_hash=_hash(old_token) if old_token else None,
            new_value_hash=_hash(new_token),
            rotated_by=user_id,
            status="success",
        )
    )
    rec.status = RecommendationStatus.APPLIED
    rec.applied_at = datetime.now(UTC)
    rec.applied_by_user_id = user_id
