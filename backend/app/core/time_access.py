"""
Time-Based Access Control

Restricción de login por horario.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)


def check_time_restrictions(
    restrictions: Optional[Dict[str, Any]],
    timestamp: datetime = None,
) -> tuple[bool, Optional[str]]:
    """
    Verifica si el login está dentro del horario permitido.

    Returns:
        (allowed, reason)
    """
    if not restrictions:
        return True, None

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    # Convert to user's timezone if specified
    user_tz = restrictions.get("timezone", "UTC")
    try:
        from zoneinfo import ZoneInfo
        local_time = timestamp.astimezone(ZoneInfo(user_tz))
    except Exception:
        local_time = timestamp

    hour = local_time.hour
    weekday = local_time.weekday()  # 0=Monday

    # Check allowed hours
    allowed_hours = restrictions.get("allowed_hours", [0, 23])
    if isinstance(allowed_hours, list) and len(allowed_hours) == 2:
        start, end = allowed_hours
        if not (start <= hour <= end):
            return False, f"Horario no permitido: {hour}:00 (permitido: {start}:00-{end}:00)"

    # Check blocked days
    blocked_days = restrictions.get("blocked_days", [])
    if weekday in blocked_days:
        days_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return False, f"Día bloqueado: {days_names[weekday]}"

    return True, None
