"""Delegation Layer — SellIA → Real Estate Agent integration."""

import logging
from typing import Any, Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class DelegationResult(str, Enum):
    HANDLED_BY_SELLIAS = "handled_by_sellias"
    DELEGATED_TO_REAL_ESTATE = "delegated_to_real_estate"
    DELEGATED_TO_OTHER = "delegated_to_other"


class DelegationLayer:
    """Route conversations to appropriate agent system."""

    def __init__(self):
        self.real_estate_orchestrator = None
        self.other_agents = {}
        self.delegation_log: List[Dict[str, Any]] = []

    def set_real_estate_orchestrator(self, orchestrator: Any) -> None:
        """Set real estate orchestrator reference."""
        self.real_estate_orchestrator = orchestrator
        logger.info("Real Estate Orchestrator registered for delegation")

    def register_agent_system(self, system_name: str, agent_system: Any) -> None:
        """Register external agent system."""
        self.other_agents[system_name] = agent_system
        logger.info(f"Registered agent system: {system_name}")

    async def delegate_conversation(
        self, market_profile: "MarketProfile", lead_data: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Delegate conversation to appropriate agent system."""

        if market_profile.industry.value == "real_estate":
            return await self._delegate_to_real_estate(lead_data, session_id)
        else:
            return await self._handle_with_sellias(market_profile, lead_data, session_id)

    async def _delegate_to_real_estate(self, lead_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Delegate to Real Estate Agent system."""
        if not self.real_estate_orchestrator:
            logger.error("Real Estate Orchestrator not initialized")
            return {"error": "Real estate system not available"}

        try:
            # Start conversation in real estate orchestrator
            conversation_state = self.real_estate_orchestrator.start_conversation(session_id)

            # Process initial lead data
            response = await self.real_estate_orchestrator.process_message(
                session_id, self._format_lead_for_real_estate(lead_data)
            )

            # Log delegation
            self.delegation_log.append({
                "session_id": session_id,
                "delegated_to": "real_estate_orchestrator",
                "lead_data": lead_data,
                "response": response,
            })

            logger.info(f"Delegated session {session_id} to Real Estate Orchestrator")

            return {
                "delegation_result": DelegationResult.DELEGATED_TO_REAL_ESTATE,
                "session_id": session_id,
                "orchestrator_response": response,
                "next_phase": conversation_state.phase.value,
            }

        except Exception as e:
            logger.error(f"Error delegating to real estate: {str(e)}")
            return {"error": f"Delegation failed: {str(e)}"}

    async def _handle_with_sellias(
        self, market_profile: "MarketProfile", lead_data: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Handle with SellIA's own agents."""
        logger.info(f"Handling session {session_id} with SellIA agents")

        self.delegation_log.append({
            "session_id": session_id,
            "delegated_to": "sellias_agents",
            "market_profile": market_profile.__dict__ if hasattr(market_profile, "__dict__") else {},
            "lead_data": lead_data,
        })

        return {
            "delegation_result": DelegationResult.HANDLED_BY_SELLIAS,
            "session_id": session_id,
            "market_profile": market_profile.__dict__ if hasattr(market_profile, "__dict__") else {},
            "recommended_agents": market_profile.recommended_agents,
        }

    def _format_lead_for_real_estate(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data as natural language for real estate orchestrator."""
        parts = []

        if lead_data.get("name"):
            parts.append(f"Lead name: {lead_data['name']}")

        if lead_data.get("budget_min") and lead_data.get("budget_max"):
            parts.append(f"Budget: ${lead_data['budget_min']:,} - ${lead_data['budget_max']:,}")

        if lead_data.get("property_type"):
            parts.append(f"Looking for: {lead_data['property_type']}")

        if lead_data.get("location"):
            parts.append(f"Location: {lead_data['location']}")

        if lead_data.get("motivation"):
            parts.append(f"Motivation: {lead_data['motivation']}")

        if lead_data.get("timeline"):
            parts.append(f"Timeline: {lead_data['timeline']}")

        return " ".join(parts)

    def should_use_real_estate(self, market_profile: "MarketProfile") -> bool:
        """Determine if real estate agent should be used."""
        return market_profile.industry.value == "real_estate"

    def should_escalate_to_human(self, session_id: str, reason: str) -> Dict[str, Any]:
        """Escalate conversation to human agent."""
        logger.warning(f"Escalating session {session_id} to human: {reason}")

        result = {
            "session_id": session_id,
            "escalation_reason": reason,
            "escalated_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

        # Log escalation
        self.delegation_log.append({
            "session_id": session_id,
            "action": "escalated_to_human",
            "reason": reason,
        })

        return result

    def get_delegation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get delegation history for session."""
        return [log for log in self.delegation_log if log.get("session_id") == session_id]

    def analyze_delegation_patterns(self) -> Dict[str, Any]:
        """Analyze delegation patterns."""
        total_delegations = len(self.delegation_log)

        real_estate_count = sum(1 for log in self.delegation_log if log.get("delegated_to") == "real_estate_orchestrator")
        sellias_count = sum(1 for log in self.delegation_log if log.get("delegated_to") == "sellias_agents")
        escalations = sum(1 for log in self.delegation_log if log.get("action") == "escalated_to_human")

        return {
            "total_delegations": total_delegations,
            "to_real_estate_orchestrator": real_estate_count,
            "to_sellias": sellias_count,
            "escalated_to_human": escalations,
            "real_estate_percentage": (real_estate_count / total_delegations * 100) if total_delegations > 0 else 0,
            "success_rate": ((total_delegations - escalations) / total_delegations * 100) if total_delegations > 0 else 0,
        }

    def get_agent_routing_rules(self) -> Dict[str, List[str]]:
        """Get agent routing rules."""
        return {
            "real_estate": [
                "property_valuation",
                "buyer_qualification",
                "market_analysis",
                "offer_negotiation",
                "financing_guidance",
                "legal_compliance",
                "title_verification",
                "contract_generation",
                "closing_coordination",
            ],
            "commerce": [
                "market_research",
                "pricing_strategy",
                "inventory_management",
                "sales_forecasting",
                "customer_profiling",
            ],
            "services": [
                "scope_definition",
                "resource_allocation",
                "project_planning",
                "quality_assurance",
            ],
        }
