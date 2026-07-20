"""
LLM Smart Router

Classifies tasks by complexity and routes them to the cheapest adequate model.
Simple FAQ → Ollama local or GPT-4o-mini
Medium copy → Claude 3.5 Haiku / GPT-4o-mini
Complex strategy → GPT-4o / Claude 3.5 Sonnet

Typical savings: 40-60% on mixed workloads.
"""

import re
from typing import Tuple, Optional
from enum import Enum

from app.core.logger import get_logger

logger = get_logger(__name__)


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


# Keywords that indicate complexity level
_SIMPLE_KEYWORDS = [
    "cómo", "qué es", "dónde", "cuándo", "cuál", "definición",
    "hello", "hi", "hola", "gracias", "thanks", "ok", "sí", "no",
    "status", "estado", "precio", "price", "plan", "billing",
]

_COMPLEX_KEYWORDS = [
    "estrategia", "strategy", "análisis detallado", "deep analysis",
    "plan de acción", "action plan", "investigación", "research",
    "comparativa", "benchmark", "optimización avanzada", "advanced optimization",
    "modelo de negocio", "business model", "proyección", "forecast",
    "diagnóstico completo", "full diagnostic",
]

# Model tiers by cost (cheapest first)
TIER_SIMPLE = [
    ("ollama", "llama3.2:1b"),               # free, local
    ("groq", "llama-3.1-8b-instant"),        # free, sub-second
    ("openai", "gpt-4o-mini"),               # very cheap
]
TIER_MEDIUM = [
    ("groq", "llama-3.3-70b-versatile"),     # free, strong + fast
    ("openai", "gpt-4o-mini"),
    ("anthropic", "claude-3-5-haiku-20241022"),
    ("kimi", "kimi-k2-5"),
]
TIER_COMPLEX = [
    ("openai", "gpt-4o"),
    ("anthropic", "claude-3-5-sonnet-20241022"),
    ("groq", "llama-3.3-70b-versatile"),     # free fallback for complex
    ("kimi", "kimi-k2-5"),
]


def classify_task(prompt: str) -> TaskComplexity:
    """Heuristic classifier for task complexity."""
    text = prompt.lower()
    length = len(text)

    # Fast path: very short = simple
    if length < 120:
        return TaskComplexity.SIMPLE

    # Fast path: very long = complex
    if length > 1200:
        return TaskComplexity.COMPLEX

    # Count complexity keywords
    simple_score = sum(1 for kw in _SIMPLE_KEYWORDS if kw in text)
    complex_score = sum(1 for kw in _COMPLEX_KEYWORDS if kw in text)

    # If explicit complex keywords, upgrade
    if complex_score > 0:
        return TaskComplexity.COMPLEX

    # If mostly simple keywords and short-ish
    if simple_score > 0 and length < 400:
        return TaskComplexity.SIMPLE

    # Medium length with no strong signals
    if length < 600:
        return TaskComplexity.MEDIUM

    return TaskComplexity.COMPLEX


def route_model(
    prompt: str,
    ollama_available: bool = False,
    groq_available: bool = False,
) -> Tuple[str, str, TaskComplexity]:
    """
    Returns (provider, model, complexity) for the given prompt.

    Args:
        prompt: The user prompt.
        ollama_available: Whether local Ollama is reachable.
        groq_available: Whether a Groq API key/endpoint is configured.
    """
    complexity = classify_task(prompt)

    if complexity == TaskComplexity.SIMPLE:
        tier = list(TIER_SIMPLE)
    elif complexity == TaskComplexity.MEDIUM:
        tier = list(TIER_MEDIUM)
    else:
        tier = list(TIER_COMPLEX)

    # Filter out providers that are not reachable/configured.
    if not ollama_available:
        tier = [(p, m) for p, m in tier if p != "ollama"]
    if not groq_available:
        tier = [(p, m) for p, m in tier if p != "groq"]

    if not tier:
        # Ultimate fallback
        return ("openai", "gpt-4o-mini", complexity)

    provider, model = tier[0]
    logger.info(f"LLM Router: complexity={complexity.value} → {provider}/{model}")
    return provider, model, complexity


def estimate_cost_usd(prompt: str, complexity: TaskComplexity) -> float:
    """Rough cost estimate for logging/metrics (per 1K tokens)."""
    # Approximate prices per 1K output tokens (as of 2025)
    prices = {
        TaskComplexity.SIMPLE: 0.0006,    # gpt-4o-mini
        TaskComplexity.MEDIUM: 0.003,     # haiku / mini
        TaskComplexity.COMPLEX: 0.015,    # gpt-4o / sonnet
    }
    return prices.get(complexity, 0.003)
