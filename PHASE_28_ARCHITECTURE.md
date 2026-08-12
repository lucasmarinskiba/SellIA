# Phase 28 - Email + Proposal Automation
## Architecture & Implementation Plan

**Duration**: 8 weeks (Nov 1 - Dec 20, 2026)  
**Team**: 1 backend + 1 frontend  
**Expected Impact**: +45% email open rate, 30 min → 2 min proposal generation (-93% time)  
**Launch Date**: Nov 1, 2026

---

## OVERVIEW

Phase 28 builds on Phase 27 intelligence to automate email timing and proposal generation:

```
Phase 27 Output (stakeholders + probability)
         ↓
Phase 28 System
├─ SendTimeOptimizer (ML model: when to send email for max opens)
├─ ProposalGenerator (Claude API: 2-min AI-written proposals)
└─ CompetitorDetector (NLP: auto-identify competitors, trigger counter-campaigns)
         ↓
Outputs
├─ Recommendations (optimal send times per stakeholder)
├─ AI-generated proposals (ready-to-send in 2 min vs 30 min)
└─ Competitor responses (pre-written counter-messaging)
```

---

## 1. SEND-TIME OPTIMIZER

### Problem
- Reps send emails when they're free (not when buyer is checking email)
- Open rates: ~25% baseline
- Solution: ML model predicts optimal send time per stakeholder

### Features
- **Input**: Person profile (role, company, timezone, history)
- **Output**: Recommended send time (next 72 hours)
- **Optimization**: Maximizes email open probability

### ML Model: Logistic Regression + XGBoost

```python
# Features (10):
- recipient_timezone
- recipient_role (CEO, manager, IC)
- day_of_week (Mon-Fri)
- hour_of_day (0-23)
- email_subject_length
- email_body_sentiment (positive/negative)
- day_since_last_email
- previous_open_rate (for recipient)
- company_size
- industry_vertical

# Target: P(open = 1) at time T

# Model performance:
- AUC: 0.78+ on validation
- Precision @ recall 75%: >70%
- Lift vs random: 3.2x
```

### Database Schema

```sql
CREATE TABLE send_time_predictions (
  id UUID PRIMARY KEY,
  person_id VARCHAR(255) NOT NULL,
  email_id VARCHAR(255) NOT NULL,
  
  -- Predicted optimal time
  recommended_send_time TIMESTAMP,
  predicted_open_probability FLOAT,  -- 0-100
  
  -- Alternatives (next 2 best times)
  alternative_time_1 TIMESTAMP,
  alternative_time_2 TIMESTAMP,
  
  -- Model version
  model_version VARCHAR(50),
  prediction_date TIMESTAMP,
  
  -- If sent, track actual open
  actual_send_time TIMESTAMP,
  actually_opened BOOLEAN,
  
  INDEX idx_person_email (person_id, email_id),
  FOREIGN KEY (person_id) REFERENCES persons(id)
);

CREATE TABLE email_open_tracking (
  id UUID PRIMARY KEY,
  email_id VARCHAR(255),
  person_id VARCHAR(255),
  
  sent_at TIMESTAMP,
  opened_at TIMESTAMP,
  open_delay_minutes INT,
  
  device_type VARCHAR(50),  -- mobile, desktop
  email_client VARCHAR(50),  -- Gmail, Outlook, etc
  
  INDEX idx_person_sent (person_id, sent_at DESC)
);
```

### Service: SendTimeOptimizer

