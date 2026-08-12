# Phase 29 - Voice + Sales Playbooks
## Architecture & Implementation Plan

**Duration**: 8 weeks (Dec 1 - Dec 20, 2026)  
**Team**: 1 backend + 1 frontend  
**Expected Impact**: 5-10x outbound volume, +40% rep productivity  
**Launch Date**: Dec 21, 2026

---

## OVERVIEW

Phase 29 builds on Phase 27 intelligence to enable AI-powered voice outreach + automated playbook coaching:

```
Phase 27-28 Output (deal intelligence + email optimization)
         ↓
Phase 29 System
├─ VoiceCallManager (Twilio: AI makes outbound calls at scale)
├─ PlaybookExtractor (ML: extract top performer patterns)
└─ PlaybookRecommender (Real-time: suggest plays per deal)
         ↓
Outputs
├─ AI voice agent (500+ dials/week per rep)
├─ Sales playbooks (extracted from top 20% reps)
└─ Real-time coaching (suggested plays during calls)
```

---

## 1. VOICE CALL MANAGER

### Problem
- Manual outbound calls: 20 dials/week per rep (limited by time)
- Solution: AI agent dials prospects, qualifies them, books meetings

### Features
- **Input**: Prospect list (from deal intelligence)
- **Output**: Call transcripts, sentiment analysis, meeting booked (yes/no)
- **Scale**: 500+ dials/week per rep (5-10x volume)

### Workflow

```
1. Rep selects deal + stakeholder to call
2. System generates voice script (from Phase 28)
3. Twilio initiates call
4. Claude API handles conversation in real-time:
   - Greets prospect
   - Qualifies opportunity
   - Handles objections
   - Books meeting if qualified
5. Transcript captured + analyzed
6. Rep notified: "Meeting booked with John Smith, Jan 15 at 2 PM"
7. CRM updated with call details
```

### Claude Voice Integration

```python
class VoiceCallManager:
    def __init__(self, db, twilio_client, claude_client):
        self.db = db
        self.twilio = twilio_client
        self.claude = claude_client
    
    def initiate_call(self, prospect_id: str, deal_id: str) -> VoiceCallResult:
        """Initiate AI voice call with prospect."""
        
        # 1. Generate voice script from Phase 28
        script = self._generate_voice_script(prospect_id, deal_id)
        
        # 2. Create Twilio call
        call = self.twilio.calls.create(
            to=prospect.phone,
            from_=TWILIO_PHONE,
            url=f"{API_BASE}/voice/handle-call",
            record=True,  # Record call for training
        )
        
        # 3. Start voice conversation
        conversation = self._start_conversation(call.sid, script)
        
        # 4. Store call record
        voice_call = VoiceCall(
            prospect_id=prospect_id,
            deal_id=deal_id,
            call_sid=call.sid,
            script_used=script,
            started_at=datetime.utcnow(),
        )
        self.db.add(voice_call)
        self.db.commit()
        
        return VoiceCallResult(call_id=call.sid, status="initiated")
    
    def handle_call_webhook(self, call_sid: str, input_text: str) -> str:
        """Handle incoming voice input from Twilio."""
        
        # 1. Get call context
        call = self.db.query(VoiceCall).filter(VoiceCall.call_sid == call_sid).first()
        
        # 2. Build Claude prompt with conversation history
        prompt = f"""
        You are professional sales AI calling {call.prospect.name} at {call.prospect.company}.
        
        Goal: Qualify opportunity and book meeting
        
        Context:
        - Deal value: ${call.deal.amount:,}
        - Prospect role: {call.prospect.title}
        - Previous conversations: {get_conversation_history(call.id)}
        
        Prospect just said: "{input_text}"
        
        Respond naturally:
        1. If objection, handle it with benefit statement
        2. If qualified, suggest meeting time
        3. If unqualified, politely end call
        4. Keep responses under 30 seconds
        
        Next response:
        """
        
        # 3. Call Claude for response
        response = self.claude.messages.create(
            model="claude-opus",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        ai_response = response.content[0].text
        
        # 4. Store conversation turn
        turn = ConversationTurn(
            call_id=call.id,
            speaker="prospect",
            text=input_text,
            timestamp=datetime.utcnow(),
        )
        self.db.add(turn)
        
        turn = ConversationTurn(
            call_id=call.id,
            speaker="ai",
            text=ai_response,
            timestamp=datetime.utcnow(),
        )
        self.db.add(turn)
        self.db.commit()
        
        # 5. Convert response to speech (TTS)
        audio_url = self._text_to_speech(ai_response)
        
        return audio_url
    
    def end_call(self, call_sid: str):
        """End call, analyze, update CRM."""
        
        call = self.db.query(VoiceCall).filter(VoiceCall.call_sid == call_sid).first()
        
        # 1. Get full transcript
        transcript = self._get_transcript(call_sid)
        
        # 2. Analyze outcome (sentiment, objections, decision)
        outcome = self._analyze_call(transcript)
        
        # 3. Update call record
        call.ended_at = datetime.utcnow()
        call.transcript = transcript
        call.outcome = outcome["decision"]  # "meeting_booked", "qualified", "unqualified"
        call.sentiment = outcome["sentiment"]
        call.objections_handled = outcome["objections"]
        
        if outcome["decision"] == "meeting_booked":
            # Create meeting in CRM
            meeting = Meeting(
                prospect_id=call.prospect_id,
                deal_id=call.deal_id,
                scheduled_for=outcome["meeting_time"],
                ai_booked=True,
            )
            self.db.add(meeting)
        
        self.db.commit()
        
        # 4. Notify rep
        send_notification(call.deal.owner_id, f"Call completed with {call.prospect.name}")
```

