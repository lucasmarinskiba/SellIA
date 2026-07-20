"""Pilar 2 — Auto-Reparación (Self-Repair)

Identifica fallas, previene caídas críticas y aplica soluciones automáticas
antes de que el usuario las note. Opera de forma continua en background.
"""

from __future__ import annotations

import uuid
import asyncio
from typing import Any, Optional
from enum import Enum
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_

from app.core.logger import get_logger

logger = get_logger(__name__)


class FaultType(str, Enum):
    WORKFLOW_STUCK = "workflow_stuck"
    CHANNEL_DISCONNECTED = "channel_disconnected"
    SEQUENCE_FAILED = "sequence_failed"
    DEAL_ORPHANED = "deal_orphaned"
    API_PROVIDER_DOWN = "api_provider_down"
    DB_CONNECTION_LOST = "db_connection_lost"
    TASK_QUEUE_BLOCKED = "task_queue_blocked"
    CONVERSATION_STUCK = "conversation_stuck"
    AGENT_UNRESPONSIVE = "agent_unresponsive"


class RepairStatus(str, Enum):
    DETECTED = "detected"
    REPAIRING = "repairing"
    REPAIRED = "repaired"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class FaultReport:
    fault_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    fault_type: FaultType = FaultType.WORKFLOW_STUCK
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    affected_id: Optional[str] = None
    business_id: Optional[str] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: RepairStatus = RepairStatus.DETECTED
    repair_attempts: int = 0
    repair_log: list[str] = field(default_factory=list)
    resolved_at: Optional[datetime] = None


