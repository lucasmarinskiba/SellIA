"""Emotional Intelligence Engine

Detects customer emotions from messages and adapts AI tone accordingly.
"""

import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.schemas_intelligence import EmotionResult
from app.domains.agents.models_emotion import EmotionDetection

logger = get_logger(__name__)


class EmotionDetector:
    """Detects customer emotion using LLM analysis with Redis caching."""

    @staticmethod
    async def detect_emotion(
        db: AsyncSession,
        business_id: uuid.UUID,
        message: str,
        conversation_history: Optional[List[str]] = None,
        message_id: Optional[uuid.UUID] = None,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> EmotionResult:
        """
        Analyze the emotion of a customer message using the cheapest LLM.
        Caches result in Redis for 1 hour.
        """
        # Build cache key
        cache_key_data = json.dumps(
            {"msg": message, "hist_len": len(conversation_history or [])},
            sort_keys=True,
        )
        cache_key = f"sellia:emotion:{hashlib.sha256(cache_key_data.encode()).hexdigest()[:32]}"

        # Try cache first
        try:
            import redis.asyncio as redis
            from app.core.config import get_settings

            settings = get_settings()
            redis_client = redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                await redis_client.close()
                return EmotionResult(**data)
            await redis_client.close()
        except Exception as e:
            logger.warning(f"Redis cache miss/error for emotion: {e}")

        # Build prompt
        history_text = ""
        if conversation_history:
            history_text = "\n".join(f"- {h}" for h in conversation_history[-5:])

        prompt = (
            "Analiza la emoción de este mensaje del cliente. "
            "Devuelve SOLO un JSON válido con este formato exacto:\n"
            '{"emotion": "frustrated|enthusiastic|doubtful|angry|happy|hurried|neutral", '
            '"intensity": 0.0-1.0, '
            '"triggers": ["string"]}\n\n'
            f"Historial reciente:\n{history_text}\n\n"
            f"Mensaje: {message}\n\nJSON:"
        )

        try:
            # Late import to avoid circular dependency with ai_reply
            from app.domains.agents.ai_reply import generate_raw_ai_response

            raw = await generate_raw_ai_response(
                db=db,
                business_id=business_id,
                system_prompt=(
                    "Eres un analista de emociones especializado en ventas. "
                    "Analiza el mensaje del cliente y devuelve JSON válido. "
                    "Las emociones válidas son: frustrated, enthusiastic, doubtful, "
                    "angry, happy, hurried, neutral. "
                    "La intensidad debe ser entre 0.0 y 1.0."
                ),
                user_prompt=prompt,
                max_tokens=300,
                temperature=0.2,
            )
        except Exception as e:
            logger.error(f"Emotion LLM detection failed: {e}")
            raw = None

        # Parse response
        result = EmotionResult(emotion="neutral", intensity=0.0, triggers=[])
        if raw:
            try:
                # Extract JSON from potential markdown
                json_str = raw.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                data = json.loads(json_str)
                emotion = data.get("emotion", "neutral").lower().strip()
                valid_emotions = {
                    "frustrated",
                    "enthusiastic",
                    "doubtful",
                    "angry",
                    "happy",
                    "hurried",
                    "neutral",
                }
                if emotion not in valid_emotions:
                    emotion = "neutral"
                triggers = data.get("triggers", [])
                if not isinstance(triggers, list):
                    triggers = [str(triggers)] if triggers else []
                result = EmotionResult(
                    emotion=emotion,
                    intensity=float(data.get("intensity", 0.0)),
                    triggers=triggers,
                )
            except Exception as e:
                logger.warning(f"Failed to parse emotion JSON: {e}")

        # Cache for 1 hour
        try:
            import redis.asyncio as redis
            from app.core.config import get_settings

            settings = get_settings()
            redis_client = redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            await redis_client.setex(
                cache_key, 3600, result.model_dump_json()
            )
            await redis_client.close()
        except Exception as e:
            logger.warning(f"Failed to cache emotion result: {e}")

        # Persist to DB if we have conversation_id
        if conversation_id and message_id:
            try:
                detection = EmotionDetection(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    emotion=result.emotion,
                    intensity=result.intensity,
                    triggers=result.triggers,
                )
                db.add(detection)
                await db.commit()
            except Exception as e:
                logger.warning(f"Failed to persist emotion detection: {e}")
                await db.rollback()

        return result


class ToneAdapter:
    """Adapts system prompt tone based on detected emotion."""

    _TONE_INSTRUCTIONS = {
        "angry": (
            "Sé calmado, empático, reconoce su frustración, "
            "ofrece solución concreta inmediata."
        ),
        "frustrated": (
            "Sé calmado, empático, reconoce su frustración, "
            "ofrece solución concreta inmediata."
        ),
        "enthusiastic": (
            "Sé energético, acelera el cierre, usa entusiasmo, ofrece upsell."
        ),
        "doubtful": (
            "Sé paciente, ofrece pruebas sociales, garantías, casos de éxito, FAQs."
        ),
        "hurried": (
            "Sé conciso, ve al grano, ofrece resumen bullet points."
        ),
        "happy": (
            "Sé cálido, agradece, refuerza decisión, cross-sell suave."
        ),
        "neutral": "",
    }

    @staticmethod
    def adapt_tone(system_prompt: str, emotion: EmotionResult) -> str:
        """Append tone-specific instructions to the system prompt."""
        instruction = ToneAdapter._TONE_INSTRUCTIONS.get(emotion.emotion, "")
        if not instruction:
            return system_prompt
        return (
            f"{system_prompt}\n\n"
            f"[Tono adaptado - {emotion.emotion} "
            f"(intensidad {emotion.intensity:.0%})]: {instruction}"
        )


class EmotionTimeline:
    """Retrieves emotion history for dashboard analytics."""

    @staticmethod
    async def get_emotion_timeline(
        db: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> List[EmotionDetection]:
        """Return all emotion snapshots for a conversation, ordered by time."""
        result = await db.execute(
            select(EmotionDetection)
            .where(EmotionDetection.conversation_id == conversation_id)
            .order_by(EmotionDetection.detected_at.asc())
        )
        return list(result.scalars().all())