### Database Schema

```sql
CREATE TABLE voice_calls (
  id UUID PRIMARY KEY,
  prospect_id VARCHAR(255) NOT NULL,
  deal_id VARCHAR(255) NOT NULL,
  
  call_sid VARCHAR(255) UNIQUE,  -- Twilio call ID
  script_used TEXT,
  
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  duration_seconds INT,
  
  outcome VARCHAR(50),  -- meeting_booked, qualified, unqualified
  sentiment VARCHAR(50),  -- positive, neutral, negative
  
  FOREIGN KEY (prospect_id),
  FOREIGN KEY (deal_id),
  INDEX idx_prospect (prospect_id),
  INDEX idx_deal (deal_id)
);

CREATE TABLE call_transcripts (
  id UUID PRIMARY KEY,
  call_id UUID NOT NULL,
  
  speaker VARCHAR(50),  -- prospect, ai
  text TEXT,
  timestamp TIMESTAMP,
  
  FOREIGN KEY (call_id) REFERENCES voice_calls(id)
);

CREATE TABLE voice_call_metrics (
  id UUID PRIMARY KEY,
  call_id UUID NOT NULL,
  
  objections_raised INT,
  objections_handled INT,
  questions_asked INT,
  time_to_qualification SECONDS INT,
  
  FOREIGN KEY (call_id) REFERENCES voice_calls(id)
);
```

---

## 2. PLAYBOOK EXTRACTOR

### Problem
- Top 20% of reps close 40% of deals
- But their tactics aren't documented/shared
- Solution: ML extracts playbooks from top performer patterns

### Implementation

