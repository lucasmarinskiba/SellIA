"""Voice Agent Schemas"""

from uuid import UUID
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker: str


class VoiceCallBase(BaseModel):
    business_id: UUID
    customer_id: UUID
    conversation_id: Optional[UUID] = None
    phone_number: str
    direction: str
    status: str = "ringing"


class VoiceCallCreate(VoiceCallBase):
    pass


class VoiceCallUpdate(BaseModel):
    status: Optional[str] = None
    recording_url: Optional[str] = None
    recording_duration: Optional[int] = None
    transcript: Optional[str] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None
    ai_summary: Optional[str] = None
    outcome: Optional[str] = None
    cost_usd: Optional[float] = None
    extra_data: Optional[Dict[str, Any]] = None
    ended_at: Optional[datetime] = None


class VoiceCallResponse(VoiceCallBase):
    id: UUID
    recording_url: Optional[str] = None
    recording_duration: Optional[int] = None
    transcript: Optional[str] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None
    ai_summary: Optional[str] = None
    outcome: Optional[str] = None
    cost_usd: float = 0
    extra_data: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
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
    is_active: Optional[bool] = None
    voice_id: Optional[str] = None
    tts_provider: Optional[str] = None
    stt_provider: Optional[str] = None
    language: Optional[str] = None
    greeting_message: Optional[str] = None
    max_call_duration: Optional[int] = None
    allowed_hours_start: Optional[time] = None
    allowed_hours_end: Optional[time] = None


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
    audio_b64: Optional[str] = None
