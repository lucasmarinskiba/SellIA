"""Brain Orchestrator - Unified Multi-Agent Coordination System.

Orquesta:
  - 52 agentes evolucionados (reasoning real)
  - 135+ skills avanzadas (data-driven)
  - 4 neural pathways (Bayesian, causal, RL)
  - 5+ capabilities (predictive, pattern, learning, anomaly, counterfactual)

Proporciona:
  - Context engine (shared state)
  - Decision routing (agent selection)
  - Inter-agent communication
  - Learning loops (feedback)
  - Monitoring 24/7
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Coroutine
from enum import Enum
from datetime import datetime, timedelta
import json
import asyncio
import logging

# Imports from evolution modules
# from app.core.brain.agents_evolution import (
#     EvolvedAgentRegistry, BaseAgent, DecisionContext
# )
# from app.core.brain.tools_evolution import EvolvedToolRegistry
# from app.core.brain.neural_networks import NeuralPathwayRegistry
# from app.core.brain.capabilities_evolution import CapabilitiesOrchestrator


# ─────────────────────────────────────────────────────────────────────────
# CONTEXT ENGINE
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class ContextSnapshot:
    """Snapshot de contexto compartido del cerebro."""
    timestamp: str
    user_id: str
    deal_id: str
    stage: str  # onboarding, engagement, upsell, retention, churn_risk
    metadata: Dict[str, Any] = field(default_factory=dict)
    signals: Dict[str, Any] = field(default_factory=dict)

    def merge(self, other: ContextSnapshot) -> ContextSnapshot:
        """Fusiona dos contextos."""
        merged_signals = {**self.signals, **other.signals}
        merged_metadata = {**self.metadata, **other.metadata}
        return ContextSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            user_id=self.user_id,
            deal_id=self.deal_id,
            stage=other.stage or self.stage,
            metadata=merged_metadata,
            signals=merged_signals,
        )


class ContextEngine:
    """Motor de contexto: mantiene estado compartido entre agentes."""

    def __init__(self):
        self.contexts: Dict[str, ContextSnapshot] = {}
        self.history: List[Dict[str, Any]] = []

    def get_context(self, context_key: str) -> Optional[ContextSnapshot]:
        """Obtiene contexto por clave."""
        return self.contexts.get(context_key)

    def set_context(self, context_key: str, context: ContextSnapshot) -> None:
        """Establece contexto."""
        old_context = self.contexts.get(context_key)
        self.contexts[context_key] = context

        # Registra en histórico
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "key": context_key,
            "old_stage": old_context.stage if old_context else None,
            "new_stage": context.stage,
            "signals": context.signals,
        })

    def update_signal(self, context_key: str, signal_name: str,
                     signal_value: Any) -> None:
        """Actualiza una señal específica."""
        context = self.get_context(context_key)
        if context:
            context.signals[signal_name] = signal_value
            self.set_context(context_key, context)

    def get_stage(self, context_key: str) -> Optional[str]:
        """Obtiene stage actual."""
        context = self.get_context(context_key)
        return context.stage if context else None


# ─────────────────────────────────────────────────────────────────────────
# DECISION ROUTING
# ─────────────────────────────────────────────────────────────────────────


class AgentSelector:
    """Selecciona agente óptimo para una tarea."""

    def __init__(self):
        self.routing_rules = self._build_routing_rules()

    def _build_routing_rules(self) -> Dict[str, List[str]]:
        """Mapea stage → agentes primarios."""
        return {
            "prospecting": [
                "agent.pipeline.captador",
                "agent.expert.lead_filter",
                "agent.expert.acquisition_strategist",
            ],
            "qualification": [
                "agent.pipeline.calificador",
                "agent.expert.lead_qualifier",
            ],
            "nurture": [
                "agent.pipeline.nutridor",
                "agent.predictive",
                "agent.content_curator",
            ],
            "discovery": [
                "agent.pipeline.diagnostico",
                "agent.legend.ross",
            ],
            "proposal": [
                "agent.pipeline.propuesta",
                "agent.persuasion_master",
                "agent.revenue_optimization",
            ],
            "objection": [
                "agent.pipeline.objeciones",
                "agent.legend.belfort",
                "agent.sales_closer",
            ],
            "closing": [
                "agent.pipeline.cerrador",
                "agent.sales_closer",
                "agent.autonomous.negotiator",
            ],
            "onboarding": [
                "agent.pipeline.onboarding",
                "agent.lifecycle.optimizer",
            ],
            "retention": [
                "agent.pipeline.retentor",
                "agent.anomaly.detector",
                "agent.pr.strategist",
            ],
            "churn_prevention": [
                "agent.anomaly.detector",
                "agent.lifecycle.optimizer",
            ],
        }

    def select_agents(self, stage: str, context: Dict[str, Any]) -> List[str]:
        """Selecciona agentes primarios + secundarios."""
        primary = self.routing_rules.get(stage, [])
        secondary = self._select_secondary(stage, context)
        return primary + secondary

    def _select_secondary(self, stage: str, context: Dict[str, Any]) -> List[str]:
        """Selecciona agentes secundarios basado en contexto."""
        secondary = []

        # Si deal_value es alto, agrega revenue optimization
        if context.get("deal_value", 0) > 10000:
            secondary.append("agent.revenue_optimization")

        # Si hay riesgo de churn, agrega churn prevention
        if context.get("churn_risk", 0) > 0.5:
            secondary.append("agent.anomaly.detector")

        # Si stage es conversion, agrega persuasion masters
        if stage in ["proposal", "objection"]:
            secondary.append("agent.persuasion_master")

        return secondary


# ─────────────────────────────────────────────────────────────────────────
# ORCHESTRATION LOGIC
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class OrchestratedDecision:
    """Decisión orquestada de múltiples agentes."""
    timestamp: str
    context_key: str
    stage: str
    primary_decision: str
    primary_agent: str
    secondary_inputs: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    action_recommended: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class BrainOrchestrator:
    """Orquestador principal del cerebro."""

    def __init__(self):
        self.context_engine = ContextEngine()
        self.agent_selector = AgentSelector()
        self.decisions: List[OrchestratedDecision] = []
        self.logger = logging.getLogger(__name__)

        # Refs to registries (inyectadas en init real)
        # self.agents: EvolvedAgentRegistry
        # self.tools: EvolvedToolRegistry
        # self.neural_paths: NeuralPathwayRegistry
        # self.capabilities: CapabilitiesOrchestrator

    async def decide(self, context_key: str, stage: str,
                    signals: Dict[str, Any]) -> OrchestratedDecision:
        """
        Toma decisión coordinada:
        1. Actualiza contexto
        2. Selecciona agentes
        3. Ejecuta en paralelo
        4. Integra resultados
        5. Registra para aprendizaje
        """

        # 1. Actualiza contexto
        context = ContextSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            user_id=signals.get("user_id", "unknown"),
            deal_id=signals.get("deal_id", "unknown"),
            stage=stage,
            signals=signals,
        )
        self.context_engine.set_context(context_key, context)

        # 2. Selecciona agentes
        agent_ids = self.agent_selector.select_agents(stage, signals)

        # 3. Ejecuta en paralelo (mock)
        primary_agent = agent_ids[0] if agent_ids else "agent.fallback"
        primary_decision = await self._execute_agent(primary_agent, context)

        # 4. Ejecuta agentes secundarios
        secondary_inputs = []
        for agent_id in agent_ids[1:]:
            result = await self._execute_agent(agent_id, context)
            if result:
                secondary_inputs.append({
                    "agent": agent_id,
                    "output": result,
                })

        # 5. Integra resultados
        integrated_decision = self._integrate_decisions(
            primary_decision, secondary_inputs
        )

        # 6. Crea decisión orquestada
        orchestrated = OrchestratedDecision(
            timestamp=datetime.utcnow().isoformat(),
            context_key=context_key,
            stage=stage,
            primary_decision=integrated_decision.get("decision", "none"),
            primary_agent=primary_agent,
            secondary_inputs=secondary_inputs,
            confidence=integrated_decision.get("confidence", 0.5),
            action_recommended=integrated_decision.get("action", ""),
        )

        self.decisions.append(orchestrated)
        return orchestrated

    async def _execute_agent(self, agent_id: str,
                            context: ContextSnapshot) -> Optional[Dict[str, Any]]:
        """Ejecuta un agente (mock)."""
        # En production, invoca real agent
        return {
            "agent_id": agent_id,
            "decision": "action",
            "confidence": 0.8,
        }

    def _integrate_decisions(self, primary: Dict[str, Any],
                            secondary: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Integra múltiples decisiones en una sola."""
        # Weighted average de confidencias
        confidences = [primary.get("confidence", 0.5)]
        for sec in secondary:
            confidences.append(sec.get("output", {}).get("confidence", 0.5))

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Primary decision overrides
        action = primary.get("action", "continue")

        return {
            "decision": primary.get("decision", "none"),
            "action": action,
            "confidence": avg_confidence,
            "secondary_alignment": self._check_alignment(primary, secondary),
        }

    def _check_alignment(self, primary: Dict[str, Any],
                        secondary: List[Dict[str, Any]]) -> bool:
        """¿Agentes alineados?"""
        if not secondary:
            return True
        primary_action = primary.get("action")
        aligned = sum(
            1 for sec in secondary
            if sec.get("output", {}).get("action") == primary_action
        )
        return aligned >= len(secondary) / 2


