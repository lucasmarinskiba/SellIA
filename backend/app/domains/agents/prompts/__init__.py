"""Agent prompts - Modular loader

Loads agent prompts from category files in the categories/ directory.
Each category file exports an AGENTS dict: {slug: prompt_text}.
"""

import os
import importlib.util
from pathlib import Path
from typing import Dict


def _load_category_prompts() -> Dict[str, str]:
    """Dynamically load all agent prompts from category files."""
    prompts: Dict[str, str] = {}
    categories_dir = Path(__file__).parent / "categories"

    if not categories_dir.exists():
        return prompts

    for file_path in sorted(categories_dir.glob("*.py")):
        if file_path.name.startswith("_"):
            continue

        spec = importlib.util.spec_from_file_location(
            f"agents.prompts.categories.{file_path.stem}", file_path
        )
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "AGENTS"):
            agents = module.AGENTS
            if isinstance(agents, dict):
                # Validate no duplicates
                for slug in agents:
                    if slug in prompts:
                        raise ValueError(
                            f"Duplicate agent slug '{slug}' in {file_path.name}"
                        )
                prompts.update(agents)

    return prompts


AGENT_PROMPTS: Dict[str, str] = _load_category_prompts()


# Re-export composer for convenience
from app.domains.agents.prompts.composer import compose_system_prompt


def get_system_prompt(
    slug: str, business_context: dict = None, custom_instructions: str = None
) -> str:
    """Build the complete system prompt for an agent.

    NOTE: For functional auto-pilot agents with voice overrides,
    use compose_system_prompt() instead.
    """
    base = AGENT_PROMPTS.get(slug, AGENT_PROMPTS.get("alex-hormozi", ""))

    context_block = ""
    if business_context:
        ctx_parts = []
        if business_context.get("name"):
            ctx_parts.append(f"Business Name: {business_context['name']}")
        if business_context.get("type"):
            ctx_parts.append(f"Business Type: {business_context['type']}")
        if business_context.get("description"):
            ctx_parts.append(f"Description: {business_context['description']}")
        if business_context.get("catalog_summary"):
            ctx_parts.append(f"Products/Services: {business_context['catalog_summary']}")
        if ctx_parts:
            context_block = "\n\nBUSINESS CONTEXT:\n" + "\n".join(ctx_parts)

    custom = ""
    if custom_instructions:
        custom = f"\n\nCUSTOM INSTRUCTIONS FROM BUSINESS OWNER:\n{custom_instructions}"

    return (
        base
        + context_block
        + custom
        + "\n\nIMPORTANT: Respond in the same language the user is writing in (Spanish, English, etc.). Keep responses concise but actionable. Always end with a clear next step or action item."
    )
