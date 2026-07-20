"""SellIA Autonomous Operations — Sistema de Computación Autónoma.

Los 4 pilares de la autonomía enterprise:
  1. Auto-Configuración: Ajuste dinámico según carga y entorno.
  2. Auto-Reparación: Detección y corrección de fallas sin intervención.
  3. Auto-Optimización: Mejora continua de rendimiento y recursos.
  4. Auto-Protección: Defensa activa contra amenazas en tiempo real.
"""

from app.domains.agents.autonomous.self_config import SelfConfigEngine
from app.domains.agents.autonomous.self_repair import SelfRepairEngine
from app.domains.agents.autonomous.self_optimization import SelfOptimizationEngine
from app.domains.agents.autonomous.self_protection import SelfProtectionEngine
from app.domains.agents.autonomous.operations_center import AutonomousOperationsCenter

__all__ = [
    "SelfConfigEngine",
    "SelfRepairEngine",
    "SelfOptimizationEngine",
    "SelfProtectionEngine",
    "AutonomousOperationsCenter",
]
