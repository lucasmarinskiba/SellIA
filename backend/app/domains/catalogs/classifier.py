"""AI Catalog Item Classifier.

Infers type (service/good/digital) and category from a product/service's
name+description. Same mold as app/domains/support/ai_classifier.py's
classify_ticket: LLM call with a strict JSON response shape, safe fallback
if it fails -- an import must never block on a classification error.
"""

import json
import uuid
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalogs.models import CatalogItemType
from app.domains.agents.ai_reply import generate_raw_ai_response


async def classify_catalog_item(
    db: AsyncSession,
    business_id: uuid.UUID,
    name: str,
    description: str = "",
) -> Tuple[CatalogItemType, Optional[str], float]:
    """Classify a product/service by name+description.

    Returns:
        (type, category, confidence). category is a short real-world rubro
        (e.g. "Servicios jurídicos", "Videojuegos") or None if the model
        couldn't tell. Falls back to (GOOD, None, 0.0) on any failure --
        callers should treat a low confidence as "best guess", not fact.
    """
    system_prompt = """You are a product/service classifier for an e-commerce catalog.
Analyze the item and respond with ONLY a JSON object in this exact format:
{"type": "service|good|digital", "category": "short real-world category in Spanish, or null", "confidence": 0.0-1.0}

Rules:
- type: "service" for things done for the customer (legal advice, PC repair, accounting, appraisals, real estate services), "digital" for non-physical deliverables (video games, PDFs, software, courses, licenses), "good" for physical items shipped/handed over.
- category: a short, specific real-world rubro in Spanish (e.g. "Servicios jurídicos", "Reparación de PC", "Videojuegos", "Contaduría", "Tasaciones", "Bienes raíces", "Electrónica", "Indumentaria"). null if genuinely unclear.
- confidence: how sure you are (0.0 to 1.0).
- Respond ONLY with the JSON object, no markdown, no explanations."""

    user_prompt = f"""Nombre: {name}
Descripción: {description or '(sin descripción)'}

Clasificá este ítem:"""

    try:
        response = await generate_raw_ai_response(
            db=db,
            business_id=business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=100,
            temperature=0.1,
        )
        if not response:
            return CatalogItemType.GOOD, None, 0.0

        data = json.loads(response.strip())
        item_type = _safe_type(data.get("type", "good"))
        category = data.get("category")
        if category is not None:
            category = str(category).strip()[:120] or None
        confidence = float(data.get("confidence", 0.5))

        return item_type, category, confidence
    except Exception:
        return CatalogItemType.GOOD, None, 0.0


def _safe_type(value: str) -> CatalogItemType:
    mapping = {
        "service": CatalogItemType.SERVICE,
        "good": CatalogItemType.GOOD,
        "digital": CatalogItemType.DIGITAL,
    }
    return mapping.get(str(value).lower(), CatalogItemType.GOOD)
