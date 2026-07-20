"""
Escalation Handler — Ruta problemas a humanos.

Triggers para escalación:
- Refund request (need verification)
- Complaint (need personalization)
- Complex negotiation (stuck on price)
- Payment failed (fraud check?)
- Regulatory (unknown law applies)
- Volume surge (queue backing up)
- Max retries exceeded

Notificación: email, SMS, Slack, dashboard
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class Escalation:
    """Representa escalación a humano."""
    id: str
    job_id: str
    job_type: str
    severity: str  # critical, high, medium, low
    reason: str
    created_at: datetime
    assigned_to: Optional[str] = None
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    notifications_sent: List[str] = None

    def __post_init__(self):
        if self.notifications_sent is None:
            self.notifications_sent = []


class EscalationHandler:
    """Gestiona escalaciones a humanos."""

    def __init__(self, notification_service=None):
        self.notification_service = notification_service
        self.escalations: Dict[str, Escalation] = {}
        self.escalation_queue: List[Escalation] = []
        self.lock = asyncio.Lock()

    async def escalate(
        self,
        job: Any,
        reason: str,
        severity: str = "high",
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Escalates job a revisión humana.

        Args:
            job: Job a escalar
            reason: Razón de escalación
            severity: critical, high, medium, low
            context: Información adicional

        Returns:
            Escalation ID
        """
        import uuid

        escalation = Escalation(
            id=str(uuid.uuid4()),
            job_id=job.id,
            job_type=job.job_type.value,
            severity=severity,
            reason=reason,
            created_at=datetime.utcnow(),
        )

        async with self.lock:
            self.escalations[escalation.id] = escalation
            self.escalation_queue.append(escalation)

        logger.warning(
            f"Job escalated: {job.id} (severity: {severity}, reason: {reason})"
        )

        # Notify humans
        await self.notify_human(escalation, context)

        return escalation.id

    async def notify_human(
        self,
        escalation: Escalation,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Notifica humano sobre escalación."""
        message = self._build_notification_message(escalation, context)

        notifications = []

        # Email
        if self.notification_service:
            try:
                await self.notification_service.send_email(
                    to="escalations@company.com",
                    subject=f"[ESCALATION] {escalation.severity.upper()}: {escalation.reason}",
                    body=message,
                )
                notifications.append("email")
            except Exception as e:
                logger.error(f"Failed to send escalation email: {str(e)}")

        # Slack (if configured)
        try:
            await self._send_slack_alert(escalation, message)
            notifications.append("slack")
        except Exception as e:
            logger.debug(f"Slack notification not available: {str(e)}")

        # SMS for critical
        if escalation.severity == "critical" and self.notification_service:
            try:
                await self.notification_service.send_sms(
                    to="+5491123456789",  # TODO: Get from config
                    message=f"CRITICAL ESCALATION: {escalation.reason}",
                )
                notifications.append("sms")
            except Exception as e:
                logger.debug(f"SMS notification failed: {str(e)}")

        escalation.notifications_sent = notifications
        logger.info(f"Escalation notified via: {', '.join(notifications)}")

    async def resolve_escalation(
        self,
        escalation_id: str,
        resolution: str,
        assigned_to: Optional[str] = None,
    ) -> bool:
        """Marca escalación como resuelta."""
        async with self.lock:
            if escalation_id not in self.escalations:
                return False

            escalation = self.escalations[escalation_id]
            escalation.resolved = True
            escalation.resolution = resolution
            escalation.resolved_at = datetime.utcnow()
            escalation.assigned_to = assigned_to

            logger.info(f"Escalation resolved: {escalation_id}")
            return True

    async def get_escalation(self, escalation_id: str) -> Optional[Escalation]:
        """Obtiene detalles de escalación."""
        async with self.lock:
            return self.escalations.get(escalation_id)

    async def get_pending_escalations(self, limit: int = 50) -> List[Escalation]:
        """Obtiene escalaciones pendientes."""
        async with self.lock:
            pending = [e for e in self.escalation_queue if not e.resolved]
            # Sort by severity + creation time
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            pending.sort(
                key=lambda e: (
                    severity_order.get(e.severity, 99),
                    e.created_at,
                )
            )
            return pending[:limit]

    async def get_escalation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Estadísticas de escalaciones."""
        async with self.lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent = [
                e for e in self.escalations.values()
                if e.created_at >= cutoff
            ]

            by_severity = {
                "critical": len([e for e in recent if e.severity == "critical"]),
                "high": len([e for e in recent if e.severity == "high"]),
                "medium": len([e for e in recent if e.severity == "medium"]),
                "low": len([e for e in recent if e.severity == "low"]),
            }

            by_type = {}
            for escalation in recent:
                by_type[escalation.job_type] = by_type.get(escalation.job_type, 0) + 1

            pending = len([e for e in recent if not e.resolved])
            resolved = len([e for e in recent if e.resolved])

            return {
                "total": len(recent),
                "pending": pending,
                "resolved": resolved,
                "by_severity": by_severity,
                "by_type": by_type,
                "avg_resolution_time": self._calculate_avg_resolution_time(recent),
            }

    def _build_notification_message(
        self,
        escalation: Escalation,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Construye mensaje de notificación."""
        message = f"""
ESCALATION ALERT
================
ID: {escalation.id}
Job: {escalation.job_id}
Type: {escalation.job_type}
Severity: {escalation.severity.upper()}
Reason: {escalation.reason}
Created: {escalation.created_at.isoformat()}

ACTION REQUIRED: Review and resolve this escalation in the dashboard.

"""
        if context:
            message += "CONTEXT:\n"
            for key, value in context.items():
                message += f"  {key}: {value}\n"

        return message

    async def _send_slack_alert(self, escalation: Escalation, message: str) -> None:
        """Envía alerta a Slack."""
        # TODO: Implement Slack integration
        logger.debug("Slack alert would be sent here")

    @staticmethod
    def _calculate_avg_resolution_time(escalations: List[Escalation]) -> Optional[float]:
        """Calcula tiempo promedio de resolución."""
        resolved = [e for e in escalations if e.resolved and e.resolved_at]
        if not resolved:
            return None

        total_time = sum(
            (e.resolved_at - e.created_at).total_seconds()
            for e in resolved
        )
        return total_time / len(resolved)

    async def cleanup_old(self, days: int = 30) -> int:
        """Limpia escalaciones viejas."""
        async with self.lock:
            cutoff = datetime.utcnow() - timedelta(days=days)
            original_count = len(self.escalations)

            escalations_to_keep = {
                eid: e for eid, e in self.escalations.items()
                if e.created_at >= cutoff or not e.resolved
            }

            removed = original_count - len(escalations_to_keep)
            self.escalations = escalations_to_keep

            logger.info(f"Escalations cleanup: {removed} old entries removed")
            return removed


class EscalationPolicy:
    """Define policies para qué debe escalarse."""

    # Severity por error pattern
    ERROR_SEVERITY = {
        "payment_failed": "critical",
        "inventory_out_of_sync": "high",
        "platform_api_error": "high",
        "customer_complaint": "high",
        "refund_request": "high",
        "platform_timeout": "medium",
        "rate_limit": "low",
    }

    # Auto-escalate después de N retries
    AUTO_ESCALATE_AFTER_RETRIES = {
        "post_product": 3,
        "process_payment": 2,
        "sync_inventory": 2,
        "respond_inquiry": 1,
    }

    @classmethod
    def should_escalate(cls, job: Any, error: str) -> tuple[bool, str, str]:
        """
        Determina si un job debe escalarse.

        Returns:
            (should_escalate, severity, reason)
        """
        # Check if max retries exceeded
        if job.attempts >= job.max_retries:
            job_type_val = job.job_type.value
            max_retries = cls.AUTO_ESCALATE_AFTER_RETRIES.get(job_type_val, 3)
            if job.attempts >= max_retries:
                return (
                    True,
                    "high",
                    f"Max retries exceeded for {job_type_val}",
                )

        # Check error patterns
        for pattern, severity in cls.ERROR_SEVERITY.items():
            if pattern.lower() in error.lower():
                return (True, severity, f"Error pattern detected: {pattern}")

        return (False, "low", "")
