"""Signed ``state`` for the OAuth round trip (Mercado Libre, Meta).

The provider hands ``state`` back untouched to our callback, which has no session of its own. It used to be the
bare channel id, so anyone who knew an id could finish someone else's authorization with a different account.
The signed state binds the channel to the user who started the flow, expires, and cannot be forged without
the server secret.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from uuid import UUID

DEFAULT_TTL_SECONDS = 15 * 60
_PURPOSE = "channel-oauth-v1"


def _signature(secret: str, channel_id: UUID, user_id: UUID, expires: int) -> str:
    message = f"{_PURPOSE}|{channel_id}|{user_id}|{expires}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def sign_state(
    secret: str, channel_id: UUID, user_id: UUID, ttl: int = DEFAULT_TTL_SECONDS, now: float | None = None
) -> str:
    expires = int((time.time() if now is None else now) + ttl)
    return f"{channel_id}.{user_id}.{expires}.{_signature(secret, channel_id, user_id, expires)}"


def verify_state(secret: str, state: str, now: float | None = None) -> tuple[UUID, UUID]:
    """The (channel_id, user_id) a valid state was issued for; ValueError if forged, malformed or expired."""
    parts = (state or "").split(".")
    if len(parts) != 4:
        raise ValueError("state malformado")
    raw_channel, raw_user, raw_expires, signature = parts
    try:
        channel_id, user_id, expires = UUID(raw_channel), UUID(raw_user), int(raw_expires)
    except ValueError as e:
        raise ValueError("state malformado") from e
    if not hmac.compare_digest(signature, _signature(secret, channel_id, user_id, expires)):
        raise ValueError("state inválido")
    if (time.time() if now is None else now) > expires:
        raise ValueError("state vencido")
    return channel_id, user_id
