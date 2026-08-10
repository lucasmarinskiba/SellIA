"""Agent Router - Orchestrates lead flow through specialized agents."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.domains.agents.base_agent import (
    AgentType,
    AgentContext,
    AgentDecision,
)
from app.domains.agents.specialized_agents import AGENT_REGISTRY

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Central orchestrator that routes leads through the pipeline
    using the most appropriate specialized agent at each stage.
    """

    def __init__(self, max_hops: int = 10, escalation_threshold: int = 3):
        self.max_hops = max_hops
        self.escalation_threshold = escalation_threshold
        self.routing_history: List[Dict[str, Any]] = []

    async def route_lead(self, context: AgentContext) -> Dict[str, Any]:
        """
        Main orchestration: Route lead through agent pipeline
        until closed, escalated to human, or max hops reached.
        """
        context.created_at = context.created_at or datetime.utcnow()
        context.agent_history = []

        hop_count = 0
        escalation_count = 0
        current_agent = None

        while hop_count < self.max_hops:
            hop_count += 1

            # Find best agent for current context
            next_agent_type = await self._find_best_agent(context)

            if not next_agent_type:
                logger.warning(f"No suitable agent found for lead {context.lead_id}")
                return await self._escalate_to_human(context, "No agent match")

            current_agent = AGENT_REGISTRY.get(next_agent_type)
            if not current_agent:
                logger.error(f"Agent not found: {next_agent_type}")
                return await self._escalate_to_human(
                    context, f"Agent missing: {next_agent_type}"
                )

            logger.info(
                f"Lead {context.lead_id} → {current_agent.name} (hop {hop_count})"
            )

            # Execute agent
            try:
                start_time = datetime.utcnow()
                decision = await current_agent.execute(context)
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Record in history
                context.agent_history.append(
                    {
                        "agent": current_agent.name,
                        "agent_type": next_agent_type.value,
                        "action": decision.action,
                        "confidence": decision.confidence,
                        "reasoning": decision.reasoning,
                        "elapsed_ms": elapsed_ms,
                        "timestamp": start_time.isoformat(),
                    }
                )

                # Update context for next agent
                context.assigned_agent = current_agent.name
                context.updated_at = datetime.utcnow()

                # Check if should escalate
                if decision.should_escalate:
                    escalation_count += 1
                    if escalation_count >= self.escalation_threshold:
                        logger.warning(
                            f"Escalation threshold reached for lead {context.lead_id}"
                        )
                        return await self._escalate_to_human(
                            context, f"Agent requested escalation {escalation_count} times"
                        )

                # Check if pipeline complete
                if decision.next_agent is None:
                    logger.info(
                        f"Lead {context.lead_id} completed pipeline: {current_agent.name}"
                    )
                    return await self._finalize_lead(context, decision)

                # Update stage for next agent
                context.current_stage = decision.next_agent.value

            except Exception as e:
                logger.exception(
                    f"Agent execution failed: {next_agent_type} for lead {context.lead_id}"
                )
                return await self._escalate_to_human(
                    context, f"Agent error: {str(e)}"
                )

        # Max hops reached
        logger.warning(
            f"Max hops ({self.max_hops}) reached for lead {context.lead_id}"
        )
        return await self._escalate_to_human(
            context, f"Pipeline max hops exceeded"
        )

    async def _find_best_agent(self, context: AgentContext) -> Optional[AgentType]:
        """
        Evaluate all agents and find best match for current context.
        Agents are scored by suitability.
        """
        scores: Dict[AgentType, float] = {}

        for agent_type, agent in AGENT_REGISTRY.items():
            try:
                # Check if agent can handle this context
                can_handle = await agent.evaluate(context)
                if not can_handle:
                    continue

                # Calculate score based on agent performance
                base_score = 0.8 if can_handle else 0.0
                performance_bonus = agent.success_rate * 0.2
                scores[agent_type] = base_score + performance_bonus

            except Exception as e:
                logger.error(f"Agent evaluation failed: {agent_type} - {e}")
                continue

        if not scores:
            return None

        # Return agent with highest score
        best_agent = max(scores, key=scores.get)
        logger.debug(
            f"Agent selection scores: {[(k.value, v) for k, v in scores.items()]}"
        )
        return best_agent

    async def _escalate_to_human(
        self, context: AgentContext, reason: str
    ) -> Dict[str, Any]:
        """Escalate to human sales representative."""
        logger.warning(f"Escalating lead {context.lead_id}: {reason}")

        return {
            "status": "escalated",
            "escalation_reason": reason,
            "lead_context": context.dict(),
            "assigned_to": "human_sales_rep",
            "action": "route_to_human_queue",
            "priority": "high" if context.intent_score >= 0.8 else "medium",
        }

    async def _finalize_lead(
        self, context: AgentContext, final_decision: AgentDecision
    ) -> Dict[str, Any]:
        """Finalize completed lead journey."""
        return {
            "status": "completed",
            "lead_context": context.dict(),
            "final_action": final_decision.action,
            "final_data": final_decision.data,
            "total_hops": len(context.agent_history),
            "completion_time_hours": (
                (datetime.utcnow() - context.created_at).total_seconds() / 3600
            ),
            "agent_path": [h["agent"] for h in context.agent_history],
        }

    async def get_agent_performance(self) -> Dict[str, Any]:
        """Get metrics for all agents."""
        performance = {}

        for agent_type, agent in AGENT_REGISTRY.items():
            perf = await agent.get_metrics()
            performance[agent_type.value] = {
                **perf,
                "execution_count": agent.execution_count,
                "success_rate": agent.success_rate,
                "avg_response_time_ms": agent.avg_response_time,
            }

        return performance

    async def batch_route_leads(
        self, contexts: List[AgentContext]
    ) -> List[Dict[str, Any]]:
        """Route multiple leads in parallel."""
        logger.info(f"Batch routing {len(contexts)} leads")

        results = await asyncio.gather(
            *[self.route_lead(ctx) for ctx in contexts],
            return_exceptions=False,
        )

        return results
