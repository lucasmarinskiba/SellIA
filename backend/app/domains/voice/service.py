"""Voice Agent Service

Handles STT, TTS, and AI-driven voice call processing.
"""

import uuid
import base64
from typing import Optional
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.voice.models import VoiceCall, VoiceConfig

logger = get_logger(__name__)


class VoiceService:
    """Service layer for voice capabilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # STT / TTS
    # ------------------------------------------------------------------

    async def transcribe_audio(self, audio_bytes: bytes, provider: str = "openai_whisper") -> str:
        """Transcribe audio bytes to text using the configured provider."""
        settings = get_settings()
        api_key = settings.OPENAI_API_KEY

        if provider == "openai_whisper" and api_key:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
                        data={"model": "whisper-1", "language": "es"},
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data.get("text", "")
            except Exception as e:
                logger.warning(f"Whisper transcription failed: {e}")

        # Fallback: return mock transcript for development
        logger.info("STT fallback: returning mock transcript")
        return "[Transcripción no disponible - modo simulado]"

    async def generate_speech(self, text: str, voice_config: VoiceConfig) -> bytes:
        """Generate speech audio bytes from text using the configured TTS provider."""
        settings = get_settings()

        if voice_config.tts_provider == "openai" and settings.OPENAI_API_KEY:
            try:
                voice_id = voice_config.voice_id if voice_config.voice_id in ("alloy", "echo", "fable", "onyx", "nova", "shimmer") else "alloy"
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/audio/speech",
                        headers={
                            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "tts-1",
                            "input": text,
                            "voice": voice_id,
                        },
                    )
                    response.raise_for_status()
                    return response.content
            except Exception as e:
                logger.warning(f"OpenAI TTS failed: {e}")

        elif voice_config.tts_provider == "elevenlabs" and settings.ELEVENLABS_API_KEY:
            try:
                voice_id = voice_config.voice_id or "21m00Tcm4TlvDq8ikWAM"
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                        headers={
                            "xi-api-key": settings.ELEVENLABS_API_KEY,
                            "Content-Type": "application/json",
                        },
                        json={
                            "text": text,
                            "model_id": "eleven_multilingual_v2",
                            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                        },
                    )
                    response.raise_for_status()
                    return response.content
            except Exception as e:
                logger.warning(f"ElevenLabs TTS failed: {e}")

        # Fallback: return empty bytes (frontend should handle gracefully)
        logger.info("TTS fallback: returning empty audio")
        return b""

    # ------------------------------------------------------------------
    # Call segment processing
    # ------------------------------------------------------------------

    async def process_call_segment(
        self,
        call_id: uuid.UUID,
        audio_chunk: bytes,
    ) -> dict:
        """Process an audio segment: transcribe -> AI reply -> speech."""
        result = await self.db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
        call = result.scalar_one_or_none()
        if not call:
            raise ValueError("Call not found")

        # 1. Transcribe
        transcript = await self.transcribe_audio(audio_chunk, provider=call.extra_data.get("stt_provider", "openai_whisper"))

        # 2. Get or create conversation
        conversation = None
        if call.conversation_id:
            from app.domains.channels.models import Conversation
            conv_result = await self.db.execute(select(Conversation).where(Conversation.id == call.conversation_id))
            conversation = conv_result.scalar_one_or_none()

        if not conversation:
            from app.domains.channels.models import Conversation, ConversationStatus
            conversation = Conversation(
                business_id=call.business_id,
                lead_phone=call.phone_number,
                status=ConversationStatus.ACTIVE,
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
            call.conversation_id = conversation.id
            await self.db.commit()

        # 3. Store transcript as inbound message
        from app.domains.channels.models import Message, MessageDirection, MessageStatus
        inbound_msg = Message(
            conversation_id=conversation.id,
            direction=MessageDirection.INBOUND,
            content=transcript,
            content_type="text",
            status=MessageStatus.SENT,
        )
        self.db.add(inbound_msg)
        await self.db.commit()

        # 4. Generate AI response
        from app.domains.agents.ai_reply import generate_ai_response
        ai_text = await generate_ai_response(
            db=self.db,
            conversation=conversation,
            personality_slug="vendedor",
            business_id=call.business_id,
            max_tokens=1500,
        )
        if not ai_text:
            ai_text = "Lo siento, no pude entender eso. ¿Podrías repetirlo?"

        # 5. Store AI response as outbound message
        outbound_msg = Message(
            conversation_id=conversation.id,
            direction=MessageDirection.OUTBOUND,
            content=ai_text,
            content_type="text",
            status=MessageStatus.SENT,
        )
        self.db.add(outbound_msg)
        await self.db.commit()

        # Update call transcript
        if call.transcript:
            call.transcript += f"\nCustomer: {transcript}\nAI: {ai_text}"
        else:
            call.transcript = f"Customer: {transcript}\nAI: {ai_text}"
        await self.db.commit()

        # 6. Generate speech
        voice_config = await self._get_voice_config(call.business_id)
        audio_bytes = await self.generate_speech(ai_text, voice_config)

        return {
            "transcript": transcript,
            "ai_response_text": ai_text,
            "audio_b64": base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None,
        }

    # ------------------------------------------------------------------
    # Call lifecycle
    # ------------------------------------------------------------------

    async def create_call(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        phone_number: str,
        direction: str,
    ) -> VoiceCall:
        """Create a new voice call record."""
        call = VoiceCall(
            business_id=business_id,
            customer_id=customer_id,
            phone_number=phone_number,
            direction=direction,
            status="ringing",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(call)
        await self.db.commit()
        await self.db.refresh(call)
        return call

    async def end_call(
        self,
        call_id: uuid.UUID,
        outcome: Optional[str] = None,
    ) -> VoiceCall:
        """End a voice call and set outcome."""
        result = await self.db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
        call = result.scalar_one_or_none()
        if not call:
            raise ValueError("Call not found")

        call.status = "completed"
        call.ended_at = datetime.now(timezone.utc)
        if outcome:
            call.outcome = outcome
        await self.db.commit()
        await self.db.refresh(call)
        return call

    async def get_call_transcript(self, call_id: uuid.UUID) -> Optional[str]:
        """Retrieve the transcript for a call."""
        result = await self.db.execute(select(VoiceCall).where(VoiceCall.id == call_id))
        call = result.scalar_one_or_none()
        return call.transcript if call else None

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    async def _get_voice_config(self, business_id: uuid.UUID) -> VoiceConfig:
        """Get or create default voice config for a business."""
        result = await self.db.execute(select(VoiceConfig).where(VoiceConfig.business_id == business_id))
        config = result.scalar_one_or_none()
        if not config:
            config = VoiceConfig(
                business_id=business_id,
                voice_id="alloy",
                tts_provider="openai",
                stt_provider="openai_whisper",
                greeting_message="Hola, soy el asistente virtual de esta empresa. ¿En qué puedo ayudarte?",
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        return config

    async def get_config(self, business_id: uuid.UUID) -> Optional[VoiceConfig]:
        result = await self.db.execute(select(VoiceConfig).where(VoiceConfig.business_id == business_id))
        return result.scalar_one_or_none()

    async def upsert_config(self, data: dict) -> VoiceConfig:
        business_id = data["business_id"]
        result = await self.db.execute(select(VoiceConfig).where(VoiceConfig.business_id == business_id))
        config = result.scalar_one_or_none()

        if config:
            for field, value in data.items():
                if value is not None and hasattr(config, field):
                    setattr(config, field, value)
            config.updated_at = datetime.now(timezone.utc)
        else:
            config = VoiceConfig(**data)
            self.db.add(config)

        await self.db.commit()
        await self.db.refresh(config)
        return config
