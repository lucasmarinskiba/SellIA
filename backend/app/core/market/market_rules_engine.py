"""Market Rules Engine — Load & apply market-specific rules."""

import yaml
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MarketRulesEngine:
    """Load YAML rules and apply to sales process."""

    _rules_cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def load_rules(market_type: str, rules_file: str) -> Dict[str, Any]:
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
    def get_sales_phases(rules: Dict[str, Any]) -> List[str]:
        """Get sales cycle phases from rules."""
        return rules.get("sales_phases", ["discovery", "qualification", "proposal", "negotiation", "closing"])

    @staticmethod
    def get_sales_cycle_timeline(rules: Dict[str, Any]) -> Dict[str, int]:
        """Get sales cycle timeline (min, avg, max days)."""
        return rules.get("sales_cycle", {"min": 5, "avg": 30, "max": 90})

    @staticmethod
    def get_pricing_rules(rules: Dict[str, Any]) -> Dict[str, Any]:
        """Get pricing rules (fixed/dynamic/negotiable)."""
        return rules.get("pricing_rules", {"type": "fixed"})

    @staticmethod
    def get_payment_rules(rules: Dict[str, Any]) -> Dict[str, Any]:
        """Get payment rules (one-time/recurring/installments)."""
        return rules.get("payment_rules", {"type": "one_time", "terms": 0})

    @staticmethod
    def get_commission_structure(rules: Dict[str, Any]) -> Dict[str, Any]:
        """Get commission/margin structure."""
        return rules.get("commission_structure", {"type": "percentage", "rate": 10})

    @staticmethod
    def get_legal_requirements(rules: Dict[str, Any], jurisdiction: str = "default") -> List[str]:
        """Get legal/compliance requirements."""
        legal = rules.get("legal_requirements", {})
        return legal.get(jurisdiction, [])

    @staticmethod
    def is_phase_required(rules: Dict[str, Any], phase: str) -> bool:
        """Check if phase is required in sales cycle."""
        phases = MarketRulesEngine.get_sales_phases(rules)
        return phase in phases

    @staticmethod
    def get_phase_duration(rules: Dict[str, Any], phase: str) -> Dict[str, int]:
        """Get expected duration for phase (min, avg, max days)."""
        phase_durations = rules.get("phase_durations", {})
        return phase_durations.get(phase, {"min": 1, "avg": 7, "max": 14})

    @staticmethod
    def _get_default_rules() -> Dict[str, Any]:
        """Default rules if file not found."""
        return {
            "sales_phases": ["discovery", "qualification", "proposal", "negotiation", "closing"],
            "sales_cycle": {"min": 5, "avg": 30, "max": 90},
            "pricing_rules": {"type": "flexible"},
            "payment_rules": {"type": "one_time"},
            "commission_structure": {"type": "percentage", "rate": 10},
            "legal_requirements": {},
        }

    @staticmethod
    def apply_rules_to_context(rules: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
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
