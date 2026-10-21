"""
Session Integrity Service

Anti-tamper para sesiones con nonce rotativo.
Cada request incluye X-Session-Nonce que se rota.
"""

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.security.models import SessionNonce

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
        age = (datetime.now(UTC) - sn.rotated_at).total_seconds()
        if age > NONCE_ROTATION_INTERVAL_SECONDS:
            sn.nonce = generate_nonce()
            sn.rotated_at = datetime.now(UTC)
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
