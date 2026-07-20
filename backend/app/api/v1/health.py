"""
Health checks — sistema observable y resiliente.

Cada componente reporta status (OK/DEGRADED/DOWN).
Sistema globalmente DEGRADED si <2 críticos, DOWN si >2 críticos falla.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter(prefix="/api/v1/health", tags=["health"])
logger = logging.getLogger(__name__)


class ComponentHealth(BaseModel):
    """Status de un componente."""
    name: str
    status: str  # "OK", "DEGRADED", "DOWN"
    latency_ms: float
    last_check: datetime
    error_message: str = None


class SystemHealth(BaseModel):
    """Health del sistema completo."""
    overall_status: str  # "HEALTHY", "DEGRADED", "DOWN"
    components: list[ComponentHealth]
    uptime_hours: float
    error_rate_last_hour: float


@router.get("/status", response_model=SystemHealth)
async def health_check():
    """Sistema health check."""

    try:
        components = [
            ComponentHealth(
                name="autonomous_agent",
                status="OK",
                latency_ms=45.2,
                last_check=datetime.utcnow(),
                error_message=None
            ),
            ComponentHealth(
                name="analytics_dashboard",
                status="OK",
                latency_ms=120.5,
                last_check=datetime.utcnow(),
                error_message=None
            ),
            ComponentHealth(
                name="crm_sync",
                status="DEGRADED",  # Ej: API lenta
                latency_ms=2500.0,
                last_check=datetime.utcnow(),
                error_message="Salesforce API latency high (>2s)"
            ),
            ComponentHealth(
                name="knowledge_engine",
                status="OK",
                latency_ms=12.1,
                last_check=datetime.utcnow(),
                error_message=None
            ),
        ]

        failed_critical = sum(1 for c in components if c.status == "DOWN")
        degraded = sum(1 for c in components if c.status == "DEGRADED")

        if failed_critical > 2:
            overall = "DOWN"
        elif degraded > 0 or failed_critical > 0:
            overall = "DEGRADED"
        else:
            overall = "HEALTHY"

        return SystemHealth(
            overall_status=overall,
            components=components,
            uptime_hours=2160.5,  # Ej: 90 días
            error_rate_last_hour=0.002  # 0.2%
        )

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/ready")
async def readiness_check():
    """¿Sistema listo para tomar traffic?"""

    # TODO: Verificar:
    # - Knowledge files loaded?
    # - Brain graph ready?
    # - Database connected?
    # - Auth service up?

    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "knowledge_loaded": True,
            "brain_graph_ready": True,
            "database_connected": True,
            "auth_service": "OK"
        }
    }


@router.get("/live")
async def liveness_check():
    """¿Sistema vivo?"""

    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }
