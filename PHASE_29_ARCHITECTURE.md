# Phase 29 - Scale: Voice Agent + Sales Playbooks Architecture

**Duration**: 10 weeks (Weeks 15-24)  
**Team Size**: 2 backend engineers + 1 ML engineer + 1 frontend engineer  
**Expected Impact**: 5-10x outbound volume, +40% rep productivity  
**Prerequisites**: Phase 27 (deal intelligence), Phase 28 (email engagement)

---

## STRATEGIC OVERVIEW

Phase 29 implements 2 transformative systems:

1. **AI Voice Agent** - Outbound calling at scale (5-10x volume vs manual)
2. **Sales Playbook Engine** - Extract top-performer patterns, auto-recommend actions

Both integrate with Phase 27 deal intelligence to coordinate multi-channel sequences.

---

## 1. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND (React 19)                     │
│  Voice Call Builder | Playbook Library | Call Coaching  │
│  Performance Analytics | Script Management              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              API LAYER (FastAPI)                        │
│  /api/v1/voice/initiate-call                            │
│  /api/v1/voice/call/{call_id}/transcript                │
│  /api/v1/playbooks/list                                 │
│  /api/v1/playbooks/recommend/{deal_id}                  │
│  /api/v1/playbooks/execute/{playbook_id}                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          BUSINESS LOGIC (Python Services)               │
│  VoiceCallManager (Twilio integration)                  │
│  PlaybookExtractor (ML pattern recognition)             │
│  PlaybookRecommender (contextual play selection)        │
│  CoachingEngine (real-time guidance)                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           DATA LAYER (PostgreSQL + Redis)               │
│  voice_calls | call_transcripts | call_recordings       │
│  sales_playbooks | playbook_steps | playbook_outcomes   │
│  sales_rep_performance | play_recommendations           │
└─────────────────────────────────────────────────────────┘
```

---

## 2. DATABASE SCHEMA

### Voice System

```sql
CREATE SCHEMA voice;

-- ============================================================
-- VOICE CALLS
-- ============================================================

CREATE TABLE voice.voice_calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  initiator_id VARCHAR(255),
  recipient_phone VARCHAR(20),
  recipient_name VARCHAR(255),
  recipient_company VARCHAR(255),
  
  -- Call metadata
  call_type VARCHAR(50),  -- outbound, inbound, ai_agent
  call_purpose VARCHAR(100),  -- initial_outreach, followup, objection_handling
  
  -- Timing
  initiated_at TIMESTAMP DEFAULT NOW(),
  connected_at TIMESTAMP,
  ended_at TIMESTAMP,
  duration_seconds INT,
  
  -- Recording
  recording_url VARCHAR(500),
  transcription_url VARCHAR(500),
  
  -- AI agent flag
  is_ai_agent BOOLEAN DEFAULT FALSE,
  ai_model VARCHAR(50),  -- claude, openai, twilio
  ai_script_template VARCHAR(50),
  
  -- Outcome
  outcome VARCHAR(50),  -- connected, voicemail, no_answer, declined, follow_up_scheduled
  next_steps VARCHAR(200),
  sentiment_analysis VARCHAR(20),  -- positive, neutral, negative
  
  -- Coaching
  rep_coaching_score FLOAT,  -- 0-100 (if human rep)
  coaching_notes TEXT,
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE,
  CONSTRAINT fk_initiator FOREIGN KEY (initiator_id) 
    REFERENCES public.users(id) ON DELETE SET NULL
);

CREATE INDEX idx_voice_calls_deal ON voice.voice_calls(deal_id);
CREATE INDEX idx_voice_calls_initiator ON voice.voice_calls(initiator_id);
CREATE INDEX idx_voice_calls_initiated ON voice.voice_calls(initiated_at DESC);

-- Call transcripts
CREATE TABLE voice.call_transcripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id UUID,
  
  -- Transcript
  full_transcript TEXT,
  transcript_segments JSONB,  -- [{speaker: "AI|REP|PROSPECT", text: "...", timestamp: 123}]
  
  -- Analysis
  key_topics JSONB,  -- ["pain points", "budget", "timeline"]
  objections_raised JSONB,  -- [{objection: "...", response: "..."}]
  buying_signals JSONB,  -- ["budget confirmed", "timeline aligned"]
  
  -- Sentiment
  overall_sentiment VARCHAR(20),  -- positive, neutral, negative
  prospect_engagement_score FLOAT,  -- 0-100
  
  transcribed_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_call FOREIGN KEY (call_id) 
    REFERENCES voice.voice_calls(id) ON DELETE CASCADE
);

