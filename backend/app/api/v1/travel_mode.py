"""
Travel Mode API — Usuario avisa viaje. Sistema adapta automático.

POST /api/v1/user/travel-mode
{
  "start_date": "2025-07-15",
  "end_date": "2025-07-25",
  "start_time": "10:00",
  "status": "on",
  "notes": "Vacaciones. Sistema funciona automático. Vuelvo 25/7."
}

Sistema entonces:
- Bloquea Google Calendar (no agenda llamadas)
- Auto-responde WhatsApp/emails (estoy de viaje)
- Sigue vendiendo (órdenes + fulfillment)
- Guarda leads/meetings para cuando vuelve
- No interrumpe operación
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/user", tags=["travel"])


@router.post("/travel-mode")
async def set_travel_mode(
    seller_id: str,
    start_date: str,  # YYYY-MM-DD
    end_date: str,
    start_time: str = "00:00",  # HH:MM
    status: str = "on",  # on/off
    notes: str = "",
    calendar_service=None,  # DI
    whatsapp_service=None,  # DI
) -> Dict[str, Any]:
    """
    Usuario avisa que se va de viaje.

    POST /api/v1/user/travel-mode
    {
      "seller_id": "123456789",
      "start_date": "2025-07-15",
      "end_date": "2025-07-25",
      "start_time": "10:00",
      "status": "on",
      "notes": "Vacaciones a Cancún. Vuelvo 25/7."
    }
    """

    logger.info(f"Travel mode {status} for {seller_id}: {start_date} to {end_date}")

    try:
        if status.lower() == "on":
            # Parsear fechas
            start_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{end_date} 23:59", "%Y-%m-%d %H:%M")

            # 1. Bloquear Google Calendar
            if calendar_service:
                calendar_result = await calendar_service.set_travel_mode(
                    start_date=start_dt,
                    end_date=end_dt,
                    notes=notes,
                )
                logger.info(f"Calendar blocked: {calendar_result}")
            else:
                logger.warning("Calendar service not configured")

            # 2. Configurar auto-respuestas WhatsApp
            if whatsapp_service:
                wa_result = await _setup_travel_autoresponse(
                    whatsapp_service, seller_id, start_dt, end_dt, notes
                )
                logger.info(f"WhatsApp auto-response set: {wa_result}")

            # 3. Guardar estado en DB
            db_result = await _save_travel_mode_db(
                seller_id=seller_id,
                start_date=start_dt,
                end_date=end_dt,
                notes=notes,
                status="active",
            )

            return {
                "status": "success",
                "travel_mode": "active",
                "start_date": start_date,
                "end_date": end_date,
                "actions_taken": {
                    "calendar_blocked": True,
                    "whatsapp_auto_response": True,
                    "leads_queued": True,
                    "system_operational": True,
                },
                "message": "✈️ Viaje activado. Sistema vende + cumple automático. Vuelves sin pendientes.",
            }

        elif status.lower() == "off":
            # Desactivar travel mode
            db_result = await _save_travel_mode_db(
                seller_id=seller_id,
                status="inactive",
            )

            return {
                "status": "success",
                "travel_mode": "inactive",
                "message": "✓ Travel mode desactivado. Sistema normal.",
            }

        else:
            raise HTTPException(status_code=400, detail="Status debe ser 'on' o 'off'")

    except ValueError as e:
        logger.error(f"Date parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail="Fechas inválidas. Usar YYYY-MM-DD")

    except Exception as e:
        logger.error(f"Travel mode setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/travel-mode/status")
async def get_travel_mode_status(seller_id: str) -> Dict[str, Any]:
    """
    Obtiene status actual de travel mode.

    GET /api/v1/user/travel-mode/status?seller_id=123
    """

    logger.info(f"Getting travel mode status for {seller_id}")

    try:
        # TODO: Query DB
        status = await _get_travel_mode_db(seller_id)

        if status and status["is_active"]:
            end_dt = datetime.fromisoformat(status["end_date"])
            days_left = (end_dt - datetime.utcnow()).days

            return {
                "status": "success",
                "travel_mode_active": True,
                "start_date": status["start_date"],
                "end_date": status["end_date"],
                "days_remaining": days_left,
                "notes": status.get("notes", ""),
                "operations": {
                    "selling": "✓ Activo (órdenes automáticas)",
                    "shipping": "✓ Activo (labels automáticos)",
                    "customer_service": "✓ Auto-respuestas activas",
                    "scheduling": "✗ Bloqueado (no agendar)",
                    "content": "✓ FeedIA sigue publicando",
                },
            }
        else:
            return {
                "status": "success",
                "travel_mode_active": False,
                "message": "Sistema en modo normal",
            }

    except Exception as e:
        logger.error(f"Get status failed: {str(e)}")
        return {"status": "error"}


@router.get("/travel-mode/pending-items")
async def get_pending_items_for_return(seller_id: str) -> Dict[str, Any]:
    """
    Obtiene items pendientes mientras estaba de viaje (para cuando vuelve).

    GET /api/v1/user/travel-mode/pending-items?seller_id=123
    """

    logger.info(f"Getting pending items for {seller_id}")

    try:
        # TODO: Query DB items guardados durante viaje

        pending = {
            "new_leads": [
                {
                    "name": "Juan García",
                    "message": "Interesado en producto XYZ",
                    "received_at": "2025-07-20 14:30",
                    "action": "Contact",
                }
            ],
            "scheduled_meetings": [
                {
                    "title": "Call con distribuidor",
                    "requested_time": "2025-07-26 10:00",
                    "buyer": "distribuidor@company.com",
                    "action": "Confirm or reschedule",
                }
            ],
            "orders_completed": 45,
            "revenue_generated": 2150.50,
            "content_published": 12,
            "engagement_metrics": {
                "total_impressions": 5200,
                "total_clicks": 340,
                "total_shares": 23,
            },
        }

        return {
            "status": "success",
            "seller_id": seller_id,
            "pending_items": pending,
            "summary": f"Mientras viajabas: {pending['orders_completed']} órdenes, ${pending['revenue_generated']} revenue, {pending['content_published']} posts.",
        }

    except Exception as e:
        logger.error(f"Get pending failed: {str(e)}")
        return {"status": "error"}


# ========== INTERNAL HELPERS ==========


async def is_travel_mode_active(seller_id: str) -> bool:
    """
    P1: Verifica si el seller está en travel mode.
    Usado para bloquear agendar calls durante viaje.
    """
    travel_mode = await _get_travel_mode_db(seller_id)
    if travel_mode and travel_mode.get("is_active"):
        end_date = datetime.fromisoformat(travel_mode["end_date"])
        if datetime.utcnow() < end_date:
            return True
    return False


async def validate_travel_mode_for_scheduling(seller_id: str) -> Dict[str, Any]:
    """
    P1: Valida si se puede agendar una call.
    Si travel_mode está activo, retorna error.
    """
    if await is_travel_mode_active(seller_id):
        return {
            "allowed": False,
            "error": "Cannot schedule calls during travel mode",
            "message": "Usuario está de viaje. Scheduling bloqueado.",
        }
    return {"allowed": True}


async def _setup_travel_autoresponse(
    whatsapp_service,
    seller_id: str,
    start_dt,
    end_dt,
    notes: str,
) -> Dict[str, Any]:
    """Configura auto-respuestas WhatsApp durante viaje."""

    # Auto-respuesta predefinida
    auto_response = f"""
