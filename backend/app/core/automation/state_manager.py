"""
State Manager — TRACKING estado de cada job/task.

Maneja:
- State transitions (pending → running → success/failed/escalated)
- Audit trail completo de cada job
- Queries: jobs by status, by type, by date range
- Job recovery after crashes
- Analytics: success rate, avg duration, by job type
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class StateManager:
    """Maneja state de jobs."""

    def __init__(self):
        self.jobs: Dict[str, Any] = {}  # job_id → Job
        self.job_status_index: Dict[str, List[str]] = defaultdict(list)  # status → [job_id, ...]
        self.job_type_index: Dict[str, List[str]] = defaultdict(list)  # job_type → [job_id, ...]
        self.lock = asyncio.Lock()

    async def create(self, job: Any) -> None:
        """Crea nuevo job en state store."""
        async with self.lock:
            self.jobs[job.id] = job
            self.job_status_index[job.status.value].append(job.id)
            self.job_type_index[job.job_type.value].append(job.id)
            logger.debug(f"Job created in state: {job.id}")

    async def update(self, job_id: str, job: Any) -> None:
        """Actualiza job state."""
        async with self.lock:
            if job_id not in self.jobs:
                logger.warning(f"Job not in state: {job_id}")
                return

            old_job = self.jobs[job_id]
            old_status = old_job.status.value if old_job else None

            self.jobs[job_id] = job

            # Update indexes if status changed
            if old_status and old_status != job.status.value:
                if job_id in self.job_status_index[old_status]:
                    self.job_status_index[old_status].remove(job_id)
                self.job_status_index[job.status.value].append(job_id)

            logger.debug(
                f"Job updated: {job_id} {old_status} → {job.status.value}"
            )

    async def get(self, job_id: str) -> Optional[Any]:
        """Obtiene un job."""
        async with self.lock:
            return self.jobs.get(job_id)

    async def count_by_status(self, status: Any) -> int:
        """Cuenta jobs por status."""
        async with self.lock:
            status_value = status.value if hasattr(status, 'value') else str(status)
            return len(self.job_status_index.get(status_value, []))

    async def get_by_status(self, status: Any, limit: int = 100) -> List[Any]:
        """Obtiene jobs por status."""
        async with self.lock:
            status_value = status.value if hasattr(status, 'value') else str(status)
            job_ids = self.job_status_index.get(status_value, [])[-limit:]
            return [self.jobs[jid] for jid in job_ids if jid in self.jobs]

    async def get_by_type(self, job_type: Any, limit: int = 100) -> List[Any]:
        """Obtiene jobs por type."""
        async with self.lock:
            job_type_value = job_type.value if hasattr(job_type, 'value') else str(job_type)
            job_ids = self.job_type_index.get(job_type_value, [])[-limit:]
            return [self.jobs[jid] for jid in job_ids if jid in self.jobs]

    async def get_recent(self, hours: int = 1, limit: int = 100) -> List[Any]:
        """Obtiene jobs recientes."""
        async with self.lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent = [
                job for job in self.jobs.values()
                if job.created_at >= cutoff
            ]
            return sorted(
                recent,
                key=lambda j: j.created_at,
                reverse=True,
            )[:limit]

    async def get_history(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene historial completo de un job."""
        async with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return None

            return {
                "id": job.id,
                "type": job.job_type.value,
                "priority": job.priority.value,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "duration_seconds": job.duration_seconds,
                "attempts": job.attempts,
                "max_retries": job.max_retries,
                "error": job.error,
                "result": job.result,
                "escalation_reason": job.escalation_reason,
            }

    async def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Estadísticas de jobs (últimas N horas)."""
        async with self.lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent_jobs = [
                job for job in self.jobs.values()
                if job.created_at >= cutoff
            ]

            if not recent_jobs:
                return {
                    "total": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0.0,
                    "by_status": {},
                    "by_type": {},
                }

            # Count by status
            by_status = defaultdict(int)
            for job in recent_jobs:
                by_status[job.status.value] += 1

            # Count by type
            by_type = defaultdict(int)
            for job in recent_jobs:
                by_type[job.job_type.value] += 1

            # Success rate
            success_count = by_status.get("success", 0)
            total = len(recent_jobs)
            success_rate = (success_count / total * 100) if total > 0 else 0.0

            # Avg duration (solo completados)
            completed_jobs = [j for j in recent_jobs if j.completed_at]
            avg_duration = (
                sum(j.duration_seconds for j in completed_jobs) / len(completed_jobs)
                if completed_jobs else 0.0
            )

            return {
                "total": total,
                "success_rate": f"{success_rate:.1f}%",
                "avg_duration_seconds": f"{avg_duration:.2f}",
                "by_status": dict(by_status),
                "by_type": dict(by_type),
                "time_range_hours": hours,
            }

    async def mark_for_review(self, job_id: str, reason: str) -> None:
        """Marca job para revisión humana."""
        async with self.lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.escalation_reason = reason
                logger.warning(f"Job marked for review: {job_id} ({reason})")

    async def cleanup_old(self, days: int = 7) -> int:
        """Limpia jobs viejos (archive)."""
        async with self.lock:
            cutoff = datetime.utcnow() - timedelta(days=days)
            original_count = len(self.jobs)

            # Keep only recent jobs + pending jobs
            new_jobs = {}
            for job_id, job in self.jobs.items():
                if job.created_at >= cutoff or job.status.value in ["pending", "running"]:
                    new_jobs[job_id] = job
                else:
                    # Remove from indexes
                    status_val = job.status.value
                    job_type_val = job.job_type.value
                    if job_id in self.job_status_index[status_val]:
                        self.job_status_index[status_val].remove(job_id)
                    if job_id in self.job_type_index[job_type_val]:
                        self.job_type_index[job_type_val].remove(job_id)

            self.jobs = new_jobs
            removed = original_count - len(self.jobs)
            logger.info(f"State cleanup: removed {removed} old jobs")
            return removed

    async def export_metrics(self) -> Dict[str, Any]:
        """Exporta métricas para monitoring."""
        async with self.lock:
            stats = await self.get_statistics(hours=24)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "jobs_total": len(self.jobs),
                "status_distribution": dict(
                    (status, len(job_ids))
                    for status, job_ids in self.job_status_index.items()
                ),
                "type_distribution": dict(
                    (job_type, len(job_ids))
                    for job_type, job_ids in self.job_type_index.items()
                ),
                "recent_stats": stats,
            }


class JobRecovery:
    """Recupera jobs después de crashes."""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    async def recover_crashed_jobs(self) -> int:
        """Recupera jobs que estaban running cuando se crasheó."""
        from automation_engine import JobStatus

        running_jobs = await self.state_manager.get_by_status(JobStatus.RUNNING)
        recovered = 0

        for job in running_jobs:
            # Mark as failed (will be retried if applicable)
            job.status = JobStatus.FAILED
            job.error = "Job interrupted due to system restart"
            job.completed_at = datetime.utcnow()
            await self.state_manager.update(job.id, job)
            recovered += 1

        logger.info(f"Recovered {recovered} crashed jobs")
        return recovered

    async def get_jobs_requiring_attention(self) -> Dict[str, List[Any]]:
        """Retorna jobs que requieren atención humana."""
        from automation_engine import JobStatus

        escalated = await self.state_manager.get_by_status(JobStatus.ESCALATED, limit=50)
        failed = await self.state_manager.get_by_status(JobStatus.FAILED, limit=50)

        return {
            "escalated": escalated,
            "failed": failed,
        }
