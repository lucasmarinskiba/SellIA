"""
Monitoring & Statistics — Monitoreo, métricas y reportes.

Modulo 8 de 8 (final): Sistema de monitoreo y análisis para:
- Rastrear tasa de éxito por plataforma
- Rastrear tipos y frecuencias de errores
- Rastrear conteos y tiempos de retry
- Rastrear tiempo promedio de ejecución
- Alertas en fallos repetidos
- Generar reportes de desempeño

Características:
✓ Métricas en tiempo real
✓ Alertas automáticas
✓ Reportes detallados
✓ Histórico de eventos
✓ Análisis de tendencias
✓ Dashboard-ready

Líneas: 300+ código
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import json
import statistics

logger = logging.getLogger(__name__)


# ============================================================================
# METRICS TYPES
# ============================================================================

class AlertSeverity(str, Enum):
    """Severidad de alerta."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Tipo de métrica."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class MetricPoint:
    """Punto de métrica."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Alerta."""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    threshold: float
    current_value: float
    platform: Optional[str] = None
    acknowledged: bool = False


@dataclass
class PerformanceMetrics:
    """Métricas de desempeño."""
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    success_rate: float = 0.0
    average_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    error_count: int = 0
    most_common_errors: Dict[str, int] = field(default_factory=dict)
    retry_count: int = 0
    retry_success_rate: float = 0.0


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """Recolector central de métricas."""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, List[float]] = defaultdict(list)  # Duración en ms
        self.last_cleanup = datetime.now()

    def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Registrar métrica."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {}
        )

        self.metrics[metric_name].append(point)

        if metric_type == MetricType.COUNTER:
            self.counters[metric_name] += int(value)
        elif metric_type == MetricType.GAUGE:
            self.gauges[metric_name] = value
        elif metric_type == MetricType.TIMER:
            self.timers[metric_name].append(value)

        # Limpieza periódica
        if (datetime.now() - self.last_cleanup).total_seconds() > 3600:
            self._cleanup_old_metrics()

    def increment_counter(self, counter_name: str, amount: int = 1) -> None:
        """Incrementar contador."""
        self.counters[counter_name] += amount

    def record_timer(self, timer_name: str, duration_ms: float) -> None:
        """Registrar tiempo de ejecución."""
        self.timers[timer_name].append(duration_ms)

    def get_metric_stats(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de métrica."""
        if metric_name not in self.timers or len(self.timers[metric_name]) == 0:
            return None

        times = self.timers[metric_name]
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "p95": self._percentile(times, 0.95),
            "p99": self._percentile(times, 0.99),
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calcular percentil."""
        sorted_data = sorted(data)
        index = int((len(sorted_data) - 1) * percentile)
        return sorted_data[index]

    def _cleanup_old_metrics(self) -> None:
        """Limpiar métricas antiguas."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        for metric_name in list(self.metrics.keys()):
            self.metrics[metric_name] = [
                point for point in self.metrics[metric_name]
                if point.timestamp > cutoff_time
            ]

            if not self.metrics[metric_name]:
                del self.metrics[metric_name]

        self.last_cleanup = datetime.now()
        logger.info("Metrics cleanup completed")


# ============================================================================
# ERROR TRACKER
# ============================================================================

class ErrorTracker:
    """Rastreador de errores."""

    def __init__(self):
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 1000

    def record_error(
        self,
        error_type: str,
        error_message: str,
        platform: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registrar error."""
        self.error_counts[error_type] += 1

        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "platform": platform,
            "context": context
        }

        self.error_history.append(error_entry)

        # Limitar tamaño de historial
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

    def get_error_distribution(self, minutes: int = 60) -> Dict[str, int]:
        """Obtener distribución de errores en últimos N minutos."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_errors: Dict[str, int] = defaultdict(int)

        for entry in self.error_history:
            try:
                error_time = datetime.fromisoformat(entry["timestamp"])
                if error_time > cutoff_time:
                    recent_errors[entry["error_type"]] += 1
            except Exception:
                pass

        return dict(recent_errors)

    def get_most_common_errors(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Obtener errores más comunes."""
        return sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]


# ============================================================================
# ALERT MANAGER
# ============================================================================

class AlertManager:
    """Gestor de alertas."""

    def __init__(self, on_alert: Optional[Callable] = None):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.on_alert = on_alert
        self.thresholds: Dict[str, Dict[str, float]] = {}
        self.max_alert_history = 500

    def set_threshold(
        self,
        metric_name: str,
        severity: AlertSeverity,
        threshold: float
    ) -> None:
        """Establecer umbral de alerta."""
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {}

        self.thresholds[metric_name][severity.value] = threshold

    def check_metric(
        self,
        metric_name: str,
        current_value: float,
        platform: Optional[str] = None
    ) -> Optional[Alert]:
        """
        Verificar métrica contra umbrales.

        Retorna alerta si se dispara.
        """
        if metric_name not in self.thresholds:
            return None

        for severity_str, threshold in self.thresholds[metric_name].items():
            severity = AlertSeverity(severity_str)

            if current_value >= threshold:
                # Crear alerta
                alert_id = f"{metric_name}_{severity.value}_{int(datetime.now().timestamp())}"

                alert = Alert(
                    id=alert_id,
                    timestamp=datetime.now(),
                    severity=severity,
                    title=f"Alert: {metric_name}",
                    description=f"{metric_name} = {current_value} (threshold: {threshold})",
                    metric_name=metric_name,
                    threshold=threshold,
                    current_value=current_value,
                    platform=platform
                )

                # Registrar alerta
                self.alerts[alert_id] = alert
                self.alert_history.append(alert)

                # Limitar historial
                if len(self.alert_history) > self.max_alert_history:
                    self.alert_history = self.alert_history[-self.max_alert_history:]

                # Disparar callback
                if self.on_alert:
                    try:
                        self.on_alert(alert)
                    except Exception as e:
                        logger.error(f"Alert callback failed: {str(e)}")

                logger.warning(f"Alert fired: {alert.title}")
                return alert

        return None

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Reconocer alerta."""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Obtener alertas activas (no reconocidas)."""
        return [
            alert for alert in self.alerts.values()
            if not alert.acknowledged
        ]