```python
class PlaybookExtractor:
    """Extract sales playbooks from top performer call transcripts."""
    
    def extract_playbooks(self, top_performer_ids: List[str]) -> List[SalesPlaybook]:
        """Extract playbooks from top 20% performers."""
        
        # 1. Get all calls from top performers
        calls = self.db.query(VoiceCall).filter(
            VoiceCall.rep_id.in_(top_performer_ids)
        ).all()
        
        # 2. Extract patterns
        playbooks = []
        for call in calls:
            if call.outcome == "meeting_booked":
                playbook = self._extract_from_call(call)
                playbooks.append(playbook)
        
        # 3. Cluster similar playbooks
        clusters = self._cluster_playbooks(playbooks)
        
        # 4. Create consolidated playbooks
        final_playbooks = []
        for cluster in clusters:
            consolidated = self._consolidate_cluster(cluster)
            final_playbooks.append(consolidated)
        
        return final_playbooks
    
    def _extract_from_call(self, call: VoiceCall) -> Dict[str, Any]:
        """Extract playbook elements from single call."""
        
        transcript = call.get_transcript()
        
        # Use Claude to identify playbook elements
        prompt = f"""
        Analyze this sales call and extract playbook elements:
        
        Transcript: {transcript}
        
        Identify:
        1. Opening statement (how rep introduces themselves)
        2. Discovery questions (questions asked to qualify)
        3. Value proposition (how benefits are presented)
        4. Objection handlers (responses to common objections)
        5. Closing statement (how meeting is booked)
        
        Format as JSON.
        """
        
        response = self.claude.messages.create(
            model="claude-opus",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
    
    def _cluster_playbooks(self, playbooks: List[Dict]) -> List[List[Dict]]:
        """Cluster similar playbooks together."""
        
        # Use similarity scoring to group related playbooks
        # Simplified: group by industry/deal stage
        
        clusters = {}
        for pb in playbooks:
            key = f"{pb['industry']}-{pb['deal_stage']}"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(pb)
        
        return list(clusters.values())
    
    def _consolidate_cluster(self, cluster: List[Dict]) -> SalesPlaybook:
        """Create single playbook from cluster."""
        
        playbook = SalesPlaybook(
            name=f"Playbook: {cluster[0]['industry']} - {cluster[0]['deal_stage']}",
            industry=cluster[0]['industry'],
            deal_stage=cluster[0]['deal_stage'],
            win_rate=self._calculate_win_rate(cluster),
            steps=[
                {
                    "step": 1,
                    "name": "Opening",
                    "script": self._consolidate_step(cluster, "opening"),
                },
                {
                    "step": 2,
                    "name": "Discovery",
                    "script": self._consolidate_step(cluster, "discovery"),
                },
                # ... more steps
            ],
        )
        
        return playbook
```

### Database Schema

```sql
CREATE TABLE sales_playbooks (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  industry VARCHAR(255),
  deal_stage VARCHAR(50),
  
  win_rate FLOAT,  -- % of calls that book meeting
  usage_count INT DEFAULT 0,
  
  steps JSONB,  -- [{step: 1, name: "Opening", script: "..."}]
  extracted_from_calls INT,  -- How many calls analyzed
  
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  
  INDEX idx_industry_stage (industry, deal_stage)
);

CREATE TABLE playbook_executions (
  id UUID PRIMARY KEY,
  playbook_id UUID NOT NULL,
  call_id UUID NOT NULL,
  
  step_number INT,
  rep_deviation FLOAT,  -- How much rep deviated from script
  
  FOREIGN KEY (playbook_id),
  FOREIGN KEY (call_id)
);
```

---

## 3. PLAYBOOK RECOMMENDER

### Real-Time Coaching

```python
class PlaybookRecommender:
    """Recommend playbooks in real-time during calls."""
    
    def recommend_playbook(self, deal_id: str, context: Dict) -> Optional[SalesPlaybook]:
        """Recommend playbook for current deal."""
        
        deal = self.db.query(Deal).get(deal_id)
        
        # 1. Find matching playbooks
        candidates = self.db.query(SalesPlaybook).filter(
            (SalesPlaybook.industry == deal.company.industry) |
            (SalesPlaybook.deal_stage == deal.stage)
        ).all()
        
        if not candidates:
            return None
        
        # 2. Score by win rate + relevance
        scores = [
            (pb, pb.win_rate * 0.7 + self._relevance_score(pb, deal) * 0.3)
            for pb in candidates
        ]
        
        best = max(scores, key=lambda x: x[1])
        return best[0]
    
    def get_next_step(self, playbook_id: str, call_id: str, current_step: int) -> Optional[str]:
        """Get next playbook step based on call progress."""
        
        playbook = self.db.query(SalesPlaybook).get(playbook_id)
        
        if current_step >= len(playbook.steps):
            return None
        
        next_step = playbook.steps[current_step]
        return next_step["script"]
```