CREATE INDEX idx_transcripts_call ON voice.call_transcripts(call_id);

-- ============================================================
-- SALES PLAYBOOKS
-- ============================================================

CREATE TABLE voice.sales_playbooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Metadata
  name VARCHAR(255),
  description TEXT,
  category VARCHAR(50),  -- initial_outreach, followup, objection_handling, expansion
  target_deal_stage VARCHAR(50),  -- prospect, qualified, negotiation
  target_persona VARCHAR(100),  -- economic_buyer, user_buyer, champion
  
  -- Playbook structure
  steps JSONB,  -- [{order: 1, step_type: "discovery", prompt: "...", duration: 180}]
  success_criteria JSONB,  -- [{metric: "next_meeting_scheduled", target: true}]
  
  -- Performance
  avg_conversion_rate FLOAT,
  avg_deal_value_impact FLOAT,
  usage_count INT DEFAULT 0,
  win_rate FLOAT,
  
  -- Versioning
  version VARCHAR(10),
  created_by VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_creator FOREIGN KEY (created_by) 
    REFERENCES public.users(id) ON DELETE SET NULL
);

CREATE INDEX idx_playbooks_category ON voice.sales_playbooks(category);
CREATE INDEX idx_playbooks_stage ON voice.sales_playbooks(target_deal_stage);
CREATE INDEX idx_playbooks_conversion ON voice.sales_playbooks(avg_conversion_rate DESC);

-- Playbook execution
CREATE TABLE voice.playbook_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  playbook_id UUID,
  call_id UUID,
  rep_id VARCHAR(255),
  
  -- Execution details
  script_used TEXT,
  adherence_score FLOAT,  -- 0-100 (how well rep followed playbook)
  
  -- Outcome
  completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMP,
  steps_completed INT,
  total_steps INT,
  
  -- Result
  outcome_achieved BOOLEAN,
  conversion BOOLEAN,
  deal_value_impact FLOAT,
  
  CONSTRAINT fk_playbook FOREIGN KEY (playbook_id) 
    REFERENCES voice.sales_playbooks(id) ON DELETE SET NULL,
  CONSTRAINT fk_call FOREIGN KEY (call_id) 
    REFERENCES voice.voice_calls(id) ON DELETE SET NULL,
  CONSTRAINT fk_rep FOREIGN KEY (rep_id) 
    REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_playbook_executions_playbook ON voice.playbook_executions(playbook_id);
CREATE INDEX idx_playbook_executions_call ON voice.playbook_executions(call_id);

-- ============================================================
-- PERFORMANCE TRACKING
-- ============================================================

CREATE TABLE voice.sales_rep_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rep_id VARCHAR(255) UNIQUE,
  
  -- Call volume
  calls_made INT DEFAULT 0,
  calls_connected INT DEFAULT 0,
  connection_rate FLOAT,  -- 0-100
  
  -- Conversion
  deals_closed INT DEFAULT 0,
  close_rate FLOAT,  -- 0-100
  avg_deal_value FLOAT,
  
  -- Coaching
  top_playbooks JSONB,  -- [{playbook_id, usage_count, conversion_rate}]
  coaching_score FLOAT,  -- 0-100
  improvement_areas JSONB,  -- ["objection handling", "discovery questions"]
  
  -- Time tracking
  avg_call_duration INT,  -- seconds
  productivity_score FLOAT,  -- 0-100
  
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_rep FOREIGN KEY (rep_id) 
    REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_rep_perf_close_rate ON voice.sales_rep_performance(close_rate DESC);

-- ============================================================
-- AI CALL SCRIPTS
-- ============================================================

CREATE TABLE voice.ai_call_scripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Metadata
  name VARCHAR(255),
  purpose VARCHAR(100),  -- initial_outreach, followup, objection_handling
  
  -- Script structure
  opening_statement TEXT,
  discovery_questions JSONB,  -- ["What challenges are you facing?", "What's your timeline?"]
  value_proposition TEXT,
  objection_handlers JSONB,  -- [{objection: "too expensive", response: "..."}]
  closing_statement TEXT,
  
  -- Configuration
  ai_model VARCHAR(50),  -- claude, openai, twilio-virtual-agent
  temperature FLOAT,  -- 0-1 (creativity level)
  
  -- Performance
  avg_call_duration INT,
  success_rate FLOAT,
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_playbook FOREIGN KEY (playbook_id) 
    REFERENCES voice.sales_playbooks(id) ON DELETE SET NULL
);

