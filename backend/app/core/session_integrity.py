"""
Session Integrity Service

Anti-tamper para sesiones con nonce rotativo.
Cada request incluye X-Session-Nonce que se rota.
"""

import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.security.models import SessionNonce
from app.core.logger import get_logger

logger = get_logger(__name__)

NONCE_LENGTH = 32
NONCE_ROTATION_INTERVAL_SECONDS = 300  # 5 minutos


def generate_nonce() -> str:
    return secrets.token_hex(NONCE_LENGTH)


async def get_or_create_nonce(db: AsyncSession, session_hash: str) -> str:
    """Obtiene o crea un nonce para la sesión."""
    result = await db.execute(
        select(SessionNonce).where(SessionNonce.session_hash == session_hash)
    )
    sn = result.scalar_one_or_none()

    if sn:
        # Check if rotation needed
        age = (datetime.now(timezone.utc) - sn.rotated_at).total_seconds()
        if age > NONCE_ROTATION_INTERVAL_SECONDS:
            sn.nonce = generate_nonce()
            sn.rotated_at = datetime.now(timezone.utc)
            await db.commit()
    else:
        sn = SessionNonce(
            session_hash=session_hash,
            nonce=generate_nonce(),
        )
        db.add(sn)
        await db.commit()
        await db.refresh(sn)

    return sn.nonce


async def verify_nonce(db: AsyncSession, session_hash: str, nonce: str) -> bool:
    """Verifica que el nonce coincida con el almacenado."""
    result = await db.execute(
        select(SessionNonce).where(SessionNonce.session_hash == session_hash)
    )
    sn = result.scalar_one_or_none()

    if not sn:
        return False
    if sn.nonce != nonce:
        logger.warning(f"Session nonce mismatch for {session_hash}")
        return False
    return True


async def invalidate_session_nonce(db: AsyncSession, session_hash: str) -> None:
    """Invalida el nonce de una sesión (logout o tamper detectado)."""
    result = await db.execute(
        select(SessionNonce).where(SessionNonce.session_hash == session_hash)
    )
    sn = result.scalar_one_or_none()
    if sn:
        sn.nonce = "INVALIDATED"
        await db.commit()
