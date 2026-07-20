"""
Trusted Device Manager

Gestiona dispositivos de confianza del usuario.
- Detecta dispositivos nuevos
- Envía email de confirmación
- Permite bloquear/remover dispositivos
- Recordar dispositivo por 30 días
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.domains.security.models import TrustedDevice
from app.core.logger import get_logger

logger = get_logger(__name__)


def get_device_fingerprint(ip: str, user_agent: Optional[str], accept_lang: Optional[str]) -> str:
    """Genera un fingerprint del dispositivo."""
    import hashlib
    raw = f"{ip}:{user_agent or ''}:{accept_lang or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def get_trusted_device(
    db: AsyncSession,
    user_id: uuid.UUID,
    fingerprint: str,
) -> Optional[TrustedDevice]:
    """Obtiene un dispositivo de confianza por fingerprint."""
    result = await db.execute(
        select(TrustedDevice).where(
            TrustedDevice.user_id == user_id,
            TrustedDevice.device_fingerprint == fingerprint,
        )
    )
    return result.scalar_one_or_none()


async def record_device_login(
    db: AsyncSession,
    user_id: uuid.UUID,
    ip: str,
    user_agent: Optional[str],
    country: Optional[str],
) -> tuple[TrustedDevice, bool]:
    """
    Registra un login desde un dispositivo.

    Returns:
        (device, is_new) — is_new=True si es la primera vez que se ve este dispositivo
    """
    fingerprint = get_device_fingerprint(ip, user_agent, None)
    device = await get_trusted_device(db, user_id, fingerprint)
    is_new = False

    if device:
        device.last_seen_at = datetime.now(timezone.utc)
        device.ip_address = ip
        await db.commit()
    else:
        device = TrustedDevice(
            user_id=user_id,
            device_fingerprint=fingerprint,
            device_name=_parse_device_name(user_agent),
            os=_parse_os(user_agent),
            browser=_parse_browser(user_agent),
            ip_address=ip,
            country=country,
            is_trusted=False,  # requiere confirmación
        )
        db.add(device)
        await db.commit()
        await db.refresh(device)
        is_new = True
        logger.info(f"New device detected for user {user_id}: {fingerprint}")

    return device, is_new


async def trust_device(db: AsyncSession, device_id: uuid.UUID) -> Optional[TrustedDevice]:
    """Marca un dispositivo como de confianza."""
    result = await db.execute(select(TrustedDevice).where(TrustedDevice.id == device_id))
    device = result.scalar_one_or_none()
    if device:
        device.is_trusted = True
        device.is_blocked = False
        await db.commit()
        await db.refresh(device)
    return device


async def block_device(db: AsyncSession, device_id: uuid.UUID) -> Optional[TrustedDevice]:
    """Bloquea un dispositivo."""
    result = await db.execute(select(TrustedDevice).where(TrustedDevice.id == device_id))
    device = result.scalar_one_or_none()
    if device:
        device.is_blocked = True
        device.is_trusted = False
        await db.commit()
        await db.refresh(device)
    return device


async def list_user_devices(db: AsyncSession, user_id: uuid.UUID) -> List[TrustedDevice]:
    """Lista todos los dispositivos de un usuario."""
    result = await db.execute(
        select(TrustedDevice).where(TrustedDevice.user_id == user_id)
        .order_by(desc(TrustedDevice.last_seen_at))
    )
    return list(result.scalars().all())


async def is_device_trusted(db: AsyncSession, user_id: uuid.UUID, fingerprint: str) -> bool:
    """Verifica si un dispositivo es de confianza."""
    device = await get_trusted_device(db, user_id, fingerprint)
    if not device:
        return False
    if device.is_blocked:
        return False
    if device.is_trusted:
        # Check if still within remember period
        if device.remember_days:
            expiry = device.first_seen_at + timedelta(days=device.remember_days)
            if datetime.now(timezone.utc) > expiry:
                device.is_trusted = False
                return False
        return True
    return False


async def check_suspicious_device_activity(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Detecta si hay más de 5 dispositivos nuevos en 24h."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(TrustedDevice).where(
            TrustedDevice.user_id == user_id,
            TrustedDevice.first_seen_at >= since,
            TrustedDevice.is_trusted == False,
        )
    )
    new_devices = result.scalars().all()
    return len(new_devices) > 5


def _parse_device_name(ua: Optional[str]) -> str:
    if not ua:
        return "Unknown"
    if "iPhone" in ua:
        return "iPhone"
    if "iPad" in ua:
        return "iPad"
    if "Android" in ua:
        return "Android Device"
    if "Windows" in ua:
        return "Windows PC"
    if "Mac" in ua:
        return "Mac"
    return "Unknown Device"


def _parse_os(ua: Optional[str]) -> str:
    if not ua:
        return "Unknown"
    if "Windows" in ua:
        return "Windows"
    if "Mac OS" in ua:
        return "macOS"
    if "Linux" in ua:
        return "Linux"
    if "Android" in ua:
        return "Android"
    if "iOS" in ua or "iPhone" in ua:
        return "iOS"
    return "Unknown"


def _parse_browser(ua: Optional[str]) -> str:
    if not ua:
        return "Unknown"
    if "Chrome" in ua and "Edg" not in ua:
        return "Chrome"
    if "Firefox" in ua:
        return "Firefox"
    if "Safari" in ua and "Chrome" not in ua:
        return "Safari"
    if "Edg" in ua:
        return "Edge"
    return "Unknown"