# ─────────────────────────────────────────────────────────────────────────
# LEARNING LOOPS
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class DecisionOutcome:
    """Outcome de decisión para aprendizaje."""
    decision_id: str
    successful: bool
    stage: str
    agents_involved: List[str]
    actual_outcome: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class LearningLoopManager:
    """Gestor de loops de aprendizaje."""

    def __init__(self):
        self.outcomes: List[DecisionOutcome] = []
        self.agent_performance: Dict[str, Dict[str, float]] = {}

    def record_outcome(self, outcome: DecisionOutcome) -> None:
        """Registra outcome."""
        self.outcomes.append(outcome)
        self._update_agent_scores(outcome)

    def _update_agent_scores(self, outcome: DecisionOutcome) -> None:
        """Actualiza scores de agentes."""
        success_points = 1.0 if outcome.successful else 0.0

        for agent_id in outcome.agents_involved:
            if agent_id not in self.agent_performance:
                self.agent_performance[agent_id] = {
                    "decisions": 0,
                    "successes": 0,
                    "success_rate": 0.5,
                }

            stats = self.agent_performance[agent_id]
            stats["decisions"] += 1
            stats["successes"] += success_points
            stats["success_rate"] = stats["successes"] / stats["decisions"]

    def get_agent_performance(self, agent_id: str) -> Dict[str, float]:
        """Obtiene performance de un agente."""
        return self.agent_performance.get(agent_id, {
            "decisions": 0,
            "successes": 0,
            "success_rate": 0.5,
        })

    def suggest_improvements(self, stage: str) -> List[str]:
        """Sugiere mejoras basadas en aprendizajes."""
        improvements = []

        # Analiza agents que trabajan en este stage
        stage_outcomes = [o for o in self.outcomes if o.stage == stage]
        if not stage_outcomes:
            return improvements

        success_rate = sum(1 for o in stage_outcomes if o.successful) / len(stage_outcomes)

        if success_rate < 0.6:
            improvements.append(f"Stage {stage}: Success rate {success_rate:.0%}, improve tactics")

        return improvements


