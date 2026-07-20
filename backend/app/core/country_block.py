"""
Bloqueo por país configurable.
En producción con Cloudflare, usa CF-IPCountry.
"""

import os
from typing import Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.security.models import SecurityConfig


async def get_blocked_countries() -> Set[str]:
    """Obtiene la lista de países bloqueados desde la configuración de seguridad."""
    # Prioridad 1: variable de entorno
    env_blocked = os.getenv("BLOCKED_COUNTRIES", "")
    if env_blocked:
        return {c.strip().upper() for c in env_blocked.split(",") if c.strip()}

    # Prioridad 2: base de datos
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(SecurityConfig))
            config = result.scalar_one_or_none()
            if config and config.blocked_countries:
                return {c.strip().upper() for c in config.blocked_countries.split(",") if c.strip()}
    except Exception:
        pass

    return set()


def is_country_blocked(country_code: Optional[str], blocked: Set[str]) -> bool:
    """Verifica si un código de país está bloqueado."""
    if not country_code or not blocked:
        return False
    return country_code.strip().upper() in blocked
