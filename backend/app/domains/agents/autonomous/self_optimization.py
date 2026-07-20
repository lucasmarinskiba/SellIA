"""Pilar 3 — Auto-Optimización (Self-Optimization)

Monitorea el rendimiento del sistema y reasigna recursos automáticamente
para maximizar conversiones, velocidad de respuesta y calidad de atención.
"""

from __future__ import annotations

import uuid
import asyncio
from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizationInsight:
    """Insight generado por el motor de optimización."""
    category: str
    metric: str
    current_value: float
    benchmark_value: float
    gap_percent: float
    recommendation: str
    action_taken: str = ""
    priority: int = 5  # 1=crítico, 10=bajo
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SelfOptimizationEngine:
    """Motor de auto-optimización continua del sistema SellIA."""

    # Benchmarks objetivo del sistema
    BENCHMARKS = {
        "response_time_seconds": 30,        # tiempo de respuesta máximo al lead
        "deal_conversion_rate": 0.20,       # 20% de deals calificados deben cerrar
        "nurture_engagement_rate": 0.35,    # 35% de leads en nurturing deben responder
        "onboarding_completion_rate": 0.85, # 85% de clientes deben completar onboarding
        "message_open_rate": 0.60,          # 60% de mensajes deben ser abiertos
        "churn_rate_monthly": 0.05,         # máximo 5% de churn mensual
        "upsell_rate": 0.25,               # 25% de clientes deben comprar upsell
        "nps_score": 8.0,                  # NPS promedio objetivo
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._optimization_history: list[OptimizationInsight] = []
        self._ab_test_results: dict[str, Any] = {}

    async def run_optimization_cycle(
        self, business_id: Optional[uuid.UUID] = None
    ) -> dict[str, Any]:
        """Ejecuta un ciclo completo de análisis y optimización."""
        logger.info("[SelfOptimization] Iniciando ciclo de optimización")

        insights_groups = await asyncio.gather(
            self._optimize_response_times(business_id),
            self._optimize_pipeline_conversion(business_id),
            self._optimize_message_performance(business_id),
            self._optimize_agent_assignment(business_id),
            self._optimize_send_times(business_id),
            return_exceptions=True,
        )

        all_insights: list[OptimizationInsight] = []
        for group in insights_groups:
            if isinstance(group, list):
                all_insights.extend(group)

        all_insights.sort(key=lambda i: i.priority)
        self._optimization_history.extend(all_insights)
        if len(self._optimization_history) > 500:
            self._optimization_history = self._optimization_history[-250:]

        actions_taken = [i for i in all_insights if i.action_taken]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "insights_generated": len(all_insights),
            "actions_taken": len(actions_taken),
            "top_insights": [
                {
                    "category": i.category,
                    "metric": i.metric,
                    "gap_percent": round(i.gap_percent, 1),
                    "recommendation": i.recommendation,
                    "action": i.action_taken,
                }
                for i in all_insights[:5]
            ],
        }

    async def _optimize_response_times(
        self, business_id: Optional[uuid.UUID]
    ) -> list[OptimizationInsight]:
        """Optimiza tiempos de respuesta de agentes a nuevos leads."""
        insights = []
        try:
            from app.domains.channels.models import Conversation, Message
            threshold = datetime.now(timezone.utc) - timedelta(days=7)

            query = select(func.avg(
                func.extract("epoch", Message.created_at - Conversation.created_at)
            )).select_from(Message).join(
                Conversation, Message.conversation_id == Conversation.id
            ).where(
                and_(
                    Message.created_at >= threshold,
                    Message.sender_type == "agent",
                )
            )
            if business_id:
                query = query.where(Conversation.business_id == business_id)

            result = await self.db.execute(query)
            avg_response = result.scalar() or 0

            benchmark = self.BENCHMARKS["response_time_seconds"]
            gap = ((avg_response - benchmark) / benchmark * 100) if benchmark > 0 else 0

            if avg_response > benchmark * 1.5:
                action = await self._apply_response_optimization(business_id)
                insights.append(OptimizationInsight(
                    category="response_time",
                    metric="avg_first_response_seconds",
                    current_value=round(avg_response, 1),
                    benchmark_value=benchmark,
                    gap_percent=round(gap, 1),
                    recommendation=f"Tiempo promedio de respuesta {round(avg_response/60, 1)} min — objetivo <{benchmark}s. Activar respuesta automática inmediata.",
                    action_taken=action,
                    priority=2,
                ))
        except Exception as e:
            logger.warning(f"[SelfOptimization] Error en response time: {e}")
        return insights

    async def _apply_response_optimization(self, business_id: Optional[uuid.UUID]) -> str:
        """Habilita respuesta automática inmediata para reducir tiempo."""
        try:
            from app.domains.agents.models import AgentConfig
            result = await self.db.execute(
                select(AgentConfig).where(
                    AgentConfig.business_id == business_id,
                    AgentConfig.ai_auto_reply_enabled == False,
                ).limit(5)
            )
            configs = result.scalars().all()
            for config in configs:
                config.ai_auto_reply_enabled = True
            if configs:
                await self.db.commit()
                return f"Auto-reply habilitado en {len(configs)} configuraciones de agente"
        except Exception as e:
            logger.warning(f"[SelfOptimization] Error habilitando auto-reply: {e}")
        return "Sin cambio aplicado"

    async def _optimize_pipeline_conversion(
        self, business_id: Optional[uuid.UUID]
    ) -> list[OptimizationInsight]:
        """Detecta cuellos de botella en el pipeline y activa recovery."""
        insights = []
        try:
            from app.domains.crm.models import Deal
            threshold = datetime.now(timezone.utc) - timedelta(days=30)

            stage_counts_q = select(
                Deal.pipeline_stage,
                func.count(Deal.id).label("count"),
            ).where(Deal.is_active == True)
            if business_id:
                stage_counts_q = stage_counts_q.where(Deal.business_id == business_id)

            result = await self.db.execute(stage_counts_q.group_by(Deal.pipeline_stage))
            stage_data = {row[0]: row[1] for row in result}

            prospecting = stage_data.get("prospecting", 0)
            qualifying = stage_data.get("qualifying", 0)
            closing = stage_data.get("closing", 0)

            if prospecting > 0 and qualifying == 0:
                insights.append(OptimizationInsight(
                    category="pipeline",
                    metric="prospect_to_qualify_rate",
                    current_value=0,
                    benchmark_value=0.50,
                    gap_percent=-100,
                    recommendation="Ningún prospecto está pasando a calificación. Revisar proceso de calificación y mensajes de captación.",
                    priority=1,
                ))

            if qualifying > 0 and closing == 0:
                insights.append(OptimizationInsight(
                    category="pipeline",
                    metric="qualify_to_close_rate",
                    current_value=0,
                    benchmark_value=0.20,
                    gap_percent=-100,
                    recommendation="Cuello de botella en calificación → cierre. Activar secuencias de diagnóstico urgentes.",
                    priority=1,
                ))
        except Exception as e:
            logger.warning(f"[SelfOptimization] Error en pipeline conversion: {e}")
        return insights

    async def _optimize_message_performance(
        self, business_id: Optional[uuid.UUID]
    ) -> list[OptimizationInsight]:
        """Analiza y optimiza el rendimiento de mensajes y secuencias."""
        insights = []
        try:
            from app.domains.automations.models import SequenceEmailLog
            threshold = datetime.now(timezone.utc) - timedelta(days=14)

            query = select(
                func.count(SequenceEmailLog.id).label("total"),
                func.sum(
                    func.cast(SequenceEmailLog.status == "opened", "integer")
                ).label("opened"),
            ).where(SequenceEmailLog.sent_at >= threshold)

            result = await self.db.execute(query)
            row = result.one_or_none()

            if row and row[0] and row[0] > 0:
                open_rate = (row[1] or 0) / row[0]
                benchmark = self.BENCHMARKS["message_open_rate"]
                gap = ((open_rate - benchmark) / benchmark * 100)

                if open_rate < benchmark * 0.7:
                    insights.append(OptimizationInsight(
                        category="messaging",
                        metric="message_open_rate",
                        current_value=round(open_rate * 100, 1),
                        benchmark_value=round(benchmark * 100, 1),
                        gap_percent=round(gap, 1),
                        recommendation="Tasa de apertura baja. Recomendado: cambiar horarios de envío y revisar asuntos/primeras líneas.",
                        priority=3,
                    ))
        except Exception as e:
            logger.warning(f"[SelfOptimization] Error en message performance: {e}")
        return insights

    async def _optimize_agent_assignment(
        self, business_id: Optional[uuid.UUID]
    ) -> list[OptimizationInsight]:
        """Analiza qué agentes/personalidades tienen mejores tasas de conversión."""
        insights = []
        try:
            from app.domains.agents.models import AgentConversation, AgentPersonality
            from app.domains.crm.models import Deal

            threshold = datetime.now(timezone.utc) - timedelta(days=30)

            agent_conv_query = select(
                AgentConversation.personality_id,
                func.count(AgentConversation.id).label("conversations"),
            ).where(
                AgentConversation.created_at >= threshold,
                AgentConversation.is_active == True,
            )
            if business_id:
                agent_conv_query = agent_conv_query.where(
                    AgentConversation.business_id == business_id
                )

            result = await self.db.execute(
                agent_conv_query.group_by(AgentConversation.personality_id)
                .order_by(desc("conversations"))
                .limit(5)
            )
            top_agents = result.all()

            if top_agents:
                top_agent_id = top_agents[0][0]
                pers_result = await self.db.execute(
                    select(AgentPersonality).where(AgentPersonality.id == top_agent_id)
                )
                top_pers = pers_result.scalar_one_or_none()
                if top_pers:
                    insights.append(OptimizationInsight(
                        category="agent_assignment",
                        metric="top_performing_agent",
                        current_value=float(top_agents[0][1]),
                        benchmark_value=float(top_agents[0][1]),
                        gap_percent=0,
                        recommendation=f"Agente más usado: {top_pers.name} ({top_agents[0][1]} conversaciones). Considerar asignarlo como agente por defecto.",
                        priority=5,
                    ))
        except Exception as e:
            logger.warning(f"[SelfOptimization] Error en agent assignment: {e}")
        return insights

    async def _optimize_send_times(
        self, business_id: Optional[uuid.UUID]
    ) -> list[OptimizationInsight]:
        """Determina los mejores horarios de envío de mensajes por análisis de respuestas."""
        insights = []
        try:
            from app.domains.channels.models import Message
            threshold = datetime.now(timezone.utc) - timedelta(days=30)

            query = select(
                func.extract("hour", Message.created_at).label("hour"),
                func.count(Message.id).label("message_count"),
            ).where(
                and_(
                    Message.created_at >= threshold,
                    Message.sender_type == "contact",
                )
            )
            if business_id:
                from app.domains.channels.models import Conversation
                query = query.join(Conversation, Message.conversation_id == Conversation.id)
                query = query.where(Conversation.business_id == business_id)

            result = await self.db.execute(
                query.group_by("hour").order_by(desc("message_count")).limit(3)
            )
            top_hours = result.all()

            if top_hours:
                peak_hours = [int(row[0]) for row in top_hours]
                insights.append(OptimizationInsight(
                    category="send_time",
                    metric="peak_engagement_hours",
                    current_value=float(peak_hours[0]),
                    benchmark_value=float(peak_hours[0]),
                    gap_percent=0,
                    recommendation=f"Horas pico de respuesta del cliente: {', '.join(f'{h}:00' for h in peak_hours)}. Programar campañas en estos horarios para mayor efectividad.",
                    priority=6,
                ))
        except Exception as e:
            logger.warning(f"[SelfOptimization] Error en send times: {e}")
        return insights

    async def run_ab_test_analysis(
        self, business_id: uuid.UUID
    ) -> dict[str, Any]:
        """Analiza resultados de A/B tests y promueve el ganador."""
        try:
            from app.domains.feedback.models import FeatureFlag

            result = await self.db.execute(
                select(FeatureFlag).where(
                    FeatureFlag.business_id == business_id,
                    FeatureFlag.is_ab_test == True,
                    FeatureFlag.is_active == True,
                )
            )
            active_tests = result.scalars().all()

            if not active_tests:
                return {"status": "no_active_tests"}

            promoted = []
            for test in active_tests:
                results = test.ab_results or {}
                variant_a = results.get("variant_a", {}).get("conversion_rate", 0)
                variant_b = results.get("variant_b", {}).get("conversion_rate", 0)
                sample_size = results.get("total_samples", 0)

                if sample_size >= 100 and abs(variant_a - variant_b) > 0.05:
                    winner = "a" if variant_a > variant_b else "b"
                    test.winner = winner
                    test.is_ab_test = False
                    promoted.append({"test": test.name, "winner": winner})
                    logger.info(f"[SelfOptimization] A/B test '{test.name}' → ganador: variante {winner}")

            if promoted:
                await self.db.commit()

            return {"tests_analyzed": len(active_tests), "promoted": promoted}
        except Exception as e:
            logger.warning(f"[SelfOptimization] Error en A/B analysis: {e}")
            return {"status": "error", "error": str(e)}

    def get_top_insights(self, n: int = 10) -> list[dict[str, Any]]:
        """Retorna los N insights más recientes y prioritarios."""
        sorted_insights = sorted(
            self._optimization_history,
            key=lambda i: (i.priority, -i.timestamp.timestamp()),
        )
        return [
            {
                "category": i.category,
                "metric": i.metric,
                "current": i.current_value,
                "benchmark": i.benchmark_value,
                "gap_percent": i.gap_percent,
                "recommendation": i.recommendation,
            }
            for i in sorted_insights[:n]
        ]