-- ============================================================
-- Grants
-- ============================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA voice TO sellia_user;
```

---

## 3. VOICE CALL SYSTEM

### VoiceCallManager Service (350 lines)

**File**: `backend/app/services/voice/voice_call_manager.py`

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import twilio.rest
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

@dataclass
class VoiceCall:
    """Voice call record."""
    call_id: str
    deal_id: str
    recipient_phone: str
    duration_seconds: int
    transcript: Optional[str]
    outcome: str  # connected, voicemail, no_answer
    sentiment: Optional[str]  # positive, neutral, negative
    next_steps: Optional[str]

class VoiceCallManager:
    """Manage outbound AI voice calls at scale."""
    
    def __init__(self, twilio_sid: str, twilio_token: str):
        self.twilio_client = twilio.rest.Client(twilio_sid, twilio_token)
        self.db = SessionLocal()
    
    async def initiate_ai_call(
        self,
        deal_id: str,
        prospect_phone: str,
        prospect_name: str,
        script_template: str,  # initial_outreach, followup, objection_handling
        context: Dict[str, Any]  # {company, pain_points, deal_value, etc}
    ) -> VoiceCall:
        """Initiate AI voice call (Twilio + Claude)."""
        
        # 1. Build AI script from template
        script = await self._build_ai_script(
            script_template=script_template,
            prospect_name=prospect_name,
            context=context
        )
        
        # 2. Create Twilio call
        call = self.twilio_client.calls.create(
            to=prospect_phone,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            url=f"https://api.production.com/webhooks/voice/ivr",
            machine_detection="Enable",
            async_amd=True,
            record=True
        )
        
        # 3. Log call in database
        voice_call = VoiceCall(
            id=call.sid,
            deal_id=deal_id,
            initiator_id=None,  # AI agent (no human)
            recipient_phone=prospect_phone,
            recipient_name=prospect_name,
            call_type="ai_agent",
            ai_model="claude",
            ai_script_template=script_template,
            is_ai_agent=True
        )
        
        self.db.add(voice_call)
        self.db.commit()
        
        logger.info(f"Initiated AI call {call.sid} to {prospect_phone}")
        
        return voice_call
    
    async def _build_ai_script(
        self,
        script_template: str,
        prospect_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Build personalized script using Claude."""
        
        prompt = f"""Generate a professional outbound sales call script for:

Prospect: {prospect_name}
Company: {context.get('company', 'Unknown')}
Pain Points: {context.get('pain_points', 'TBD')}
Budget: ${context.get('deal_value', 0):,.0f}
Timeline: {context.get('timeline', 'Unknown')}

Script template: {script_template}

Generate a natural, conversational script with:
1. Warm opening (reference or connection)
2. Discovery questions (2-3 probing questions)
3. Value proposition (customized)
4. Objection handler (1-2 common objections)
5. Call-to-action (next meeting or followup)

Make it sound human, not robotic. Keep to 3-5 minutes of speaking time."""
        
        response = anthropic.Anthropic().messages.create(
            model="claude-opus",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def process_call_transcript(
        self,
        call_id: str,
        transcript_text: str
    ) -> Dict[str, Any]:
        """Process transcript, extract insights."""
        
        # 1. Get call record
        call = self.db.query(VoiceCall).filter_by(id=call_id).first()
        
        # 2. Send to speech-to-text if needed
        # (Twilio already transcribed)
        
        # 3. Analyze with Claude
        prompt = f"""Analyze this sales call transcript:

{transcript_text}

Extract:
1. Key topics discussed (list)
2. Objections raised (list with responses)
3. Buying signals (explicit commitments, budget confirmation, timeline)
4. Overall sentiment (positive/neutral/negative)
5. Next steps agreed
6. Prospect engagement score (0-100)

Return as JSON."""
        
        response = anthropic.Anthropic().messages.create(
            model="claude-opus",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = json.loads(response.content[0].text)
        
        # 4. Store analysis
        transcript = CallTranscript(
            call_id=call_id,
            full_transcript=transcript_text,
            key_topics=analysis["key_topics"],
            objections_raised=analysis["objections"],
            buying_signals=analysis["buying_signals"],
            overall_sentiment=analysis["sentiment"],
            prospect_engagement_score=analysis["engagement_score"]
        )
        
        self.db.add(transcript)
        call.outcome = "connected"
        call.sentiment_analysis = analysis["sentiment"]
        call.next_steps = analysis["next_steps"]
        self.db.commit()
        
        return analysis
    
    async def get_call_insights(self, call_id: str) -> Dict[str, Any]:
        """Get comprehensive call insights."""
        
        call = self.db.query(VoiceCall).filter_by(id=call_id).first()
        transcript = self.db.query(CallTranscript).filter_by(call_id=call_id).first()
        
        return {
            "call_id": call_id,
            "deal_id": call.deal_id,
            "duration": call.duration_seconds,
            "outcome": call.outcome,
            "sentiment": call.sentiment_analysis,
            "transcript": transcript.full_transcript if transcript else None,
            "key_topics": transcript.key_topics if transcript else [],
            "buying_signals": transcript.buying_signals if transcript else [],
            "next_steps": call.next_steps
        }
```

---

## 4. SALES PLAYBOOK SYSTEM

### PlaybookExtractor Service (300 lines)

**File**: `backend/app/services/voice/playbook_extractor.py`

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from sqlalchemy import func, select
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

@dataclass
class SalesPlaybook:
    """Extracted sales playbook from top performers."""
    name: str
    category: str
    steps: List[Dict[str, Any]]
    success_criteria: List[Dict[str, Any]]
    avg_conversion_rate: float
    win_rate: float

class PlaybookExtractor:
    """Extract playbooks from top-performer behavior."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def extract_playbooks_from_top_performers(self) -> List[SalesPlaybook]:
        """Identify top 20% reps, extract their playbooks."""
        
        # 1. Identify top performers
        top_reps = await self._get_top_performers(percentile=80)
        
        # 2. Extract their call patterns
        playbooks = []
        
        for rep in top_reps:
            # Get all their calls
            calls = self.db.query(VoiceCall).filter_by(
                initiator_id=rep.id
            ).order_by(VoiceCall.initiated_at).all()
            
            # Cluster by call type (initial_outreach, followup, objection_handling)
            by_type = {}
            for call in calls:
                if call.call_type not in by_type:
                    by_type[call.call_type] = []
                by_type[call.call_type].append(call)
            
            # Extract playbook per type
            for call_type, type_calls in by_type.items():
                playbook = await self._extract_playbook_from_calls(
                    calls=type_calls,
                    rep_id=rep.id,
                    call_type=call_type
                )
                playbooks.append(playbook)
        
        return playbooks
    
    async def _get_top_performers(self, percentile: int = 80) -> List:
        """Get top X% of reps by close rate."""
        
        query = select(SalesRepPerformance).order_by(
            SalesRepPerformance.close_rate.desc()
        ).limit(int(self.db.query(func.count(SalesRepPerformance.id)).scalar() * (100 - percentile) / 100))
        
        return self.db.execute(query).scalars().all()
    
    async def _extract_playbook_from_calls(
        self,
        calls: List,
        rep_id: str,
        call_type: str
    ) -> SalesPlaybook:
        """Extract patterns from individual calls."""
        
        # Analyze successful calls (where conversion = True)
        successful = [c for c in calls if c.outcome == "connected"]
        
        # Extract common patterns
        common_topics = await self._find_common_topics(successful)
        common_objections = await self._find_common_objections(successful)
        common_next_steps = await self._find_common_next_steps(successful)
        
        # Calculate metrics
        conversion_rate = len([c for c in calls if c.outcome == "connected"]) / len(calls) if calls else 0
        win_rate = len([c for c in calls if c.call_type == "ai_agent"]) / len(calls) if calls else 0
        
        # Build playbook steps
        steps = [
            {
                "order": 1,
                "step_type": "discovery",
                "prompt": f"Ask about: {', '.join(common_topics[:3])}",
                "duration": 180
            },
            {
                "order": 2,
                "step_type": "objection_handling",
                "prompt": f"Handle: {', '.join(common_objections[:2])}",
                "duration": 60
            },
            {
                "order": 3,
                "step_type": "closing",
                "prompt": f"Propose: {common_next_steps[0] if common_next_steps else 'Next meeting'}",
                "duration": 60
            }
        ]
        
        return SalesPlaybook(
            name=f"{rep_id} - {call_type} Playbook",
            category=call_type,
            steps=steps,
            success_criteria=[
                {"metric": "prospect_engagement", "target": 75},
                {"metric": "next_step_scheduled", "target": True}
            ],
            avg_conversion_rate=conversion_rate,
            win_rate=win_rate
        )
    
    async def _find_common_topics(self, calls: List) -> List[str]:
        """Find most common topics in successful calls."""
        
        topics = []
        for call in calls[:10]:
            transcript = self.db.query(CallTranscript).filter_by(
                call_id=call.id
            ).first()
            
            if transcript:
                topics.extend(transcript.key_topics or [])
        
        # Return top 5 most common
        from collections import Counter
        return [t for t, _ in Counter(topics).most_common(5)]
    
    async def _find_common_objections(self, calls: List) -> List[str]:
        """Find most common objections + how they were handled."""
        
        objections = []
        for call in calls[:10]:
            transcript = self.db.query(CallTranscript).filter_by(
                call_id=call.id
            ).first()
            
            if transcript:
                objections.extend(transcript.objections_raised or [])
        
        return [o for o, _ in Counter(objections).most_common(5)]
    
    async def _find_common_next_steps(self, calls: List) -> List[str]:
        """Find most common next steps proposed."""
        
        next_steps = []
        for call in calls[:10]:
            if call.next_steps:
                next_steps.append(call.next_steps)
        
        return next_steps[:5]
```

### PlaybookRecommender Service (200 lines)

```python
class PlaybookRecommender:
    """Recommend playbooks based on deal context."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_recommended_playbooks(
        self,
        deal_id: str,
        rep_id: str
    ) -> List[Dict[str, Any]]:
        """Get personalized playbook recommendations."""
        
        # Get deal details
        deal = self.db.query(Deal).filter_by(id=deal_id).first()
        
        # Get rep performance
        rep_perf = self.db.query(SalesRepPerformance).filter_by(
            rep_id=rep_id
        ).first()
        
        # Get playbooks for this deal stage + persona
        query = select(SalesPlaybook).where(
            (SalesPlaybook.target_deal_stage == deal.stage) |
            (SalesPlaybook.category == "followup")
        ).order_by(SalesPlaybook.avg_conversion_rate.desc()).limit(5)
        
        playbooks = self.db.execute(query).scalars().all()
        
        # Score playbooks by rep's past performance
        recommendations = []
        for pb in playbooks:
            # If rep used this playbook before, boost score
            rep_uses = self.db.query(PlaybookExecution).filter_by(
                playbook_id=pb.id,
                rep_id=rep_id
            ).count()
            
            score = pb.avg_conversion_rate * 100
            if rep_uses > 0:
                score *= 1.2  # Boost familiar playbooks
            
            recommendations.append({
                "playbook_id": pb.id,
                "name": pb.name,
                "category": pb.category,
                "conversion_rate": pb.avg_conversion_rate,
                "match_score": score,
                "reason": f"Based on {deal.stage} stage + rep's {rep_uses} prior uses"
            })
        
        return recommendations