```python
class SendTimeOptimizer:
    def __init__(self, db, ml_model):
        self.db = db
        self.model = ml_model  # Trained model
    
    def predict_send_times(self, person_id: str, email_draft: str) -> SendTimeRecommendation:
        """Predict optimal send times for next 72 hours."""
        
        # 1. Extract features
        person = get_person(person_id)
        email_features = extract_email_features(email_draft)
        
        # 2. Generate candidate times (72 hours ahead, hourly)
        candidates = generate_candidate_times(person.timezone, hours=72)
        
        # 3. Score each time
        scores = self.model.predict_proba(
            [person_features + email_features + time_features for time in candidates]
        )
        
        # 4. Return top 3
        top_3_indices = np.argsort(scores)[-3:][::-1]
        return SendTimeRecommendation(
            recommended_time=candidates[top_3_indices[0]],
            confidence=scores[top_3_indices[0]],
            alternatives=[
                candidates[top_3_indices[1]],
                candidates[top_3_indices[2]],
            ]
        )
    
    def track_open(self, email_id: str, person_id: str, opened_at: datetime):
        """Track email open, update model feedback."""
        email = get_email(email_id)
        delay_minutes = (opened_at - email.sent_at).total_seconds() / 60
        
        # Store open event
        open_event = EmailOpenTracking(
            email_id=email_id,
            person_id=person_id,
            sent_at=email.sent_at,
            opened_at=opened_at,
            open_delay_minutes=delay_minutes,
        )
        db.add(open_event)
        
        # Update prediction accuracy
        # (for model retraining feedback loop)
        db.commit()
```

### API Endpoints

```
POST /api/v1/email/predict-send-times
Body: { person_id, email_draft }
Response: { recommended_time, confidence, alternatives }

POST /api/v1/email/track-open
Body: { email_id, person_id, opened_at }
Response: { success, feedback_stored }

GET /api/v1/email/model-performance
Response: { auc: 0.78, precision: 0.71, lift: 3.2 }
```

---

## 2. PROPOSAL GENERATOR

### Problem
- Reps spend 30 min per proposal (research, formatting, customization)
- Only 30% send proposals on first outreach
- Solution: Claude API generates professional proposals in 2 min

### Workflow

```
1. Rep clicks "Generate Proposal"
2. System gathers context:
   - Deal data (value, stage, timeline)
   - Stakeholders (names, roles, engagement)
   - Company info (industry, size, use cases)
   - Probability/health score (from Phase 27)
3. Prompt sent to Claude Opus:
   - "Draft proposal for [company] [stakeholders]"
   - Tone: professional, customized to buyer
   - Length: 2-3 pages (1500 words)
4. Claude returns proposal in <30 sec
5. Rep reviews, edits, sends
6. Proposal tracked for views + engagement
```

### Claude API Integration

```python
class ProposalGenerator:
    def __init__(self, claude_client, db):
        self.claude = claude_client  # Anthropic SDK
        self.db = db
    
    def generate_proposal(self, deal_id: str, options: ProposalOptions = None) -> ProposalDraft:
        """Generate AI proposal for deal."""
        
        # 1. Gather context
        deal = self.db.query(Deal).get(deal_id)
        stakeholders = self.db.query(DealStakeholder).filter(...).all()
        probability = self.db.query(DealProbabilityScore).filter(...).first()
        
        # 2. Build prompt
        prompt = f"""
        Generate professional sales proposal for:
        
        Company: {deal.company_name}
        Deal Value: ${deal.value:,}
        Stage: {deal.stage}
        Timeline: {deal.timeline}
        
        Stakeholders:
        {format_stakeholders(stakeholders)}
        
        Deal Health: {probability.close_probability}% close probability
        
        Requirements:
        - Formal, professional tone
        - Address economic buyer directly
        - Show ROI calculation
        - Include implementation timeline
        - Add case study (similar company)
        - Format: HTML ready to send
        - Length: 2-3 pages
        
        Generate proposal:
        """
        
        # 3. Call Claude
        response = self.claude.messages.create(
            model="claude-opus",
            max_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        proposal_html = response.content[0].text
        
        # 4. Save draft
        draft = ProposalDraft(
            deal_id=deal_id,
            html_content=proposal_html,
            generation_method="claude_opus",
            generated_by_user_id=current_user_id,
            generated_at=datetime.utcnow(),
        )
        self.db.add(draft)
        self.db.commit()
        
        return draft
    
    def send_proposal(self, draft_id: str, email_to: str):
        """Send proposal via email."""
        draft = self.db.query(ProposalDraft).get(draft_id)
        
        # Use SendTimeOptimizer to find best time
        optimizer = SendTimeOptimizer(self.db, self.model)
        send_time = optimizer.predict_send_times(email_to, draft.html_content)
        
        # Queue email
        send_email_with_proposal.delay(
            email_to=email_to,
            proposal_html=draft.html_content,
            send_at=send_time.recommended_time,
        )
        
        # Track
        draft.sent_to = email_to
        draft.sent_at = datetime.utcnow()
        self.db.add(draft)
        self.db.commit()
```

