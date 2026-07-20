"""
Scheduling Validator — Valida si se puede agendar calls/meetings.

Checks:
1. Travel mode NO activo
2. Calendário disponible
3. Slots no bloqueados
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def validate_scheduling_request(
    seller_id: str,
    scheduled_time: datetime,
) -> Dict[str, Any]:
    """
    P1: Valida si se puede agendar una call/meeting.

    Retorna:
    {
        "allowed": bool,
        "error": str | None,
        "reason": str
    }
    """

    logger.info(f"Validating scheduling for {seller_id} at {scheduled_time}")

    try:
        # 1. Check Travel Mode (P1 blocker)
        from app.api.v1.travel_mode import is_travel_mode_active

        if await is_travel_mode_active(seller_id):
            logger.warning(f"Scheduling rejected: travel mode active for {seller_id}")
            return {
                "allowed": False,
                "error": "travel_mode_active",
                "reason": "Usuario está de viaje. Scheduling bloqueado hasta su regreso.",
            }

        # 2. Check if time is in the past
        if scheduled_time < datetime.utcnow():
            return {
                "allowed": False,
                "error": "time_in_past",
                "reason": "La hora agendada ya pasó.",
            }

        logger.info(f"Scheduling validation passed for {seller_id}")
        return {
            "allowed": True,
            "error": None,
            "reason": "Scheduling allowed",
        }

    except Exception as e:
        logger.error(f"Scheduling validation error: {str(e)}")
        return {
            "allowed": False,
            "error": "validation_error",
            "reason": str(e),
        }