class SelfRepairEngine:
    """Motor de auto-reparación del sistema SellIA."""

    MAX_REPAIR_ATTEMPTS = 3
    STUCK_WORKFLOW_THRESHOLD_MINUTES = 30
    STUCK_CONVERSATION_THRESHOLD_HOURS = 48
    ORPHANED_DEAL_THRESHOLD_DAYS = 7

    def __init__(self, db: AsyncSession):
        self.db = db
        self._active_faults: dict[str, FaultReport] = {}
        self._repair_history: list[FaultReport] = []

    async def run_repair_cycle(self, business_id: Optional[uuid.UUID] = None) -> dict[str, Any]:
        """Ejecuta un ciclo completo de diagnóstico y reparación."""
        logger.info("[SelfRepair] Iniciando ciclo de auto-reparación")

        detected: list[FaultReport] = []
        repaired: list[FaultReport] = []
        failed: list[FaultReport] = []
        escalated: list[FaultReport] = []

        # Detección de fallas en paralelo
        fault_groups = await asyncio.gather(
            self._detect_stuck_workflows(business_id),
            self._detect_orphaned_deals(business_id),
            self._detect_stuck_conversations(business_id),
            self._detect_failed_sequences(business_id),
            self._detect_channel_issues(business_id),
            return_exceptions=True,
        )

        for group in fault_groups:
            if isinstance(group, list):
                detected.extend(group)
            elif isinstance(group, Exception):
                logger.warning(f"[SelfRepair] Error en detección: {group}")

        # Reparación de cada falla detectada
        for fault in detected:
            self._active_faults[fault.fault_id] = fault
            result = await self._attempt_repair(fault)

            if result == RepairStatus.REPAIRED:
                repaired.append(fault)
                self._repair_history.append(fault)
            elif result == RepairStatus.FAILED:
                failed.append(fault)
            elif result == RepairStatus.ESCALATED:
                escalated.append(fault)
                await self._notify_owner_of_fault(fault, business_id)

        # Limpiar fallas resueltas del dict activo
        for fault in repaired:
            self._active_faults.pop(fault.fault_id, None)

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detected": len(detected),
            "repaired": len(repaired),
            "failed": len(failed),
            "escalated": len(escalated),
            "active_faults": len(self._active_faults),
            "fault_details": [
                {"id": f.fault_id, "type": f.fault_type, "status": f.status}
                for f in detected
            ],
        }

        logger.info(f"[SelfRepair] Ciclo: detectadas={len(detected)}, reparadas={len(repaired)}, escaladas={len(escalated)}")
        return summary

    # ─────────────────────────────────────────────
    # DETECTORES DE FALLAS
    # ─────────────────────────────────────────────

    async def _detect_stuck_workflows(
        self, business_id: Optional[uuid.UUID]
    ) -> list[FaultReport]:
        """Detecta workflows que llevan demasiado tiempo en ejecución."""
        faults = []
        try:
            from app.domains.automations.models import WorkflowExecution, WorkflowExecutionStatus
            threshold = datetime.now(timezone.utc) - timedelta(
                minutes=self.STUCK_WORKFLOW_THRESHOLD_MINUTES
            )

            query = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.status == WorkflowExecutionStatus.RUNNING,
                    WorkflowExecution.started_at < threshold,
                )
            )
            if business_id:
                query = query.where(WorkflowExecution.business_id == business_id)

            result = await self.db.execute(query.limit(20))
            stuck = result.scalars().all()

            for exe in stuck:
                faults.append(FaultReport(
                    fault_type=FaultType.WORKFLOW_STUCK,
                    severity="medium",
                    description=f"Workflow execution {exe.id} atascado por +{self.STUCK_WORKFLOW_THRESHOLD_MINUTES} min",
                    affected_id=str(exe.id),
                    business_id=str(exe.business_id) if exe.business_id else None,
                ))
        except Exception as e:
            logger.warning(f"[SelfRepair] Error detectando workflows atascados: {e}")
        return faults

    async def _detect_orphaned_deals(
        self, business_id: Optional[uuid.UUID]
    ) -> list[FaultReport]:
        """Detecta deals sin actividad ni asignación por demasiados días."""
        faults = []
        try:
            from app.domains.crm.models import Deal
            threshold = datetime.now(timezone.utc) - timedelta(
                days=self.ORPHANED_DEAL_THRESHOLD_DAYS
            )

            query = select(Deal).where(
                and_(
                    Deal.is_active == True,
                    Deal.updated_at < threshold,
                )
            )
            if business_id:
                query = query.where(Deal.business_id == business_id)

            result = await self.db.execute(query.limit(50))
            orphaned = result.scalars().all()

            for deal in orphaned:
                faults.append(FaultReport(
                    fault_type=FaultType.DEAL_ORPHANED,
                    severity="high",
                    description=f"Deal '{deal.title}' sin actividad hace +{self.ORPHANED_DEAL_THRESHOLD_DAYS} días",
                    affected_id=str(deal.id),
                    business_id=str(deal.business_id) if deal.business_id else None,
                ))
        except Exception as e:
            logger.warning(f"[SelfRepair] Error detectando deals huérfanos: {e}")
        return faults

    async def _detect_stuck_conversations(
        self, business_id: Optional[uuid.UUID]
    ) -> list[FaultReport]:
        """Detecta conversaciones activas sin mensajes por demasiado tiempo."""
        faults = []
        try:
            from app.domains.channels.models import Conversation
            threshold = datetime.now(timezone.utc) - timedelta(
                hours=self.STUCK_CONVERSATION_THRESHOLD_HOURS
            )

            query = select(Conversation).where(
                and_(
                    Conversation.is_active == True,
                    Conversation.last_message_at < threshold,
                    Conversation.needs_human == False,
                )
            )
            if business_id:
                query = query.where(Conversation.business_id == business_id)

            result = await self.db.execute(query.limit(30))
            stuck = result.scalars().all()

            for conv in stuck:
                faults.append(FaultReport(
                    fault_type=FaultType.CONVERSATION_STUCK,
                    severity="medium",
                    description=f"Conversación sin actividad hace +{self.STUCK_CONVERSATION_THRESHOLD_HOURS}h",
                    affected_id=str(conv.id),
                    business_id=str(conv.business_id) if conv.business_id else None,
                ))
        except Exception as e:
            logger.warning(f"[SelfRepair] Error detectando conversaciones atascadas: {e}")
        return faults

    async def _detect_failed_sequences(
        self, business_id: Optional[uuid.UUID]
    ) -> list[FaultReport]:
        """Detecta secuencias de email/mensajes que fallaron."""
        faults = []
        try:
            from app.domains.automations.models import SequenceEmailLog
            threshold = datetime.now(timezone.utc) - timedelta(hours=6)

            query = select(SequenceEmailLog).where(
                and_(
                    SequenceEmailLog.status == "failed",
                    SequenceEmailLog.created_at >= threshold,
                )
            )
            result = await self.db.execute(query.limit(20))
            failed_logs = result.scalars().all()

            if len(failed_logs) > 5:
                faults.append(FaultReport(
                    fault_type=FaultType.SEQUENCE_FAILED,
                    severity="high" if len(failed_logs) > 20 else "medium",
                    description=f"{len(failed_logs)} envíos de secuencia fallaron en las últimas 6h",
                    business_id=str(business_id) if business_id else None,
                ))
        except Exception as e:
            logger.warning(f"[SelfRepair] Error detectando secuencias fallidas: {e}")
        return faults

    async def _detect_channel_issues(
        self, business_id: Optional[uuid.UUID]
    ) -> list[FaultReport]:
        """Detecta canales de comunicación con problemas de conexión."""
        faults = []
        try:
            from app.domains.channels.models import ChannelConnection
            query = select(ChannelConnection).where(
                ChannelConnection.is_active == True,
                ChannelConnection.status == "error",
            )
            if business_id:
                query = query.where(ChannelConnection.business_id == business_id)

            result = await self.db.execute(query)
            errored = result.scalars().all()

            for ch in errored:
                faults.append(FaultReport(
                    fault_type=FaultType.CHANNEL_DISCONNECTED,
                    severity="high",
                    description=f"Canal {ch.platform} en estado de error",
                    affected_id=str(ch.id),
                    business_id=str(ch.business_id) if ch.business_id else None,
                ))
        except Exception as e:
            logger.warning(f"[SelfRepair] Error detectando problemas de canal: {e}")
        return faults

    # ─────────────────────────────────────────────
    # MOTORES DE REPARACIÓN
    # ─────────────────────────────────────────────

    async def _attempt_repair(self, fault: FaultReport) -> RepairStatus:
        """Intenta reparar una falla específica."""
        fault.status = RepairStatus.REPAIRING
        fault.repair_attempts += 1

        repair_handlers = {
            FaultType.WORKFLOW_STUCK: self._repair_stuck_workflow,
            FaultType.DEAL_ORPHANED: self._repair_orphaned_deal,
            FaultType.CONVERSATION_STUCK: self._repair_stuck_conversation,
            FaultType.SEQUENCE_FAILED: self._repair_failed_sequence,
            FaultType.CHANNEL_DISCONNECTED: self._repair_disconnected_channel,
        }

        handler = repair_handlers.get(fault.fault_type)
        if not handler:
            fault.status = RepairStatus.ESCALATED
            return RepairStatus.ESCALATED

        try:
            success = await handler(fault)
            if success:
                fault.status = RepairStatus.REPAIRED
                fault.resolved_at = datetime.now(timezone.utc)
                fault.repair_log.append(f"Reparado exitosamente en intento #{fault.repair_attempts}")
                logger.info(f"[SelfRepair] Falla {fault.fault_type} reparada: {fault.fault_id}")
                return RepairStatus.REPAIRED
            else:
                if fault.repair_attempts >= self.MAX_REPAIR_ATTEMPTS:
                    fault.status = RepairStatus.ESCALATED
                    fault.repair_log.append(f"Escalado tras {fault.repair_attempts} intentos fallidos")
                    return RepairStatus.ESCALATED
                fault.status = RepairStatus.FAILED
                return RepairStatus.FAILED
        except Exception as e:
            fault.repair_log.append(f"Error en reparación: {str(e)[:200]}")
            fault.status = RepairStatus.FAILED
            logger.error(f"[SelfRepair] Error reparando {fault.fault_type}: {e}")
            return RepairStatus.FAILED

    async def _repair_stuck_workflow(self, fault: FaultReport) -> bool:
        """Reinicia o cancela un workflow atascado."""
        try:
            from app.domains.automations.models import WorkflowExecution, WorkflowExecutionStatus
            await self.db.execute(
                update(WorkflowExecution)
                .where(WorkflowExecution.id == uuid.UUID(fault.affected_id))
                .values(
                    status=WorkflowExecutionStatus.FAILED,
                    completed_at=datetime.now(timezone.utc),
                    error_message="Auto-terminado por SelfRepair: timeout de ejecución",
                )
            )
            await self.db.commit()
            fault.repair_log.append("Workflow atascado terminado forzosamente")
            return True
        except Exception as e:
            fault.repair_log.append(f"Error al terminar workflow: {e}")
            return False

    async def _repair_orphaned_deal(self, fault: FaultReport) -> bool:
        """Reactiva un deal huérfano con una alerta y seguimiento."""
        try:
            from app.domains.crm.models import Deal
            await self.db.execute(
                update(Deal)
                .where(Deal.id == uuid.UUID(fault.affected_id))
                .values(
                    updated_at=datetime.now(timezone.utc),
                    notes="[SellIA Auto-Repair] Deal reactivado — sin actividad detectada. Requiere seguimiento.",
                )
            )
            await self.db.commit()
            fault.repair_log.append("Deal actualizado y marcado para seguimiento")
            return True
        except Exception as e:
            fault.repair_log.append(f"Error al reparar deal: {e}")
            return False

    async def _repair_stuck_conversation(self, fault: FaultReport) -> bool:
        """Envía mensaje de reactivación a conversación atascada."""
        try:
            from app.domains.channels.models import Conversation
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == uuid.UUID(fault.affected_id))
                .values(needs_reactivation=True)
            )
            await self.db.commit()
            fault.repair_log.append("Conversación marcada para reactivación automática")
            return True
        except Exception as e:
            fault.repair_log.append(f"Error al marcar conversación: {e}")
            return False

    async def _repair_failed_sequence(self, fault: FaultReport) -> bool:
        """Reinicia los envíos fallidos de secuencias recientes."""
        try:
            from app.domains.automations.models import SequenceEmailLog
            threshold = datetime.now(timezone.utc) - timedelta(hours=6)

            await self.db.execute(
                update(SequenceEmailLog)
                .where(
                    and_(
                        SequenceEmailLog.status == "failed",
                        SequenceEmailLog.created_at >= threshold,
                    )
                )
                .values(
                    status="pending",
                    retry_count=SequenceEmailLog.retry_count + 1,
                )
            )
            await self.db.commit()
            fault.repair_log.append("Envíos fallidos marcados para reintento")
            return True
        except Exception as e:
            fault.repair_log.append(f"Error al reintentar secuencias: {e}")
            return False

    async def _repair_disconnected_channel(self, fault: FaultReport) -> bool:
        """Intenta reconectar un canal de comunicación desconectado."""
        try:
            from app.domains.channels.models import ChannelConnection
            await self.db.execute(
                update(ChannelConnection)
                .where(ChannelConnection.id == uuid.UUID(fault.affected_id))
                .values(
                    status="reconnecting",
                    last_reconnect_attempt=datetime.now(timezone.utc),
                )
            )
            await self.db.commit()
            fault.repair_log.append("Canal marcado para reconexión automática")
            return True
        except Exception as e:
            fault.repair_log.append(f"Error al reconectar canal: {e}")
            return False

    async def _notify_owner_of_fault(
        self, fault: FaultReport, business_id: Optional[uuid.UUID]
    ) -> None:
        """Notifica al dueño del negocio sobre una falla que requiere atención."""
        try:
            if not business_id:
                return

            from app.domains.alerts.models import Alert, AlertSeverity
            severity_map = {
                "critical": AlertSeverity.CRITICAL,
                "high": AlertSeverity.HIGH,
                "medium": AlertSeverity.MEDIUM,
                "low": AlertSeverity.LOW,
            }

            alert = Alert(
                business_id=business_id,
                title=f"🔧 [Auto-Repair] Falla escalada: {fault.fault_type}",
                message=f"{fault.description}\n\nIntentos de reparación: {fault.repair_attempts}/{self.MAX_REPAIR_ATTEMPTS}\nSe requiere intervención manual.",
                severity=severity_map.get(fault.severity, AlertSeverity.MEDIUM),
                is_read=False,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(alert)
            await self.db.commit()
            logger.info(f"[SelfRepair] Alerta de falla enviada al dueño: {fault.fault_type}")
        except Exception as e:
            logger.error(f"[SelfRepair] Error notificando falla: {e}")

    def get_active_faults(self) -> list[FaultReport]:
        return list(self._active_faults.values())

    def get_repair_stats(self) -> dict[str, Any]:
        total = len(self._repair_history)
        repaired = sum(1 for f in self._repair_history if f.status == RepairStatus.REPAIRED)
        return {
            "total_repairs": total,
            "success_rate": round(repaired / total * 100, 1) if total > 0 else 100,
            "active_faults": len(self._active_faults),
            "last_repair": self._repair_history[-1].detected_at.isoformat() if self._repair_history else None,
        }