### Database Schema

```sql
CREATE TABLE proposal_drafts (
  id UUID PRIMARY KEY,
  deal_id VARCHAR(255) NOT NULL,
  
  html_content TEXT,  -- Generated HTML
  word_count INT,
  
  -- Generation
  generation_method VARCHAR(50),  -- claude_opus, template, etc
  generated_by_user_id VARCHAR(255),
  generated_at TIMESTAMP,
  
  -- Usage
  sent_to VARCHAR(255),
  sent_at TIMESTAMP,
  
  -- Tracking
  view_count INT DEFAULT 0,
  last_viewed_at TIMESTAMP,
  days_to_close INT,  -- If deal won
  
  FOREIGN KEY (deal_id) REFERENCES deals(id),
  INDEX idx_deal (deal_id),
  INDEX idx_sent_at (sent_at DESC)
);

CREATE TABLE proposal_views (
  id UUID PRIMARY KEY,
  draft_id UUID NOT NULL,
  
  viewed_by VARCHAR(255),  -- Recipient email
  viewed_at TIMESTAMP,
  duration_seconds INT,  -- How long they viewed
  pages_viewed INT,
  
  FOREIGN KEY (draft_id) REFERENCES proposal_drafts(id),
  INDEX idx_draft (draft_id),
  INDEX idx_viewed_at (viewed_at DESC)
);
```

### Metrics

```
Generation:
- Time to generate: <30 seconds (Claude)
- Quality score: 8.5+/10 (rep feedback)
- Edit rate: 20% (reps need edits)

Sending:
- Proposals sent per week: +200% vs manual
- View rate: 65%+ (vs 30% before)
- Time to close: -15% (better early proposals)

Cost:
- Claude API: ~$0.03 per proposal (15K input tokens @ $3/1M)
- Savings: 28 min * $25/hr = $11.67 per proposal
- ROI per proposal: 388x
```

---

## 3. COMPETITOR DETECTOR

### Problem
- Reps don't know if competing solution mentioned
- No structured response for objections
- Solution: NLP detects competitor mentions, triggers response campaigns

### Implementation

```python
class CompetitorDetector:
    COMPETITORS = [
        "outreach", "chorus", "salesloft", "pipedrive",
        "salesforce", "hubspot", "ringcentral", "gong"
    ]
    
    def detect_competitors(self, email_text: str) -> List[CompetitorMention]:
        """Extract competitor mentions from email/call transcript."""
        
        mentions = []
        text_lower = email_text.lower()
        
        for competitor in self.COMPETITORS:
            if competitor in text_lower:
                # Extract context (sentence containing mention)
                sentences = email_text.split(".")
                for sentence in sentences:
                    if competitor.lower() in sentence.lower():
                        mentions.append(CompetitorMention(
                            competitor=competitor,
                            context=sentence.strip(),
                            confidence=0.95,  # Exact match
                        ))
        
        return mentions
    
    def generate_response(self, competitor: str, context: str) -> str:
        """Generate counter-message for competitor mention."""
        
        response_prompt = f"""
        Buyer mentioned: "{competitor}"
        Context: "{context}"
        
        Generate short, professional response that:
        1. Acknowledges competitor (don't bash)
        2. Positions our unique value
        3. Asks for meeting to discuss differences
        
        Keep under 100 words. Tone: consultative, not defensive.
        """
        
        response = self.claude.messages.create(
            model="claude-opus",
            max_tokens=500,
            messages=[{"role": "user", "content": response_prompt}]
        )
        
        return response.content[0].text
```

### Database Schema

```sql
CREATE TABLE competitor_mentions (
  id UUID PRIMARY KEY,
  deal_id VARCHAR(255),
  person_id VARCHAR(255),
  
  competitor_name VARCHAR(255),
  source VARCHAR(50),  -- email, call_transcript, message
  context TEXT,
  
  detected_at TIMESTAMP,
  confidence FLOAT,  -- 0-1
  
  FOREIGN KEY (deal_id) REFERENCES deals(id),
  INDEX idx_deal_competitor (deal_id, competitor_name)
);

CREATE TABLE competitor_responses (
  id UUID PRIMARY KEY,
  mention_id UUID NOT NULL,
  
  response_type VARCHAR(50),  -- ai_generated, template, manual
  response_text TEXT,
  
  sent_at TIMESTAMP,
  sent_to VARCHAR(255),
  
  FOREIGN KEY (mention_id) REFERENCES competitor_mentions(id)
);
```

