"""Agent Loader — Load agents dynamically per market."""

import importlib
import sys
from typing import Any, Dict, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentLoader:
    """Load and cache agents per market."""

    _agent_cache: Dict[str, Any] = {}
    _loaded_modules: set[str] = set()

    @staticmethod
    def load_agents_for_market(market_profile: "MarketProfile") -> List[Any]:
        """Load agents matching market profile."""
        agents = []

        for agent_id in market_profile.recommended_agents:
            if agent_id in AgentLoader._agent_cache:
                agents.append(AgentLoader._agent_cache[agent_id])
            else:
                try:
                    agent = AgentLoader._load_agent(agent_id, market_profile)
                    if agent:
                        agents.append(agent)
                        AgentLoader._agent_cache[agent_id] = agent
                except Exception as e:
                    logger.error(f"Error loading agent {agent_id}: {e}")

        return agents

    @staticmethod
    def _load_agent(agent_id: str, market_profile: "MarketProfile") -> Any:
        """Load single agent by ID."""

        if agent_id == "sellIA_base":
            return AgentLoader._load_sellIA_base()
        elif agent_id.startswith("realEstate_"):
            return AgentLoader._load_real_estate_agent(agent_id, market_profile)
        elif agent_id.startswith("commerce_"):
            return AgentLoader._load_commerce_agent(agent_id, market_profile)
        elif agent_id.startswith("services_"):
            return AgentLoader._load_services_agent(agent_id, market_profile)
        elif agent_id.startswith("finance_"):
            return AgentLoader._load_finance_agent(agent_id, market_profile)
        elif agent_id.startswith("digital_"):
            return AgentLoader._load_digital_agent(agent_id, market_profile)

        return None

    @staticmethod
    def _load_sellIA_base() -> Dict[str, Any]:
        """Load SellIA base agent."""
        return {
            "id": "sellIA_base",
            "name": "SellIA Base Agent",
            "type": "orchestrator",
            "capabilities": ["lead_capture", "qualification", "negotiation", "closing", "payment", "delivery", "retention"],
            "priority": 100,
        }

    @staticmethod
    def _load_real_estate_agent(agent_id: str, profile: "MarketProfile") -> Dict[str, Any]:
        """Load Real Estate agent from external Agente Inmobiliario system."""
        agents = {
            "realEstate_leadScorer": {
                "id": "realEstate_leadScorer",
                "name": "Real Estate Lead Scorer",
                "type": "qualifier",
                "capabilities": ["lead_scoring", "buyer_profiling", "property_fit"],
                "priority": 90,
                "source": "Agente IA - Agente Inmobiliario",
            },
            "realEstate_propertyAnalyzer": {
                "id": "realEstate_propertyAnalyzer",
                "name": "Property Analyzer",
                "type": "analyzer",
                "capabilities": ["valuation", "market_comparison", "investment_analysis"],
                "priority": 85,
                "source": "Agente IA - Agente Inmobiliario",
            },
            "realEstate_negotiator": {
                "id": "realEstate_negotiator",
                "name": "Real Estate Negotiator",
                "type": "negotiator",
                "capabilities": ["offer_strategy", "terms_negotiation", "closing"],
                "priority": 95,
                "source": "Agente IA - Agente Inmobiliario",
            },
        }
        return agents.get(agent_id)

    @staticmethod
    def _load_commerce_agent(agent_id: str, profile: "MarketProfile") -> Dict[str, Any]:
        """Load Commerce agent from Asesor Comercial system."""
        agents = {
            "commerce_prospector": {
                "id": "commerce_prospector",
                "name": "Commerce Prospector",
                "type": "prospector",
                "capabilities": ["market_research", "competitor_analysis", "opportunity_identification"],
                "priority": 85,
                "source": "Agente IA - Asesor Comercial",
            },
            "commerce_advisor": {
                "id": "commerce_advisor",
                "name": "Commercial Advisor",
                "type": "advisor",
                "capabilities": ["strategy", "pricing", "positioning"],
                "priority": 90,
                "source": "Agente IA - Asesor Comercial",
            },
            "commerce_negotiator": {
                "id": "commerce_negotiator",
                "name": "Commerce Negotiator",
                "type": "negotiator",
                "capabilities": ["deal_structure", "terms_negotiation", "contract"],
                "priority": 95,
                "source": "Agente IA - Asesor Comercial",
            },
        }
        return agents.get(agent_id)

    @staticmethod
    def _load_services_agent(agent_id: str, profile: "MarketProfile") -> Dict[str, Any]:
        """Load Services agent."""
        agents = {
            "services_qualifier": {
                "id": "services_qualifier",
                "name": "Services Qualifier",
                "type": "qualifier",
                "capabilities": ["needs_analysis", "scope_definition", "fit_assessment"],
                "priority": 85,
            },
            "services_deliveryCoordinator": {
                "id": "services_deliveryCoordinator",
                "name": "Delivery Coordinator",
                "type": "coordinator",
                "capabilities": ["project_planning", "milestone_tracking", "quality_assurance"],
                "priority": 80,
            },
        }
        return agents.get(agent_id)

    @staticmethod
    def _load_finance_agent(agent_id: str, profile: "MarketProfile") -> Dict[str, Any]:
        """Load Finance agent."""
        agents = {
            "finance_advisor": {
                "id": "finance_advisor",
                "name": "Finance Advisor",
                "type": "advisor",
                "capabilities": ["portfolio_analysis", "risk_assessment", "strategy"],
                "priority": 90,
            },
            "finance_riskAssessor": {
                "id": "finance_riskAssessor",
                "name": "Risk Assessor",
                "type": "analyzer",
                "capabilities": ["risk_profiling", "compliance", "aml_kyc"],
                "priority": 95,
            },
        }
        return agents.get(agent_id)

    @staticmethod
    def _load_digital_agent(agent_id: str, profile: "MarketProfile") -> Dict[str, Any]:
        """Load Digital Products agent."""
        agents = {
            "digital_converter": {
                "id": "digital_converter",
                "name": "Digital Converter",
                "type": "converter",
                "capabilities": ["landing_page_optimization", "funnel_design", "cro"],
                "priority": 85,
            },
            "digital_retention": {
                "id": "digital_retention",
                "name": "Retention Agent",
                "type": "retention",
                "capabilities": ["churn_prevention", "upsell", "community_building"],
                "priority": 80,
            },
        }
        return agents.get(agent_id)

    @staticmethod
    def reload_agents() -> None:
        """Force reload all agents (used by continuous learner)."""
        AgentLoader._agent_cache.clear()
        AgentLoader._loaded_modules.clear()
        logger.info("Agent cache cleared. Next load will refresh from sources.")

    @staticmethod
    def get_loaded_agents() -> List[str]:
        """List all loaded agent IDs."""
        return list(AgentLoader._agent_cache.keys())
