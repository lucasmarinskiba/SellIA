"""Voice Sales + Playbook Management (Phase 29)."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_sales import (
    VoiceCall,
    CallTranscript,
    VoiceCallMetrics,
    SalesPlaybook,
    PlaybookExecution,
    SalesRepPerformance,
    AICallScript,
    MeetingBooking,
)
import logging
import json

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)


def _as_uuid(value: str) -> Optional[uuid.UUID]:
    """A UUID from an id that came in as text, or None when it is not one (treated as not found)."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


@dataclass
class VoiceCallResult:
    """Voice call initiation result."""

    call_id: str
    prospect_id: str
    deal_id: str
    status: str  # initiated, in_progress, completed
    script: str


@dataclass
class PlaybookRecommendation:
    """Playbook recommendation for deal."""

    playbook_id: str
    name: str
    industry: str
    deal_stage: str
    win_rate: float
    next_step: str
    confidence: float


class VoiceCallManager:
    """Manage AI voice calls via Twilio + Claude."""

    def __init__(self, db: AsyncSession, twilio_client=None, claude_api_key: Optional[str] = None):
        self.db = db
        self.twilio = twilio_client
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    async def initiate_call(self, prospect_id: str, deal_id: str) -> VoiceCallResult:
        """Initiate AI voice call with prospect."""

        try:
            from app.domains.crm.models import Deal  # NOTE: app.models.deal never existed -- redirected to the real Deal model used elsewhere in the app (same app.core.database.Base)

            # 1. Get prospect + deal context
            deal_uuid = _as_uuid(deal_id)
            deal = (await self.db.execute(select(Deal).where(Deal.id == deal_uuid))).scalar_one_or_none() if deal_uuid else None
            if not deal:
                raise ValueError(f"Deal {deal_id} not found")

            # 2. Generate voice script
            script = self._generate_voice_script(prospect_id, deal_id)

            # 3. Create Twilio call (if Twilio available)
            call_sid = None
            if self.twilio:
                try:
                    call = self.twilio.calls.create(
                        to=f"+1{prospect_id}",  # Placeholder: real phone from DB
                        from_="+1555SELLAI",  # Placeholder Twilio number
                        url="https://api.sellia.com/voice/handle-call",
                        record=True,
                    )
                    call_sid = call.sid
                except Exception as e:
                    logger.warning(f"Twilio call creation failed: {e}")

            # 4. Store voice call record
            voice_call = VoiceCall(
                prospect_id=prospect_id,
                deal_id=deal_id,
                call_sid=call_sid,
                script_used=script,
                started_at=datetime.utcnow(),
                status="initiated",
            )
            self.db.add(voice_call)
            await self.db.commit()

            logger.info(f"Voice call initiated for prospect {prospect_id}, deal {deal_id}")

            return VoiceCallResult(
                call_id=str(voice_call.id),
                prospect_id=prospect_id,
                deal_id=deal_id,
                status="initiated",
                script=script,
            )

        except Exception as e:
            logger.error(f"Error initiating voice call: {e}")
            raise

    async def handle_call_input(self, call_id: str, input_text: str) -> str:
        """Handle incoming voice input from prospect."""

        try:
            # 1. Get call context
            call = await self._call(call_id)
            if not call:
                return "Call not found"

            # 2. Get conversation history
            history = await self._get_conversation_history(call_id)

            # 3. Build Claude prompt
            prompt = f"""
            You are professional AI sales agent calling {call.prospect_id} about {call.deal_id}.

            Initial script: {call.script_used}

            Conversation history:
            {json.dumps(history, indent=2)}

            Prospect just said: "{input_text}"

            Respond naturally:
            1. If objection, handle it with benefit statement
            2. If qualified, suggest meeting
            3. Keep response under 30 seconds

            Next response:
            """

            # 4. Get Claude response
            if not self.claude:
                logger.warning("Claude not available. Using template response.")
                response_text = "That sounds great. Can we schedule a brief call to discuss further?"
            else:
                message = self.claude.messages.create(
                    model="claude-opus",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = message.content[0].text

            # 5. Store conversation turn
            prospect_turn = CallTranscript(
                call_id=call_id,
                speaker="prospect",
                text=input_text,
                timestamp=datetime.utcnow(),
            )
            self.db.add(prospect_turn)

            ai_turn = CallTranscript(
                call_id=call_id,
                speaker="ai",
                text=response_text,
                timestamp=datetime.utcnow(),
            )
            self.db.add(ai_turn)
            await self.db.commit()

            return response_text

        except Exception as e:
            logger.error(f"Error handling call input: {e}")
            return "I didn't catch that. Could you repeat?"

    async def end_call(self, call_id: str, outcome: str = "unqualified") -> Dict[str, Any]:
        """End call, analyze, and update metrics."""

        try:
            call = await self._call(call_id)
            if not call:
                return {"error": "Call not found"}

            # 1. Get full transcript
            transcript_turns = (
                await self.db.execute(
                    select(CallTranscript).where(CallTranscript.call_id == _as_uuid(call_id)).order_by(CallTranscript.timestamp)
                )
            ).scalars().all()

            full_transcript = "\n".join([f"{t.speaker}: {t.text}" for t in transcript_turns])

            # 2. Analyze call (sentiment, objections, decision)
            analysis = self._analyze_call(full_transcript)

            # 3. Update call record
            # The module stores naive UTC everywhere (datetime.utcnow). Read started_at back as naive UTC
            # too: the table's timestamp columns are not all the same kind, so mixing aware and naive values
            # in one UPDATE or one subtraction fails.
            ended_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            started = call.started_at
            if started.tzinfo is not None:
                started = started.astimezone(timezone.utc).replace(tzinfo=None)
            call.ended_at = ended_utc
            call.transcript = full_transcript
            call.outcome = outcome  # or analysis["decision"]
            call.status = "completed"
            call.duration_seconds = int((ended_utc - started).total_seconds())

            # 4. Store metrics
            metrics = VoiceCallMetrics(
                call_id=call_id,
                objections_raised=analysis.get("objections_count", 0),
                objections_handled=analysis.get("objections_handled", 0),
                questions_asked=len([t for t in transcript_turns if t.speaker == "ai" and "?" in t.text]),
            )
            self.db.add(metrics)

            # 5. Create meeting if booked
            if analysis.get("decision") == "meeting_booked":
                meeting = MeetingBooking(
                    prospect_id=call.prospect_id,
                    deal_id=call.deal_id,
                    scheduled_for=analysis.get("meeting_time"),
                    ai_booked=True,
                    call_id=call_id,
                )
                self.db.add(meeting)

            self.db.add(call)
            await self.db.commit()

            logger.info(f"Call {call_id} ended with outcome: {outcome}")

            return {
                "call_id": str(call_id),
                "outcome": outcome,
                "duration": call.duration_seconds,
                "meeting_booked": analysis.get("decision") == "meeting_booked",
                "analysis": analysis,
            }

        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return {"error": str(e)}

    def _generate_voice_script(self, prospect_id: str, deal_id: str) -> str:
        """Generate voice script from Phase 28."""

        script = f"""
        Hi, this is SellIA AI calling. I'm reaching out to [Prospect Name] at [Company].

        The reason for my call is [brief value prop].

        Do you have 60 seconds to chat?
        """

        return script

    async def _call(self, call_id: str) -> Optional[VoiceCall]:
        call_uuid = _as_uuid(call_id)
        if call_uuid is None:
            return None
        return (await self.db.execute(select(VoiceCall).where(VoiceCall.id == call_uuid))).scalar_one_or_none()

    async def _get_conversation_history(self, call_id: str) -> List[Dict[str, str]]:
        """Get conversation turn history."""

        turns = (
            await self.db.execute(
                select(CallTranscript).where(CallTranscript.call_id == _as_uuid(call_id)).order_by(CallTranscript.timestamp)
            )
        ).scalars().all()

        return [{"speaker": t.speaker, "text": t.text} for t in turns]

    def _analyze_call(self, transcript: str) -> Dict[str, Any]:
        """Analyze call using Claude."""

        if not self.claude:
            return {
                "decision": "unqualified",
                "sentiment": "neutral",
                "objections_count": 0,
                "objections_handled": 0,
            }

        prompt = f"""
        Analyze this sales call transcript:

        {transcript}

        Determine:
        1. Decision: "meeting_booked", "qualified", or "unqualified"
        2. Sentiment: "positive", "neutral", or "negative"
        3. Objections raised and handled
        4. Next meeting time if booked

        Return JSON.
        """

        try:
            message = self.claude.messages.create(
                model="claude-opus",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            return json.loads(message.content[0].text)
        except Exception as e:
            logger.error(f"Error analyzing call: {e}")
            return {"decision": "unqualified"}


class PlaybookExtractor:
    """Extract sales playbooks from top performer patterns."""

    def __init__(self, db: AsyncSession, claude_api_key: Optional[str] = None):
        self.db = db
        self.claude = Anthropic(api_key=claude_api_key) if Anthropic and claude_api_key else None

    async def extract_playbooks(self, top_performer_ids: List[str]) -> List[Dict[str, Any]]:
        """Extract playbooks from top 20% performers."""

        try:
            # 1. Get successful calls from top performers
            successful_calls = (
                await self.db.execute(
                    select(VoiceCall).where(VoiceCall.outcome.in_(["meeting_booked", "qualified"])).limit(100)
                )
            ).scalars().all()

            if not successful_calls:
                logger.warning("No successful calls to extract from")
                return []

            # 2. Extract patterns using Claude
            playbooks = []
            for call in successful_calls[:20]:  # Sample 20 calls
                playbook = self._extract_from_call(call)
                if playbook:
                    playbooks.append(playbook)

            # 3. Cluster similar playbooks
            clusters = self._cluster_playbooks(playbooks)

            # 4. Consolidate into master playbooks
            master_playbooks = []
            for cluster in clusters:
                consolidated = self._consolidate_cluster(cluster)
                if consolidated:
                    master_playbooks.append(consolidated)

            logger.info(f"Extracted {len(master_playbooks)} playbooks from {len(successful_calls)} calls")

            return master_playbooks

        except Exception as e:
            logger.error(f"Error extracting playbooks: {e}")
            return []

    def _extract_from_call(self, call: VoiceCall) -> Optional[Dict[str, Any]]:
        """Extract playbook elements from single call."""

        if not self.claude or not call.transcript:
            return None

        prompt = f"""
        Analyze this successful sales call and extract playbook elements:

        Transcript:
        {call.transcript}

        Extract:
        1. Opening statement (introduction)
        2. Discovery questions asked
        3. Value proposition presented
        4. Objections encountered and responses
        5. Closing/booking approach

        Return as JSON with these fields.
        """

        try:
            message = self.claude.messages.create(
                model="claude-opus",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            return json.loads(message.content[0].text)
        except Exception as e:
            logger.error(f"Error extracting from call: {e}")
            return None

    def _cluster_playbooks(self, playbooks: List[Dict]) -> List[List[Dict]]:
        """Cluster similar playbooks."""

        # Simplified: group by deal outcome pattern
        clusters = {}
        for pb in playbooks:
            # Use first few words of opening as clustering key
            key = pb.get("opening", "default")[:30]
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(pb)

        return list(clusters.values())

    def _consolidate_cluster(self, cluster: List[Dict]) -> Optional[SalesPlaybook]:
        """Create playbook from cluster."""

        try:
            playbook = SalesPlaybook(
                name=f"Extracted Playbook {datetime.utcnow().timestamp()}",
                win_rate=0.75,  # Placeholder
                usage_count=0,
                extracted_from_calls=len(cluster),
                created_at=datetime.utcnow(),
            )

            return playbook
        except Exception as e:
            logger.error(f"Error consolidating cluster: {e}")
            return None


class PlaybookRecommender:
    """Recommend playbooks in real-time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _first_step_name(steps) -> str:
        """Playbook steps are objects ({"step": 1, "name": "Opening", ...}); the answer needs their name."""
        first = steps[0] if steps else None
        if isinstance(first, dict):
            return str(first.get("name") or "Opening")
        return str(first) if first else "Opening"

    async def recommend_playbook(self, deal_id: str) -> Optional[PlaybookRecommendation]:
        """Get recommended playbook for deal."""

        try:
            from app.domains.crm.models import Deal  # NOTE: app.models.deal never existed -- redirected to the real Deal model used elsewhere in the app (same app.core.database.Base)

            from app.domains.businesses.models import Business

            deal_uuid = _as_uuid(deal_id)
            deal = (await self.db.execute(select(Deal).where(Deal.id == deal_uuid))).scalar_one_or_none() if deal_uuid else None
            if not deal:
                return None

            # Deal has no industry: the business type plays that role. The stage is a LeadStage enum
            # while playbooks store its value as text (the old code compared the enum object, and read
            # deal.industry, which does not exist, so this method always returned None).
            business = (await self.db.execute(select(Business).where(Business.id == deal.business_id))).scalar_one_or_none()
            industry = business.type.value if business is not None and business.type is not None else None
            stage = deal.stage.value if deal.stage is not None else None

            conditions = []
            if industry:
                conditions.append(SalesPlaybook.industry.ilike(f"%{industry}%"))
            if stage:
                conditions.append(SalesPlaybook.deal_stage == stage)
            if not conditions:
                return None

            # 1. Find matching playbooks (by industry/stage)
            candidates = (
                await self.db.execute(
                    select(SalesPlaybook).where(or_(*conditions)).order_by(SalesPlaybook.win_rate.desc()).limit(1)
                )
            ).scalars().first()

            if not candidates:
                return None

            # 2. Return best match
            return PlaybookRecommendation(
                playbook_id=str(candidates.id),
                name=candidates.name,
                industry=candidates.industry or "general",
                deal_stage=candidates.deal_stage or "unknown",
                win_rate=candidates.win_rate or 0.5,
                next_step=self._first_step_name(candidates.steps),
                confidence=0.85,
            )

        except Exception as e:
            logger.error(f"Error recommending playbook: {e}")
            return None