---

## 4. API ENDPOINTS (7 total)

```
POST /api/v1/email/predict-send-times
     → Recommend when to send email

POST /api/v1/email/track-open
     → Track email opens (webhook from email provider)

GET  /api/v1/proposal/generate
     Body: { deal_id, options? }
     → Generate AI proposal

POST /api/v1/proposal/send
     Body: { draft_id, email_to, send_time? }
     → Send proposal (with optimization)

GET  /api/v1/proposal/{draft_id}/views
     → Track proposal views

POST /api/v1/competitor/detect
     Body: { text }
     → Detect competitor mentions

POST /api/v1/competitor/respond
     Body: { mention_id, auto_generate? }
     → Generate counter-message
```

---

## 5. FRONTEND COMPONENTS (2 total)

### Component 1: EmailCampaignBuilder

```typescript
export default function EmailCampaignBuilder({ dealId }) {
  // 1. Email template selector
  // 2. Draft email content
  // 3. Recipient picker (from stakeholders)
  // 4. "Predict Send Times" button
  // 5. Calendar view showing recommended times
  // 6. "Schedule" vs "Send Now" buttons
}
```

### Component 2: ProposalGenerator

```typescript
export default function ProposalGenerator({ dealId }) {
  // 1. "Generate Proposal" button
  // 2. Loading spinner (while Claude generates)
  // 3. Preview (embedded HTML)
  // 4. Edit options (tone, length, focus areas)
  // 5. "Send to Stakeholder" dropdown
  // 6. Sent history + view tracking
}
```

---

## DATABASE ADDITIONS

**4 new tables**:
- `send_time_predictions` (send time optimization)
- `email_open_tracking` (event tracking)
- `proposal_drafts` (generated proposals)
- `proposal_views` (engagement tracking)
- `competitor_mentions` (NLP detection)
- `competitor_responses` (counter-campaigns)

**6 new tables, 12+ indexes**

---

## INTEGRATION WITH PHASE 27

**Inputs from Phase 27**:
- Stakeholder list + engagement scores
- Deal probability score
- Deal health assessment
- Recommended next-best-actions

**Outputs to Phase 28**:
- Email timing recommendations
- Auto-generated proposals
- Competitor response campaigns

**Data Flow**:
```
Phase 27 Dashboard
    ↓
"Send Email" action
    ↓
Phase 28: SendTimeOptimizer
         + ProposalGenerator
    ↓
Optimal send time + proposal draft
    ↓
Rep sends email
    ↓
Track open + views
    ↓
Feedback loop → improve predictions
```

---

## SUCCESS CRITERIA

**Email Optimization**:
- ✅ Send time prediction accuracy: 75%+ (AUC 0.78+)
- ✅ Email open rate: +45% (25% → 36%+)
- ✅ Time-to-open: <2 hours (vs 12+ hours without optimization)

**Proposal Generation**:
- ✅ Generation time: <2 minutes (vs 30 min manual)
- ✅ Proposal view rate: 65%+
- ✅ Rep satisfaction: 8.5+/10
- ✅ Cost per proposal: <$0.10

**Competitor Detection**:
- ✅ Detection rate: 95%+ (identify mentions)
- ✅ Response quality: 8+/10 (relevant, professional)
- ✅ Win-back rate: +15% (recover deals after competitor mention)

---

## TIMELINE

**Week 1-2**: SendTimeOptimizer (ML model)
**Week 3-4**: ProposalGenerator (Claude integration)
**Week 5-6**: CompetitorDetector (NLP + response)
**Week 7-8**: Frontend components + integration testing

**Launch**: Nov 1, 2026

---

## DEPENDENCIES

- Claude API (Anthropic SDK)
- Email service (SendGrid/AWS SES)
- NLP library (spaCy or scikit-learn)
- XGBoost (model training)

---

**Phase 28 Ready to Build**