### UI Integration

Rep sees real-time suggestions:
```
┌─ Current Call: John Smith (Acme Corp) ─┐
│ Playbook: "Enterprise Sales - Discovery" │
│ Current Step: Discovery Questions       │
│                                          │
│ Suggested Next: "Ask about budget"     │
│ Win Rate: 78%                           │
└──────────────────────────────────────────┘
```

---

## 4. DATABASE TABLES (8 total)

```
voice_calls           - Call records
call_transcripts      - Conversation turn-by-turn
voice_call_metrics    - Call analytics
sales_playbooks       - Extracted playbooks
playbook_executions   - Playbook usage tracking
sales_rep_performance - Rep statistics
ai_call_scripts       - Generated voice scripts
meeting_bookings      - AI-booked meetings
```

---

## 5. API ENDPOINTS (5 total)

```
POST /api/v1/voice/initiate-call
     Body: { prospect_id, deal_id }
     → Start AI voice call

GET  /api/v1/voice/call/{call_id}
     → Get call transcript + outcome

GET  /api/v1/playbooks
     → List available playbooks

POST /api/v1/playbooks/recommend
     Body: { deal_id }
     → Get recommended playbook for deal

GET  /api/v1/voice/metrics
     → Call volume, conversion, sentiment
```

---

## 6. FRONTEND COMPONENTS (2 total)

### Component 1: VoiceCallBuilder

```typescript
export default function VoiceCallBuilder({ dealId }) {
  // 1. Select stakeholder to call
  // 2. Choose voiceScript template
  // 3. Start call button
  // 4. Live transcript view
  // 5. Real-time playbook recommendation
  // 6. Call outcome tracking
}
```

### Component 2: PlaybookLibrary

```typescript
export default function PlaybookLibrary() {
  // 1. List all playbooks (by industry/stage)
  // 2. Playbook details (steps, win rate, usage)
  // 3. Search/filter
  // 4. "Use This Playbook" for active calls
  // 5. Performance metrics (win rate, call metrics)
}
```

---

## SUCCESS CRITERIA

**Volume**:
- ✅ 5-10x outbound calls (20 → 100-200 dials/week)
- ✅ 500+ calls/week per AI agent
- ✅ 99%+ call completion (no drops)

**Quality**:
- ✅ Meeting booking rate: 40%+ (from AI calls)
- ✅ Call duration: 4-6 minutes (natural length)
- ✅ Sentiment accuracy: 90%+ (detecting prospect tone)
- ✅ Transcript accuracy: 95%+ (real-time transcription)

**Playbooks**:
- ✅ 10+ playbooks extracted
- ✅ Win rate improvement: +15-20%
- ✅ Rep usage: 70%+ of active reps
- ✅ Rep satisfaction: 8+/10

**Rep Productivity**:
- ✅ Time freed up: 20+ hours/week (no manual dialing)
- ✅ Coaching effectiveness: +40% faster ramp (new reps)
- ✅ Adoption: 80%+ of team using by week 2

---

## TIMELINE

**Week 1-2**: VoiceCallManager (Twilio integration)
**Week 3-4**: PlaybookExtractor (ML pattern extraction)
**Week 5-6**: PlaybookRecommender (real-time coaching)
**Week 7-8**: Frontend components + integration testing

**Launch**: Dec 21, 2026

---

## DEPENDENCIES

- Twilio API (voice calling)
- Claude API (conversation handling)
- Speech-to-text (transcription)
- Text-to-speech (voice response)
- Redis (call state management)

---

**Phase 29 Ready to Build**
