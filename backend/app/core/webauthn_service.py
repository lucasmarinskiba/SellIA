"""
WebAuthn / Passkeys Service

Registro y autenticación con passkeys usando webauthn library.
"""

import uuid
import base64
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.security.models import WebAuthnCredential
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Configuración WebAuthn
RP_ID = settings.WEBAUTHN_RP_ID or "localhost"
RP_NAME = settings.WEBAUTHN_RP_NAME or "SellIA"
RP_ORIGIN = settings.WEBAUTHN_RP_ORIGIN or "http://localhost:3000"


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _base64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def generate_registration_options(user_id: uuid.UUID, username: str) -> Dict[str, Any]:
    """Genera opciones para registrar un passkey."""
    challenge = _base64url_encode(uuid.uuid4().bytes)
    user_id_b64 = _base64url_encode(user_id.bytes)

    return {
        "challenge": challenge,
        "rp": {"id": RP_ID, "name": RP_NAME},
        "user": {
            "id": user_id_b64,
            "name": username,
            "displayName": username,
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},   # ES256
            {"type": "public-key", "alg": -257}, # RS256
        ],
        "authenticatorSelection": {
            "residentKey": "preferred",
            "userVerification": "preferred",
        },
        "attestation": "none",
    }


def generate_authentication_options() -> Dict[str, Any]:
    """Genera opciones para autenticar con passkey."""
    challenge = _base64url_encode(uuid.uuid4().bytes)
    return {
        "challenge": challenge,
        "rpId": RP_ID,
        "userVerification": "preferred",
    }


async def register_credential(
    db: AsyncSession,
    user_id: uuid.UUID,
    credential_id: str,
    public_key: str,
    sign_count: int = 0,
    device_name: Optional[str] = None,
) -> WebAuthnCredential:
    """Registra una credencial WebAuthn."""
    # Check if already exists
    result = await db.execute(
        select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.public_key = public_key
        existing.sign_count = sign_count
        existing.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing

    cred = WebAuthnCredential(
        user_id=user_id,
        credential_id=credential_id,
        public_key=public_key,
        sign_count=sign_count,
        device_name=device_name or "Passkey",
    )
    db.add(cred)
    await db.commit()
    await db.refresh(cred)
    logger.info(f"WebAuthn credential registered for user {user_id}")
    return cred


async def get_user_credentials(db: AsyncSession, user_id: uuid.UUID) -> list[WebAuthnCredential]:
    """Obtiene las credenciales de un usuario."""
    result = await db.execute(
        select(WebAuthnCredential).where(
            WebAuthnCredential.user_id == user_id,
            WebAuthnCredential.is_active == True,
        )
    )
    return list(result.scalars().all())


async def verify_assertion(
    db: AsyncSession,
    credential_id: str,
    new_sign_count: int,
) -> bool:
    """Verifica y actualiza el sign count de una credencial."""
    result = await db.execute(
        select(WebAuthnCredential).where(
            WebAuthnCredential.credential_id == credential_id,
            WebAuthnCredential.is_active == True,
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        return False

    # Anti-replay: sign count must increase
    if new_sign_count <= cred.sign_count:
        logger.warning(f"Possible replay attack: sign count {new_sign_count} <= {cred.sign_count}")
        return False

    cred.sign_count = new_sign_count
    cred.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    return True


async def remove_credential(db: AsyncSession, cred_id: uuid.UUID) -> bool:
    """Elimina una credencial."""
    result = await db.execute(select(WebAuthnCredential).where(WebAuthnCredential.id == cred_id))
    cred = result.scalar_one_or_none()
    if not cred:
        return False
    await db.delete(cred)
    await db.commit()
    return True
