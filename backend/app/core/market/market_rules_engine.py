"""Market Rules Engine — Load & apply market-specific rules."""

import logging
from typing import Any, ClassVar

import yaml

logger = logging.getLogger(__name__)


class MarketRulesEngine:
    """Load YAML rules and apply to sales process."""

    _rules_cache: ClassVar[dict[str, dict[str, Any]]] = {}

    @staticmethod
    def load_rules(market_type: str, rules_file: str) -> dict[str, Any]:
        """Load YAML rules for market."""
        if market_type in MarketRulesEngine._rules_cache:
            return MarketRulesEngine._rules_cache[market_type]

        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f) or {}
            MarketRulesEngine._rules_cache[market_type] = rules
            logger.info(f"Loaded rules for {market_type} from {rules_file}")
            return rules
        except FileNotFoundError:
            logger.warning(f"Rules file {rules_file} not found. Using defaults.")
            return MarketRulesEngine._get_default_rules()

    @staticmethod
    def get_sales_phases(rules: dict[str, Any]) -> list[str]:
        """Get sales cycle phases from rules."""
        return rules.get(
            "sales_phases",
            ["discovery", "qualification", "proposal", "negotiation", "closing"],
        )

    @staticmethod
    def get_sales_cycle_timeline(rules: dict[str, Any]) -> dict[str, int]:
        """Get sales cycle timeline (min, avg, max days)."""
        return rules.get("sales_cycle", {"min": 5, "avg": 30, "max": 90})

    @staticmethod
    def get_pricing_rules(rules: dict[str, Any]) -> dict[str, Any]:
        """Get pricing rules (fixed/dynamic/negotiable)."""
        return rules.get("pricing_rules", {"type": "fixed"})

    @staticmethod
    def get_payment_rules(rules: dict[str, Any]) -> dict[str, Any]:
        """Get payment rules (one-time/recurring/installments)."""
        return rules.get("payment_rules", {"type": "one_time", "terms": 0})

    @staticmethod
    def get_commission_structure(rules: dict[str, Any]) -> dict[str, Any]:
        """Get commission/margin structure."""
        return rules.get("commission_structure", {"type": "percentage", "rate": 10})

    @staticmethod
    def get_legal_requirements(
        rules: dict[str, Any], jurisdiction: str = "default"
    ) -> list[str]:
        """Get legal/compliance requirements."""
        legal = rules.get("legal_requirements", {})
        return legal.get(jurisdiction, [])

    @staticmethod
    def is_phase_required(rules: dict[str, Any], phase: str) -> bool:
        """Check if phase is required in sales cycle."""
        phases = MarketRulesEngine.get_sales_phases(rules)
        return phase in phases

    @staticmethod
    def get_phase_duration(rules: dict[str, Any], phase: str) -> dict[str, int]:
        """Get expected duration for phase (min, avg, max days)."""
        phase_durations = rules.get("phase_durations", {})
        return phase_durations.get(phase, {"min": 1, "avg": 7, "max": 14})

    @staticmethod
    def _get_default_rules() -> dict[str, Any]:
        """Default rules if file not found."""
        return {
            "sales_phases": [
                "discovery",
                "qualification",
                "proposal",
                "negotiation",
                "closing",
            ],
            "sales_cycle": {"min": 5, "avg": 30, "max": 90},
            "pricing_rules": {"type": "flexible"},
            "payment_rules": {"type": "one_time"},
            "commission_structure": {"type": "percentage", "rate": 10},
            "legal_requirements": {},
        }

    @staticmethod
    def apply_rules_to_context(
        rules: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply market rules to conversation context."""
        context["sales_phases"] = MarketRulesEngine.get_sales_phases(rules)
        context["expected_cycle"] = MarketRulesEngine.get_sales_cycle_timeline(rules)
        context["pricing"] = MarketRulesEngine.get_pricing_rules(rules)
        context["payment"] = MarketRulesEngine.get_payment_rules(rules)
        context["commission"] = MarketRulesEngine.get_commission_structure(rules)
        return context

    @staticmethod
    def clear_cache() -> None:
        """Clear cached rules (used by continuous learner)."""
        MarketRulesEngine._rules_cache.clear()
        logger.info("Rules cache cleared.")
