"""
Fase A: AI FOMO Copywriter Agent

Generates personalized FOMO copy (subject lines, urgency messages, CTAs, SMS)
using the project's existing multi-provider LLM fallback infra
(app.domains.agents.llm_provider.generate_with_fallback).

Responsibilities:
- Generate N variants of copy for a given FOMO campaign type
- Multi-language support (es/en/pt)
- Parse + validate structured LLM output (JSON), with safe fallback
- Score/select best variant using historical performance when available,
  or content heuristics on cold start
"""

import json
import re
import uuid
from typing import Dict, List, Any, Optional
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import SystemMessage, HumanMessage

from app.domains.agents.llm_provider import generate_with_fallback
from app.core.logger import get_logger

logger = get_logger(__name__)


class SupportedLanguage(str, Enum):
    ES = "es"
    EN = "en"
    PT = "pt"


class CopyTone(str, Enum):
    URGENT = "urgent"
    FRIENDLY = "friendly"
    LUXURY = "luxury"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"


LANGUAGE_INSTRUCTIONS = {
    SupportedLanguage.ES: "Escribe TODO el contenido en español latinoamericano, natural y persuasivo.",
    SupportedLanguage.EN: "Write ALL content in natural, persuasive English.",
    SupportedLanguage.PT: "Escreva TODO o conteúdo em português brasileiro, natural e persuasivo.",
}

TONE_INSTRUCTIONS = {
    CopyTone.URGENT: "Tono: urgencia alta, acción inmediata, sin ser agresivo o spam.",
    CopyTone.FRIENDLY: "Tono: cercano, cálido, como un amigo recomendando algo bueno.",
    CopyTone.LUXURY: "Tono: exclusivo, aspiracional, elegante. Evita gritar 'descuento'.",
    CopyTone.PLAYFUL: "Tono: divertido, emojis moderados, energético.",
    CopyTone.PROFESSIONAL: "Tono: profesional, directo, confiable, sin exageraciones.",
}


class AICopywriterPromptBuilder:
    """Builds structured prompts that force JSON-parseable LLM output"""

    @staticmethod
    def build_campaign_copy_prompt(
        campaign_type: str,
        product_name: str,
        product_description: str,
        audience: str,
        tone: CopyTone,
        language: SupportedLanguage,
        variant_count: int,
    ) -> List[Any]:
        system = SystemMessage(content=(
            "Eres un copywriter senior especializado en marketing FOMO (Fear Of Missing Out) "
            "para e-commerce y SaaS. Generas copy persuasivo, ético y de alta conversión. "
            "SIEMPRE respondes con JSON válido y NADA más — sin texto antes o después, "
            "sin markdown fences, sin explicaciones."
        ))

        schema_hint = {
            "subject_lines": ["string, 40-50 chars"] * variant_count,
            "preview_texts": ["string, 60-90 chars"] * variant_count,
            "urgency_messages": ["string, short punchy phrase"] * variant_count,
            "cta_texts": ["string, 2-5 words, action verb"] * variant_count,
            "sms_variants": ["string, max 160 chars"] * variant_count,
        }

        human = HumanMessage(content=f"""
Genera copy FOMO para esta campaña:

Tipo de campaña: {campaign_type}
Producto/Servicio: {product_name}
Descripción: {product_description}
Audiencia: {audience}

{TONE_INSTRUCTIONS[tone]}
{LANGUAGE_INSTRUCTIONS[language]}

Genera exactamente {variant_count} variantes de cada tipo de contenido.

Reglas:
- NO uses mayúsculas excesivas (no "GRATIS" gritando)
- NO prometas algo falso o no verificable
- Urgencia debe sentirse real, no manipuladora
- CTAs con verbo de acción claro
- SMS respeta límite de 160 caracteres

Responde ÚNICAMENTE con este JSON (sin texto adicional, sin ```json):
{json.dumps(schema_hint, ensure_ascii=False, indent=2)}
""")
        return [system, human]

    @staticmethod
    def build_translation_prompt(
        content: Dict[str, Any],
        target_language: SupportedLanguage,
    ) -> List[Any]:
        system = SystemMessage(content=(
            "Eres un traductor especializado en copy de marketing. Traduces manteniendo "
            "el tono persuasivo y la intención FOMO original. Respondes SOLO con JSON válido."
        ))
        human = HumanMessage(content=f"""
Traduce este contenido de marketing a {LANGUAGE_INSTRUCTIONS[target_language]}
manteniendo la MISMA estructura JSON y la intención persuasiva:

{json.dumps(content, ensure_ascii=False, indent=2)}

Responde ÚNICAMENTE con el JSON traducido, misma estructura de keys.
""")
        return [system, human]


