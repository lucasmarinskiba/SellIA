"""Voice call tracking + agent config -- backed by the real VoiceCall/
VoiceConfig models (app.domains.voice.models), not in-memory dicts.

Rewrite history: this used to be a module-level singleton with plain dict
attributes (call_records, agent_personas, call_transcripts, call_events) --
state shared across every business in the app, gone on every restart, and
never actually connected to Twilio or anything real. A real, unused
VoiceCall/VoiceConfig pair of models already existed elsewhere in the
codebase covering almost this exact concept -- wired to those instead of
building a parallel, duplicate persistence layer.

One real simplification from the original design: the mock supported
multiple named "personas" per user (each with its own system_prompt/voice/
temperature). VoiceConfig is one-row-per-business (`business_id` is
UNIQUE), which is the actual real constraint already in production -- a
business has ONE voice agent configuration, not several. Adapted the API
to that reality rather than inventing multi-persona support the schema
was never built for.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.voice.models import VoiceCall, VoiceConfig


class VoiceAgentManager:
    @staticmethod
    async def get_or_create_config(business_id: UUID, db: AsyncSession, **defaults) -> VoiceConfig:
        """Get this business's voice config, creating a default one if none exists yet."""
        result = await db.execute(select(VoiceConfig).where(VoiceConfig.business_id == business_id))
        config = result.scalar_one_or_none()
        if config:
            return config

        config = VoiceConfig(
            business_id=business_id,
            voice_id=defaults.get("voice_id", "default"),
            tts_provider=defaults.get("tts_provider", "openai"),
            stt_provider=defaults.get("stt_provider", "openai_whisper"),
            language=defaults.get("language", "es"),
            greeting_message=defaults.get("greeting_message", "Hola, gracias por tu llamada."),
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def update_config(
        business_id: UUID,
        db: AsyncSession,
        voice_id: Optional[str] = None,
        language: Optional[str] = None,
        greeting_message: Optional[str] = None,
        agent_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> VoiceConfig:
        """Update (or create) this business's voice agent configuration."""
        config = await VoiceAgentManager.get_or_create_config(business_id, db)
        if voice_id is not None:
            config.voice_id = voice_id
        if language is not None:
            config.language = language
        if greeting_message is not None:
            config.greeting_message = greeting_message
        if agent_name is not None:
            config.agent_name = agent_name
        if system_prompt is not None:
            config.system_prompt = system_prompt
        if temperature is not None:
            config.temperature = temperature
        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def initiate_outbound_call(
        business_id: UUID, customer_id: UUID, phone_number: str, db: AsyncSession,
        conversation_id: Optional[UUID] = None, twilio_call_id: Optional[str] = None,
    ) -> VoiceCall:
        call = VoiceCall(
            business_id=business_id, customer_id=customer_id, conversation_id=conversation_id,
            phone_number=phone_number, direction="outbound", status="queued",
            extra_data={"twilio_call_id": twilio_call_id} if twilio_call_id else {},
            started_at=datetime.now(timezone.utc),
        )
        db.add(call)
        await db.commit()
        await db.refresh(call)
        return call

    @staticmethod
    async def handle_inbound_call(
        business_id: UUID, customer_id: UUID, phone_number: str, db: AsyncSession,
        conversation_id: Optional[UUID] = None, twilio_call_id: Optional[str] = None,
    ) -> VoiceCall:
        call = VoiceCall(
            business_id=business_id, customer_id=customer_id, conversation_id=conversation_id,
            phone_number=phone_number, direction="inbound", status="ringing",
            extra_data={"twilio_call_id": twilio_call_id} if twilio_call_id else {},
            started_at=datetime.now(timezone.utc),
        )
        db.add(call)
        await db.commit()
        await db.refresh(call)
        return call

    @staticmethod
    async def append_transcript_segment(
        call_id: UUID, business_id: UUID, speaker: str, text: str, db: AsyncSession, timestamp: float = 0.0,
    ) -> VoiceCall:
        call = await VoiceAgentManager._get_owned_call(call_id, business_id, db)
        segments = list(call.transcript_segments or [])
        segments.append({"speaker": speaker, "text": text, "start": timestamp})
        call.transcript_segments = segments
        call.transcript = "\n".join(f"{s['speaker']}: {s['text']}" for s in segments)
        await db.commit()
        await db.refresh(call)
        return call

    @staticmethod
    async def update_call_status(call_id: UUID, business_id: UUID, status: str, db: AsyncSession) -> VoiceCall:
        call = await VoiceAgentManager._get_owned_call(call_id, business_id, db)
        call.status = status
        if status == "in_progress" and not call.started_at:
            call.started_at = datetime.now(timezone.utc)
        elif status == "completed":
            call.ended_at = datetime.now(timezone.utc)
            if call.started_at:
                call.recording_duration = int((call.ended_at - call.started_at).total_seconds())
        await db.commit()
        await db.refresh(call)
        return call

    @staticmethod
    async def set_recording_url(call_id: UUID, business_id: UUID, recording_url: str, db: AsyncSession) -> VoiceCall:
        call = await VoiceAgentManager._get_owned_call(call_id, business_id, db)
        call.recording_url = recording_url
        await db.commit()
        await db.refresh(call)
        return call

    @staticmethod
    async def set_ai_summary(call_id: UUID, business_id: UUID, summary: str, db: AsyncSession) -> VoiceCall:
        call = await VoiceAgentManager._get_owned_call(call_id, business_id, db)
        call.ai_summary = summary
        await db.commit()
        await db.refresh(call)
        return call

    @staticmethod
    async def analyze_sentiment(call_id: UUID, business_id: UUID, sentiment: str, score: float, db: AsyncSession) -> VoiceCall:
        call = await VoiceAgentManager._get_owned_call(call_id, business_id, db)
        # VoiceCall has no dedicated sentiment column -- stored in extra_data
        # (JSONB) rather than adding 2 more columns for a single feature.
        extra = dict(call.extra_data or {})
        extra["sentiment"] = sentiment
        extra["sentiment_score"] = score
        call.extra_data = extra
        await db.commit()
        await db.refresh(call)
        return call

    @staticmethod
    async def get_call_detail(call_id: UUID, business_id: UUID, db: AsyncSession) -> Optional[VoiceCall]:
        result = await db.execute(
            select(VoiceCall).where(VoiceCall.id == call_id, VoiceCall.business_id == business_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_business_calls(business_id: UUID, db: AsyncSession, limit: int = 50) -> list[VoiceCall]:
        result = await db.execute(
            select(VoiceCall).where(VoiceCall.business_id == business_id)
            .order_by(VoiceCall.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_call_analytics(business_id: UUID, db: AsyncSession, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await db.execute(
            select(VoiceCall).where(VoiceCall.business_id == business_id, VoiceCall.created_at > cutoff)
        )
        calls = result.scalars().all()

        completed = [c for c in calls if c.status == "completed"]
        failed = [c for c in calls if c.status == "failed"]
        total_duration = sum(c.recording_duration or 0 for c in completed)
        sentiments = [c.extra_data.get("sentiment_score") for c in completed if c.extra_data and c.extra_data.get("sentiment_score") is not None]

        return {
            "total_calls": len(calls),
            "total_duration_seconds": total_duration,
            "avg_duration_seconds": total_duration / len(completed) if completed else 0,
            "completed_calls": len(completed),
            "failed_calls": len(failed),
            "completion_rate": len(completed) / len(calls) if calls else 0,
            "avg_sentiment_score": sum(sentiments) / len(sentiments) if sentiments else 0,
            "period_days": days,
        }

    @staticmethod
    async def find_call_by_twilio_id(twilio_call_id: str, db: AsyncSession) -> Optional[VoiceCall]:
        """Look up a call by its Twilio CallSid, stored in extra_data (no
        dedicated column). Used by the Twilio status-callback webhook."""
        result = await db.execute(
            select(VoiceCall).where(VoiceCall.extra_data["twilio_call_id"].astext == twilio_call_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_owned_call(call_id: UUID, business_id: UUID, db: AsyncSession) -> VoiceCall:
        result = await db.execute(
            select(VoiceCall).where(VoiceCall.id == call_id, VoiceCall.business_id == business_id)
        )
        call = result.scalar_one_or_none()
        if not call:
            raise ValueError(f"Call {call_id} not found")
        return call
