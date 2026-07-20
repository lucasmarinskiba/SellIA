"""Test market rules engine."""

import pytest
from app.core.market import MarketRulesEngine


def test_load_default_rules():
    """Test loading default rules."""
    rules = MarketRulesEngine._get_default_rules()
    
    assert "sales_phases" in rules
    assert "sales_cycle" in rules
    assert "pricing_rules" in rules


def test_get_sales_phases():
    """Test getting sales phases."""
    rules = MarketRulesEngine._get_default_rules()
    phases = MarketRulesEngine.get_sales_phases(rules)
    
    assert isinstance(phases, list)
    assert len(phases) > 0


def test_get_sales_cycle_timeline():
    """Test getting sales cycle timeline."""
    rules = MarketRulesEngine._get_default_rules()
    timeline = MarketRulesEngine.get_sales_cycle_timeline(rules)
    
    assert "min" in timeline
    assert "avg" in timeline
    assert "max" in timeline
    assert timeline["min"] <= timeline["avg"] <= timeline["max"]


def test_apply_rules_to_context():
    """Test applying rules to context."""
    rules = MarketRulesEngine._get_default_rules()
    context = {}
    
    result = MarketRulesEngine.apply_rules_to_context(rules, context)
    
    assert "sales_phases" in result
    assert "expected_cycle" in result
    assert "pricing" in result