```

---

## 5. API ENDPOINTS

```python
@router.post("/voice/initiate-call")
async def initiate_ai_call(
    deal_id: str,
    prospect_phone: str,
    prospect_name: str,
    script_template: str = "initial_outreach",
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Initiate AI voice call."""
    
    manager = VoiceCallManager(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_TOKEN")
    )
    
    call = await manager.initiate_ai_call(
        deal_id=deal_id,
        prospect_phone=prospect_phone,
        prospect_name=prospect_name,
        script_template=script_template
    )
    
    return {"call_id": call.id, "status": "calling"}

@router.get("/voice/call/{call_id}")
async def get_call_insights(
    call_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get call transcript + insights."""
    
    manager = VoiceCallManager(None, None)
    manager.db = db
    
    insights = await manager.get_call_insights(call_id)
    return insights

@router.get("/playbooks/list")
async def list_playbooks(
    category: str = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """List all sales playbooks."""
    
    query = select(SalesPlaybook)
    if category:
        query = query.where(SalesPlaybook.category == category)
    
    playbooks = db.execute(query).scalars().all()
    
    return {
        "playbooks": [
            {
                "id": pb.id,
                "name": pb.name,
                "category": pb.category,
                "conversion_rate": pb.avg_conversion_rate,
                "usage_count": pb.usage_count
            }
            for pb in playbooks
        ]
    }

@router.get("/playbooks/recommend/{deal_id}")
async def get_playbook_recommendations(
    deal_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get recommended playbooks for deal + rep."""
    
    recommender = PlaybookRecommender(db)
    recommendations = await recommender.get_recommended_playbooks(
        deal_id=deal_id,
        rep_id=current_user["id"]
    )
    
    return {"recommendations": recommendations}
```

---

## 6. FRONTEND COMPONENTS

### VoiceCallBuilder.tsx

```typescript
export const VoiceCallBuilder: React.FC = () => {
  const [dealId, setDealId] = useState('');
  const [prospectPhone, setProspectPhone] = useState('');
  const [prospectName, setProspectName] = useState('');
  const [scriptTemplate, setScriptTemplate] = useState('initial_outreach');
  const [calling, setCalling] = useState(false);

  const handleInitiateCall = async () => {
    setCalling(true);
    const response = await fetch('/api/v1/voice/initiate-call', {
      method: 'POST',
      body: JSON.stringify({
        deal_id: dealId,
        prospect_phone: prospectPhone,
        prospect_name: prospectName,
        script_template: scriptTemplate
      })
    });
    
    const result = await response.json();
    // Poll for call completion
    pollCallStatus(result.call_id);
  };

  return (
    <Card>
      <h2>AI Voice Call Initiator</h2>
      <TextInput placeholder="Deal ID" value={dealId} onChange={...} />
      <TextInput placeholder="Phone" value={prospectPhone} onChange={...} />
      <TextInput placeholder="Name" value={prospectName} onChange={...} />
      <Select value={scriptTemplate} onChange={...}>
        <option value="initial_outreach">Initial Outreach</option>
        <option value="followup">Follow-up</option>
        <option value="objection_handling">Objection Handling</option>
      </Select>
      <Button onClick={handleInitiateCall} disabled={calling}>
        {calling ? 'Calling...' : 'Initiate Call'}
      </Button>
    </Card>
  );
};
```

### PlaybookLibrary.tsx

```typescript
export const PlaybookLibrary: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<any[]>([]);
  const [category, setCategory] = useState('initial_outreach');

  useEffect(() => {
    fetch(`/api/v1/playbooks/list?category=${category}`)
      .then(r => r.json())
      .then(data => setPlaybooks(data.playbooks));
  }, [category]);

  return (
    <div>
      <h2>Sales Playbooks</h2>
      <Select value={category} onChange={(e) => setCategory(e.target.value)}>
        <option value="initial_outreach">Initial Outreach</option>
        <option value="followup">Follow-up</option>
        <option value="objection_handling">Objection Handling</option>
      </Select>
      
      <div className="playbooks-list">
        {playbooks.map(pb => (
          <Card key={pb.id}>
            <h3>{pb.name}</h3>
            <Badge>{(pb.conversion_rate * 100).toFixed(1)}% conversion</Badge>
            <p>Used {pb.usage_count} times</p>
            <Button>Use Playbook</Button>
          </Card>
        ))}
      </div>
    </div>
  );
};
```

---

## 7. IMPLEMENTATION TIMELINE

**Week 15-16**: Voice Infrastructure
- [ ] Twilio integration setup
- [ ] VoiceCallManager service
- [ ] AI script generation (Claude)
- [ ] Call transcript processing

**Week 17-18**: Playbook Extraction
- [ ] PlaybookExtractor service
- [ ] Top performer identification
- [ ] Pattern extraction (topics, objections)
- [ ] Playbook database population

**Week 19-20**: Recommendations + Coaching
- [ ] PlaybookRecommender service
- [ ] Real-time play recommendations
- [ ] Rep coaching module
- [ ] Performance tracking

**Week 21-24**: Frontend + Integration
- [ ] VoiceCallBuilder component
- [ ] PlaybookLibrary component
- [ ] Call analytics dashboard
- [ ] E2E testing + UAT

---

## 8. SUCCESS CRITERIA

**Technical**:
- [ ] 1000+ calls processed per day
- [ ] Call transcript accuracy 95%+
- [ ] Playbook recommendations < 500ms
- [ ] 99.9% uptime (Twilio)

**Product**:
- [ ] 5-10x outbound volume increase
- [ ] +40% rep productivity
- [ ] Playbooks used in 50%+ of calls
- [ ] Top playbooks 20%+ conversion

---

**Phase 29 Architecture Ready** ✅