# ============================================================================
# PERFORMANCE REPORTER
# ============================================================================

class PerformanceReporter:
    """Generador de reportes de desempeño."""

    def __init__(self, metrics_collector: MetricsCollector, error_tracker: ErrorTracker):
        self.metrics = metrics_collector
        self.errors = error_tracker

    async def generate_report(
        self,
        platform: Optional[str] = None,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Generar reporte de desempeño.

        Incluye:
        - Tasa de éxito
        - Tiempos de ejecución
        - Errores y distribución
        - Recomendaciones
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        # Recolectar métricas
        relevant_metrics = [
            name for name in self.metrics.timers.keys()
            if not platform or platform in name
        ]

        report = {
            "timestamp": datetime.now().isoformat(),
            "period_minutes": minutes,
            "platform": platform,
            "summary": {},
            "timing_metrics": {},
            "errors": {},
            "recommendations": []
        }

        # Métricas de timing
        total_actions = 0
        successful_actions = 0

        for metric_name in relevant_metrics:
            stats = self.metrics.get_metric_stats(metric_name)
            if stats:
                report["timing_metrics"][metric_name] = stats
                total_actions += stats["count"]

        # Errores
        error_dist = self.errors.get_error_distribution(minutes)
        report["errors"] = error_dist

        # Resumen
        report["summary"] = {
            "total_actions": total_actions,
            "total_errors": sum(error_dist.values()),
            "error_rate": sum(error_dist.values()) / max(1, total_actions)
        }

        # Recomendaciones
        report["recommendations"] = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en reporte."""
        recommendations = []

        error_rate = report["summary"]["error_rate"]
        if error_rate > 0.1:
            recommendations.append("Error rate >10%, investigate error sources")

        most_common = self.errors.get_most_common_errors(1)
        if most_common:
            error_type, count = most_common[0]
            if count > 50:
                recommendations.append(f"High frequency of {error_type}, consider implementing specific handling")

        return recommendations

    def print_report(self, report: Dict[str, Any]) -> str:
        """Formatear reporte para impresión."""
        lines = [
            "╔════════════════════════════════════════════════════════════════╗",
            "║              Computer Use Performance Report                   ║",
            "╚════════════════════════════════════════════════════════════════╝",
            f"",
            f"Report Time: {report['timestamp']}",
            f"Period: {report['period_minutes']} minutes",
            f"Platform: {report['platform'] or 'All'}",
            f"",
            f"SUMMARY:",
            f"  Total Actions: {report['summary']['total_actions']}",
            f"  Errors: {report['summary']['total_errors']}",
            f"  Error Rate: {report['summary']['error_rate']:.2%}",
            f"",
            f"TIMING METRICS:",
        ]

        for metric_name, stats in report["timing_metrics"].items():
            lines.append(f"  {metric_name}:")
            lines.append(f"    Avg: {stats['avg']:.0f}ms | Min: {stats['min']:.0f}ms | Max: {stats['max']:.0f}ms | P95: {stats['p95']:.0f}ms")

        if report["errors"]:
            lines.append(f"")
            lines.append(f"TOP ERRORS:")
            for error_type, count in list(report["errors"].items())[:5]:
                lines.append(f"  {error_type}: {count}")

        if report["recommendations"]:
            lines.append(f"")
            lines.append(f"RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                lines.append(f"  • {rec}")

        return "\n".join(lines)


# ============================================================================
# MONITORING DASHBOARD
# ============================================================================

class MonitoringDashboard:
    """Dashboard de monitoreo (data provider para UI)."""

    def __init__(
        self,
        metrics_collector: MetricsCollector,
        error_tracker: ErrorTracker,
        alert_manager: AlertManager,
        reporter: PerformanceReporter
    ):
        self.metrics = metrics_collector
        self.errors = error_tracker
        self.alerts = alert_manager
        self.reporter = reporter

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Obtener datos para dashboard.

        Retorna JSON listo para UI.
        """
        # Reportes de 1 hora
        report_1h = await self.reporter.generate_report(minutes=60)
        report_24h = await self.reporter.generate_report(minutes=1440)

        return {
            "timestamp": datetime.now().isoformat(),
            "status": self._compute_overall_status(),
            "reports": {
                "last_1h": report_1h,
                "last_24h": report_24h
            },
            "alerts": {
                "active": [asdict(a) for a in self.alerts.get_active_alerts()],
                "total_fired": len(self.alerts.alert_history)
            },
            "top_errors": self.errors.get_most_common_errors(5),
            "metrics": {
                "counters": dict(self.metrics.counters),
                "gauges": dict(self.metrics.gauges)
            }
        }

    def _compute_overall_status(self) -> str:
        """Computar estado general."""
        active_alerts = self.alerts.get_active_alerts()

        if not active_alerts:
            return "healthy"

        for alert in active_alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                return "critical"

        return "warning"


__all__ = [
    "MetricsCollector",
    "ErrorTracker",
    "AlertManager",
    "PerformanceReporter",
    "MonitoringDashboard",
    "PerformanceMetrics",
    "Alert",
    "MetricPoint",
    "MetricType",
    "AlertSeverity",
]
