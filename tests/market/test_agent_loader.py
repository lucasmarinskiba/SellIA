"""Test agent loader."""

import pytest
from app.core.market import AgentLoader, MarketDetector, Industry, BusinessModel


def test_load_sellIA_base():
    """Test loading base SellIA agent."""
    agent = AgentLoader._load_sellIA_base()
    
    assert agent["id"] == "sellIA_base"
    assert agent["type"] == "orchestrator"
    assert "lead_capture" in agent["capabilities"]


def test_load_real_estate_agents():
    """Test loading real estate agents."""
    agents = AgentLoader._load_real_estate_agent("realEstate_leadScorer", None)
    
    assert agents is not None
    assert agents["type"] == "qualifier"


def test_load_agents_for_market():
    """Test loading agents for market profile."""
    profile = MarketDetector.detect_market("Vendo propiedades inmobiliarias")
    agents = AgentLoader.load_agents_for_market(profile)
    
    assert len(agents) > 0
    assert any(a.get("id") == "realEstate_leadScorer" for a in agents)
