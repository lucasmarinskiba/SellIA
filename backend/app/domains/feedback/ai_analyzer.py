"""
AI Feedback Analyzer

Analiza feedback de usuarios con LLM para:
- Clasificar tipo, categoría, severidad
- Detectar duplicados
- Generar soluciones propuestas
- Asignar plan objetivo según complejidad
"""

import uuid
import json
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.feedback.models import FeedbackType, FeedbackSeverity, UserFeedback
from app.domains.feedback.service import FeedbackService
from app.domains.agents.ai_reply import generate_raw_ai_response


# Keywords para clasificación rápida sin LLM
BUG_KEYWORDS = ["bug", "error", "falla", "crashea", "no funciona", "broken", "se rompe", "problema"]
IDEA_KEYWORDS = ["sugerencia", "sería bueno", "me gustaría", "feature", "funcionalidad", "agregar", "falta"]
COMPLAINT_KEYWORDS = ["malo", "pesimo", "terrible", "odia", "frustrante", "inútil", "decepcionado"]
PRAISE_KEYWORDS = ["excelente", "genial", "me encanta", "perfecto", "buenísimo", "increíble"]

SEVERITY_KEYWORDS = {
    "critical": ["seguridad", "hackeado", "robo", "pérdida de datos", "caído", "no puedo acceder"],
    "high": ["lento", "timeout", "falla constantemente", "bloquea"],
    "low": ["diseño", "color", "tipografía", "margen", "alineación"],
}


async def analyze_feedback(
    db: AsyncSession,
    business_id: uuid.UUID,
    title: str,
    description: str,
) -> Tuple[FeedbackType, str, FeedbackSeverity, str, str, float, Optional[uuid.UUID]]:
    """
    Analiza feedback con LLM.

    Returns:
        (type, category, severity, analysis, solution_proposal, confidence, duplicate_of_id)
    """
    content = f"{title} {description}".lower()

    # 1. Fast path: keyword classification
    feedback_type = _keyword_classify_type(content)
    severity = _keyword_classify_severity(content)

    # 2. Detect duplicates
    svc = FeedbackService(db)
    existing, _ = await svc.list_feedback(limit=100)
    duplicate_id = _detect_duplicate(title, description, existing)

    if duplicate_id:
        return feedback_type, "general", severity, "Detectado como duplicado.", "", 0.3, duplicate_id

    # 3. LLM deep analysis
    system_prompt = """You are a Product Feedback Analysis AI. Analyze user feedback and respond with ONLY a JSON object:

{
  "category": "ux|performance|security|billing|feature|integration|documentation|other",
  "severity": "low|medium|high|critical",
  "analysis": "Brief analysis of the issue in Spanish",
  "solution_proposal": "Concrete steps to solve this",
  "target_plan": "free|starter|pro|enterprise",
  "effort_hours": number,
  "confidence": 0.0-1.0
}

Rules:
- target_plan: free (simple bugfix), starter (small feature), pro (medium feature), enterprise (complex/custom)
- effort_hours: realistic estimation
- confidence: how sure you are about the analysis
- Respond ONLY with valid JSON, no markdown."""

    user_prompt = f"""Title: {title}
Description: {description}

Analyze this feedback:"""

    try:
        response = await generate_raw_ai_response(
            db=db,
            business_id=business_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=400,
            temperature=0.2,
        )
        if not response:
            return feedback_type, "general", severity, "", "", 0.5, None

        data = json.loads(response.strip())

        # Override with LLM if confidence high
        if data.get("confidence", 0) > 0.7:
            feedback_type = _safe_type(data.get("type", feedback_type.value))
            severity = _safe_severity(data.get("severity", severity.value))

        return (
            feedback_type,
            data.get("category", "general"),
            severity,
            data.get("analysis", ""),
            data.get("solution_proposal", ""),
            data.get("confidence", 0.5),
            None,
        )
    except Exception:
        return feedback_type, "general", severity, "", "", 0.5, None


def _keyword_classify_type(content: str) -> FeedbackType:
    scores = {
        FeedbackType.BUG: sum(1 for kw in BUG_KEYWORDS if kw in content),
        FeedbackType.IDEA: sum(1 for kw in IDEA_KEYWORDS if kw in content),
        FeedbackType.COMPLAINT: sum(1 for kw in COMPLAINT_KEYWORDS if kw in content),
        FeedbackType.PRAISE: sum(1 for kw in PRAISE_KEYWORDS if kw in content),
    }
    return max(scores, key=scores.get) if max(scores.values()) > 0 else FeedbackType.OTHER


def _keyword_classify_severity(content: str) -> FeedbackSeverity:
    for sev, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in content for kw in keywords):
            return _safe_severity(sev)
    return FeedbackSeverity.MEDIUM


def _detect_duplicate(title: str, description: str, existing: list[UserFeedback]) -> Optional[uuid.UUID]:
    """Detecta duplicados por similitud de palabras clave."""
    import re
    new_words = set(re.findall(r"\b\w{4,}\b", f"{title} {description}".lower()))
    if not new_words:
        return None

    for fb in existing:
        existing_words = set(re.findall(r"\b\w{4,}\b", f"{fb.title} {fb.description}".lower()))
        if not existing_words:
            continue
        intersection = new_words & existing_words
        similarity = len(intersection) / max(len(new_words), len(existing_words))
        if similarity > 0.75:
            return fb.id
    return None


def _safe_type(value: str) -> FeedbackType:
    mapping = {
        "bug": FeedbackType.BUG,
        "idea": FeedbackType.IDEA,
        "complaint": FeedbackType.COMPLAINT,
        "praise": FeedbackType.PRAISE,
    }
    return mapping.get(value.lower(), FeedbackType.OTHER)


def _safe_severity(value: str) -> FeedbackSeverity:
    mapping = {
        "low": FeedbackSeverity.LOW,
        "medium": FeedbackSeverity.MEDIUM,
        "high": FeedbackSeverity.HIGH,
        "critical": FeedbackSeverity.CRITICAL,
    }
    return mapping.get(value.lower(), FeedbackSeverity.MEDIUM)
