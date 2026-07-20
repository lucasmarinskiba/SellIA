"""Brain Orchestrator V3 — Market-Adaptive Orchestration."""

from typing import Dict, Any, Optional
import logging
from app.core.market import (
    MarketDetector,
    AgentLoader,
    MarketRulesEngine,
    ContinuousLearner,
    MarketContextInjector,
)

logger = logging.getLogger(__name__)


class BrainOrchestratorV3:
    """Orchestrate agents per market."""

    def __init__(self):
        self.detector = MarketDetector()
        self.learner = ContinuousLearner()
        self.context_map: Dict[str, Dict[str, Any]] = {}

    def initialize_for_seller(self, seller_id: str, user_input: str, company_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initialize market detection & agent loading for seller."""

        # Detect market
        market_profile = MarketDetector.detect_market(user_input, company_data)
        logger.info(f"Market detected for {seller_id}: {market_profile.industry.value} ({market_profile.confidence_score:.2%})")

        # Load agents
        agents = AgentLoader.load_agents_for_market(market_profile)
        logger.info(f"Loaded {len(agents)} agents for {market_profile.industry.value}")

        # Load rules
        rules = MarketRulesEngine.load_rules(
            market_profile.industry.value,
            market_profile.recommended_rules_file,
        )

        # Store context
        self.context_map[seller_id] = {
            "market_profile": market_profile,
            "agents": agents,
            "rules": rules,
            "initialized_at": str(__import__("datetime").datetime.utcnow()),
        }

        return {
            "seller_id": seller_id,
            "market": market_profile.industry.value,
            "agents": [a.get("id") for a in agents],
            "sales_phases": MarketRulesEngine.get_sales_phases(rules),
            "expected_cycle": MarketRulesEngine.get_sales_cycle_timeline(rules),
        }

    def get_market_context(self, seller_id: str) -> Optional[Dict[str, Any]]:
        """Get market context for seller."""
        return self.context_map.get(seller_id)

    def customize_prompt(self, seller_id: str, prompt: str, agent_id: str = "sellIA_base") -> str:
        """Customize prompt with market context."""
        context = self.get_market_context(seller_id)
        if not context:
            return prompt

        market_profile = context["market_profile"]
        rules = context["rules"]

        # Inject market context
        prompt = MarketContextInjector.inject_market_context(prompt, market_profile, rules)

        # Inject guardrails
        prompt = MarketContextInjector.inject_guardrails(prompt, market_profile, rules)

        return prompt

    def sync_external_systems(self) -> Dict[str, Any]:
        """Sync agents from external Real Estate & Commercial systems."""
        sync_result = self.learner.sync_from_external_systems()
        if sync_result["new_agents"]:
            AgentLoader.reload_agents()
            MarketRulesEngine.clear_cache()
            logger.info(f"Synced {len(sync_result['new_agents'])} new agents")
        return sync_result

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "active_sellers": len(self.context_map),
            "learning_status": self.learner.get_learning_status(),
            "loaded_agents": AgentLoader.get_loaded_agents(),
        }
