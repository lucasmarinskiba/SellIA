"""Agentes IA - System Prompts de Expertos

DEPRECATED: This module is kept for backward compatibility.
All prompts have been moved to the prompts/ package for modularity.

Use: from app.domains.agents.prompts import AGENT_PROMPTS, get_system_prompt, compose_system_prompt
"""

from app.domains.agents.prompts import AGENT_PROMPTS, get_system_prompt, compose_system_prompt

__all__ = ["AGENT_PROMPTS", "get_system_prompt", "compose_system_prompt"]
