"""Prompt Composer — Combines functional role prompts with expert voice prompts.

Allows auto-pilot agents (captador, vendedor, etc.) to reason and communicate
using the frameworks, philosophy, and style of any expert personality.
"""

from typing import Optional
from app.domains.agents.prompts import AGENT_PROMPTS


# Auto-pilot functional slugs that can be composed with expert voices
FUNCTIONAL_SLUGS = {"captador", "cualificador", "vendedor", "post-venta"}


def compose_system_prompt(
    base_slug: str,
    voice_slug: Optional[str] = None,
    business_context: dict = None,
    custom_instructions: str = None,
) -> str:
    """
    Compose a system prompt that layers an expert's voice over a functional role.

    If voice_slug is provided and base_slug is a functional auto-pilot agent,
    the resulting prompt combines the functional tasks with the expert's philosophy.
    Otherwise, returns the standard prompt for base_slug.
    """
    base_prompt = AGENT_PROMPTS.get(base_slug, AGENT_PROMPTS.get("alex-hormozi", ""))

    # If no voice override, return standard prompt
    if not voice_slug or voice_slug == base_slug:
        return _finalize_prompt(base_prompt, business_context, custom_instructions)

    voice_prompt = AGENT_PROMPTS.get(voice_slug)
    if not voice_prompt:
        # Voice not found, fall back to base
        return _finalize_prompt(base_prompt, business_context, custom_instructions)

    # Compose: functional role + expert voice
    composed = f"""# TU ROL FUNCIONAL

You are an AI agent with the following functional role and responsibilities:

{base_prompt}

---

# TU VOZ Y FILOSOFIA EXPERTA

You must execute your functional role while adopting the mindset, frameworks, communication style, and philosophy of the following expert:

{voice_prompt}

---

# SINTESIS: COMO APLICAR TU VOZ A TU ROL

1. **Mantén tus objetivos funcionales**: Tu trabajo primario sigue siendo el descrito en TU ROL FUNCIONAL. Debes captar leads, cualificar, vender, o fidelizar según corresponda.

2. **Aplica la filosofía del experto**: Usa los frameworks, principios y mentalidad del experto para abordar cada situación. Piensa como él/ella pensaría.

3. **Adopta el estilo de comunicación**: Habla, escribe y te expresas usando el tono, vocabulario y patrones del experto. Si el experto usa frases características, usalas.

4. **Usa las reglas del experto**: Aplica las reglas y restricciones del experto a tus interacciones con clientes.

5. **Sé coherente**: No alternes entre estilos. Mantén la voz del experto de principio a fin en cada interacción.

Eres el agente funcional '{base_slug}' que piensa, razona y comunica con la voz de '{voice_slug}'.
"""

    return _finalize_prompt(composed, business_context, custom_instructions)


def _finalize_prompt(base_text: str, business_context: dict, custom_instructions: str) -> str:
    """Append business context and custom instructions to any prompt."""
    context_block = ""
    if business_context:
        ctx_parts = []
        if business_context.get("name"):
            ctx_parts.append(f"Business Name: {business_context['name']}")
        if business_context.get("type"):
            ctx_parts.append(f"Business Type: {business_context['type']}")
        if business_context.get("enriched"):
            ctx_parts.append(f"Business Profile: {business_context['enriched']}")
        if business_context.get("description"):
            ctx_parts.append(f"Description: {business_context['description']}")
        if business_context.get("catalog_summary"):
            ctx_parts.append(f"Products/Services:\n{business_context['catalog_summary']}")
        if ctx_parts:
            context_block = "\n\nBUSINESS CONTEXT:\n" + "\n".join(ctx_parts)

    # Business-type-specific prompt adaptation
    adaptation = ""
    if business_context and business_context.get("prompt_adaptation"):
        adaptation = f"\n\nBUSINESS TYPE ADAPTATION:\n{business_context['prompt_adaptation']}"

    custom = ""
    if custom_instructions:
        custom = f"\n\nCUSTOM INSTRUCTIONS FROM BUSINESS OWNER:\n{custom_instructions}"

    return (
        base_text
        + context_block
        + adaptation
        + custom
        + "\n\nIMPORTANT: Respond in the same language the user is writing in (Spanish, English, etc.). Keep responses concise but actionable. Always end with a clear next step or action item."
    )
