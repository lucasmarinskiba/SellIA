"""Centro de Operaciones Autónomas — AutonomousOperationsCenter

El coordinador maestro de los 4 pilares de autonomía enterprise.
Orquesta Auto-Configuración, Auto-Reparación, Auto-Optimización y Auto-Protección
en un ciclo continuo que opera 24/7 sin intervención humana.

Arquitectura:
  ┌─────────────────────────────────────────────────────────┐
  │           AUTONOMOUS OPERATIONS CENTER                   │
  │                                                         │
  │  [Auto-Config] [Auto-Repair] [Auto-Optim] [Auto-Prot]  │
  │         │            │            │            │        │
  │         └────────────┴────────────┴────────────┘        │
  │                       │                                 │
  │              [Health Score Engine]                      │
  │                       │                                 │
  │         [Alerting] [Reporting] [Escalation]             │
  └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import uuid
import asyncio
from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import get_logger
from app.domains.agents.autonomous.self_config import SelfConfigEngine
from app.domains.agents.autonomous.self_repair import SelfRepairEngine
from app.domains.agents.autonomous.self_optimization import SelfOptimizationEngine
from app.domains.agents.autonomous.self_protection import SelfProtectionEngine

logger = get_logger(__name__)


@dataclass
class SystemHealthSnapshot:
    """Instantánea del estado de salud del sistema en un momento dado."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    overall_health_score: int = 100          # 0-100
    config_status: str = "ok"               # ok | warning | critical
    repair_status: str = "ok"
    optimization_status: str = "ok"
    protection_status: str = "ok"
    active_faults: int = 0
    threat_score: int = 0
    pending_optimizations: int = 0
    load_state: str = "normal_load"
    uptime_percent: float = 100.0
    messages_processed_24h: int = 0
    deals_active: int = 0
    revenue_at_risk: float = 0.0
    recommended_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_health_score": self.overall_health_score,
            "pillars": {
                "config": self.config_status,
                "repair": self.repair_status,
                "optimization": self.optimization_status,
                "protection": self.protection_status,
            },
            "metrics": {
                "active_faults": self.active_faults,
                "threat_score": self.threat_score,
                "pending_optimizations": self.pending_optimizations,
                "load_state": self.load_state,
                "uptime_percent": self.uptime_percent,
                "messages_24h": self.messages_processed_24h,
                "deals_active": self.deals_active,
                "revenue_at_risk": self.revenue_at_risk,
            },
            "recommended_actions": self.recommended_actions,
        }


