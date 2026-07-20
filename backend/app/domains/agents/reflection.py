"""Chain-of-Thought and Self-Reflection Systems for SellIA.

Provides explicit reasoning traceability and post-conversation self-analysis
to continuously improve agent behavior.
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.domains.agents.models_reflection import AgentReflection, ChainOfThoughtLog
from app.domains.channels.models import Conversation, Message

logger = get_logger(__name__)


# ------------------------------------------------------------------
# Pydantic Structured Output Models
# ------------------------------------------------------------------

class ThoughtStep(BaseModel):
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None


class ThoughtProcess(BaseModel):
    steps: List[ThoughtStep] = Field(default_factory=list)


class ReflectionResult(BaseModel):
    what_went_well: str
    what_could_improve: str
    customer_insights: str
    future_recommendations: str
    score: int = Field(ge=0, le=100)


# ------------------------------------------------------------------
# Chain-of-Thought
# ------------------------------------------------------------------

class ChainOfThought:
    """Generates explicit reasoning steps for complex AI responses."""

    @staticmethod
    async def generate_thought_process(
        db: AsyncSession,
        query: str,
        context: Dict[str, Any],
        tools_used: List[str],
    ) -> List[ThoughtStep]:
        """Generate explicit reasoning steps for a given query.

        Steps:
        1. "Pienso que el cliente quiere... porque dijo..."
        2. "La mejor estrategia sería... dado que..."
        3. "Necesito verificar... usando [tool]"
        4. "Basado en eso, debería responder..."
        """
        system_prompt = (
            "Eres un experto en razonamiento paso a paso para ventas. "
            "Analiza la consulta del cliente y genera un proceso de pensamiento explícito "
            "en español. Devuelve SOLO un JSON válido con la estructura exacta:\n"
            '{"steps": [{"step_number": 1, "thought": "...", "action": "...", "observation": "..."}]}\n\n'
            "Reglas:\n"
            "- step 1: Interpreta la intención del cliente y por qué.\n"
            "- step 2: Elige la mejor estrategia de ventas y justifícala.\n"
            "- step 3: Indica qué herramienta o verificación necesitas.\n"
            "- step 4: Resume qué respuesta darás basado en todo lo anterior.\n"
            "- Usa español. Sé conciso."
        )

        user_prompt = (
            f"Consulta del cliente: {query}\n\n"
            f"Contexto disponible: {json.dumps(context, ensure_ascii=False)}\n\n"
            f"Herramientas disponibles: {', '.join(tools_used) if tools_used else 'ninguna'}"
        )

        # Resolve a business_id for LLM routing; fallback to a nil UUID
        business_id = context.get("business_id")
        if business_id is None:
            business_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

        try:
            response = await generate_raw_ai_response(
                db=db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1200,
                temperature=0.3,
            )
            if not response:
                return []

            parsed = _parse_json_response(response, ThoughtProcess)
            return parsed.steps if parsed else []
        except Exception as e:
            logger.warning(f"Chain-of-thought generation failed: {e}")
            return []

    @staticmethod
    async def log_thought_process(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        message_id: Optional[uuid.UUID],
        thought_steps: List[ThoughtStep],
    ) -> Optional[ChainOfThoughtLog]:
        """Persist a chain-of-thought to the database."""
        if not thought_steps:
            return None

        log = ChainOfThoughtLog(
            conversation_id=conversation_id,
            message_id=message_id,
            thought_steps=[step.model_dump() for step in thought_steps],
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        logger.info(f"Logged {len(thought_steps)} thought steps for conversation {conversation_id}")
        return log


# ------------------------------------------------------------------
# Self-Reflection
# ------------------------------------------------------------------

class SelfReflection:
    """Analyzes a completed conversation to extract learnings."""

    @staticmethod
    async def reflect_on_conversation(
        db: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> Optional[ReflectionResult]:
        """After conversation ends, analyze:

        1. "¿Qué hice bien?" — identify successful tactics
        2. "¿Qué podría haber hecho mejor?" — identify missed opportunities
        3. "¿Qué aprendí sobre este cliente?" — new insights
        4. "¿Cómo debería abordar clientes similares en el futuro?"
        """
        # Fetch conversation transcript
        transcript = await SelfReflection._build_transcript(db, conversation_id)
        if not transcript:
            logger.warning(f"No transcript found for reflection on {conversation_id}")
            return None

        system_prompt = (
            "Eres un experto en análisis de conversaciones de ventas. "
            "Realiza una auto-reflexión profunda sobre la conversación proporcionada. "
            "Devuelve SOLO un JSON válido con esta estructura exacta:\n"
            '{\n'
            '  "what_went_well": "...",\n'
            '  "what_could_improve": "...",\n'
            '  "customer_insights": "...",\n'
            '  "future_recommendations": "...",\n'
            '  "score": 75\n'
            '}\n\n'
            "Reglas:\n"
            "- what_went_well: tácticas exitosas que usaste.\n"
            "- what_could_improve: oportunidades perdidas y cómo mejorar.\n"
            "- customer_insights: nuevos aprendizajes sobre este cliente específico.\n"
            "- future_recommendations: cómo abordar clientes similares en el futuro.\n"
            "- score: auto-evaluación del 0 al 100.\n"
            "- Responde en español. Sé específico y accionable."
        )

        user_prompt = (
            "Transcripción de la conversación de ventas:\n\n"
            f"{transcript}\n\n"
            "Realiza la auto-reflexión solicitada."
        )

        # Resolve business_id from conversation for LLM routing
        business_id = await SelfReflection._resolve_business_id(db, conversation_id)

        try:
            response = await generate_raw_ai_response(
                db=db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500,
                temperature=0.4,
            )
            if not response:
                return None

            result = _parse_json_response(response, ReflectionResult)
            return result
        except Exception as e:
            logger.warning(f"Self-reflection generation failed: {e}")
            return None

    @staticmethod
    async def save_reflection(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        agent_type: str,
        result: ReflectionResult,
    ) -> AgentReflection:
        """Persist a reflection result to the database."""
        record = AgentReflection(
            conversation_id=conversation_id,
            agent_type=agent_type,
            what_went_well=result.what_went_well,
            what_could_improve=result.what_could_improve,
            customer_insights=result.customer_insights,
            future_recommendations=result.future_recommendations,
            score=result.score,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        logger.info(f"Saved reflection for conversation {conversation_id} (score={result.score})")
        return record

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _build_transcript(
        db: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> Optional[str]:
        """Build a text transcript from conversation messages."""
        result = await db.execute(
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

    @staticmethod
    async def _resolve_business_id(
        db: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> uuid.UUID:
        """Resolve business_id from a conversation."""
        result = await db.execute(
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
