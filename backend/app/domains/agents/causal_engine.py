"""Causal Reasoning Engine for SellIA.

Identifies root causes of failed deals, detects objection patterns across
conversations, and generates data-driven pitch recommendations.
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.models_causal import ObjectionPattern as ObjectionPatternModel
from app.domains.agents.models_causal import CausalAnalysis as CausalAnalysisModel
from app.domains.channels.models import Conversation, Message
from app.domains.agents.prompt_optimizer import ConversationOutcome

logger = get_logger(__name__)


# ------------------------------------------------------------------
# Pydantic Structured Output Models
# ------------------------------------------------------------------

class CausalAnalysis(BaseModel):
    surface_reason: str
    root_cause: str
    contributing_factors: List[str] = Field(default_factory=list)
    recommended_fix: str
    confidence: float = Field(ge=0.0, le=1.0)


class ObjectionPattern(BaseModel):
    pattern_name: str
    objection_text: str
    root_cause: str
    frequency_percent: float
    overcome_rate: float
    affected_segments: List[str] = Field(default_factory=list)
    recommended_response: str


class Recommendation(BaseModel):
    segment: str
    insight: str
    recommended_action: str
    priority: str = Field(default="medium")  # low, medium, high


class PatternsWrapper(BaseModel):
    patterns: List[ObjectionPattern] = Field(default_factory=list)


class RecommendationsWrapper(BaseModel):
    recommendations: List[Recommendation] = Field(default_factory=list)


# ------------------------------------------------------------------
# CausalAnalyzer
# ------------------------------------------------------------------

class CausalAnalyzer:
    """Analyzes sales conversations to find root causes and patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Single conversation analysis
    # ------------------------------------------------------------------

    async def analyze_failed_deal(
        self,
        conversation_id: uuid.UUID,
    ) -> Optional[CausalAnalysis]:
        """For lost deals, identifies root cause:

        - "El cliente rechazó porque el precio era alto RELATIVO a su percepción de valor"
        - "La objeción 'lo voy a pensar' apareció después de que no se explicó X feature"
        - Uses LLM with prompt: "Analiza por qué falló esta conversación de ventas.
          Identifica la CAUSA RAÍZ, no solo el síntoma."
        """
        transcript = await self._build_transcript(conversation_id)
        if not transcript:
            logger.warning(f"No transcript for causal analysis of {conversation_id}")
            return None

        outcome = await self._get_outcome(conversation_id)
        business_id = await self._resolve_business_id(conversation_id)

        system_prompt = (
            "Eres un experto en análisis causal de ventas. Tu trabajo es identificar la "
            "CAUSA RAÍZ de por qué falló una conversación de ventas, NO solo el síntoma.\n\n"
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{\n'
            '  "surface_reason": "Lo que dijo el cliente (síntoma)",\n'
            '  "root_cause": "La verdadera causa raíz del rechazo",\n'
            '  "contributing_factors": ["factor 1", "factor 2"],\n'
            '  "recommended_fix": "Qué debería hacerse diferente la próxima vez",\n'
            '  "confidence": 0.85\n'
            '}\n\n'
            "Reglas:\n"
            "- surface_reason: la objeción superficial del cliente.\n"
            "- root_cause: el verdadero motivo (ej: falta de percepción de valor, no urgencia).\n"
            "- contributing_factors: lista de factores que contribuyeron.\n"
            "- recommended_fix: acción concreta y medible para prevenirlo.\n"
            "- confidence: nivel de confianza de 0.0 a 1.0.\n"
            "- Responde en español. Sé específico y basado en evidencia."
        )

        user_prompt = (
            f"Resultado de la conversación: {outcome or 'desconocido'}\n\n"
            f"Transcripción:\n\n{transcript}\n\n"
            "Analiza por qué falló esta conversación de ventas. "
            "Identifica la CAUSA RAÍZ, no solo el síntoma."
        )

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500,
                temperature=0.3,
            )
            if not response:
                return None

            result = _parse_json_response(response, CausalAnalysis)
            return result
        except Exception as e:
            logger.warning(f"Causal analysis generation failed: {e}")
            return None

    async def save_causal_analysis(
        self,
        conversation_id: uuid.UUID,
        business_id: uuid.UUID,
        deal_outcome: str,
        result: CausalAnalysis,
    ) -> CausalAnalysisModel:
        """Persist a causal analysis result to the database."""
        record = CausalAnalysisModel(
            conversation_id=conversation_id,
            business_id=business_id,
            deal_outcome=deal_outcome,
            surface_reason=result.surface_reason,
            root_cause=result.root_cause,
            contributing_factors=result.contributing_factors,
            recommended_fix=result.recommended_fix,
            confidence=result.confidence,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        logger.info(f"Saved causal analysis for conversation {conversation_id}")
        return record

    # ------------------------------------------------------------------
    # Pattern detection across conversations
    # ------------------------------------------------------------------

    async def detect_objection_patterns(
        self,
        business_id: uuid.UUID,
        days: int = 30,
    ) -> List[ObjectionPattern]:
        """Aggregates across conversations:

        - Pattern: "Precio alto" → Cause: "Falta de comunicación de valor"
          → Frequency: 23% → Overcome rate: 15%
        - Pattern: "Lo voy a pensar" → Cause: "Falta de urgencia/scarcity"
          → Frequency: 31% → Overcome rate: 8%
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all conversations with outcomes in the period
        result = await self.db.execute(
            select(ConversationOutcome, Conversation)
            .join(Conversation, ConversationOutcome.conversation_id == Conversation.id)
            .where(
                and_(
                    Conversation.business_id == business_id,
                    ConversationOutcome.created_at >= cutoff,
                )
            )
        )
        rows = result.all()
        if not rows:
            return []

        # Build aggregated context for LLM
        summaries = []
        lost_count = 0
        total_count = len(rows)
        for outcome, conversation in rows:
            status = outcome.outcome
            if status in ("lost", "no_progress", "objection_unresolved"):
                lost_count += 1
            summaries.append(
                f"Conversation {outcome.conversation_id}: outcome={status}, "
                f"feedback={outcome.feedback or 'N/A'}"
            )

        business_id_for_llm = business_id

        system_prompt = (
            "Eres un analista de datos de ventas. Analiza los resultados de conversaciones "
            "y detecta patrones de objeciones recurrentes.\n\n"
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{\n'
            '  "patterns": [\n'
            '    {\n'
            '      "pattern_name": "Nombre corto del patrón",\n'
            '      "objection_text": "Texto típico de la objeción",\n'
            '      "root_cause": "Causa raíz identificada",\n'
            '      "frequency_percent": 23.5,\n'
            '      "overcome_rate": 15.0,\n'
            '      "affected_segments": ["segmento1", "segmento2"],\n'
            '      "recommended_response": "Cómo responder recomendado"\n'
            '    }\n'
            '  ]\n'
            '}\n\n'
            "Reglas:\n"
            "- frequency_percent: porcentaje estimado de conversaciones afectadas.\n"
            "- overcome_rate: porcentaje estimado en que la objeción fue superada.\n"
            "- affected_segments: segmentos de clientes afectados.\n"
            "- recommended_response: respuesta recomendada específica.\n"
            "- Responde en español. Máximo 5 patrones, prioriza los más frecuentes."
        )

        user_prompt = (
            f"Negocio: {business_id}\n"
            f"Período: últimos {days} días\n"
            f"Total conversaciones analizadas: {total_count}\n"
            f"Conversaciones perdidas/sin progreso: {lost_count}\n\n"
            "Resúmenes de conversaciones:\n"
            + "\n".join(summaries[:50])  # Cap context size
            + "\n\nDetecta los patrones de objeciones más importantes."
        )

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id_for_llm,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
                temperature=0.3,
            )
            if not response:
                return []

            parsed = _parse_json_response(response, PatternsWrapper)
            if parsed and hasattr(parsed, "patterns"):
                return parsed.patterns
            return []
        except Exception as e:
            logger.warning(f"Objection pattern detection failed: {e}")
            return []

    async def sync_objection_patterns(
        self,
        business_id: uuid.UUID,
        patterns: List[ObjectionPattern],
    ) -> List[ObjectionPatternModel]:
        """Upsert detected objection patterns into the database."""
        saved = []
        for pattern in patterns:
            # Check if pattern already exists
            result = await self.db.execute(
                select(ObjectionPatternModel).where(
                    and_(
                        ObjectionPatternModel.business_id == business_id,
                        ObjectionPatternModel.pattern_name == pattern.pattern_name,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.objection_text = pattern.objection_text
                existing.root_cause = pattern.root_cause
                existing.frequency_percent = pattern.frequency_percent
                existing.overcome_rate = pattern.overcome_rate
                existing.affected_segments = pattern.affected_segments
                existing.recommended_response = pattern.recommended_response
                existing.updated_at = datetime.now(timezone.utc)
                saved.append(existing)
            else:
                record = ObjectionPatternModel(
                    business_id=business_id,
                    pattern_name=pattern.pattern_name,
                    objection_text=pattern.objection_text,
                    root_cause=pattern.root_cause,
                    frequency_count=int(pattern.frequency_percent * 10),  # heuristic
                    frequency_percent=pattern.frequency_percent,
                    overcome_count=int(pattern.overcome_rate * 10),  # heuristic
                    overcome_rate=pattern.overcome_rate,
                    affected_segments=pattern.affected_segments,
                    recommended_response=pattern.recommended_response,
                )
                self.db.add(record)
                saved.append(record)

        await self.db.commit()
        for record in saved:
            await self.db.refresh(record)

        logger.info(f"Synced {len(saved)} objection patterns for business {business_id}")
        return saved

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    async def generate_pitch_recommendations(
        self,
        business_id: uuid.UUID,
    ) -> List[Recommendation]:
        """Based on causal analysis:

        - "Para segmento X, enfatizar Y en los primeros 3 mensajes"
        - "Cuando el cliente menciona Z, responder con W en vez de V"
        """
        # Load existing patterns and analyses for context
        patterns_result = await self.db.execute(
            select(ObjectionPatternModel)
            .where(ObjectionPatternModel.business_id == business_id)
            .order_by(ObjectionPatternModel.frequency_percent.desc())
            .limit(10)
        )
        patterns = patterns_result.scalars().all()

        analyses_result = await self.db.execute(
            select(CausalAnalysisModel)
            .where(CausalAnalysisModel.business_id == business_id)
            .order_by(CausalAnalysisModel.created_at.desc())
            .limit(10)
        )
        analyses = analyses_result.scalars().all()

        if not patterns and not analyses:
            return []

        context_parts = []
        if patterns:
            context_parts.append("Patrones de objeciones detectados:")
            for p in patterns:
                context_parts.append(
                    f"- {p.pattern_name}: {p.objection_text} | "
                    f"Causa: {p.root_cause} | Frecuencia: {p.frequency_percent}% | "
                    f"Superación: {p.overcome_rate}% | Respuesta: {p.recommended_response}"
                )

        if analyses:
            context_parts.append("\nAnálisis causales recientes:")
            for a in analyses:
                context_parts.append(
                    f"- {a.deal_outcome}: {a.root_cause} | Fix: {a.recommended_fix}"
                )

        system_prompt = (
            "Eres un estratega de ventas senior. Basado en los análisis causales y patrones "
            "de objeciones, genera recomendaciones concretas para mejorar los pitches.\n\n"
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{\n'
            '  "recommendations": [\n'
            '    {\n'
            '      "segment": "Segmento o situación objetivo",\n'
            '      "insight": "Insight clave descubierto",\n'
            '      "recommended_action": "Acción concreta y específica",\n'
            '      "priority": "high"\n'
            '    }\n'
            '  ]\n'
            '}\n\n'
            "Reglas:\n"
            "- segment: a quién o en qué situación aplica.\n"
            "- insight: qué descubrimiento causal justifica la recomendación.\n"
            "- recommended_action: instrucción ultra-específica (ej: 'enfatizar Y en los primeros 3 mensajes').\n"
            "- priority: 'high', 'medium', o 'low'.\n"
            "- Responde en español. Máximo 7 recomendaciones, prioriza alto impacto."
        )

        user_prompt = (
            "Contexto de análisis causal del negocio:\n\n"
            + "\n".join(context_parts)
            + "\n\nGenera recomendaciones de pitch basadas en estos datos."
        )

        try:
            response = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
                temperature=0.4,
            )
            if not response:
                return []

            parsed = _parse_json_response(response, RecommendationsWrapper)
            if parsed and hasattr(parsed, "recommendations"):
                return parsed.recommendations
            return []
        except Exception as e:
            logger.warning(f"Pitch recommendation generation failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _build_transcript(
        self,
        conversation_id: uuid.UUID,
    ) -> Optional[str]:
        """Build a text transcript from conversation messages."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = result.scalars().all()
        if not messages:
            return None

        lines = []
        for msg in messages:
            role = "Cliente" if msg.direction.value == "inbound" else "Agente"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)

    async def _get_outcome(
        self,
        conversation_id: uuid.UUID,
    ) -> Optional[str]:
        """Get the recorded outcome for a conversation."""
        result = await self.db.execute(
            select(ConversationOutcome.outcome)
            .where(ConversationOutcome.conversation_id == conversation_id)
            .order_by(ConversationOutcome.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _resolve_business_id(
        self,
        conversation_id: uuid.UUID,
    ) -> uuid.UUID:
        """Resolve business_id from a conversation."""
        result = await self.db.execute(
            select(Conversation.business_id)
            .where(Conversation.id == conversation_id)
        )
        business_id = result.scalar_one_or_none()
        return business_id or uuid.UUID("00000000-0000-0000-0000-000000000000")


# ------------------------------------------------------------------
# JSON parsing helper
# ------------------------------------------------------------------

def _parse_json_response(text: str, model_class) -> Optional[Any]:
    """Robustly parse a JSON response into a Pydantic model."""
    text = text.strip()

    # Try direct parse
    try:
        data = json.loads(text)
        return model_class.model_validate(data)
    except Exception:
        pass

    # Try markdown code blocks
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.index("```", start)
            data = json.loads(text[start:end].strip())
            return model_class.model_validate(data)
        except Exception:
            pass

    if "```" in text:
        try:
            start = text.index("```") + 3
            end = text.index("```", start)
            data = json.loads(text[start:end].strip())
            return model_class.model_validate(data)
        except Exception:
            pass

    # Try JSON between braces
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
        return model_class.model_validate(data)
    except Exception:
        pass

    logger.warning(f"Could not parse JSON response into {model_class.__name__}")
    return None
