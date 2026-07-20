"""Sellía Brain Prompt Library — 200+ prompts across 5 domains.

This module provides a comprehensive prompt library for the Sellía Brain system,
featuring 200+ carefully crafted prompts optimized for autonomous sales execution:

CORE PROMPTS (200):
- 50 Marketing Prompts: Content, campaigns, channels, audience analysis, conversion, retention
- 50 Sales Prompts: Discovery, qualification, proposal, negotiation, closing, account management
- 50 Positioning Prompts: Value prop, brand messaging, competitive positioning, market entry
- 50 Retention Prompts: Customer experience, engagement, churn prevention, loyalty, upsell, NPS

EXPERT VOICES (335+):
- 20 Expert Voice Systems with 335+ specialized prompts
- Trump (18), Belfort (18), Hormozi (18), Cardone (18)
- Buffett (17), Kiyosaki (17), Robbins (17), GaryVee (17), Dalio (17)
- Miner (16), Elliott (16), Loidi (16), Ribas (15), Galperin (15)
- Rocca (15), Galuccio (15), Ravikant (15), Taleb (15), Graham (14), Benioff (14)

Each prompt includes:
  - Business context (SaaS, e-commerce, services, real estate, etc.)
  - Variables for dynamic injection
  - Example input/output
  - Success metrics
  - Industry-specific variations
  - Best practice tips

Usage - Base Prompts:
  from app.core.prompts import PromptRegistry, PromptOrchestrator

  registry = PromptRegistry()
  prompt = registry.get_prompt("market_research", industry="SaaS")
  result = PromptOrchestrator.execute(prompt, context_vars)

Usage - Expert Voices:
  from app.core.prompts.expert_voices import (
      ExpertVoiceManager, SalesContext, SalesScenario
  )

  manager = ExpertVoiceManager()
  scenario = SalesScenario(context=SalesContext.CLOSING, ...)
  result = await manager.get_expert_response(scenario, customer_message)
"""

from .prompt_registry import PromptRegistry
from .prompt_orchestrator import PromptOrchestrator
from .marketing_prompts import MarketingPrompts
from .sales_prompts import SalesPrompts
from .positioning_prompts import PositioningPrompts
from .retention_prompts import RetentionPrompts

# Import expert voices system
try:
    from .expert_voices import (
        ExpertVoiceManager,
        ExpertType, SalesContext,
        ExpertSelector, SalesScenario,
        ExpertOrchestrator, PromptExecutionMode,
        EXPERT_COUNT, PROMPT_COUNT
    )
except ImportError:
    # Expert voices module may not be available
    pass

__all__ = [
    "PromptRegistry",
    "PromptOrchestrator",
    "MarketingPrompts",
    "SalesPrompts",
    "PositioningPrompts",
    "RetentionPrompts",
    # Expert voices (if available)
    "ExpertVoiceManager",
    "ExpertType",
    "SalesContext",
    "ExpertSelector",
    "SalesScenario",
    "ExpertOrchestrator",
    "PromptExecutionMode",
]
