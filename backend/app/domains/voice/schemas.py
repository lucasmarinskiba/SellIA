"""Voice Agent Schemas"""

from datetime import datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker: str


class VoiceCallBase(BaseModel):
    business_id: UUID
    customer_id: UUID
    conversation_id: UUID | None = None
    phone_number: str
    direction: str
    status: str = "ringing"


class VoiceCallCreate(VoiceCallBase):
    pass


class VoiceCallUpdate(BaseModel):
    status: str | None = None
    recording_url: str | None = None
    recording_duration: int | None = None
    transcript: str | None = None
    transcript_segments: list[TranscriptSegment] | None = None
    ai_summary: str | None = None
    outcome: str | None = None
    cost_usd: float | None = None
    extra_data: dict[str, Any] | None = None
    ended_at: datetime | None = None


class VoiceCallResponse(VoiceCallBase):
    id: UUID
    recording_url: str | None = None
    recording_duration: int | None = None
    transcript: str | None = None
    transcript_segments: list[TranscriptSegment] | None = None
    ai_summary: str | None = None
    outcome: str | None = None
    cost_usd: float = 0
    extra_data: dict[str, Any] = {}
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceConfigBase(BaseModel):
    business_id: UUID
    is_active: bool = True
    voice_id: str
    tts_provider: str
    stt_provider: str
    language: str = "es"
    greeting_message: str
    max_call_duration: int = 600
    allowed_hours_start: time = time(9, 0)
    allowed_hours_end: time = time(18, 0)


class VoiceConfigCreate(VoiceConfigBase):
    pass


class VoiceConfigUpdate(BaseModel):
    is_active: bool | None = None
    voice_id: str | None = None
    tts_provider: str | None = None
    stt_provider: str | None = None
    language: str | None = None
    greeting_message: str | None = None
    max_call_duration: int | None = None
    allowed_hours_start: time | None = None
    allowed_hours_end: time | None = None


class VoiceConfigResponse(VoiceConfigBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpeechRequest(BaseModel):
    text: str


class TranscriptionResponse(BaseModel):
    transcript: str


class CallSegmentResponse(BaseModel):
    transcript: str
    ai_response_text: str
    audio_b64: str | None = None
