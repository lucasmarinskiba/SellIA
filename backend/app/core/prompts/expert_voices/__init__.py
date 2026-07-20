"""
Expert Voices Module - 350 Expert Prompts for Sales Excellence
Production-ready expert voice system for Agente de Vendedor Automático (Sellía)

Contains 20 expert voices with 350+ tactical sales prompts
Fully integrated orchestration, selection, and execution pipeline
"""

# Import all expert prompt collections
from trump_prompts import TRUMP_PROMPTS, TrumpPrompt
from belfort_prompts import BELFORT_PROMPTS, BelfortPrompt
from buffett_prompts import BUFFETT_PROMPTS, BuffettPrompt
from kiyosaki_prompts import KIYOSAKI_PROMPTS, KiyosakiPrompt
from hormozi_cardone_prompts import (
    HORMOZI_PROMPTS, CARDONE_PROMPTS,
    HormoziCardonePrompt
)
from other_experts_prompts import (
    ROBBINS_PROMPTS, GARYVEE_PROMPTS, DALIO_PROMPTS, MINER_PROMPTS,
    ELLIOTT_PROMPTS, LOIDI_PROMPTS, RIBAS_PROMPTS, GALPERIN_PROMPTS,
    ROCCA_PROMPTS, GALUCCIO_PROMPTS, RAVIKANT_PROMPTS, TALEB_PROMPTS,
    GRAHAM_PROMPTS, BENIOFF_PROMPTS, ExpertPrompt
)

# Import orchestration and selection systems
from prompt_registry import (
    ExpertType, SalesContext, ExpertMetadata,
    EXPERT_METADATA, PROMPT_INVENTORY, TOTAL_PROMPTS,
    CONTEXT_RECOMMENDATIONS,
    get_expert_metadata, get_best_experts_for_context,
    get_all_expert_types, get_prompt_distribution
)

from expert_selector import (
    ExpertSelector, SalesScenario, ExpertSelection
)

from expert_orchestrator import (
    ExpertOrchestrator, PromptExecutionContext, PromptExecutionResult,
    PromptExecutionMode, PromptExecutionError
)

# Consolidated prompt repository
ALL_EXPERT_PROMPTS = {
    "trump": TRUMP_PROMPTS,
    "belfort": BELFORT_PROMPTS,
    "buffett": BUFFETT_PROMPTS,
    "kiyosaki": KIYOSAKI_PROMPTS,
    "hormozi": HORMOZI_PROMPTS,
    "cardone": CARDONE_PROMPTS,
    "robbins": ROBBINS_PROMPTS,
    "garyvee": GARYVEE_PROMPTS,
    "dalio": DALIO_PROMPTS,
    "miner": MINER_PROMPTS,
    "elliott": ELLIOTT_PROMPTS,
    "loidi": LOIDI_PROMPTS,
    "ribas": RIBAS_PROMPTS,
    "galperin": GALPERIN_PROMPTS,
    "rocca": ROCCA_PROMPTS,
    "galuccio": GALUCCIO_PROMPTS,
    "ravikant": RAVIKANT_PROMPTS,
    "taleb": TALEB_PROMPTS,
    "graham": GRAHAM_PROMPTS,
    "benioff": BENIOFF_PROMPTS,
}

# Flattened prompt list for indexing
FLAT_PROMPT_LIST = (
    TRUMP_PROMPTS +
    BELFORT_PROMPTS +
    BUFFETT_PROMPTS +
    KIYOSAKI_PROMPTS +
    HORMOZI_PROMPTS +
    CARDONE_PROMPTS +
    ROBBINS_PROMPTS +
    GARYVEE_PROMPTS +
    DALIO_PROMPTS +
    MINER_PROMPTS +
    ELLIOTT_PROMPTS +
    LOIDI_PROMPTS +
    RIBAS_PROMPTS +
    GALPERIN_PROMPTS +
    ROCCA_PROMPTS +
    GALUCCIO_PROMPTS +
    RAVIKANT_PROMPTS +
    TALEB_PROMPTS +
    GRAHAM_PROMPTS +
    BENIOFF_PROMPTS
)

# Metadata
__version__ = "1.0.0"
__title__ = "Expert Voices - 350 Sales Prompts"
__description__ = "Production-ready expert voice system for autonomous sales agents"
__author__ = "Agente IA - Vendedor Automático (Sellía)"

