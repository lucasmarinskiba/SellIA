"""
IP Allowlist Service

Restricción de login por IP para cuentas Enterprise/Pro.
"""

import uuid
import ipaddress
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.security.models import IPAllowlist
from app.core.logger import get_logger

logger = get_logger(__name__)


async def add_ip(
    db: AsyncSession,
    user_id: uuid.UUID,
    ip_address: str,
    label: Optional[str] = None,
) -> IPAllowlist:
    """Agrega una IP a la lista blanca."""
    entry = IPAllowlist(
        user_id=user_id,
        ip_address=ip_address,
        label=label or ip_address,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def remove_ip(db: AsyncSession, entry_id: uuid.UUID) -> bool:
    """Elimina una IP de la lista blanca."""
    result = await db.execute(select(IPAllowlist).where(IPAllowlist.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        return False
    await db.delete(entry)
    await db.commit()
    return True


async def list_ips(db: AsyncSession, user_id: uuid.UUID) -> List[IPAllowlist]:
    """Lista IPs permitidas."""
    result = await db.execute(
        select(IPAllowlist).where(
            IPAllowlist.user_id == user_id,
            IPAllowlist.is_active == True,
        )
    )
    return list(result.scalars().all())


async def is_ip_allowed(db: AsyncSession, user_id: uuid.UUID, ip_address: str) -> bool:
    """Verifica si una IP está permitida."""
    entries = await list_ips(db, user_id)
    if not entries:
        return True  # No hay restricciones

    for entry in entries:
        if _ip_matches(entry.ip_address, ip_address):
            return True
    return False


def _ip_matches(pattern: str, ip: str) -> bool:
    """Verifica si una IP coincide con un patrón (IP exacta o CIDR)."""
    try:
        if "/" in pattern:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(pattern, strict=False)
        return pattern == ip
    except ValueError:
        return pattern == ip
