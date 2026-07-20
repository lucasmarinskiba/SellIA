"""Pricing Recommendation Engine — AI-powered pricing strategy for deals.

Analyzes conversation context, deal history, and catalog to recommend
optimal pricing, discounts, and packaging strategies using expert voices.
"""

import uuid
from typing import Dict, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.crm.models import Deal, LeadStage
from app.domains.channels.models import Conversation, Message
from app.domains.catalogs.models import CatalogItem
from app.domains.agents.ai_reply import generate_ai_response


async def generate_pricing_recommendation(
    db: AsyncSession,
    deal: Deal,
    business_id: uuid.UUID,
    voice_slug: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Generate a pricing strategy recommendation for a deal.

    Analyzes:
    - Conversation signals (price sensitivity, urgency, budget hints)
    - Deal value and stage
    - Catalog pricing context
    - Similar deals in the pipeline

    Returns a dict with pricing recommendation, or None if generation fails.
    """
    if not deal.conversation_id:
        return None

    result = await db.execute(
        select(Conversation).where(Conversation.id == deal.conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return None

    # Recent messages for price sensitivity analysis
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(20)
    )
    messages = list(reversed(result.scalars().all()))
    conversation_summary = "\n".join([
        f"{'Lead' if m.direction.value == 'inbound' else 'Agent'}: {m.content[:250]}"
        for m in messages
    ])

    # Catalog context
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.business_id == business_id,
            CatalogItem.is_active == True,
        ).limit(10)
    )
    catalog_items = result.scalars().all()
    catalog_summary = "\n".join([
        f"- {item.name}: ${item.price} {item.currency}"
        for item in catalog_items
    ]) if catalog_items else "Sin catálogo."

    # Pipeline context: avg deal value, similar deals
    result = await db.execute(
        select(func.avg(Deal.value), func.count(Deal.id)).where(
            Deal.business_id == business_id,
            Deal.is_active == True,
            Deal.stage != LeadStage.CLOSED_LOST,
        )
    )
    avg_value, total_deals = result.one_or_none() or (0, 0)
    avg_value = float(avg_value) if avg_value else 0

    custom_prompt = f"""Analiza esta oportunidad y recomienda una estrategia de precios.

DATOS DEL DEAL:
- Valor actual: ${deal.value} {deal.currency}
- Etapa: {deal.stage.value if deal.stage else 'N/A'}
- Contacto: {deal.contact_name or 'N/A'}
- Probabilidad: {deal.probability}%

HISTORIAL DE CONVERSACIÓN (últimos mensajes):
{conversation_summary}

CATÁLOGO DE REFERENCIA:
{catalog_summary}

CONTEXTO DEL PIPELINE:
- Promedio de deals ganados: ${avg_value:.0f}
- Total deals activos: {total_deals}

Genera tu recomendación en este formato exacto:
RECOMMENDED_PRICE: <precio recomendado con justificación corta>
DISCOUNT_STRATEGY: <si conviene ofrecer descuento, cuánto y cómo>
PACKAGING: <cómo estructurar la oferta: tiers, bundles, addons>
ANCHORING: <técnica de anclaje de precio sugerida>
OBJECTION_PREP: <qué objeciones de precio anticipar y cómo responder>
CONFIDENCE: <alta/media/baja>"""

    ai_response = await generate_ai_response(
        db=db,
        conversation=conversation,
        personality_slug="sales-finance",
        business_id=business_id,
        custom_prompt=custom_prompt,
        voice_slug=voice_slug or "hormozi",
        max_tokens=1000,
    )

    if not ai_response:
        return None

    recommendation = {
        "recommended_price": "",
        "discount_strategy": "",
        "packaging": "",
        "anchoring": "",
        "objection_prep": "",
        "confidence": "",
        "raw": ai_response,
        "generated_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    }

    current_key = None
    key_map = {
        "RECOMMENDED_PRICE": "recommended_price",
        "DISCOUNT_STRATEGY": "discount_strategy",
        "PACKAGING": "packaging",
        "ANCHORING": "anchoring",
        "OBJECTION_PREP": "objection_prep",
        "CONFIDENCE": "confidence",
    }

    for line in ai_response.split("\n"):
        stripped = line.strip()
        matched = False
        for prefix, key in key_map.items():
            if stripped.upper().startswith(f"{prefix}:"):
                current_key = key
                recommendation[key] = stripped.split(":", 1)[1].strip()
                matched = True
                break
        if not matched and current_key and stripped:
            recommendation[current_key] += " " + stripped

    # Store in deal extra_data
    if not deal.extra_data:
        deal.extra_data = {}
    deal.extra_data["pricing_recommendation"] = recommendation
    await db.commit()

    return recommendation
