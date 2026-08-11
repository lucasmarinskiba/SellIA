from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import uuid


class CallStatus(str, Enum):
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CallType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass
class AgentPersona:
    id: str
    user_id: str
    name: str
    system_prompt: str
    voice_id: str
    language: str
    speaking_rate: float
    temperature: float
    description: Optional[str] = None
    instructions: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CallRecord:
    id: str
    twilio_call_id: str
    user_id: str
    agent_persona_id: str
    contact_number: str
    call_type: CallType
    status: CallStatus
    duration_seconds: int = 0
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class CallTranscript:
    id: str
    call_id: str
    speaker: str
    text: str
    timestamp: float
    confidence: Optional[float] = None
    emotion: Optional[str] = None


class VoiceAgentManager:
    def __init__(self):
        self.call_records: dict[str, CallRecord] = {}
        self.agent_personas: dict[str, AgentPersona] = {}
        self.call_transcripts: dict[str, list[CallTranscript]] = {}
        self.call_events: dict[str, list[dict]] = {}

    def create_agent_persona(
        self,
        user_id: str,
        name: str,
        system_prompt: str,
        voice_id: str,
        language: str = "en-US",
        speaking_rate: float = 1.0,
        temperature: float = 0.7,
        description: Optional[str] = None,
        instructions: Optional[dict] = None,
    ) -> AgentPersona:
        """Create agent persona for voice calls."""
        persona_id = str(uuid.uuid4())
        persona = AgentPersona(
            id=persona_id,
            user_id=user_id,
            name=name,
            system_prompt=system_prompt,
            voice_id=voice_id,
            language=language,
            speaking_rate=speaking_rate,
            temperature=temperature,
            description=description,
            instructions=instructions or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.agent_personas[persona_id] = persona
        return persona

    def initiate_outbound_call(
        self,
        user_id: str,
        agent_persona_id: str,
        contact_number: str,
        contact_name: Optional[str] = None,
        deal_id: Optional[str] = None,
    ) -> CallRecord:
        """Initiate outbound call."""
        call_id = str(uuid.uuid4())
        twilio_call_id = f"twilio_{call_id}"

        call = CallRecord(
            id=call_id,
            twilio_call_id=twilio_call_id,
            user_id=user_id,
            agent_persona_id=agent_persona_id,
            contact_number=contact_number,
            call_type=CallType.OUTBOUND,
            status=CallStatus.QUEUED,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        self.call_records[call_id] = call
        self.call_transcripts[call_id] = []
        self.call_events[call_id] = []

        self._log_event(
            call_id,
            "call_initiated",
            {
                "call_type": "outbound",
                "contact_number": contact_number,
                "contact_name": contact_name,
            },
        )

        return call

    def handle_inbound_call(
        self,
        user_id: str,
        agent_persona_id: str,
        contact_number: str,
        contact_name: Optional[str] = None,
    ) -> CallRecord:
        """Handle inbound call."""
        call_id = str(uuid.uuid4())
        twilio_call_id = f"twilio_{call_id}"

        call = CallRecord(
            id=call_id,
            twilio_call_id=twilio_call_id,
            user_id=user_id,
            agent_persona_id=agent_persona_id,
            contact_number=contact_number,
            call_type=CallType.INBOUND,
            status=CallStatus.RINGING,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        self.call_records[call_id] = call
        self.call_transcripts[call_id] = []
        self.call_events[call_id] = []

        self._log_event(
            call_id,
            "inbound_call_received",
            {
                "contact_number": contact_number,
                "contact_name": contact_name,
            },
        )

        return call

    def add_transcript(
        self, call_id: str, speaker: str, text: str, timestamp: float, confidence: Optional[float] = None
    ) -> CallTranscript:
        """Add transcript line to call."""
        transcript = CallTranscript(
            id=str(uuid.uuid4()),
            call_id=call_id,
            speaker=speaker,
            text=text,
            timestamp=timestamp,
            confidence=confidence,
        )

        if call_id not in self.call_transcripts:
            self.call_transcripts[call_id] = []

        self.call_transcripts[call_id].append(transcript)
        return transcript

    def update_call_status(self, call_id: str, status: CallStatus) -> CallRecord:
        """Update call status."""
        if call_id not in self.call_records:
            raise ValueError(f"Call {call_id} not found")

        call = self.call_records[call_id]
        call.status = status

        if status == CallStatus.IN_PROGRESS:
            call.started_at = datetime.utcnow()
        elif status == CallStatus.COMPLETED:
            call.ended_at = datetime.utcnow()
            if call.started_at:
                call.duration_seconds = int(
                    (call.ended_at - call.started_at).total_seconds()
                )

        self._log_event(call_id, "status_changed", {"new_status": status})
        return call

    def set_recording_url(self, call_id: str, recording_url: str) -> CallRecord:
        """Set recording URL for completed call."""
        if call_id not in self.call_records:
            raise ValueError(f"Call {call_id} not found")

        call = self.call_records[call_id]
        call.recording_url = recording_url

        self._log_event(call_id, "recording_saved", {"url": recording_url})
        return call

    def set_transcript_summary(self, call_id: str, summary: str) -> CallRecord:
        """Set AI-generated transcript summary."""
        if call_id not in self.call_records:
            raise ValueError(f"Call {call_id} not found")

        call = self.call_records[call_id]
        call.transcript = summary

        self._log_event(call_id, "transcript_generated", {"summary": summary})
        return call

    def analyze_sentiment(self, call_id: str, sentiment: str, score: float) -> CallRecord:
        """Set sentiment analysis result."""
        if call_id not in self.call_records:
            raise ValueError(f"Call {call_id} not found")

        call = self.call_records[call_id]
        call.sentiment = sentiment
        call.sentiment_score = score

        self._log_event(call_id, "sentiment_analyzed", {"sentiment": sentiment, "score": score})
        return call

    def get_call_detail(self, call_id: str) -> dict:
        """Get full call details with transcript."""
        if call_id not in self.call_records:
            raise ValueError(f"Call {call_id} not found")

        call = self.call_records[call_id]
        transcripts = self.call_transcripts.get(call_id, [])
        events = self.call_events.get(call_id, [])

        return {
            "call": asdict(call),
            "transcripts": [asdict(t) for t in transcripts],
            "events": events,
        }

    def get_user_calls(self, user_id: str, limit: int = 50) -> list[CallRecord]:
        """Get recent calls for user."""
        user_calls = [
            c for c in self.call_records.values() if c.user_id == user_id
        ]
        return sorted(
            user_calls, key=lambda x: x.created_at or datetime.min, reverse=True
        )[:limit]

    def get_call_analytics(self, user_id: str, days: int = 30) -> dict:
        """Get call analytics for user."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        user_calls = [
            c
            for c in self.call_records.values()
            if c.user_id == user_id and c.created_at and c.created_at > cutoff_date
        ]

        completed_calls = [c for c in user_calls if c.status == CallStatus.COMPLETED]
        failed_calls = [c for c in user_calls if c.status == CallStatus.FAILED]

        total_duration = sum(c.duration_seconds for c in completed_calls)
        avg_duration = (
            total_duration / len(completed_calls) if completed_calls else 0
        )

        avg_sentiment = (
            sum(c.sentiment_score or 0 for c in completed_calls) / len(completed_calls)
            if completed_calls
            else 0
        )

        return {
            "total_calls": len(user_calls),
            "total_duration_seconds": total_duration,
            "avg_duration_seconds": avg_duration,
            "completed_calls": len(completed_calls),
            "failed_calls": len(failed_calls),
            "completion_rate": (
                len(completed_calls) / len(user_calls)
                if user_calls
                else 0
            ),
            "avg_sentiment_score": avg_sentiment,
            "period_days": days,
        }

    def _log_event(self, call_id: str, event_type: str, event_data: dict) -> None:
        """Log call event."""
        if call_id not in self.call_events:
            self.call_events[call_id] = []

        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.call_events[call_id].append(event)

    def clear_cache(self) -> None:
        """Clear in-memory cache."""
        self.call_records.clear()
        self.agent_personas.clear()
        self.call_transcripts.clear()
        self.call_events.clear()
