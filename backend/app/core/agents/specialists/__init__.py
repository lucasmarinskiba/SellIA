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

from .advertising_agent import AdPlatform, AdvertisingAgent, BidStrategy
from .business_agent import BusinessAgent, CostType, RevenueModel, UnitEconomics
from .development_agent import DevelopmentAgent, GrowthHackingTactic, TechStackLayer
from .financial_agent import (
    FinancialAgent,
    FinancialMetric,
    PricingModel,
    PricingStrategy,
)
from .innovation_agent import DisruptionType, InnovationAgent
from .marketing_agent import AudienceSegment, MarketingAgent, MarketingChannel
from .methodology_agent import BusinessStage, BusinessType, MethodologyAgent
from .negotiation_agent import NegotiationAgent, NegotiationPhase, NegotiationType
from .sales_agent import ObjectionType, SalesAgent, SalesMethodology, SalesStage
from .storytelling_agent import CommunicationFramework, StorytellingAgent, StoryType

__all__ = [
    "AdPlatform",
    # Advertising Agent
    "AdvertisingAgent",
    "AudienceSegment",
    "BidStrategy",
    # Business Agent
    "BusinessAgent",
    "BusinessStage",
    "BusinessType",
    "CommunicationFramework",
    "CostType",
    # Development Agent
    "DevelopmentAgent",
    "DisruptionType",
    # Financial Agent
    "FinancialAgent",
    "FinancialMetric",
    "GrowthHackingTactic",
    # Innovation Agent
    "InnovationAgent",
    # Marketing Agent
    "MarketingAgent",
    "MarketingChannel",
    # Methodology Agent
    "MethodologyAgent",
    # Negotiation Agent
    "NegotiationAgent",
    "NegotiationPhase",
    "NegotiationType",
    "ObjectionType",
    "PricingModel",
    "PricingStrategy",
    "RevenueModel",
    # Sales Agent
    "SalesAgent",
    "SalesMethodology",
    "SalesStage",
    "StoryType",
    # Storytelling Agent
    "StorytellingAgent",
    "TechStackLayer",
    "UnitEconomics",
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