class LLMResponseParser:
    """Safely parse LLM JSON output, with repair fallback"""

    @staticmethod
    def parse_json_response(raw_content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from LLM response, tolerant of markdown fences"""
        if not raw_content:
            return None

        cleaned = raw_content.strip()

        # Strip markdown code fences if present
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fallback: extract first {...} block
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                logger.warning("Failed to parse extracted JSON block from LLM response")

        return None

    @staticmethod
    def validate_campaign_copy_schema(data: Dict[str, Any]) -> bool:
        """Verify the parsed response has the expected structure"""
        required_keys = {
            "subject_lines", "preview_texts", "urgency_messages",
            "cta_texts", "sms_variants"
        }
        if not required_keys.issubset(data.keys()):
            return False
        return all(isinstance(data[key], list) and len(data[key]) > 0 for key in required_keys)


class VariantScorer:
    """Score and rank copy variants — historical performance when available,
    content heuristics on cold start"""

    URGENCY_KEYWORDS = [
        "hoy", "ahora", "último", "última", "solo", "quedan", "termina",
        "expira", "limitado", "exclusivo", "today", "now", "last", "only",
        "expires", "limited", "exclusive",
    ]

    @staticmethod
    def score_by_heuristics(text: str) -> float:
        """Cold-start scoring: no historical data yet, score by known-good patterns"""
        score = 50.0  # baseline
        text_lower = text.lower()

        # Urgency keyword presence (max +20)
        urgency_hits = sum(1 for kw in VariantScorer.URGENCY_KEYWORDS if kw in text_lower)
        score += min(urgency_hits * 5, 20)

        # Optimal length bonus (subject lines: 40-50 chars sweet spot)
        length = len(text)
        if 35 <= length <= 55:
            score += 15
        elif length > 80:
            score -= 10

        # Personalization token presence (+10)
        if "{{" in text and "}}" in text:
            score += 10

        # Emoji presence (moderate use, +5, but not too many)
        emoji_count = sum(1 for ch in text if ord(ch) > 0x1F300)
        if emoji_count == 1:
            score += 5
        elif emoji_count > 3:
            score -= 10

        # Excessive caps penalty
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.3:
            score -= 15

        return max(0.0, min(100.0, score))

    @staticmethod
    def score_by_historical_performance(
        variant_text: str,
        historical_data: List[Dict[str, Any]],
    ) -> float:
        """Score using historical open_rate/click_rate of similar variants.
        Falls back to heuristic score if no matching history."""
        if not historical_data:
            return VariantScorer.score_by_heuristics(variant_text)

        # Find similar variants by simple feature matching (length bucket, urgency keyword overlap)
        variant_urgency = set(
            kw for kw in VariantScorer.URGENCY_KEYWORDS if kw in variant_text.lower()
        )

        matches = []
        for record in historical_data:
            record_text = record.get("text", "")
            record_urgency = set(
                kw for kw in VariantScorer.URGENCY_KEYWORDS if kw in record_text.lower()
            )
            overlap = len(variant_urgency & record_urgency)
            if overlap > 0 or abs(len(record_text) - len(variant_text)) < 10:
                matches.append(record)

        if not matches:
            return VariantScorer.score_by_heuristics(variant_text)

        avg_open_rate = sum(m.get("open_rate", 0) for m in matches) / len(matches)
        avg_click_rate = sum(m.get("click_rate", 0) for m in matches) / len(matches)

        # Blend: 60% historical performance signal, 40% heuristics
        historical_score = (avg_open_rate * 60) + (avg_click_rate * 100)
        heuristic_score = VariantScorer.score_by_heuristics(variant_text)

        return (historical_score * 0.6) + (heuristic_score * 0.4)

    @staticmethod
    def rank_variants(
        variants: List[str],
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Rank variants best-to-worst with scores"""
        scored = []
        for variant in variants:
            score = VariantScorer.score_by_historical_performance(
                variant, historical_data or []
            )
            scored.append({"text": variant, "score": round(score, 2)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored


class AICopywriterAgent:
    """Fase A: Main agent — orchestrates copy generation, parsing, scoring"""

    @staticmethod
    async def generate_campaign_copy(
        db: AsyncSession,
        business_id: uuid.UUID,
        campaign_type: str,
        product_name: str,
        product_description: str,
        audience: str = "general",
        tone: CopyTone = CopyTone.URGENT,
        language: SupportedLanguage = SupportedLanguage.ES,
        variant_count: int = 5,
    ) -> Dict[str, Any]:
        """Generate full set of FOMO copy variants for a campaign"""
        messages = AICopywriterPromptBuilder.build_campaign_copy_prompt(
            campaign_type=campaign_type,
            product_name=product_name,
            product_description=product_description,
            audience=audience,
            tone=tone,
            language=language,
            variant_count=variant_count,
        )

        response = await generate_with_fallback(
            db=db,
            business_id=business_id,
            messages=messages,
            temperature=0.8,  # more creative for copywriting
            max_tokens=2000,
            use_semantic_cache=False,  # each campaign should get fresh variety
        )

        if response is None:
            return AICopywriterAgent._fallback_copy(
                campaign_type, product_name, variant_count
            )

        parsed = LLMResponseParser.parse_json_response(response.content)

        if parsed is None or not LLMResponseParser.validate_campaign_copy_schema(parsed):
            logger.warning(
                f"AI copywriter returned invalid schema for campaign_type={campaign_type}, "
                f"falling back to templates"
            )
            return AICopywriterAgent._fallback_copy(
                campaign_type, product_name, variant_count
            )

        return {
            "campaign_type": campaign_type,
            "language": language.value,
            "tone": tone.value,
            "generated_by": response.provider,
            "model": response.model,
            "content": parsed,
        }

    @staticmethod
    async def generate_and_rank(
        db: AsyncSession,
        business_id: uuid.UUID,
        campaign_type: str,
        product_name: str,
        product_description: str,
        audience: str = "general",
        tone: CopyTone = CopyTone.URGENT,
        language: SupportedLanguage = SupportedLanguage.ES,
        variant_count: int = 5,
        historical_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, Any]:
        """Generate copy AND rank each content type by predicted performance"""
        result = await AICopywriterAgent.generate_campaign_copy(
            db=db,
            business_id=business_id,
            campaign_type=campaign_type,
            product_name=product_name,
            product_description=product_description,
            audience=audience,
            tone=tone,
            language=language,
            variant_count=variant_count,
        )

        content = result["content"]
        ranked = {}
        for content_type, variants in content.items():
            hist = (historical_data or {}).get(content_type, [])
            ranked[content_type] = VariantScorer.rank_variants(variants, hist)

        result["ranked_content"] = ranked
        result["recommended"] = {
            content_type: variants[0]["text"] if variants else None
            for content_type, variants in ranked.items()
        }
        return result

    @staticmethod
    async def translate_copy(
        db: AsyncSession,
        business_id: uuid.UUID,
        content: Dict[str, Any],
        target_language: SupportedLanguage,
    ) -> Dict[str, Any]:
        """Translate existing copy to another language, preserving persuasive intent"""
        messages = AICopywriterPromptBuilder.build_translation_prompt(
            content, target_language
        )

        response = await generate_with_fallback(
            db=db,
            business_id=business_id,
            messages=messages,
            temperature=0.5,
            max_tokens=2000,
            use_semantic_cache=True,
        )

        if response is None:
            return {"error": "translation_failed", "original": content}

        parsed = LLMResponseParser.parse_json_response(response.content)
        if parsed is None:
            return {"error": "translation_parse_failed", "original": content}

        return {
            "language": target_language.value,
            "content": parsed,
        }

    @staticmethod
    def _fallback_copy(
        campaign_type: str,
        product_name: str,
        variant_count: int,
    ) -> Dict[str, Any]:
        """Deterministic fallback when LLM is unavailable or returns bad output"""
        base_subjects = [
            f"{product_name} - Oferta especial hoy",
            f"No te pierdas esto: {product_name}",
            f"Últimas horas: {product_name}",
            f"{product_name} está por agotarse",
            f"Solo para ti: {product_name}",
        ]
        base_urgency = [
            "Oferta por tiempo limitado",
            "Stock limitado",
            "Termina pronto",
            "Últimas unidades",
            "Precio especial hoy",
        ]
        base_ctas = ["Comprar ahora", "Ver oferta", "Aprovechar ahora", "Reservar ya", "Obtener acceso"]
        base_sms = [
            f"{product_name}: oferta especial disponible ahora. No te la pierdas.",
        ]

        def cycle(items: List[str], n: int) -> List[str]:
            return [items[i % len(items)] for i in range(n)]

        return {
            "campaign_type": campaign_type,
            "language": "es",
            "tone": "urgent",
            "generated_by": "fallback_template",
            "model": "static",
            "content": {
                "subject_lines": cycle(base_subjects, variant_count),
                "preview_texts": cycle(base_urgency, variant_count),
                "urgency_messages": cycle(base_urgency, variant_count),
                "cta_texts": cycle(base_ctas, variant_count),
                "sms_variants": cycle(base_sms, variant_count),
            },
        }