class AutonomousOperationsCenter:
    """Centro de Operaciones Autónomas — coordinador maestro del sistema SellIA."""

    # Ciclos de ejecución (en segundos)
    CYCLE_INTERVALS = {
        "protection": 300,       # cada 5 minutos — escaneo de amenazas
        "repair": 600,           # cada 10 minutos — detección y reparación de fallas
        "config": 1800,          # cada 30 minutos — reconfiguración adaptativa
        "optimization": 86400,   # cada 24 horas — análisis de optimización
        "health_report": 21600,  # cada 6 horas — reporte de salud al dueño
    }

    # Umbrales para alertas al dueño
    ALERT_THRESHOLDS = {
        "health_score_warning": 70,
        "health_score_critical": 50,
        "threat_score_warning": 30,
        "threat_score_critical": 60,
        "faults_warning": 3,
        "faults_critical": 10,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._config_engine = SelfConfigEngine(db)
        self._repair_engine = SelfRepairEngine(db)
        self._optimization_engine = SelfOptimizationEngine(db)
        self._protection_engine = SelfProtectionEngine(db)
        self._health_history: list[SystemHealthSnapshot] = []
        self._last_cycle_times: dict[str, datetime] = {}
        self._is_running = False

    # ─────────────────────────────────────────────
    # CICLO MAESTRO DE OPERACIONES AUTÓNOMAS
    # ─────────────────────────────────────────────

    async def run_full_autonomous_cycle(
        self, business_id: Optional[uuid.UUID] = None
    ) -> dict[str, Any]:
        """
        Ejecuta el ciclo completo de los 4 pilares autónomos en paralelo.
        Este es el método principal llamado por Celery cada 5 minutos.
        """
        cycle_start = datetime.now(timezone.utc)
        logger.info(f"[AOC] ═══ Iniciando ciclo autónomo completo para business={business_id} ═══")

        results: dict[str, Any] = {
            "cycle_start": cycle_start.isoformat(),
            "business_id": str(business_id) if business_id else "global",
        }

        # Determinar qué pilares ejecutar en este ciclo
        pillars_to_run = self._get_pillars_due_for_execution()
        logger.info(f"[AOC] Pilares a ejecutar: {pillars_to_run}")

        # Ejecutar pilares en paralelo para máxima eficiencia
        pillar_tasks = []
        if "protection" in pillars_to_run:
            pillar_tasks.append(("protection", self._run_protection_pillar(business_id)))
        if "repair" in pillars_to_run:
            pillar_tasks.append(("repair", self._run_repair_pillar(business_id)))
        if "config" in pillars_to_run:
            pillar_tasks.append(("config", self._run_config_pillar(business_id)))
        if "optimization" in pillars_to_run:
            pillar_tasks.append(("optimization", self._run_optimization_pillar(business_id)))

        if pillar_tasks:
            pillar_names, pillar_coros = zip(*pillar_tasks)
            pillar_results = await asyncio.gather(*pillar_coros, return_exceptions=True)
            for name, result in zip(pillar_names, pillar_results):
                if isinstance(result, Exception):
                    logger.error(f"[AOC] Error en pilar {name}: {result}")
                    results[name] = {"status": "error", "error": str(result)[:200]}
                else:
                    results[name] = result
                self._last_cycle_times[name] = datetime.now(timezone.utc)

        # Calcular y registrar salud del sistema
        snapshot = await self._calculate_health_snapshot(business_id, results)
        self._health_history.append(snapshot)
        if len(self._health_history) > 200:
            self._health_history = self._health_history[-100:]

        results["health_snapshot"] = snapshot.to_dict()

        # Alertar al dueño si la salud está por debajo del umbral
        if "health_report" in pillars_to_run or snapshot.overall_health_score < self.ALERT_THRESHOLDS["health_score_warning"]:
            await self._send_health_report(snapshot, business_id)

        cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        results["cycle_duration_seconds"] = round(cycle_duration, 2)
        results["pillars_executed"] = list(pillars_to_run)

        logger.info(
            f"[AOC] ═══ Ciclo completado en {cycle_duration:.1f}s | "
            f"Salud: {snapshot.overall_health_score}/100 | "
            f"Fallas: {snapshot.active_faults} | "
            f"Amenazas: {snapshot.threat_score} ═══"
        )
        return results

    def _get_pillars_due_for_execution(self) -> set[str]:
        """Determina qué pilares deben ejecutarse en este ciclo según sus intervalos."""
        now = datetime.now(timezone.utc)
        due = set()
        for pillar, interval_seconds in self.CYCLE_INTERVALS.items():
            last_run = self._last_cycle_times.get(pillar)
            if last_run is None or (now - last_run).total_seconds() >= interval_seconds:
                due.add(pillar)
        return due

    # ─────────────────────────────────────────────
    # EJECUCIÓN DE PILARES INDIVIDUALES
    # ─────────────────────────────────────────────

    async def _run_protection_pillar(
        self, business_id: Optional[uuid.UUID]
    ) -> dict[str, Any]:
        """Ejecuta el pilar de Auto-Protección."""
        try:
            result = await self._protection_engine.run_protection_cycle(business_id)
            logger.info(f"[AOC][Protection] Amenazas: {result.get('threats_detected', 0)}, Score: {result.get('threat_score', 0)}")
            return {"status": "ok", **result}
        except Exception as e:
            logger.error(f"[AOC][Protection] Error: {e}")
            return {"status": "error", "error": str(e)[:200]}

    async def _run_repair_pillar(
        self, business_id: Optional[uuid.UUID]
    ) -> dict[str, Any]:
        """Ejecuta el pilar de Auto-Reparación."""
        try:
            result = await self._repair_engine.run_repair_cycle(business_id)
            logger.info(f"[AOC][Repair] Detectadas: {result.get('detected', 0)}, Reparadas: {result.get('repaired', 0)}")
            return {"status": "ok", **result}
        except Exception as e:
            logger.error(f"[AOC][Repair] Error: {e}")
            return {"status": "error", "error": str(e)[:200]}

    async def _run_config_pillar(
        self, business_id: Optional[uuid.UUID]
    ) -> dict[str, Any]:
        """Ejecuta el pilar de Auto-Configuración."""
        try:
            result = await self._config_engine.run_config_cycle(business_id)
            logger.info(f"[AOC][Config] Estado de carga: {result.get('load_state', 'unknown')}")
            return {"status": "ok", **result}
        except Exception as e:
            logger.error(f"[AOC][Config] Error: {e}")
            return {"status": "error", "error": str(e)[:200]}

    async def _run_optimization_pillar(
        self, business_id: Optional[uuid.UUID]
    ) -> dict[str, Any]:
        """Ejecuta el pilar de Auto-Optimización."""
        try:
            result = await self._optimization_engine.run_optimization_cycle(business_id)
            logger.info(f"[AOC][Optimization] Insights: {result.get('insights_generated', 0)}, Acciones: {result.get('actions_taken', 0)}")
            return {"status": "ok", **result}
        except Exception as e:
            logger.error(f"[AOC][Optimization] Error: {e}")
            return {"status": "error", "error": str(e)[:200]}

    # ─────────────────────────────────────────────
    # CÁLCULO DE SALUD DEL SISTEMA
    # ─────────────────────────────────────────────

    async def _calculate_health_snapshot(
        self,
        business_id: Optional[uuid.UUID],
        cycle_results: dict[str, Any],
    ) -> SystemHealthSnapshot:
        """Calcula una instantánea del estado de salud del sistema."""
        snapshot = SystemHealthSnapshot()

        # --- Datos de protección ---
        prot = cycle_results.get("protection", {})
        snapshot.threat_score = prot.get("threat_score", 0)
        snapshot.protection_status = (
            "critical" if snapshot.threat_score >= self.ALERT_THRESHOLDS["threat_score_critical"]
            else "warning" if snapshot.threat_score >= self.ALERT_THRESHOLDS["threat_score_warning"]
            else "ok"
        )

        # --- Datos de reparación ---
        rep = cycle_results.get("repair", {})
        snapshot.active_faults = rep.get("active_faults", 0)
        snapshot.repair_status = (
            "critical" if snapshot.active_faults >= self.ALERT_THRESHOLDS["faults_critical"]
            else "warning" if snapshot.active_faults >= self.ALERT_THRESHOLDS["faults_warning"]
            else "ok"
        )

        # --- Datos de configuración ---
        conf = cycle_results.get("config", {})
        snapshot.load_state = conf.get("load_state", "normal_load")
        snapshot.config_status = (
            "warning" if snapshot.load_state == "high_load" else "ok"
        )

        # --- Datos de optimización ---
        opt = cycle_results.get("optimization", {})
        snapshot.pending_optimizations = opt.get("insights_generated", 0)
        snapshot.optimization_status = (
            "warning" if snapshot.pending_optimizations >= 5 else "ok"
        )

        # --- Métricas de negocio ---
        try:
            from sqlalchemy import func
            from app.domains.channels.models import Message
            from app.domains.crm.models import Deal

            threshold_24h = datetime.now(timezone.utc) - timedelta(hours=24)

            msg_query = select(func.count(Message.id)).where(
                Message.created_at >= threshold_24h
            )
            msg_result = await self.db.execute(msg_query)
            snapshot.messages_processed_24h = msg_result.scalar() or 0

            deals_query = select(func.count(Deal.id)).where(Deal.is_active == True)
            if business_id:
                deals_query = deals_query.where(Deal.business_id == business_id)
            deals_result = await self.db.execute(deals_query)
            snapshot.deals_active = deals_result.scalar() or 0
        except Exception as e:
            logger.warning(f"[AOC] No se pudieron obtener métricas de negocio: {e}")

        # --- Score general de salud (0-100) ---
        snapshot.overall_health_score = self._calculate_health_score(snapshot)

        # --- Acciones recomendadas ---
        snapshot.recommended_actions = self._generate_recommendations(snapshot)

        return snapshot

    def _calculate_health_score(self, snapshot: SystemHealthSnapshot) -> int:
        """Calcula el score de salud general del sistema (100 = perfecto)."""
        score = 100

        # Penalizar por amenazas
        score -= min(30, snapshot.threat_score // 2)

        # Penalizar por fallas activas
        score -= min(25, snapshot.active_faults * 3)

        # Penalizar por estado de carga
        if snapshot.load_state == "high_load":
            score -= 10

        # Penalizar por optimizaciones pendientes críticas
        if snapshot.pending_optimizations >= 5:
            score -= 5

        # Pilares en estado crítico
        critical_pillars = sum(
            1 for s in [
                snapshot.config_status,
                snapshot.repair_status,
                snapshot.optimization_status,
                snapshot.protection_status,
            ]
            if s == "critical"
        )
        score -= critical_pillars * 10

        return max(0, min(100, score))

    def _generate_recommendations(self, snapshot: SystemHealthSnapshot) -> list[str]:
        """Genera lista de acciones recomendadas según el estado del sistema."""
        recs = []

        if snapshot.threat_score >= self.ALERT_THRESHOLDS["threat_score_critical"]:
            recs.append("🚨 URGENTE: Score de amenaza crítico. Revisar logs de seguridad inmediatamente.")
        elif snapshot.threat_score >= self.ALERT_THRESHOLDS["threat_score_warning"]:
            recs.append("⚠️ Amenazas detectadas. Revisar el panel de seguridad hoy.")

        if snapshot.active_faults >= self.ALERT_THRESHOLDS["faults_critical"]:
            recs.append("🔧 URGENTE: Múltiples fallas activas. Intervención manual requerida.")
        elif snapshot.active_faults >= self.ALERT_THRESHOLDS["faults_warning"]:
            recs.append("🔧 Fallas detectadas y en proceso de reparación automática.")

        if snapshot.load_state == "high_load":
            recs.append("⚡ Sistema bajo alta carga. Considerar escalar recursos o reducir tareas en segundo plano.")

        if snapshot.deals_active == 0:
            recs.append("💡 Sin deals activos en el pipeline. Activar campaña de captación.")

        if snapshot.messages_processed_24h < 10:
            recs.append("📨 Actividad de mensajería baja en las últimas 24h. Verificar conexiones de canales.")

        if snapshot.overall_health_score >= 90:
            recs.append("✅ Sistema operando en condiciones óptimas. Sin acciones requeridas.")

        return recs[:5]  # Máximo 5 recomendaciones

    # ─────────────────────────────────────────────
    # REPORTES Y ALERTAS AL DUEÑO
    # ─────────────────────────────────────────────

    async def _send_health_report(
        self,
        snapshot: SystemHealthSnapshot,
        business_id: Optional[uuid.UUID],
    ) -> None:
        """Envía reporte de salud del sistema al dueño del negocio."""
        if not business_id:
            return

        health_emoji = (
            "🟢" if snapshot.overall_health_score >= 80
            else "🟡" if snapshot.overall_health_score >= 60
            else "🔴"
        )

        report_lines = [
            f"{health_emoji} *Reporte de Salud del Sistema SellIA*",
            f"📊 Score General: {snapshot.overall_health_score}/100",
            f"",
            f"*Estado de Pilares:*",
            f"⚙️ Auto-Configuración: {snapshot.config_status.upper()}",
            f"🔧 Auto-Reparación: {snapshot.repair_status.upper()} ({snapshot.active_faults} fallas activas)",
            f"📈 Auto-Optimización: {snapshot.optimization_status.upper()} ({snapshot.pending_optimizations} insights)",
            f"🛡️ Auto-Protección: {snapshot.protection_status.upper()} (score: {snapshot.threat_score}/100)",
            f"",
            f"*Métricas de Negocio:*",
            f"💬 Mensajes procesados (24h): {snapshot.messages_processed_24h}",
            f"🎯 Deals activos: {snapshot.deals_active}",
            f"⚡ Estado de carga: {snapshot.load_state.replace('_', ' ').title()}",
            f"",
        ]

        if snapshot.recommended_actions:
            report_lines.append("*Acciones Recomendadas:*")
            report_lines.extend(snapshot.recommended_actions)

        report_text = "\n".join(report_lines)

        try:
            from app.domains.alerts.models import Alert, AlertSeverity
            severity = (
                AlertSeverity.CRITICAL if snapshot.overall_health_score < self.ALERT_THRESHOLDS["health_score_critical"]
                else AlertSeverity.HIGH if snapshot.overall_health_score < self.ALERT_THRESHOLDS["health_score_warning"]
                else AlertSeverity.LOW
            )
            alert = Alert(
                business_id=business_id,
                title=f"{health_emoji} Reporte de Salud SellIA — Score: {snapshot.overall_health_score}/100",
                message=report_text,
                severity=severity,
                is_read=False,
                created_at=snapshot.timestamp,
            )
            self.db.add(alert)
            await self.db.commit()
            logger.info(f"[AOC] Reporte de salud enviado. Score: {snapshot.overall_health_score}/100")
        except Exception as e:
            logger.error(f"[AOC] Error enviando reporte de salud: {e}")

    # ─────────────────────────────────────────────
    # API PÚBLICA DEL CENTRO DE OPERACIONES
    # ─────────────────────────────────────────────

    def get_latest_health(self) -> Optional[dict[str, Any]]:
        """Retorna el último snapshot de salud del sistema."""
        if self._health_history:
            return self._health_history[-1].to_dict()
        return None

    def get_health_trend(self, hours: int = 24) -> list[dict[str, Any]]:
        """Retorna tendencia de salud de las últimas N horas."""
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            s.to_dict()
            for s in self._health_history
            if s.timestamp >= threshold
        ]

    def get_current_llm_config(self) -> dict[str, Any]:
        """Retorna config LLM actual (delegado al motor de config)."""
        return self._config_engine.get_current_llm_config()

    def is_message_safe(self, content: str) -> bool:
        """Verifica si un mensaje es seguro para procesar (sin inyecciones)."""
        return not self._protection_engine.scan_message_for_injection(content)

    def is_ip_blocked(self, ip: str) -> bool:
        """Verifica si una IP está bloqueada."""
        return self._protection_engine.is_ip_blocked(ip)

    async def run_quick_health_check(
        self, business_id: Optional[uuid.UUID] = None
    ) -> dict[str, Any]:
        """Ejecuta un health check rápido (solo métricas, sin acciones)."""
        protection_summary = self._protection_engine.get_threat_summary()
        repair_stats = self._repair_engine.get_repair_stats()
        optimization_insights = self._optimization_engine.get_top_insights(3)
        load_state = self._config_engine.get_current_load_state()
        latest_health = self.get_latest_health()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_score": latest_health.get("overall_health_score", 100) if latest_health else 100,
            "load_state": load_state,
            "protection": protection_summary,
            "repair": repair_stats,
            "top_optimizations": optimization_insights,
            "status": "operational",
        }


# ─────────────────────────────────────────────
# FACTORY FUNCTION
# ─────────────────────────────────────────────

def get_operations_center(db: AsyncSession) -> AutonomousOperationsCenter:
    """Factory para obtener instancia del Centro de Operaciones."""
    return AutonomousOperationsCenter(db)