# ─────────────────────────────────────────────────────────────────────────
# MONITORING
# ─────────────────────────────────────────────────────────────────────────


@dataclass
class HealthMetric:
    """Métrica de salud del cerebro."""
    metric_name: str
    value: float  # 0–1
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def is_healthy(self) -> bool:
        return self.value > 0.7


class BrainHealthMonitor:
    """Monitor de salud del cerebro."""

    def __init__(self):
        self.metrics: Dict[str, List[HealthMetric]] = {}
        self.alerts: List[str] = []

    def record_metric(self, metric: HealthMetric) -> None:
        """Registra métrica."""
        if metric.metric_name not in self.metrics:
            self.metrics[metric.metric_name] = []

        self.metrics[metric.metric_name].append(metric)

        # Genera alerta si unhealthy
        if not metric.is_healthy():
            self.alerts.append(
                f"Alert: {metric.metric_name} = {metric.value:.2f} (unhealthy)"
            )

    def get_overall_health(self) -> float:
        """Calcula salud general."""
        if not self.metrics:
            return 0.5

        recent_metrics = []
        for metric_list in self.metrics.values():
            if metric_list:
                recent_metrics.append(metric_list[-1].value)

        return sum(recent_metrics) / len(recent_metrics) if recent_metrics else 0.5

    def generate_health_report(self) -> Dict[str, Any]:
        """Genera reporte de salud."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": self.get_overall_health(),
            "metrics": {
                name: metrics[-1].value if metrics else 0.0
                for name, metrics in self.metrics.items()
            },
            "alerts": self.alerts[-10:],  # Últimas 10
        }


# ─────────────────────────────────────────────────────────────────────────
# UNIFIED BRAIN CONTROLLER
# ─────────────────────────────────────────────────────────────────────────


class UnifiedBrainController:
    """Controlador unificado del cerebro."""

    def __init__(self):
        self.orchestrator = BrainOrchestrator()
        self.learning_manager = LearningLoopManager()
        self.health_monitor = BrainHealthMonitor()

    async def process(self, context_key: str, stage: str,
                     signals: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa señal + toma decisión."""

        # 1. Orquesta decisión
        decision = await self.orchestrator.decide(context_key, stage, signals)

        # 2. Registra métrica
        self.health_monitor.record_metric(HealthMetric(
            "decision_confidence",
            decision.confidence,
        ))

        return {
            "decision": decision.primary_decision,
            "action": decision.action_recommended,
            "confidence": decision.confidence,
            "agents": [decision.primary_agent] + [s["agent"] for s in decision.secondary_inputs],
        }

    def record_outcome(self, decision_id: str, successful: bool,
                      stage: str, agents: List[str]) -> None:
        """Registra outcome para aprendizaje."""
        outcome = DecisionOutcome(
            decision_id=decision_id,
            successful=successful,
            stage=stage,
            agents_involved=agents,
            actual_outcome="success" if successful else "failure",
        )
        self.learning_manager.record_outcome(outcome)

    def get_health(self) -> Dict[str, Any]:
        """Obtiene estado de salud."""
        return self.health_monitor.generate_health_report()


# Export
__all__ = [
    "ContextSnapshot", "ContextEngine",
    "AgentSelector",
    "OrchestratedDecision", "BrainOrchestrator",
    "DecisionOutcome", "LearningLoopManager",
    "HealthMetric", "BrainHealthMonitor",
    "UnifiedBrainController",
]
