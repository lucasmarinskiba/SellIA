"""
System Analyzer

Recolecta métricas, errores, y datos de todo el sistema para generar
un System Health Report que alimenta al Improvement Generator.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)


class SystemHealthReport:
    """Reporte de salud del sistema generado periódicamente."""

    def __init__(self):
        self.id = uuid.uuid4()
        self.generated_at = datetime.now(UTC)
        self.errors: list[dict[str, Any]] = []
        self.metrics: dict[str, Any] = {}
        self.conversation_failures = 0
        self.unresolved_tickets = 0
        self.top_feedback_themes: list[str] = []
        self.slow_endpoints: list[dict[str, Any]] = []
        self.recommendations: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "generated_at": self.generated_at.isoformat(),
            "errors": self.errors,
            "metrics": self.metrics,
            "conversation_failures": self.conversation_failures,
            "unresolved_tickets": self.unresolved_tickets,
            "top_feedback_themes": self.top_feedback_themes,
            "slow_endpoints": self.slow_endpoints,
            "recommendations": self.recommendations,
        }


async def generate_health_report(db: AsyncSession) -> SystemHealthReport:
    """Genera un reporte completo de salud del sistema."""
    report = SystemHealthReport()

    # 1. Métricas de endpoints (requiere Prometheus metrics en DB o logs)
    report.metrics = await _collect_prometheus_metrics()

    # 2. Tickets de soporte no resueltos
    try:
        from app.domains.support.models import SupportTicket, TicketStatus
        result = await db.execute(
            select(func.count()).select_from(SupportTicket).where(
                SupportTicket.status.in_([TicketStatus.OPEN, TicketStatus.ESCALATED])
            )
        )
        report.unresolved_tickets = result.scalar() or 0
    except Exception as e:
        logger.warning(f"Could not collect ticket metrics: {e}", exc_info=True)

    # 3. Feedback themes (top categorías reportadas)
    try:
        from app.domains.feedback.models import UserFeedback
        result = await db.execute(
            select(UserFeedback.category, func.count())
            .where(UserFeedback.created_at >= datetime.now(UTC) - timedelta(days=7))
            .group_by(UserFeedback.category)
            .order_by(desc(func.count()))
            .limit(5)
        )
        report.top_feedback_themes = [f"{cat}: {count}" for cat, count in result.all() if cat]
    except Exception as e:
        logger.warning(f"Could not collect feedback themes: {e}", exc_info=True)

    # 4. Conversaciones fallidas (sin respuesta AI)
    try:
        from app.domains.channels.models import Message
        result = await db.execute(
            select(func.count()).select_from(Message).where(
                Message.direction == "inbound",
                Message.created_at >= datetime.now(UTC) - timedelta(days=1),
                Message.content == ""  # fallback: no outbound response
            )
        )
        report.conversation_failures = result.scalar() or 0
    except Exception as e:
        logger.warning(f"Could not collect conversation metrics: {e}", exc_info=True)

    # 5. Errores recientes (de logs)
    report.errors = await _collect_recent_errors()

    # 6. Recomendaciones automáticas básicas
    report.recommendations = _generate_basic_recommendations(report)

    logger.info(f"System health report generated: {report.unresolved_tickets} unresolved tickets, {len(report.top_feedback_themes)} feedback themes")
    return report


async def _collect_prometheus_metrics() -> dict[str, Any]:
    """Intenta recolectar métricas de Prometheus."""
    metrics = {}
    try:
        # Estas métricas vendrían de Prometheus en producción
        # Por ahora, placeholders que se llenan con los contadores del backend
        from app.core.metrics import (
            SELLIA_ACTIVE_SESSIONS,
            SELLIA_FAILED_LOGINS,
            SELLIA_GEOFENCE_VIOLATIONS,
            SELLIA_LOGINS,
            SELLIA_NEW_DEVICES,
        )
        metrics["total_logins"] = SELLIA_LOGINS._value.sum() if hasattr(SELLIA_LOGINS, '_value') else 0
        metrics["failed_logins"] = SELLIA_FAILED_LOGINS._value.sum() if hasattr(SELLIA_FAILED_LOGINS, '_value') else 0
        metrics["geofence_violations"] = SELLIA_GEOFENCE_VIOLATIONS._value if hasattr(SELLIA_GEOFENCE_VIOLATIONS, '_value') else 0
        metrics["new_devices"] = SELLIA_NEW_DEVICES._value if hasattr(SELLIA_NEW_DEVICES, '_value') else 0
        metrics["active_sessions"] = SELLIA_ACTIVE_SESSIONS._value.get() if hasattr(SELLIA_ACTIVE_SESSIONS, '_value') else 0
    except Exception as e:
        logger.warning(f"Could not collect Prometheus metrics: {e}", exc_info=True)
    return metrics


async def _collect_recent_errors() -> list[dict[str, Any]]:
    """Recolecta errores recientes de los logs."""
    # En producción, esto vendría de ELK/Loki
    # Por ahora retornamos lista vacía
    return []


def _generate_basic_recommendations(report: SystemHealthReport) -> list[str]:
    """Genera recomendaciones básicas basadas en el reporte."""
    recs = []
    if report.unresolved_tickets > 10:
        recs.append(f"Hay {report.unresolved_tickets} tickets sin resolver. Considerar aumentar el equipo de soporte o mejorar las respuestas automáticas de IA.")
    if report.conversation_failures > 20:
        recs.append(f"{report.conversation_failures} conversaciones fallidas en 24h. Revisar configuración de agentes IA y prompts.")
    if len(report.top_feedback_themes) > 0:
        recs.append(f"Temas de feedback más frecuentes: {', '.join(report.top_feedback_themes[:3])}.")
    return recs
