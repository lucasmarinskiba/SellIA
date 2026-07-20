"""Business Context Adapter for Autonomous Agents.

Provides reusable helpers to inject enriched BusinessContext into
agent prompts without duplicating logic across 15+ services.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.agents.context_builder import BusinessContextBuilder


async def get_agent_prompt_context(
    db: AsyncSession,
    business_id: Any,
    include_catalog: bool = True,
    max_catalog_items: int = 10,
) -> Dict[str, Any]:
    """Load enriched business context formatted for agent prompts.

    Returns a dict with keys:
    - name, type, description
    - catalog_summary (string)
    - enriched (formatted string with business_type, industry, audience, etc.)
    - prompt_adaptation (type-specific instructions)
    """
    builder = BusinessContextBuilder(db)
    return await builder.build_system_prompt_context(
        business_id=business_id,
    )


def format_business_context_for_prompt(ctx: Dict[str, Any]) -> str:
    """Format a business context dict into a rich text block for prompts."""
    if not ctx:
        return ""

    lines = []
    if ctx.get("name"):
        lines.append(f"Business: {ctx['name']}")
    if ctx.get("type"):
        lines.append(f"Type: {ctx['type']}")
    if ctx.get("description"):
        lines.append(f"Description: {ctx['description']}")
    if ctx.get("enriched"):
        lines.append(f"Profile: {ctx['enriched']}")
    if ctx.get("catalog_summary"):
        lines.append(f"Catalog:\n{ctx['catalog_summary']}")
    if ctx.get("custom_instructions"):
        lines.append(f"Owner Instructions: {ctx['custom_instructions']}")
    if ctx.get("prompt_adaptation"):
        lines.append(f"Context: {ctx['prompt_adaptation']}")

    if not lines:
        return ""

    return "\n\nBUSINESS PROFILE:\n" + "\n".join(lines)


def enrich_system_prompt(base_prompt: str, ctx: Dict[str, Any]) -> str:
    """Prepend business context to a system prompt."""
    context_block = format_business_context_for_prompt(ctx)
    if not context_block:
        return base_prompt
    return base_prompt + "\n\n" + context_block


def enrich_user_prompt(base_prompt: str, ctx: Dict[str, Any]) -> str:
    """Append business context to a user prompt."""
    context_block = format_business_context_for_prompt(ctx)
    if not context_block:
        return base_prompt
    return context_block + "\n\nTASK:\n" + base_prompt
