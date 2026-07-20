"""Audit Log Service — Register all agent activities.

Interfaz para registrar TODA actividad de Computer Use agents.
Usado por: webhooks, auto-responders, sales closers, etc.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.domains.computer_use.models_audit_log import ComputerUseAuditLog, ComputerUseAuditLogSearchFilter

logger = logging.getLogger(__name__)


class AuditLogEntry:
    """Builder para crear audit log entries."""

    def __init__(self, user_id: str, platform: str, action_type: str):
        self.entry_id = str(uuid.uuid4())
        self.user_id = user_id
        self.platform = platform
        self.action_type = action_type

        self.session_id: Optional[str] = None
        self.agent_name: Optional[str] = None
        self.strategy_name: Optional[str] = None
        self.tactics: Optional[List[str]] = None
        self.confidence_score: float = 0.0
        self.input_data: Optional[str] = None
        self.output_data: Optional[str] = None
        self.status: str = "pending"
        self.error_message: Optional[str] = None
        self.metadata: Optional[Dict[str, Any]] = None

        self.executed_at: Optional[datetime] = None
        self.duration_ms: int = 0

        self._start_time = datetime.now(timezone.utc)

    def with_session(self, session_id: str) -> "AuditLogEntry":
        self.session_id = session_id
        return self

    def with_agent(self, agent_name: str) -> "AuditLogEntry":
        self.agent_name = agent_name
        return self

    def with_strategy(self, strategy_name: str, tactics: Optional[List[str]] = None) -> "AuditLogEntry":
        self.strategy_name = strategy_name
        self.tactics = tactics or []
        return self

    def with_confidence(self, score: float) -> "AuditLogEntry":
        self.confidence_score = max(0.0, min(1.0, score))
        return self

    def with_input(self, data: str) -> "AuditLogEntry":
        # Truncate to 5000 chars
        self.input_data = data[:5000] if data else None
        return self

    def with_output(self, data: str) -> "AuditLogEntry":
        # Truncate to 5000 chars
        self.output_data = data[:5000] if data else None
        return self

    def success(self, output: Optional[str] = None) -> "AuditLogEntry":
        self.status = "success"
        if output:
            self.with_output(output)
        return self

    def pending_approval(self) -> "AuditLogEntry":
        self.status = "pending_approval"
        return self

    def failed(self, error: str) -> "AuditLogEntry":
        self.status = "failed"
        self.error_message = error[:500]
        return self

    def escalated(self, reason: str) -> "AuditLogEntry":
        self.status = "escalated"
        self.error_message = reason[:500]
        return self

    def with_metadata(self, data: Dict[str, Any]) -> "AuditLogEntry":
        self.metadata = data
        return self

    def build(self) -> ComputerUseAuditLog:
        """Build DB model from this entry."""
        elapsed = (datetime.now(timezone.utc) - self._start_time).total_seconds() * 1000
        self.executed_at = datetime.now(timezone.utc)
        self.duration_ms = int(elapsed)

        return ComputerUseAuditLog(
            id=self.entry_id,
            user_id=self.user_id,
            session_id=self.session_id,
            created_at=self._start_time,
            executed_at=self.executed_at,
            duration_ms=self.duration_ms,
            platform=self.platform,
            action_type=self.action_type,
            agent_name=self.agent_name,
            strategy_name=self.strategy_name,
            tactics=self.tactics,
            confidence_score=self.confidence_score,
            input_data=self.input_data,
            output_data=self.output_data,
            status=self.status,
            error_message=self.error_message,
            metadata=self.metadata,
            requires_approval=(self.status == "pending_approval"),
        )


class AuditLogService:
    """Service para gestionar audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, entry: AuditLogEntry) -> ComputerUseAuditLog:
        """
        Registra una actividad en el audit log.

        entry: AuditLogEntry builder (fluent API)
        """
        model = entry.build()
        self.db.add(model)
        await self.db.commit()

        logger.info(
            f"Audit log: {entry.platform}/{entry.action_type} "
            f"status={entry.status} confidence={entry.confidence_score:.0%}"
        )

        return model

    async def get_by_id(self, log_id: str) -> Optional[ComputerUseAuditLog]:
        """Obtiene log por ID."""
        result = await self.db.execute(
            select(ComputerUseAuditLog).where(ComputerUseAuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def search(self, filter: ComputerUseAuditLogSearchFilter) -> tuple[List[ComputerUseAuditLog], int]:
        """
        Busca logs con filtros.

        Retorna: (logs, total_count)
        """
        query = select(ComputerUseAuditLog).where(
            ComputerUseAuditLog.user_id == filter.user_id
        )

        # Filtros opcionales
        conditions = []

        if filter.platform:
            conditions.append(ComputerUseAuditLog.platform == filter.platform)

        if filter.action_type:
            conditions.append(ComputerUseAuditLog.action_type == filter.action_type)

        if filter.agent_name:
            conditions.append(ComputerUseAuditLog.agent_name == filter.agent_name)

        if filter.status:
            conditions.append(ComputerUseAuditLog.status == filter.status)

        if filter.date_from:
            conditions.append(ComputerUseAuditLog.created_at >= filter.date_from)

        if filter.date_to:
            conditions.append(ComputerUseAuditLog.created_at <= filter.date_to)

        if conditions:
            query = query.where(and_(*conditions))

        # Total
        count_result = await self.db.execute(select(ComputerUseAuditLog).where(query.whereclause))
        total = len(count_result.all())

        # Paginate
        query = query.order_by(ComputerUseAuditLog.created_at.desc()).limit(filter.limit).offset(filter.offset)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return logs, total

    async def get_recent(self, user_id: str, limit: int = 50) -> List[ComputerUseAuditLog]:
        """Últimas acciones del usuario."""
        result = await self.db.execute(
            select(ComputerUseAuditLog)
            .where(ComputerUseAuditLog.user_id == user_id)
            .order_by(ComputerUseAuditLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_pending_approvals(self, user_id: str) -> List[ComputerUseAuditLog]:
        """Acciones esperando aprobación del usuario."""
        result = await self.db.execute(
            select(ComputerUseAuditLog).where(
                and_(
                    ComputerUseAuditLog.user_id == user_id,
                    ComputerUseAuditLog.status == "pending_approval",
                    ComputerUseAuditLog.user_approved.is_(None),
                )
            )
        )
        return result.scalars().all()

    async def approve(self, log_id: str, approved_by_user_id: str) -> Optional[ComputerUseAuditLog]:
        """Aprueba una acción pendiente."""
        log = await self.get_by_id(log_id)
        if not log:
            return None

        log.user_approved = True
        log.approval_at = datetime.now(timezone.utc)
        log.approved_by_user_id = approved_by_user_id
        log.status = "success"

        await self.db.commit()
        logger.info(f"Audit log {log_id} approved")

        return log

    async def reject(self, log_id: str, rejected_by_user_id: str, reason: str = None) -> Optional[ComputerUseAuditLog]:
        """Rechaza una acción pendiente."""
        log = await self.get_by_id(log_id)
        if not log:
            return None

        log.user_approved = False
        log.approval_at = datetime.now(timezone.utc)
        log.approved_by_user_id = rejected_by_user_id
        log.status = "failed"
        if reason:
            log.error_message = reason[:500]

        await self.db.commit()
        logger.info(f"Audit log {log_id} rejected")

        return log

    async def get_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Resumen de actividad últimos N días.

        Retorna: stats por platform/action_type/status
        """
        from sqlalchemy import func
        from datetime import timedelta

        date_from = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(
                ComputerUseAuditLog.platform,
                ComputerUseAuditLog.action_type,
                ComputerUseAuditLog.status,
                func.count(ComputerUseAuditLog.id).label("count"),
                func.avg(ComputerUseAuditLog.confidence_score).label("avg_confidence"),
            )
            .where(
                and_(
                    ComputerUseAuditLog.user_id == user_id,
                    ComputerUseAuditLog.created_at >= date_from,
                )
            )
            .group_by(
                ComputerUseAuditLog.platform,
                ComputerUseAuditLog.action_type,
                ComputerUseAuditLog.status,
            )
        )

        rows = result.all()

        summary = {
            "period_days": days,
            "total_actions": 0,
            "by_platform": {},
            "by_action": {},
            "by_status": {},
        }

        for platform, action, status, count, avg_conf in rows:
            summary["total_actions"] += count

            if platform not in summary["by_platform"]:
                summary["by_platform"][platform] = {"count": 0, "avg_confidence": 0}
            summary["by_platform"][platform]["count"] += count

            if action not in summary["by_action"]:
                summary["by_action"][action] = {"count": 0}
            summary["by_action"][action]["count"] += count

            if status not in summary["by_status"]:
                summary["by_status"][status] = 0
            summary["by_status"][status] += count

        return summary


def get_audit_log_service(db: AsyncSession) -> AuditLogService:
    return AuditLogService(db)
