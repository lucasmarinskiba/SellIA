"""
SellIA Specialist Agents Module

10 production-ready specialist agents providing deep expertise across:
- Business methodologies and frameworks
- Sales tactics and methodologies
- Marketing strategy and execution
- Advertising and media buying
- Business model and scaling
- Innovation and product strategy
- Technical strategy and growth hacking
- Financial modeling and pricing
- Negotiation and deal structuring
- Storytelling and communication
"""

from .methodology_agent import MethodologyAgent, BusinessStage, BusinessType
from .sales_agent import SalesAgent, SalesMethodology, SalesStage, ObjectionType
from .marketing_agent import MarketingAgent, MarketingChannel, AudienceSegment
from .advertising_agent import AdvertisingAgent, AdPlatform, BidStrategy
from .business_agent import BusinessAgent, RevenueModel, CostType, UnitEconomics
from .innovation_agent import InnovationAgent, DisruptionType
from .development_agent import DevelopmentAgent, TechStackLayer, GrowthHackingTactic
from .financial_agent import FinancialAgent, PricingStrategy, FinancialMetric, PricingModel
from .negotiation_agent import NegotiationAgent, NegotiationType, NegotiationPhase
from .storytelling_agent import StorytellingAgent, StoryType, CommunicationFramework

__all__ = [
    # Methodology Agent
    "MethodologyAgent",
    "BusinessStage",
    "BusinessType",

    # Sales Agent
    "SalesAgent",
    "SalesMethodology",
    "SalesStage",
    "ObjectionType",

    # Marketing Agent
    "MarketingAgent",
    "MarketingChannel",
    "AudienceSegment",

    # Advertising Agent
    "AdvertisingAgent",
    "AdPlatform",
    "BidStrategy",

    # Business Agent
    "BusinessAgent",
    "RevenueModel",
    "CostType",
    "UnitEconomics",

    # Innovation Agent
    "InnovationAgent",
    "DisruptionType",

    # Development Agent
    "DevelopmentAgent",
    "TechStackLayer",
    "GrowthHackingTactic",

    # Financial Agent
    "FinancialAgent",
    "PricingStrategy",
    "FinancialMetric",
    "PricingModel",

    # Negotiation Agent
    "NegotiationAgent",
    "NegotiationType",
    "NegotiationPhase",

    # Storytelling Agent
    "StorytellingAgent",
    "StoryType",
    "CommunicationFramework",
]

# Specialist agents registry for dynamic access
SPECIALIST_AGENTS = {
    "methodology": MethodologyAgent,
    "sales": SalesAgent,
    "marketing": MarketingAgent,
    "advertising": AdvertisingAgent,
    "business": BusinessAgent,
    "innovation": InnovationAgent,
    "development": DevelopmentAgent,
    "financial": FinancialAgent,
    "negotiation": NegotiationAgent,
    "storytelling": StorytellingAgent,
}

def get_agent(agent_name: str):
    """Get specialist agent by name."""
    return SPECIALIST_AGENTS.get(agent_name.lower())

def list_specialists() -> list:
    """List all available specialist agents."""
    return list(SPECIALIST_AGENTS.keys())
