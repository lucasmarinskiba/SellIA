"""Computer Use — Performance Budget

Monitorea el rendimiento de las sesiones y alerta cuando exceden
umbrales configurables: duración máxima, pasos máximos, tiempo por
paso, y stale states.
"""

import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from app.core.logger import get_logger

logger = get_logger(__name__)


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceAlert:
    level: AlertLevel
    metric: str
    current_value: float
    threshold: float
    message: str
    recommendation: str


@dataclass
class BudgetConfig:
    max_session_duration_seconds: float = 300.0  # 5 min
    max_steps: int = 50
    max_step_duration_seconds: float = 30.0
    max_stale_steps: int = 3  # pasos sin cambio consecutivos
    max_total_retries: int = 10


class PerformanceBudget:
    """Monitor de performance budget para sesiones de Computer Use."""

    def __init__(self, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()
        self._alerts: list[PerformanceAlert] = []
        self._session_start: Optional[float] = None
        self._step_start: Optional[float] = None
        self._stale_count = 0
        self._total_retries = 0
        self._on_alert: Optional[Callable[[PerformanceAlert], None]] = None

    def set_alert_handler(self, handler: Callable[[PerformanceAlert], None]) -> None:
        """Registra un callback para recibir alertas."""
        self._on_alert = handler

    def start_session(self) -> None:
        """Inicia el monitoreo de una sesión."""
        self._session_start = time.time()
        self._alerts = []
        self._stale_count = 0
        self._total_retries = 0

    def start_step(self) -> None:
        """Marca el inicio de un paso."""
        self._step_start = time.time()

    def end_step(self, step_changed: bool = True) -> list[PerformanceAlert]:
        """Marca el fin de un paso y retorna alertas generadas."""
        alerts = []

        # Check step duration
        if self._step_start:
            step_duration = time.time() - self._step_start
            if step_duration > self.config.max_step_duration_seconds:
                alert = PerformanceAlert(
                    level=AlertLevel.WARNING,
                    metric="step_duration",
                    current_value=step_duration,
                    threshold=self.config.max_step_duration_seconds,
                    message=f"Paso lento: {step_duration:.1f}s",
                    recommendation="Considerá usar 'wait' explícito o verificar si la página cargó correctamente.",
                )
                alerts.append(alert)
                self._emit(alert)

        # Check stale state
        if step_changed:
            self._stale_count = 0
        else:
            self._stale_count += 1
            if self._stale_count >= self.config.max_stale_steps:
                alert = PerformanceAlert(
                    level=AlertLevel.CRITICAL,
                    metric="stale_state",
                    current_value=self._stale_count,
                    threshold=self.config.max_stale_steps,
                    message=f"Estado sin cambios por {self._stale_count} pasos consecutivos",
                    recommendation="El agente puede estar atascado. Considerá pausar y dar instrucciones.",
                )
                alerts.append(alert)
                self._emit(alert)

        # Check total session duration
        if self._session_start:
            session_duration = time.time() - self._session_start
            if session_duration > self.config.max_session_duration_seconds:
                alert = PerformanceAlert(
                    level=AlertLevel.CRITICAL,
                    metric="session_duration",
                    current_value=session_duration,
                    threshold=self.config.max_session_duration_seconds,
                    message=f"Sesión excedió {self.config.max_session_duration_seconds}s",
                    recommendation="Considerá dividir la tarea en subtareas más pequeñas.",
                )
                alerts.append(alert)
                self._emit(alert)

        self._alerts.extend(alerts)
        return alerts

    def record_retry(self) -> None:
        """Registra un reintentoo."""
        self._total_retries += 1
        if self._total_retries > self.config.max_total_retries:
            alert = PerformanceAlert(
                level=AlertLevel.CRITICAL,
                metric="total_retries",
                current_value=self._total_retries,
                threshold=self.config.max_total_retries,
                message=f"Demasiados reintentos: {self._total_retries}",
                recommendation="La página puede estar caída o el selector puede haber cambiado.",
            )
            self._alerts.append(alert)
            self._emit(alert)

    def _emit(self, alert: PerformanceAlert) -> None:
        """Emite una alerta al handler registrado."""
        logger.warning(f"Performance alert: {alert.level.value} - {alert.message}")
        if self._on_alert:
            try:
                self._on_alert(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumen del performance budget."""
        duration = time.time() - self._session_start if self._session_start else 0
        return {
            "session_duration_seconds": round(duration, 1),
            "alerts_triggered": len(self._alerts),
            "alerts_by_level": {
                "info": sum(1 for a in self._alerts if a.level == AlertLevel.INFO),
                "warning": sum(1 for a in self._alerts if a.level == AlertLevel.WARNING),
                "critical": sum(1 for a in self._alerts if a.level == AlertLevel.CRITICAL),
            },
            "stale_count": self._stale_count,
            "total_retries": self._total_retries,
            "within_budget": len([a for a in self._alerts if a.level == AlertLevel.CRITICAL]) == 0,
        }
