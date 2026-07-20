"""
Monitoring Dashboard — Real-time view de ALL operations.

Tracks:
- Jobs queued / processing / completed
- Success rate (% of jobs succeeded)
- Error rate (% failed)
- Avg execution time (by task type)
- Platform performance (ML, Shopify, etc)
- Lead conversion rate
- Revenue generated
- Top errors (retry opportunities)
- Human escalations (learning opportunities)

Dashboard views:
- Real-time: live job execution
- Hourly: throughput, errors
- Daily: revenue, leads, conversions
- Weekly: trends, optimization opportunities
- Monthly: growth rate, profitability
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Colecta metrics en tiempo real."""

    def __init__(self):
        self.metrics: Dict[str, Any] = defaultdict(lambda: {
            "count": 0,
            "total": 0,
            "min": float("inf"),
            "max": 0,
        })
        self.events: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()
        self.max_events = 10000  # Keep last N events

    async def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Registra un metric."""
        async with self.lock:
            metric = self.metrics[metric_name]
            metric["count"] += 1
            metric["total"] += value
            metric["min"] = min(metric["min"], value)
            metric["max"] = max(metric["max"], value)

            event = {
                "metric": metric_name,
                "value": value,
                "timestamp": datetime.utcnow().isoformat(),
                "tags": tags or {},
            }
            self.events.append(event)

            # Cleanup old events
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

    async def get_metric(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene stats de un metric."""
        async with self.lock:
            metric = self.metrics.get(metric_name)
            if not metric:
                return None

            return {
                "name": metric_name,
                "count": metric["count"],
                "sum": metric["total"],
                "avg": metric["total"] / metric["count"] if metric["count"] > 0 else 0,
                "min": metric["min"] if metric["min"] != float("inf") else 0,
                "max": metric["max"],
            }

    async def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los metrics."""
        async with self.lock:
            return {
                name: {
                    "count": m["count"],
                    "sum": m["total"],
                    "avg": m["total"] / m["count"] if m["count"] > 0 else 0,
                    "min": m["min"] if m["min"] != float("inf") else 0,
                    "max": m["max"],
                }
                for name, m in self.metrics.items()
            }


class MonitoringDashboard:
    """Dashboard de operaciones 24/7."""

    def __init__(
        self,
        state_manager,
        job_queue,
        scheduler,
        escalation_handler,
    ):
        self.state_manager = state_manager
        self.job_queue = job_queue
        self.scheduler = scheduler
        self.escalation_handler = escalation_handler
        self.metrics_collector = MetricsCollector()
        self.hourly_stats: Dict[str, Dict[str, Any]] = {}
        self.daily_stats: Dict[str, Dict[str, Any]] = {}

    async def get_status(self) -> Dict[str, Any]:
        """Status actual del sistema."""
        queue_stats = await self.job_queue.get_stats()
        state_metrics = await self.state_manager.export_metrics()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "queue": queue_stats,
            "jobs": state_metrics,
            "active_tasks": len(await self.scheduler.list_tasks()),
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """KPIs principales."""
        stats_24h = await self.state_manager.get_statistics(hours=24)
        escalation_stats = await self.escalation_handler.get_escalation_stats(hours=24)
        queue_stats = await self.job_queue.get_stats()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "jobs": {
                "total": stats_24h.get("total", 0),
                "success_rate": stats_24h.get("success_rate", "0%"),
                "avg_duration_seconds": stats_24h.get("avg_duration_seconds", "0"),
                "by_status": stats_24h.get("by_status", {}),
                "by_type": stats_24h.get("by_type", {}),
            },
            "queue": {
                "queued": queue_stats.get("queued", 0),
                "active": queue_stats.get("active", 0),
                "dead_letters": queue_stats.get("dead_letter", 0),
            },
            "escalations": {
                "total": escalation_stats.get("total", 0),
                "pending": escalation_stats.get("pending", 0),
                "by_severity": escalation_stats.get("by_severity", {}),
            },
        }

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Problemas activos requiriendo atención."""
        alerts = []

        # High queue depth
        queue_stats = await self.job_queue.get_stats()
        if queue_stats["queued"] > 100:
            alerts.append({
                "severity": "high",
                "message": f"Queue backing up: {queue_stats['queued']} jobs waiting",
                "timestamp": datetime.utcnow().isoformat(),
            })

        # Dead letters
        if queue_stats["dead_letter"] > 10:
            alerts.append({
                "severity": "medium",
                "message": f"{queue_stats['dead_letter']} jobs in dead letter queue",
                "timestamp": datetime.utcnow().isoformat(),
            })

        # High escalation rate
        escalations = await self.escalation_handler.get_pending_escalations(limit=1)
        if len(escalations) > 5:
            alerts.append({
                "severity": "high",
                "message": f"{len(escalations)} unresolved escalations",
                "timestamp": datetime.utcnow().isoformat(),
            })

        # Low success rate
        stats = await self.state_manager.get_statistics(hours=1)
        success_rate_str = stats.get("success_rate", "0%")
        success_rate = float(success_rate_str.rstrip("%"))
        if success_rate < 80:
            alerts.append({
                "severity": "medium",
                "message": f"Low success rate in last hour: {success_rate:.1f}%",
                "timestamp": datetime.utcnow().isoformat(),
            })

        return alerts

    async def record_success(self, job: Any) -> None:
        """Registra job exitoso."""
        await self.metrics_collector.record_metric(
            f"job.duration.{job.job_type.value}",
            job.duration_seconds,
        )
        await self.metrics_collector.record_metric("job.success", 1)
        logger.debug(f"Success recorded: {job.id}")

    async def record_failure(self, job: Any) -> None:
        """Registra job fallido."""
        await self.metrics_collector.record_metric("job.failure", 1)
        await self.metrics_collector.record_metric(
            f"job.attempts.{job.job_type.value}",
            job.attempts,
        )
        logger.debug(f"Failure recorded: {job.id}")

    async def record_cycle(
        self,
        cycle_count: int,
        duration: float,
        tasks_processed: int,
    ) -> None:
        """Registra ciclo de automation engine."""
        await self.metrics_collector.record_metric("cycle.duration", duration)
        await self.metrics_collector.record_metric("cycle.tasks_processed", tasks_processed)

    async def record_error(self, error_type: str, error_msg: str) -> None:
        """Registra error."""
        await self.metrics_collector.record_metric(f"error.{error_type}", 1)
        logger.debug(f"Error recorded: {error_type}")

    async def get_hourly_report(self) -> Dict[str, Any]:
        """Reporte de última hora."""
        stats = await self.state_manager.get_statistics(hours=1)
        metrics = await self.metrics_collector.get_all_metrics()

        return {
            "period": "last_hour",
            "timestamp": datetime.utcnow().isoformat(),
            "jobs": stats,
            "metrics": metrics,
        }

    async def get_daily_report(self) -> Dict[str, Any]:
        """Reporte de último día."""
        stats = await self.state_manager.get_statistics(hours=24)
        escalation_stats = await self.escalation_handler.get_escalation_stats(hours=24)

        return {
            "period": "last_24_hours",
            "timestamp": datetime.utcnow().isoformat(),
            "jobs": stats,
            "escalations": escalation_stats,
        }

    async def get_weekly_report(self) -> Dict[str, Any]:
        """Reporte de última semana."""
        stats = await self.state_manager.get_statistics(hours=168)
        escalation_stats = await self.escalation_handler.get_escalation_stats(hours=168)

        return {
            "period": "last_7_days",
            "timestamp": datetime.utcnow().isoformat(),
            "jobs": stats,
            "escalations": escalation_stats,
        }

    async def export_prometheus_metrics(self) -> str:
        """Exporta metrics en formato Prometheus."""
        metrics = await self.metrics_collector.get_all_metrics()
        status = await self.get_status()

        lines = []
        for metric_name, values in metrics.items():
            lines.append(f"# HELP {metric_name} Automation engine metric")
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f'{metric_name}{{}} {values["sum"]}')

        # Add queue stats
        lines.append("# HELP queue_size Current queue depth")
        lines.append("# TYPE queue_size gauge")
        lines.append(f'queue_size{{}} {status["queue"]["size"]}')

        # Add job stats
        lines.append("# HELP jobs_active Currently processing")
        lines.append("# TYPE jobs_active gauge")
        lines.append(f'jobs_active{{}} {status["queue"]["queued"]}')

        return "\n".join(lines)


class DashboardAPI:
    """API para dashboard frontend."""

    def __init__(self, monitoring: MonitoringDashboard):
        self.monitoring = monitoring

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Datos completos para dashboard."""
        return {
            "status": await self.monitoring.get_status(),
            "metrics": await self.monitoring.get_metrics(),
            "alerts": await self.monitoring.get_alerts(),
            "hourly": await self.monitoring.get_hourly_report(),
        }

    async def get_jobs_table(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene tabla de jobs para UI."""
        recent_jobs = await self.monitoring.state_manager.get_recent(hours=1, limit=limit)

        return [
            {
                "id": job.id,
                "type": job.job_type.value,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "duration": f"{job.duration_seconds:.2f}s" if job.duration_seconds else "—",
                "attempts": job.attempts,
            }
            for job in recent_jobs
        ]

    async def get_escalations_table(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene tabla de escalaciones para UI."""
        escalations = await self.monitoring.escalation_handler.get_pending_escalations(limit=limit)

        return [
            {
                "id": e.id,
                "job_id": e.job_id,
                "severity": e.severity,
                "reason": e.reason,
                "created_at": e.created_at.isoformat(),
                "resolved": e.resolved,
            }
            for e in escalations
        ]
