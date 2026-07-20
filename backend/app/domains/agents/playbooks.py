"""Sales Playbook Generator — AI-generated sales playbooks per business.

Generates customized sales playbooks based on business context, catalog,
pipeline history, and expert sales methodologies.
"""

import uuid
from typing import Dict, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.businesses.models import Business
from app.domains.catalogs.models import CatalogItem
from app.domains.crm.models import Deal, LeadStage
from app.domains.channels.models import Conversation
from app.domains.agents.prompts import compose_system_prompt
from app.domains.agents.llm_provider import generate_with_fallback
from langchain_core.messages import SystemMessage, HumanMessage


async def generate_sales_playbook(
    db: AsyncSession,
    business_id: uuid.UUID,
    voice_slug: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Generate a complete sales playbook for a business.

    Analyzes business profile, catalog, deal history, and generates
    a structured playbook with scripts, objection handling, and workflows.

    Returns a dict with playbook sections, or None if generation fails.
    """
    # Fetch business
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        return None

    # Fetch catalog
    result = await db.execute(
        select(CatalogItem).where(
            CatalogItem.business_id == business_id,
            CatalogItem.is_active == True,
        ).limit(15)
    )
    catalog_items = result.scalars().all()
    catalog_summary = "\n".join([
        f"- {item.name} (${item.price} {item.currency}): {item.description[:150] if item.description else 'N/A'}"
        for item in catalog_items
    ]) if catalog_items else "Sin productos/servicios en catálogo."

    # Deal stats
    result = await db.execute(
        select(func.count(Deal.id), func.avg(Deal.value)).where(
            Deal.business_id == business_id,
            Deal.is_active == True,
        )
    )
    total_deals, avg_value = result.one_or_none() or (0, 0)
    avg_value = float(avg_value) if avg_value else 0

    result = await db.execute(
        select(func.count(Deal.id)).where(
            Deal.business_id == business_id,
            Deal.is_active == True,
            Deal.stage == LeadStage.CLOSED_WON,
        )
    )
    won_deals = result.scalar() or 0

    # Build prompt
    system_prompt = compose_system_prompt(
        base_slug="sales-manager",
        voice_slug=voice_slug or "hormozi",
        business_context={
            "business_name": business.name,
            "business_type": business.type.value if business.type else "mixed",
            "business_description": business.description or "",
        },
    )

    user_prompt = f"""Genera un Playbook de Ventas completo para este negocio.

PERFIL DEL NEGOCIO:
- Nombre: {business.name}
- Tipo: {business.type.value if business.type else 'mixed'}
- Descripción: {business.description or 'N/A'}

CATÁLOGO:
{catalog_summary}

MÉTRICAS ACTUALES:
- Deals totales: {total_deals}
- Deals ganados: {won_deals}
- Valor promedio: ${avg_value:.0f}

Genera el playbook en español con este formato exacto:

ELEVATOR_PITCH: <pitch de 30 segundos>
IDEAL_CUSTOMER: <perfil del cliente ideal en 2-3 bullets>
QUALIFICATION_QUESTIONS: <3 preguntas clave para cualificar>
OBJECTION_HANDLING: <3 objeciones comunes + respuestas>
CLOSING_TECHNIQUES: <2 técnicas de cierre recomendadas>
FOLLOW_UP cadencia: <frecuencia y canales de seguimiento>
UPSELL_STRATEGY: <cómo aumentar ticket promedio>"""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = await generate_with_fallback(
            db, business_id, messages, model="llama3.1", temperature=0.7, max_tokens=1500,
        )
        if not response:
            return None
        ai_response = response.content
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"LLM error: {e}")
        return None

    if not ai_response:
        return None

    playbook = {
        "elevator_pitch": "",
        "ideal_customer": "",
        "qualification_questions": "",
        "objection_handling": "",
        "closing_techniques": "",
        "follow_up_cadence": "",
        "upsell_strategy": "",
        "raw": ai_response,
        "generated_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    }

    current_key = None
    key_map = {
        "ELEVATOR_PITCH": "elevator_pitch",
        "IDEAL_CUSTOMER": "ideal_customer",
        "QUALIFICATION_QUESTIONS": "qualification_questions",
        "OBJECTION_HANDLING": "objection_handling",
        "CLOSING_TECHNIQUES": "closing_techniques",
        "FOLLOW_UP": "follow_up_cadence",
        "UPSELL_STRATEGY": "upsell_strategy",
    }

    for line in ai_response.split("\n"):
        stripped = line.strip()
        matched = False
        for prefix, key in key_map.items():
            if stripped.upper().startswith(f"{prefix}:") or stripped.upper().startswith(f"{prefix} "):
                current_key = key
                # Extract after first colon or first space
                if ":" in stripped:
                    playbook[key] = stripped.split(":", 1)[1].strip()
                else:
                    playbook[key] = stripped[len(prefix):].strip()
                matched = True
                break
        if not matched and current_key and stripped:
            playbook[current_key] += " " + stripped

    return playbook
