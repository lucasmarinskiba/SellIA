"""
AI Ticket Classifier

Clasifica automáticamente tickets por categoría y prioridad usando LLM.
Detecta urgencia y keywords críticas para escalamiento automático.
"""

import uuid
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.support.models import TicketCategory, TicketPriority
from app.domains.agents.ai_reply import generate_raw_ai_response


# Keywords que disparan escalamiento inmediato a CRITICAL
URGENT_KEYWORDS = [
    "hackeado", "hack", "robo", "fraude", "estafa", "phishing",
    "no funciona", "caído", "down", "error crítico", "bloqueado",
    "dinero", "pago", "cobro", "facturación", "tarjeta",
    "urgente", "emergencia", "ahora", "inmediato",
    "eliminar cuenta", "borrar datos", "gdpr",
]


async def classify_ticket(
    db: AsyncSession,
    business_id: uuid.UUID,
    title: str,
    description: str,
) -> Tuple[TicketCategory, TicketPriority, float]:
    """
    Clasifica un ticket usando LLM.

    Returns:
        (category, priority, confidence)
    """
    # 1. Keyword-based urgency detection (fast path)
    content_lower = f"{title} {description}".lower()
    urgent_matches = [kw for kw in URGENT_KEYWORDS if kw in content_lower]
    if len(urgent_matches) >= 2:
        return TicketCategory.SECURITY, TicketPriority.CRITICAL, 1.0

    # 2. LLM classification
    system_prompt = """You are a Support Ticket Classifier AI for a business platform.
Analyze the ticket and respond with ONLY a JSON object in this exact format:
{"category": "account|billing|technical|sales|security|feature_request|other", "priority": "low|medium|high|critical", "confidence": 0.0-1.0}

Rules:
- category: best fit for the issue type
- priority: low (questions, feature requests), medium (minor bugs), high (major bugs, billing), critical (security, data loss, fraud)
- confidence: how sure you are (0.0 to 1.0)
- Respond ONLY with the JSON object, no markdown, no explanations."""

    user_prompt = f"""Title: {title}
Description: {description}

Classify this ticket:"""

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
            return TicketCategory.OTHER, TicketPriority.MEDIUM, 0.5

        import json
        data = json.loads(response.strip())

        category = _safe_category(data.get("category", "other"))
        priority = _safe_priority(data.get("priority", "medium"))
        confidence = float(data.get("confidence", 0.5))

        # Boost priority if urgent keywords found
        if urgent_matches:
            priority = _bump_priority(priority)

        return category, priority, confidence
    except Exception:
        return TicketCategory.OTHER, TicketPriority.MEDIUM, 0.5


def _safe_category(value: str) -> TicketCategory:
    mapping = {
        "account": TicketCategory.ACCOUNT,
        "billing": TicketCategory.BILLING,
        "technical": TicketCategory.TECHNICAL,
        "sales": TicketCategory.SALES,
        "security": TicketCategory.SECURITY,
        "feature_request": TicketCategory.FEATURE_REQUEST,
    }
    return mapping.get(value.lower(), TicketCategory.OTHER)


def _safe_priority(value: str) -> TicketPriority:
    mapping = {
        "low": TicketPriority.LOW,
        "medium": TicketPriority.MEDIUM,
        "high": TicketPriority.HIGH,
        "critical": TicketPriority.CRITICAL,
    }
    return mapping.get(value.lower(), TicketPriority.MEDIUM)


def _bump_priority(current: TicketPriority) -> TicketPriority:
    bumps = {
        TicketPriority.LOW: TicketPriority.MEDIUM,
        TicketPriority.MEDIUM: TicketPriority.HIGH,
        TicketPriority.HIGH: TicketPriority.CRITICAL,
        TicketPriority.CRITICAL: TicketPriority.CRITICAL,
    }
    return bumps.get(current, current)