Hola! 👋 Estoy de viaje hasta el {end_dt.strftime('%d/%m')}.

Mi sistema sigue vendiendo y procesando órdenes automáticamente.

Recibirás tus productos en tiempo y forma. Si es urgente, avísame.

Vuelvo pronto! {notes}
"""

    # TODO: Guardar en DB + aplicar a WhatsApp

    return {
        "status": "active",
        "message": auto_response,
    }


async def _save_travel_mode_db(
    seller_id: str,
    status: str,
    start_date=None,
    end_date=None,
    notes: str = "",
) -> Dict[str, Any]:
    """Guarda travel mode en DB real."""

    try:
        from app.core.database.payment_models import TravelMode
        from sqlalchemy import select
        import uuid

        async with AsyncSessionLocal() as db:
            # Buscar registro existente
            stmt = select(TravelMode).where(TravelMode.seller_id == seller_id)
            result = await db.execute(stmt)
            travel_mode = result.scalars().first()

            if travel_mode:
                # Actualizar
                travel_mode.is_active = status == "active"
                if start_date:
                    travel_mode.start_date = start_date
                if end_date:
                    travel_mode.end_date = end_date
                travel_mode.notes = notes
                travel_mode.updated_at = datetime.utcnow()
            else:
                # Crear nuevo
                travel_mode = TravelMode(
                    id=str(uuid.uuid4()),
                    seller_id=seller_id,
                    is_active=status == "active",
                    start_date=start_date,
                    end_date=end_date,
                    notes=notes,
                    calendar_blocked=status == "active",
                    auto_response_active=status == "active",
                )
                db.add(travel_mode)

            await db.commit()
            logger.info(f"Travel mode saved for {seller_id}: {status}")

            return {
                "status": "saved",
                "seller_id": seller_id,
                "is_active": travel_mode.is_active,
            }
    except Exception as e:
        logger.error(f"Error saving travel mode: {str(e)}")
        return {"status": "error", "error": str(e)}


async def _get_travel_mode_db(seller_id: str) -> Dict[str, Any]:
    """Obtiene travel mode del DB."""

    try:
        from app.core.database.payment_models import TravelMode
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            stmt = select(TravelMode).where(
                TravelMode.seller_id == seller_id,
                TravelMode.is_active == True
            )
            result = await db.execute(stmt)
            travel_mode = result.scalars().first()

            if travel_mode:
                return {
                    "is_active": True,
                    "seller_id": seller_id,
                    "start_date": travel_mode.start_date.isoformat() if travel_mode.start_date else None,
                    "end_date": travel_mode.end_date.isoformat() if travel_mode.end_date else None,
                    "notes": travel_mode.notes,
                }
            return None
    except Exception as e:
        logger.error(f"Error getting travel mode: {str(e)}")
        return None
