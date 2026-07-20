"""Monitoring — Query time tracking, bottleneck detection, performance metrics."""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 3),
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


@dataclass
class BottleneckAlert:
    """Alert for detected bottleneck."""
    component: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str  # critical, warning, info
    detected_at: datetime
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "metric_name": self.metric_name,
            "current_value": round(self.current_value, 3),
            "threshold": self.threshold,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "message": self.message,
        }


class PerformanceMonitor:
    """Monitor application performance metrics."""

    # Performance thresholds
    THRESHOLDS = {
        "response_time_ms": {"warning": 200, "critical": 1000},
        "database_query_ms": {"warning": 100, "critical": 500},
        "cache_hit_rate": {"warning": 0.7, "critical": 0.5},  # Lower is worse
        "cpu_usage_percent": {"warning": 70, "critical": 90},
        "memory_usage_mb": {"warning": 1000, "critical": 2000},
        "error_rate_percent": {"warning": 1, "critical": 5},
        "queue_depth": {"warning": 100, "critical": 1000},
    }

    def __init__(self, max_history: int = 10000):
        """Initialize performance monitor."""
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.alerts: List[BottleneckAlert] = []
        self.bottlenecks: Dict[str, Dict[str, Any]] = {}

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "ms",
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a performance metric."""

        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            tags=tags or {},
        )

        self.metrics[name].append(metric)

        # Check thresholds
        self._check_threshold(name, value)

    def _check_threshold(self, metric_name: str, value: float) -> None:
        """Check if metric exceeds threshold."""

        if metric_name not in self.THRESHOLDS:
            return

        thresholds = self.THRESHOLDS[metric_name]
        critical = thresholds.get("critical")
        warning = thresholds.get("warning")

        # Handle inverted metrics (higher is worse for some)
        is_inverted = metric_name == "cache_hit_rate"

        if critical:
            if (not is_inverted and value > critical) or (is_inverted and value < critical):
                self._create_alert(
                    component=metric_name,
                    metric_name=metric_name,
                    current_value=value,
                    threshold=critical,
                    severity="critical",
                )

        elif warning:
            if (not is_inverted and value > warning) or (is_inverted and value < warning):
                self._create_alert(
                    component=metric_name,
                    metric_name=metric_name,
                    current_value=value,
                    threshold=warning,
                    severity="warning",
                )

    def _create_alert(
        self,
        component: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: str,
    ) -> None:
        """Create and log an alert."""

        alert = BottleneckAlert(
            component=component,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            severity=severity,
            detected_at=datetime.utcnow(),
            message=f"{component} exceeded {severity} threshold: {current_value:.2f} > {threshold:.2f}",
        )

        self.alerts.append(alert)
        logger.warning(f"Performance alert: {alert.message}")

    def record_query_time(
        self,
        query_name: str,
        execution_time_ms: float,
        rows_affected: int = 0,
    ) -> None:
        """Record database query execution time."""

        self.record_metric(
            name=f"db_query:{query_name}",
            value=execution_time_ms,
            unit="ms",
            tags={"query": query_name, "rows_affected": str(rows_affected)},
        )

    def record_endpoint_time(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int = 200,
    ) -> None:
        """Record HTTP endpoint response time."""

        self.record_metric(
            name=f"endpoint:{endpoint}",
            value=response_time_ms,
            unit="ms",
            tags={"endpoint": endpoint, "method": method, "status": str(status_code)},
        )

    def get_metric_stats(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a metric."""

        if metric_name not in self.metrics:
            return None

        values = [m.value for m in self.metrics[metric_name]]

        if not values:
            return None

        return {
            "metric": metric_name,
            "count": len(values),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "mean": round(statistics.mean(values), 2),
            "median": round(statistics.median(values), 2),
            "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
            "p95": round(sorted(values)[int(len(values) * 0.95)], 2) if values else 0.0,
            "p99": round(sorted(values)[int(len(values) * 0.99)], 2) if values else 0.0,
        }

    def detect_bottlenecks(self) -> Dict[str, Dict[str, Any]]:
        """Detect performance bottlenecks."""

        self.bottlenecks = {}

        for metric_name, metrics_list in self.metrics.items():
            if len(metrics_list) < 10:  # Need enough data
                continue

            stats = self.get_metric_stats(metric_name)
            if not stats:
                continue

            # Detect bottlenecks: high p99 values
            if stats["p99"] > 500:
                self.bottlenecks[metric_name] = {
                    "issue": "High latency detected",
                    "p99_ms": stats["p99"],
                    "mean_ms": stats["mean"],
                    "recommendation": "Consider caching or query optimization",
                }

            # Detect bottlenecks: high variance
            if stats["stdev"] and stats["stdev"] > stats["mean"] * 0.5:
                self.bottlenecks[metric_name] = {
                    "issue": "High latency variance",
                    "stdev": stats["stdev"],
                    "mean": stats["mean"],
                    "recommendation": "Investigate intermittent slowdowns",
                }

        return self.bottlenecks

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""

        # Count recent alerts by severity
        recent_alerts = [
            a for a in self.alerts
            if a.detected_at > datetime.utcnow() - timedelta(minutes=5)
        ]

        critical_count = sum(1 for a in recent_alerts if a.severity == "critical")
        warning_count = sum(1 for a in recent_alerts if a.severity == "warning")

        # Determine overall health
        if critical_count > 0:
            health_status = "critical"
        elif warning_count > 3:
            health_status = "degraded"
        else:
            health_status = "healthy"

        return {
            "status": health_status,
            "recent_alerts": len(recent_alerts),
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "bottlenecks_detected": len(self.bottlenecks),
            "metrics_tracked": len(self.metrics),
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""

        # Get top bottlenecks
        top_metrics = {}
        for metric_name in list(self.metrics.keys())[:10]:
            stats = self.get_metric_stats(metric_name)
            if stats:
                top_metrics[metric_name] = stats

        # Get recent alerts
        recent_alerts = self.alerts[-20:]  # Last 20 alerts

        self.detect_bottlenecks()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": self.get_system_health(),
            "top_metrics": top_metrics,
            "detected_bottlenecks": self.bottlenecks,
            "recent_alerts": [a.to_dict() for a in recent_alerts],
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""

        recommendations = []

        if self.bottlenecks:
            recommendations.append(
                f"Optimize {len(self.bottlenecks)} detected bottlenecks"
            )

        # Check for high error rates
        if "error_rate" in self.metrics and self.metrics["error_rate"]:
            error_rates = [m.value for m in self.metrics["error_rate"]]
            if statistics.mean(error_rates) > 1:
                recommendations.append("Investigate high error rate")

        # Check for queue depth
        if "queue_depth" in self.metrics and self.metrics["queue_depth"]:
            queue_depths = [m.value for m in self.metrics["queue_depth"]]
            if max(queue_depths) > 100:
                recommendations.append("Consider adding more workers for queue processing")

        # Check for cache hit rate
        if "cache_hit_rate" in self.metrics and self.metrics["cache_hit_rate"]:
            hit_rates = [m.value for m in self.metrics["cache_hit_rate"]]
            if statistics.mean(hit_rates) < 0.6:
                recommendations.append("Improve cache hit rate with better cache strategy")

        return recommendations

    def get_recent_metrics(
        self,
        metric_name: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get recent metrics."""

        if metric_name not in self.metrics:
            return []

        metrics_list = list(self.metrics[metric_name])[-limit:]
        return [m.to_dict() for m in metrics_list]

    def clear_metrics(self) -> int:
        """Clear all metrics."""
        count = sum(len(m) for m in self.metrics.values())
        self.metrics.clear()
        return count

    def get_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get alerts."""

        filtered = self.alerts
        if severity:
            filtered = [a for a in filtered if a.severity == severity]

        return [a.to_dict() for a in filtered[-limit:]]
