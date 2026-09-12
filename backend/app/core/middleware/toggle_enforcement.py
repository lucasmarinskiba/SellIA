"""Toggle Enforcement Middleware

Chequea si un toggle está enabled y dentro de límite antes de ejecutar endpoints.
"""

import json
from uuid import UUID
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, List

from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.domains.automations.models import AutomationToggle


# Mapeo de rutas → toggle_key que requireren
PROTECTED_ROUTES: Dict[str, str] = {
    "/api/v1/computer_use": "feature:computer_use",
    "/api/v1/sales_agents/lead_score": "agent:lead_scorer",
    "/api/v1/sales_agents/negotiate": "agent:negotiation",
    "/api/v1/email_sequences/send": "automation:email_sequences",
    "/api/v1/fomo": "automation:fomo_campaigns",
    "/api/v1/sms": "automation:sms_marketing",
    "/api/v1/dynamic_pricing": "feature:dynamic_pricing",
    "/api/v1/predictive": "feature:predictive_analytics",
}


def _map_request_to_toggle(request_path: str) -> Optional[str]:
    """Mapea request path → toggle_key requerido. Retorna None si no requiere check."""
    for protected_prefix, toggle_key in PROTECTED_ROUTES.items():
        if request_path.startswith(protected_prefix):
            return toggle_key
    return None


def _extract_business_id(request: Request) -> Optional[UUID]:
    """Extrae business_id del request (query param o header)."""
    # Try query param first
    business_id_str = request.query_params.get("business_id")
    if business_id_str:
        try:
            return UUID(business_id_str)
        except ValueError:
            pass

    # Try header
    business_id_header = request.headers.get("X-Business-ID")
    if business_id_header:
        try:
            return UUID(business_id_header)
        except ValueError:
            pass

    # Try from JSON body (if POST/PATCH)
    if request.method in ["POST", "PATCH"]:
        try:
            # Note: this is a heuristic, body might not be parsed yet
            # Better approach: use a Depends(get_business_id) in each endpoint
            pass
        except Exception:
            pass

    return None


async def toggle_enforcement_middleware(request: Request, call_next: Callable) -> any:
    """Middleware que chequea toggles antes de ejecutar requests."""

    # Determinar si este endpoint requiere toggle check
    required_toggle = _map_request_to_toggle(request.url.path)
    if not required_toggle:
        # No requiere check, continuar
        return await call_next(request)

    # Intentar extraer business_id
    business_id = _extract_business_id(request)
    if not business_id:
        # Sin business_id, denegar acceso (de todos modos, probablemente va a fallar auth después)
        raise HTTPException(
            status_code=400,
            detail="business_id requerido en query param o header X-Business-ID",
        )

    # Obtener DB session y chequear toggle
    db_session = None
    try:
        db_session = None
        async for db in get_db():
            db_session = db
            break

        if not db_session:
            # Si no hay DB, continuar (fallará en endpoint si requiere DB)
            return await call_next(request)

        # Buscar toggle
        result = await db_session.execute(
            select(AutomationToggle).where(
                AutomationToggle.business_id == business_id,
                AutomationToggle.toggle_key == required_toggle,
            )
        )
        toggle = result.scalar_one_or_none()

        # Validar que esté habilitado
        if toggle and not toggle.is_enabled:
            raise HTTPException(
                status_code=403,
                detail=f"Feature '{toggle.display_name}' deshabilitada. Habilita en Control Center.",
            )

        # Validar que no haya alcanzado límite
        if toggle and toggle.monthly_limit:
            if toggle.current_month_usage >= toggle.monthly_limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Límite mensual alcanzado: {toggle.monthly_limit} usos. Intenta el próximo mes.",
                )

        # Ejecutar endpoint
        response = await call_next(request)

        # Si fue exitoso, incrementar contador
        if response.status_code < 400 and toggle and toggle.monthly_limit:
            toggle.current_month_usage += 1
            await db_session.commit()

            # Check if usage reached/exceeded limit and send notification
            if toggle.current_month_usage >= toggle.monthly_limit:
                from app.domains.automations.tasks import send_toggle_notification
                try:
                    await send_toggle_notification(
                        db=db_session,
                        toggle_id=str(toggle.id),
                        business_id=str(business_id),
                        event_type="usage_limit_reached",
                        toggle_name=toggle.display_name,
                    )
                except Exception as e:
                    print(f"[toggle_enforcement] Error sending notification: {e}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        # Log pero no bloquear
        print(f"[toggle_enforcement] Error: {e}")
        return await call_next(request)
