"""Proposal/Quote Generator — AI-powered proposal generation for deals.

When a deal reaches PROPOSAL_SENT stage, this engine generates a professional
proposal document using expert sales voices (Belfort, Hormozi, etc.).
"""

import uuid
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.crm.models import Deal, LeadStage
from app.domains.channels.models import Conversation, Message
from app.domains.catalogs.models import CatalogItem
from app.domains.agents.ai_reply import generate_ai_response


async def generate_deal_proposal(
    db: AsyncSession,
    deal: Deal,
    business_id: uuid.UUID,
    voice_slug: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Generate a professional sales proposal for a deal.

    Analyzes conversation history, catalog items, and deal context to generate
    a structured proposal with cover letter, scope, pricing, and next steps.

    Returns a dict with proposal sections, or None if generation fails.
    """
    if not deal.conversation_id:
        return None

    # Fetch conversation and recent messages
    result = await db.execute(
        select(Conversation).where(Conversation.id == deal.conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return None

    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(15)
    )
    messages = list(reversed(result.scalars().all()))
    conversation_summary = "\n".join([
        f"{'Lead' if m.direction.value == 'inbound' else 'Agent'}: {m.content[:300]}"
        for m in messages
    ])

    # Fetch catalog items for this business (for context)
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.business_id == business_id,
            CatalogItem.is_active == True,
            CatalogItem.is_available == True,
        ).limit(10)
    )
    catalog_items = result.scalars().all()
    catalog_summary = "\n".join([
        f"- {item.name}: ${item.price} {item.currency} — {item.description[:100] if item.description else 'Sin descripción'}"
        for item in catalog_items
    ]) if catalog_items else "No hay productos/servicios en catálogo."

    custom_prompt = f"""Genera una propuesta de venta profesional en español basada en esta oportunidad.

DATOS DEL DEAL:
- Título: {deal.title}
- Descripción: {deal.description or 'N/A'}
- Valor estimado: ${deal.value} {deal.currency} (si existe)
- Contacto: {deal.contact_name or 'N/A'} ({deal.contact_email or 'Sin email'})

HISTORIAL DE CONVERSACIÓN:
{conversation_summary}

CATÁLOGO DISPONIBLE:
{catalog_summary}

Genera una propuesta estructurada con las siguientes secciones. Sé persuasivo, conciso y orientado a resultados.

Formato de respuesta exacto:
SUBJECT: <línea de asunto del email con la propuesta>
COVER: <párrafo introductorio personalizado, 2-3 oraciones>
SCOPE: <descripción del alcance de trabajo/producto, 2-3 bullets>
PRICING: <resumen de precios y opciones>
NEXT_STEPS: <qué debe hacer el cliente ahora, 1-2 oraciones>
URGENCY: <línea de cierre que cree urgencia sin ser agresivo>"""

    ai_response = await generate_ai_response(
        db=db,
        conversation=conversation,
        personality_slug="account-executive",
        business_id=business_id,
        custom_prompt=custom_prompt,
        voice_slug=voice_slug or "belfort",
        max_tokens=1200,
    )

    if not ai_response:
        return None

    # Parse structured response
    proposal = {
        "subject": "",
        "cover": "",
        "scope": "",
        "pricing": "",
        "next_steps": "",
        "urgency": "",
        "raw": ai_response,
        "generated_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    }

    current_key = None
    for line in ai_response.split("\n"):
        stripped = line.strip()
        if stripped.upper().startswith("SUBJECT:"):
            current_key = "subject"
            proposal["subject"] = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("COVER:"):
            current_key = "cover"
            proposal["cover"] = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("SCOPE:"):
            current_key = "scope"
            proposal["scope"] = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("PRICING:"):
            current_key = "pricing"
            proposal["pricing"] = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("NEXT_STEPS:"):
            current_key = "next_steps"
            proposal["next_steps"] = stripped.split(":", 1)[1].strip()
        elif stripped.upper().startswith("URGENCY:"):
            current_key = "urgency"
            proposal["urgency"] = stripped.split(":", 1)[1].strip()
        elif current_key and stripped:
            proposal[current_key] += " " + stripped

    # Store proposal in deal extra_data
    if not deal.extra_data:
        deal.extra_data = {}
    deal.extra_data["proposal"] = proposal
    await db.commit()

    return proposal