# Statistics
EXPERT_COUNT = len(ALL_EXPERT_PROMPTS)
PROMPT_COUNT = len(FLAT_PROMPT_LIST)

# Main interface for external use
class ExpertVoiceManager:
    """
    Main interface for expert voice system
    Handles initialization, selection, and execution
    """

    def __init__(self):
        self.orchestrator = ExpertOrchestrator()
        self.selector = ExpertSelector()
        self.available_experts = EXPERT_METADATA
        self.all_prompts = ALL_EXPERT_PROMPTS

    async def get_expert_response(
        self,
        scenario: SalesScenario,
        customer_message: str,
        conversation_history=None,
        additional_context=None
    ):
        """Execute expert prompt for sales situation"""
        return await self.orchestrator.execute_expert_prompt(
            scenario=scenario,
            customer_message=customer_message,
            conversation_history=conversation_history,
            additional_context=additional_context
        )

    def select_experts(self, scenario: SalesScenario):
        """Select best experts for scenario"""
        import asyncio
        return asyncio.run(self.selector.select_experts(scenario))

    def get_available_experts(self):
        """Get all available expert metadata"""
        return self.available_experts

    def get_prompt_distribution(self):
        """Get prompt distribution by expert"""
        return {name: len(prompts) for name, prompts in self.all_prompts.items()}

    def get_analytics(self):
        """Get system analytics"""
        return {
            "total_experts": EXPERT_COUNT,
            "total_prompts": PROMPT_COUNT,
            "prompt_distribution": self.get_prompt_distribution(),
            "orchestrator_analytics": self.orchestrator.get_execution_analytics(),
            "selector_analytics": self.selector.get_performance_analytics()
        }


# Public API exports
__all__ = [
    # Expert prompt collections
    "TRUMP_PROMPTS", "BELFORT_PROMPTS", "BUFFETT_PROMPTS", "KIYOSAKI_PROMPTS",
    "HORMOZI_PROMPTS", "CARDONE_PROMPTS", "ROBBINS_PROMPTS", "GARYVEE_PROMPTS",
    "DALIO_PROMPTS", "MINER_PROMPTS", "ELLIOTT_PROMPTS", "LOIDI_PROMPTS",
    "RIBAS_PROMPTS", "GALPERIN_PROMPTS", "ROCCA_PROMPTS", "GALUCCIO_PROMPTS",
    "RAVIKANT_PROMPTS", "TALEB_PROMPTS", "GRAHAM_PROMPTS", "BENIOFF_PROMPTS",

    # Prompt data structures
    "TrumpPrompt", "BelfortPrompt", "BuffettPrompt", "KiyosakiPrompt",
    "HormoziCardonePrompt", "ExpertPrompt",

    # Registries and metadata
    "ExpertType", "SalesContext", "ExpertMetadata",
    "EXPERT_METADATA", "PROMPT_INVENTORY", "TOTAL_PROMPTS",
    "CONTEXT_RECOMMENDATIONS",

    # Registry functions
    "get_expert_metadata", "get_best_experts_for_context",
    "get_all_expert_types", "get_prompt_distribution",

    # Selection and execution
    "ExpertSelector", "SalesScenario", "ExpertSelection",
    "ExpertOrchestrator", "PromptExecutionContext", "PromptExecutionResult",
    "PromptExecutionMode", "PromptExecutionError",

    # Consolidated data
    "ALL_EXPERT_PROMPTS", "FLAT_PROMPT_LIST",

    # Main interface
    "ExpertVoiceManager",

    # Module metadata
    "__version__", "__title__", "__description__", "__author__",
    "EXPERT_COUNT", "PROMPT_COUNT"
]


# Optional: Initialize default manager
_default_manager = None

def get_expert_voice_manager():
    """Get or create default expert voice manager"""
    global _default_manager
    if _default_manager is None:
        _default_manager = ExpertVoiceManager()
    return _default_manager


# Quick helper functions
def select_expert_for_context(context: SalesContext):
    """Quick helper to select expert for context"""
    manager = get_expert_voice_manager()
    recommended = CONTEXT_RECOMMENDATIONS.get(context, [])
    if recommended:
        return EXPERT_METADATA[recommended[0]]
    return None


def get_all_expert_types_list():
    """Get list of all expert types"""
    return [e.value for e in ExpertType]


def get_prompt_count_by_expert():
    """Get prompt count for each expert"""
    manager = get_expert_voice_manager()
    return manager.get_prompt_distribution()
