"""Communication Angles Service — turns Nicho + Oferta into winning angles.

Uses BusinessContext (industry, target_audience, value_proposition, price_range,
average_ticket, sales_model) to generate 3-5 structured communication angles plus
a one-line winning-offer summary. These angles are persisted on the BusinessContext
row and consumed by the qualified-lead outbound message in
`app.domains.channels.services.process_incoming_message` so the pitch a lead
receives is niche/offer-aware instead of generic.
"""

import json
import uuid
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.ai_reply import generate_raw_ai_response
from .models import BusinessContext

logger = get_logger(__name__)

DEFAULT_ANGLES = [
    {
        "angle": "Diferenciación por valor",
        "hook": "¿Sabías que la mayoría pierde tiempo/dinero por no resolver esto a tiempo?",
        "pain_point": "Falta de solución rápida y confiable",
        "cta": "Contanos tu caso y te mostramos cómo lo resolvemos",
    }
]


def _build_prompt(ctx: BusinessContext) -> tuple[str, str]:
    system_prompt = (
        "Eres un experto en copywriting y posicionamiento de ofertas (Hormozi, Halbert, Godin). "
        "A partir del nicho y la oferta de un negocio, genera ángulos de comunicación GANADORES "
        "(los que más convierten) y un resumen de oferta irresistible. "
        "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
        "{\n"
        '  "winning_offer_summary": "una frase que resume la oferta irresistible",\n'
        '  "communication_angles": [\n'
        '    {"angle": "nombre corto del ángulo", "hook": "frase de apertura/gancho", '
        '"pain_point": "dolor específico que ataca", "cta": "llamado a la acción"}\n'
        "  ]\n"
        "}\n"
        "Reglas:\n"
        "- Genera entre 3 y 5 ángulos, todos distintos entre sí (no repitas el mismo dolor).\n"
        "- Sé específico al nicho y público objetivo dados, no genérico.\n"
        "- Escribe en español, tono directo y persuasivo, sin exagerar ni prometer cosas falsas."
    )

    parts = []
    if ctx.industry:
        parts.append(f"Rubro/nicho: {ctx.industry}")
    if ctx.target_audience:
        parts.append(f"Público objetivo: {ctx.target_audience}")
    if ctx.value_proposition:
        parts.append(f"Propuesta de valor actual: {ctx.value_proposition}")
    if ctx.price_range:
        parts.append(f"Rango de precio: {ctx.price_range}")
    if ctx.average_ticket:
        parts.append(f"Ticket promedio: {ctx.average_ticket}")
    if ctx.sales_model:
        parts.append(f"Modelo de venta: {ctx.sales_model.value if hasattr(ctx.sales_model, 'value') else ctx.sales_model}")

    if not parts:
        parts.append("El negocio todavía no cargó datos de nicho/oferta; infiere lo más genérico y útil posible.")

    user_prompt = "\n".join(parts) + "\n\nJSON:"
    return system_prompt, user_prompt


def _parse_response(raw: str) -> Dict[str, Any]:
    json_str = raw.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    parsed = json.loads(json_str)
    angles = parsed.get("communication_angles") or []
    cleaned = []
    for a in angles:
        if not isinstance(a, dict):
            continue
        cleaned.append({
            "angle": str(a.get("angle", ""))[:200],
            "hook": str(a.get("hook", ""))[:500],
            "pain_point": str(a.get("pain_point", ""))[:300],
            "cta": str(a.get("cta", ""))[:200],
        })
    return {
        "winning_offer_summary": str(parsed.get("winning_offer_summary", ""))[:500],
        "communication_angles": cleaned or DEFAULT_ANGLES,
    }


async def generate_communication_angles(db: AsyncSession, ctx: BusinessContext) -> Dict[str, Any]:
    """Generates and persists winning communication angles for a BusinessContext."""
    system_prompt, user_prompt = _build_prompt(ctx)

    business_id = ctx.business_id or uuid.UUID(int=0)
    raw = await generate_raw_ai_response(
        db=db,
        business_id=business_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1200,
        temperature=0.6,
    )

    result = {"winning_offer_summary": None, "communication_angles": DEFAULT_ANGLES}
    if raw:
        try:
            result = _parse_response(raw)
        except Exception as e:
            logger.warning(f"Failed to parse communication angles JSON: {e}")

    ctx.communication_angles = result["communication_angles"]
    ctx.winning_offer_summary = result["winning_offer_summary"] or ctx.winning_offer_summary
    await db.commit()
    await db.refresh(ctx)

    return result
