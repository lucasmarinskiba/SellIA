# Phase 28 - Engagement Optimization Architecture

**Duration**: 6 weeks (Weeks 9-14)  
**Team Size**: 1 backend engineer + 1 ML engineer + 1 frontend engineer  
**Expected Impact**: +45% email engagement, +5-8% close rate improvement  
**Predecessor**: Phase 27 (deal intelligence ready)

---

## STRATEGIC OVERVIEW

Phase 28 implements 3 AI-driven engagement systems:

1. **Email Send-Time Optimizer** - ML model predicts best time to send per recipient (personalized)
2. **AI Proposal Generator** - Creates customized proposals in 2 minutes (vs 30+ min manual)
3. **Competitive Displacement Campaigns** - Auto-identify competing vendors, build counter-campaigns

All three feed into a unified **Engagement Orchestration Engine** to coordinate multi-channel sequences.

---

## 1. ARCHITECTURE LAYERS

```
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND (React 19)                     │
│  Email Campaign Builder | Proposal Generator             │
│  Competitor Intelligence | Campaign Dashboard            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              API LAYER (FastAPI)                        │
│  /api/v1/engagement/email/send-time/{person_id}         │
│  /api/v1/engagement/proposals/generate                  │
│  /api/v1/engagement/competitor/{deal_id}               │
│  /api/v1/engagement/campaigns/{campaign_id}             │
│  /api/v1/engagement/orchestration/sequence              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          BUSINESS LOGIC (Python Services)               │
│  SendTimeOptimizer (ML inference)                       │
│  ProposalGenerator (LLM + templates)                    │
│  CompetitorDetector (data enrichment)                   │
│  CampaignOrchestrator (multi-channel sequence)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           DATA LAYER (PostgreSQL + Redis)               │
│  email_send_time_predictions | proposal_templates       │
│  competitor_mentions | competitor_campaigns             │
│  campaign_sequences | engagement_orchestration_state    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. DATABASE SCHEMA

### New Tables

```sql
-- ============================================================
-- SCHEMA: engagement
-- ============================================================

CREATE SCHEMA engagement;

-- ============================================================
-- EMAIL SEND-TIME OPTIMIZATION
-- ============================================================

CREATE TABLE engagement.email_send_time_predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id VARCHAR(255),
  
  -- Predicted best send time
  optimal_send_hour INT,  -- 0-23 (UTC)
  optimal_send_day VARCHAR(10),  -- mon, tue, wed, etc
  confidence_score FLOAT,  -- 0-1 (model confidence)
  
  -- Historical performance (features for model)
  avg_open_time_hour FLOAT,
  avg_open_rate_percent FLOAT,
  email_open_count INT,
  email_click_count INT,
  
  -- Model metadata
  model_version VARCHAR(50),
  prediction_date TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_person FOREIGN KEY (person_id) 
    REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_send_time_person ON engagement.email_send_time_predictions(person_id);
CREATE INDEX idx_send_time_updated ON engagement.email_send_time_predictions(prediction_date DESC);

-- Send-time model training data (time-series)
CREATE TABLE engagement.email_open_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id VARCHAR(255),
  email_id VARCHAR(255),
  
  -- Email sent metadata
  email_sent_at TIMESTAMP,
  email_sent_hour INT,  -- 0-23 (UTC)
  email_sent_day VARCHAR(10),
  
  -- Open event
  email_opened_at TIMESTAMP,
  time_to_open_minutes INT,
  
  -- Context
  email_subject VARCHAR(255),
  email_type VARCHAR(50),  -- followup, proposal, check-in, outreach
  
  CONSTRAINT fk_person FOREIGN KEY (person_id) 
    REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_email_opens_person ON engagement.email_open_events(person_id);
CREATE INDEX idx_email_opens_sent_at ON engagement.email_open_events(email_sent_at DESC);

-- ============================================================
-- AI PROPOSAL GENERATION
-- ============================================================

CREATE TABLE engagement.proposal_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Template metadata
  name VARCHAR(255),
  description TEXT,
  template_type VARCHAR(50),  -- standard, enterprise, complex, simple
  industry VARCHAR(100),  -- SaaS, Financial, Healthcare, etc
  deal_size_segment VARCHAR(50),  -- small, mid, enterprise
  
  -- Template structure
  sections JSONB,  -- [{name: "Executive Summary", prompt: "...", examples: [...]}]
  
  -- Usage metrics
  usage_count INT DEFAULT 0,
  avg_conversion_rate FLOAT DEFAULT 0.0,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_type ON engagement.proposal_templates(template_type);
CREATE INDEX idx_templates_industry ON engagement.proposal_templates(industry);

-- Generated proposals
CREATE TABLE engagement.generated_proposals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  
  -- Generation metadata
  template_id UUID,
  generated_by_model VARCHAR(50),  -- claude-opus, claude-sonnet, etc
  generation_time_seconds FLOAT,
  
  -- Content
  title VARCHAR(255),
  executive_summary TEXT,
  solution_overview TEXT,
  implementation_plan TEXT,
  pricing_section TEXT,
  next_steps TEXT,
  
  -- Full proposal (markdown)
  full_content TEXT,
  
  -- Usage
  sent_to_count INT DEFAULT 0,
  open_count INT DEFAULT 0,
  conversion BOOLEAN DEFAULT NULL,  -- true if deal closed
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  generated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE,
  CONSTRAINT fk_template FOREIGN KEY (template_id) 
    REFERENCES engagement.proposal_templates(id) ON DELETE SET NULL
);

CREATE INDEX idx_proposals_deal ON engagement.generated_proposals(deal_id);
CREATE INDEX idx_proposals_created ON engagement.generated_proposals(created_at DESC);

-- ============================================================
-- COMPETITOR INTELLIGENCE
-- ============================================================

CREATE TABLE engagement.competitor_mentions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  
  -- Competitor info
  competitor_name VARCHAR(255),
  confidence_score FLOAT,  -- 0-1 (likelihood competitor is real threat)
  
  -- Detection context
  detection_source VARCHAR(50),  -- email, call_transcript, crm_field, web
  mentioned_in_context TEXT,  -- quote or context
  
  -- Deal stage when detected
  deal_stage VARCHAR(50),
  
  -- Recency
  first_mentioned_at TIMESTAMP,
  last_mentioned_at TIMESTAMP,
  mention_count INT DEFAULT 1,
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_competitors_deal ON engagement.competitor_mentions(deal_id);
CREATE INDEX idx_competitors_name ON engagement.competitor_mentions(competitor_name);
CREATE INDEX idx_competitors_confidence ON engagement.competitor_mentions(confidence_score DESC);

-- Competitive positioning content
CREATE TABLE engagement.competitor_positioning (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Competitor
  competitor_name VARCHAR(255),
  
  -- SellIA positioning vs. competitor
  key_differentiators JSONB,  -- [{feature: "Real-time collab", benefit: "40% faster cycle"}]
  winning_arguments JSONB,  -- [{objection: "No mobile app", counter: "Native iOS/Android shipped Phase 26"}]
  case_studies JSONB,  -- [{customer: "Acme", result: "30% win rate increase"}]
  
  -- Usage
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_positioning_competitor ON engagement.competitor_positioning(competitor_name);

-- ============================================================
-- CAMPAIGN ORCHESTRATION
-- ============================================================

CREATE TABLE engagement.email_campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  
  -- Campaign metadata
  campaign_type VARCHAR(50),  -- followup, competitive_displacement, expansion, reengagement
  campaign_name VARCHAR(255),
  objective VARCHAR(200),
  
  -- Target
  target_person_id VARCHAR(255),
  target_role VARCHAR(100),  -- Economic buyer, user buyer, coach, etc
  
  -- Sequence
  email_sequence JSONB,  -- [{order: 1, day_offset: 0, template: "..."}, ...]
  
  -- Tracking
  started_at TIMESTAMP DEFAULT NOW(),
  ended_at TIMESTAMP,
  status VARCHAR(50),  -- active, paused, completed, failed
  
  -- Results
  emails_sent INT DEFAULT 0,
  emails_opened INT DEFAULT 0,
  emails_clicked INT DEFAULT 1,
  conversions INT DEFAULT 0,
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_campaigns_deal ON engagement.email_campaigns(deal_id);
CREATE INDEX idx_campaigns_person ON engagement.email_campaigns(target_person_id);
CREATE INDEX idx_campaigns_status ON engagement.email_campaigns(status);

-- Individual emails in campaign
CREATE TABLE engagement.campaign_emails (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID,
  
  -- Email details
  sequence_order INT,
  email_subject VARCHAR(255),
  email_body TEXT,
  personalization_vars JSONB,  -- {name, company, pain_point, etc}
  
  -- Send details
  scheduled_send_time TIMESTAMP,
  actual_send_time TIMESTAMP,
  
  -- Results
  open_time TIMESTAMP,
  click_time TIMESTAMP,
  conversion BOOLEAN DEFAULT NULL,
  
  CONSTRAINT fk_campaign FOREIGN KEY (campaign_id) 
    REFERENCES engagement.email_campaigns(id) ON DELETE CASCADE
);

CREATE INDEX idx_campaign_emails_campaign ON engagement.campaign_emails(campaign_id);
CREATE INDEX idx_campaign_emails_scheduled ON engagement.campaign_emails(scheduled_send_time);

-- ============================================================
-- ORCHESTRATION STATE
-- ============================================================

CREATE TABLE engagement.orchestration_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255) UNIQUE,
  
  -- Current state
  current_phase VARCHAR(50),  -- discovery, proposal, negotiation, closing
  
  -- Active sequences
  active_campaigns JSONB,  -- [campaign_id1, campaign_id2, ...]
  next_action VARCHAR(200),  -- "Send proposal", "Call economic buyer", etc
  recommended_channel VARCHAR(50),  -- email, call, meeting, proposal
  
  -- Engagement metrics (real-time)
  engagement_score FLOAT,  -- 0-100
  momentum_indicator VARCHAR(20),  -- accelerating, stable, declining
  
  -- Last update
  last_updated TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_orchestration_deal ON engagement.orchestration_state(deal_id);
CREATE INDEX idx_orchestration_phase ON engagement.orchestration_state(current_phase);

-- ============================================================
-- Grant permissions
-- ============================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA engagement TO sellia_user;
GRANT USAGE ON SCHEMA engagement TO sellia_user;
```

---

## 3. BACKEND IMPLEMENTATION

### SendTimeOptimizer Service

**File**: `backend/app/services/engagement/send_time_optimizer.py` (300 lines)

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy import func, select
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

@dataclass
class OptimalSendTime:
    """Optimal email send time for person."""
    optimal_hour: int  # 0-23 UTC
    optimal_day: str  # mon, tue, wed, etc
    confidence: float  # 0-1
    reasoning: str  # Explanation for recommendations

class SendTimeOptimizer:
    """ML-based email send-time optimization."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.ml_model = SendTimeModel()  # XGBoost model
    
    async def get_optimal_send_time(self, person_id: str) -> OptimalSendTime:
        """Get personalized optimal send time."""
        
        # Check cache
        cached = await self._get_cached_prediction(person_id)
        if cached:
            return cached
        
        # Extract features
        features = await self._extract_features(person_id)
        
        # Run inference
        prediction = self.ml_model.predict(features)
        
        # Store prediction
        await self._store_prediction(person_id, prediction)
        
        return OptimalSendTime(
            optimal_hour=prediction["hour"],
            optimal_day=prediction["day"],
            confidence=prediction["confidence"],
            reasoning=prediction["reasoning"]
        )
    
    async def _extract_features(self, person_id: str) -> Dict[str, Any]:
        """Extract features for send-time model."""
        
        # Get past 30 days of email opens
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        query = select(EmailOpenEvent).where(
            (EmailOpenEvent.person_id == person_id) &
            (EmailOpenEvent.email_sent_at >= thirty_days_ago)
        )
        
        open_events = self.db.execute(query).scalars().all()
        
        if not open_events:
            # Return default features
            return {
                "avg_open_hour": 10,  # Default: 10am
                "avg_open_day": "tue",  # Default: Tuesday
                "email_opens_last_30d": 0,
                "timezone": "UTC"
            }
        
        # Calculate features
        open_hours = [e.email_sent_hour for e in open_events]
        open_days = [e.email_sent_day for e in open_events]
        time_to_opens = [e.time_to_open_minutes for e in open_events]
        
        features = {
            "avg_open_hour": np.mean(open_hours),
            "std_open_hour": float(np.std(open_hours)) if len(open_hours) > 1 else 0,
            "avg_open_day": max(set(open_days), key=open_days.count),
            "email_opens_last_30d": len(open_events),
            "avg_time_to_open_minutes": np.mean(time_to_opens),
            "open_rate_percent": (len(open_events) / len(set(e.email_id for e in open_events))) * 100,
            "timezone": "UTC"  # TODO: infer from user location
        }
        
        return features
    
    async def _store_prediction(self, person_id: str, prediction: Dict):
        """Store prediction in database."""
        
        pred = EmailSendTimePrediction(
            person_id=person_id,
            optimal_send_hour=prediction["hour"],
            optimal_send_day=prediction["day"],
            confidence_score=prediction["confidence"],
            model_version=self.ml_model.version
        )
        
        self.db.add(pred)
        self.db.commit()
    
    async def _get_cached_prediction(self, person_id: str) -> Optional[OptimalSendTime]:
        """Get cached prediction if fresh."""
        
        query = select(EmailSendTimePrediction).where(
            EmailSendTimePrediction.person_id == person_id
        ).order_by(EmailSendTimePrediction.prediction_date.desc()).limit(1)
        
        pred = self.db.execute(query).scalar()
        
        if pred:
            # Cache fresh for 7 days
            if (datetime.utcnow() - pred.prediction_date).days < 7:
                return OptimalSendTime(
                    optimal_hour=pred.optimal_send_hour,
                    optimal_day=pred.optimal_send_day,
                    confidence=pred.confidence_score,
                    reasoning=f"Predicted based on {pred.email_open_count} opens"
                )
        
        return None

class SendTimeModel:
    """Trained send-time optimization model."""
    
    def __init__(self):
        self.version = "1.0.0"
        import joblib
        self.model = joblib.load("/app/models/send_time_v1.0.0.pkl")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict optimal send time.
        
        Returns:
        {
            "hour": 14,  # 2pm UTC (optimal hour)
            "day": "tue",  # Tuesday
            "confidence": 0.78,
            "reasoning": "Opens peak at 2pm on Tuesdays"
        }
        """
        
        # Feature extraction
        X = np.array([
            features["avg_open_hour"],
            features["std_open_hour"],
            features["email_opens_last_30d"],
            features["avg_time_to_open_minutes"],
            features["open_rate_percent"]
        ]).reshape(1, -1)
        
        # Predict
        predictions = self.model.predict(X)[0]  # Shape: (24,) - prob for each hour
        
        optimal_hour = int(np.argmax(predictions))
        confidence = float(predictions[optimal_hour])
        
        # Map day (simplified: use most common day from features)
        day_mapping = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
        optimal_day = features.get("avg_open_day", "tue")
        
        return {
            "hour": optimal_hour,
            "day": optimal_day,
            "confidence": confidence,
            "reasoning": f"Peak opens at {optimal_hour}:00 on {optimal_day}s"
        }
```

### ProposalGenerator Service

**File**: `backend/app/services/engagement/proposal_generator.py` (400 lines)

```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import anthropic
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

@dataclass
class GeneratedProposal:
    """Generated proposal document."""
    title: str
    executive_summary: str
    solution_overview: str
    implementation_plan: str
    pricing_section: str
    next_steps: str
    full_content: str  # Markdown
    generation_time_seconds: float

class ProposalGenerator:
    """AI-powered proposal generator using Claude."""
    
    def __init__(self, db_session, anthropic_key: str):
        self.db = db_session
        self.client = anthropic.Anthropic(api_key=anthropic_key)
    
    async def generate_proposal(
        self,
        deal_id: str,
        deal_name: str,
        company: str,
        use_case: str,
        budget: float,
        success_criteria: List[str],
        template_id: Optional[str] = None
    ) -> GeneratedProposal:
        """Generate customized proposal in 2 minutes."""
        
        import time
        start_time = time.time()
        
        # 1. Select template
        template = await self._get_template(
            template_id=template_id,
            deal_budget=budget
        )
        
        # 2. Build prompt
        prompt = self._build_proposal_prompt(
            deal_name=deal_name,
            company=company,
            use_case=use_case,
            budget=budget,
            success_criteria=success_criteria,
            template=template
        )
        
        # 3. Generate with Claude
        sections = await self._generate_sections(prompt)
        
        # 4. Assemble proposal
        proposal = GeneratedProposal(
            title=sections.get("title", f"{deal_name} Proposal"),
            executive_summary=sections.get("executive_summary", ""),
            solution_overview=sections.get("solution_overview", ""),
            implementation_plan=sections.get("implementation_plan", ""),
            pricing_section=sections.get("pricing_section", ""),
            next_steps=sections.get("next_steps", ""),
            full_content=self._assemble_markdown(sections),
            generation_time_seconds=time.time() - start_time
        )
        
        # 5. Store in database
        await self._store_proposal(deal_id, proposal, template.id if template else None)
        
        return proposal
    
    def _build_proposal_prompt(
        self,
        deal_name: str,
        company: str,
        use_case: str,
        budget: float,
        success_criteria: List[str],
        template: Optional[Dict]
    ) -> str:
        """Build multi-section prompt for proposal generation."""
        
        criteria_text = "\n".join([f"- {c}" for c in success_criteria])
        
        prompt = f"""Generate a professional SaaS proposal for:

Company: {company}
Deal Name: {deal_name}
Annual Budget: ${budget:,.0f}
Use Case: {use_case}

Success Criteria:
{criteria_text}

Generate ONLY the following JSON structure (no markdown, valid JSON):
{{
    "title": "Professional proposal title",
    "executive_summary": "1-2 paragraph summary of solution and expected value",
    "solution_overview": "Detailed description of how SellIA solves their problem",
    "implementation_plan": "Week-by-week 8-week implementation timeline",
    "pricing_section": "Transparent pricing with ROI calculation",
    "next_steps": "Clear next steps and decision timeline"
}}

Key requirements:
- Personalize all sections to {company}'s use case
- Include specific ROI metrics (e.g., '30% faster sales cycle = $X value')
- Address success criteria explicitly in solution
- Use professional business language
- Include 1-2 relevant case studies from similar companies

Generate the proposal now:"""
        
        return prompt
    
    async def _generate_sections(self, prompt: str) -> Dict[str, str]:
        """Call Claude to generate proposal sections."""
        
        response = self.client.messages.create(
            model="claude-opus",  # Use Opus for best quality proposals
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Parse response
        content = response.content[0].text
        
        try:
            import json
            sections = json.loads(content)
            return sections
        except json.JSONDecodeError:
            logger.error(f"Failed to parse proposal JSON: {content}")
            return {}
    
    async def _get_template(
        self,
        template_id: Optional[str] = None,
        deal_budget: float = 50000
    ) -> Optional[Dict]:
        """Get template for proposal."""
        
        if template_id:
            query = select(ProposalTemplate).where(
                ProposalTemplate.id == template_id
            )
            return self.db.execute(query).scalar()
        
        # Auto-select by budget
        segment = "small" if deal_budget < 10000 else "mid" if deal_budget < 50000 else "enterprise"
        
        query = select(ProposalTemplate).where(
            (ProposalTemplate.template_type == "standard") &
            (ProposalTemplate.deal_size_segment == segment)
        ).order_by(ProposalTemplate.usage_count.desc()).limit(1)
        
        return self.db.execute(query).scalar()
    
    def _assemble_markdown(self, sections: Dict[str, str]) -> str:
        """Assemble sections into markdown proposal."""
        
        markdown = f"""# {sections.get("title", "Proposal")}

## Executive Summary

{sections.get("executive_summary", "")}

## Solution Overview

{sections.get("solution_overview", "")}

## Implementation Plan

{sections.get("implementation_plan", "")}

## Pricing

{sections.get("pricing_section", "")}

## Next Steps

{sections.get("next_steps", "")}

---

Generated by SellIA Deal Intelligence. For questions, contact your account team.
"""
        
        return markdown
    
    async def _store_proposal(
        self,
        deal_id: str,
        proposal: GeneratedProposal,
        template_id: Optional[str] = None
    ):
        """Store generated proposal in database."""
        
        generated = GeneratedProposal(
            deal_id=deal_id,
            template_id=template_id,
            generated_by_model="claude-opus",
            generation_time_seconds=proposal.generation_time_seconds,
            title=proposal.title,
            executive_summary=proposal.executive_summary,
            solution_overview=proposal.solution_overview,
            implementation_plan=proposal.implementation_plan,
            pricing_section=proposal.pricing_section,
            next_steps=proposal.next_steps,
            full_content=proposal.full_content
        )
        
        self.db.add(generated)
        self.db.commit()
```

### CompetitorDetector Service

**File**: `backend/app/services/engagement/competitor_detector.py` (250 lines)

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

@dataclass
class CompetitorMention:
    """Detected competitor mention."""
    competitor_name: str
    confidence: float  # 0-1
    context: str
    source: str  # email, call_transcript, crm_field, web

class CompetitorDetector:
    """Detect and track competitor mentions."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.known_competitors = [
            "Outreach",
            "Chorus",
            "SalesLoft",
            "Pipedrive",
            "HubSpot Sales",
            "Salesforce Einstein",
            "Gong",
            "Clari"
        ]
    
    async def detect_competitors_in_transcript(
        self,
        deal_id: str,
        transcript_text: str,
        source: str = "call_transcript"
    ) -> List[CompetitorMention]:
        """Detect competitor mentions in call transcript."""
        
        mentions: List[CompetitorMention] = []
        
        # 1. Extract mentions via NLP
        detected = await self._extract_mentions(transcript_text)
        
        # 2. Store mentions
        for mention in detected:
            existing = self.db.query(CompetitorMention).filter_by(
                deal_id=deal_id,
                competitor_name=mention.competitor_name
            ).first()
            
            if existing:
                existing.mention_count += 1
                existing.last_mentioned_at = datetime.utcnow()
            else:
                db_mention = CompetitorMention(
                    deal_id=deal_id,
                    competitor_name=mention.competitor_name,
                    confidence_score=mention.confidence,
                    mentioned_in_context=mention.context,
                    first_mentioned_at=datetime.utcnow(),
                    last_mentioned_at=datetime.utcnow(),
                    detection_source=source
                )
                self.db.add(db_mention)
            
            mentions.append(mention)
        
        self.db.commit()
        return mentions
    
    async def _extract_mentions(self, text: str) -> List[CompetitorMention]:
        """Extract competitor mentions from text."""
        
        mentions = []
        
        for competitor in self.known_competitors:
            if competitor.lower() in text.lower():
                # Find context (surrounding text)
                start_idx = text.lower().find(competitor.lower())
                context_start = max(0, start_idx - 50)
                context_end = min(len(text), start_idx + len(competitor) + 50)
                context = text[context_start:context_end]
                
                # Estimate confidence (high if mentioned multiple times)
                count = text.lower().count(competitor.lower())
                confidence = min(count * 0.3, 0.95)
                
                mentions.append(CompetitorMention(
                    competitor_name=competitor,
                    confidence=confidence,
                    context=context.strip(),
                    source="transcript"
                ))
        
        return mentions
    
    async def get_competitive_positioning(
        self,
        deal_id: str
    ) -> Dict[str, Any]:
        """Get positioning content for detected competitors."""
        
        # Get competitors mentioned in deal
        query = select(CompetitorMention).where(
            CompetitorMention.deal_id == deal_id
        ).order_by(CompetitorMention.confidence_score.desc())
        
        mentioned = self.db.execute(query).scalars().all()
        
        positioning = {}
        
        for mention in mentioned:
            # Get positioning content
            query = select(CompetitorPositioning).where(
                CompetitorPositioning.competitor_name == mention.competitor_name
            )
            
            pos = self.db.execute(query).scalar()
            
            if pos:
                positioning[mention.competitor_name] = {
                    "differentiators": pos.key_differentiators,
                    "winning_arguments": pos.winning_arguments,
                    "case_studies": pos.case_studies
                }
        
        return positioning
    
    async def build_displacement_campaign(
        self,
        deal_id: str,
        competitor_name: str
    ) -> Dict[str, Any]:
        """Build campaign to displace known competitor."""
        
        # Get positioning
        positioning = await self.get_competitive_positioning(deal_id)
        
        if competitor_name not in positioning:
            return {}
        
        pos = positioning[competitor_name]
        
        # Build campaign sequence
        sequence = [
            {
                "day": 0,
                "subject": f"Re: {competitor_name} Evaluation",
                "template": "competitive_positioning",
                "body": f"""I noticed {competitor_name} in your evaluation. 
                
Here's how SellIA differentiates:

{self._format_differentiators(pos['differentiators'])}

Let's discuss: [scheduling link]"""
            },
            {
                "day": 3,
                "subject": f"Case Study: {competitor_name} Alternative",
                "template": "case_study",
                "body": f"""Since you're evaluating {competitor_name}, 
you might find this case study valuable:

{self._format_case_studies(pos['case_studies'])}"""
            },
            {
                "day": 7,
                "subject": "Final thoughts on your evaluation",
                "template": "closing",
                "body": "Ready to see why SellIA wins vs. [competitor]?"
            }
        ]
        
        return {
            "competitor": competitor_name,
            "positioning": pos,
            "campaign_sequence": sequence
        }
    
    def _format_differentiators(self, diffs: List[Dict]) -> str:
        return "\n".join([
            f"• {d['feature']}: {d['benefit']}"
            for d in diffs[:3]
        ])
    
    def _format_case_studies(self, cases: List[Dict]) -> str:
        return "\n".join([
            f"**{c['customer']}**: {c['result']}"
            for c in cases[:2]
        ])
```

---

## 4. API ENDPOINTS

**File**: `backend/app/api/v1/engagement.py` (350 lines)

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime
from backend.app.dependencies import get_current_user, get_db
from backend.app.services.engagement.send_time_optimizer import SendTimeOptimizer
from backend.app.services.engagement.proposal_generator import ProposalGenerator
from backend.app.services.engagement.competitor_detector import CompetitorDetector

router = APIRouter(prefix="/api/v1/engagement", tags=["engagement"])

# ============================================================
# SEND-TIME OPTIMIZATION
# ============================================================

@router.get("/email/send-time/{person_id}")
async def get_optimal_send_time(
    person_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get personalized optimal email send time."""
    
    optimizer = SendTimeOptimizer(db)
    send_time = await optimizer.get_optimal_send_time(person_id)
    
    return {
        "person_id": person_id,
        "optimal_hour": send_time.optimal_hour,
        "optimal_day": send_time.optimal_day,
        "confidence": send_time.confidence,
        "reasoning": send_time.reasoning,
        "send_time_recommendation": f"{send_time.optimal_hour}:00 UTC on {send_time.optimal_day}s"
    }

# ============================================================
# PROPOSAL GENERATION
# ============================================================

@router.post("/proposals/generate")
async def generate_proposal(
    deal_id: str,
    deal_name: str,
    company: str,
    use_case: str,
    budget: float,
    success_criteria: list,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Generate AI proposal (2 minutes)."""
    
    generator = ProposalGenerator(db, anthropic_key=os.getenv("ANTHROPIC_API_KEY"))
    proposal = await generator.generate_proposal(
        deal_id=deal_id,
        deal_name=deal_name,
        company=company,
        use_case=use_case,
        budget=budget,
        success_criteria=success_criteria
    )
    
    return {
        "deal_id": deal_id,
        "proposal_id": proposal.id,
        "title": proposal.title,
        "generation_time_seconds": proposal.generation_time_seconds,
        "sections": {
            "executive_summary": proposal.executive_summary[:200] + "...",
            "solution_overview": proposal.solution_overview[:200] + "...",
            "pricing": proposal.pricing_section[:100] + "..."
        },
        "download_link": f"/proposals/{proposal.id}/download"
    }

@router.get("/proposals/{proposal_id}")
async def get_proposal(
    proposal_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Fetch generated proposal (markdown or PDF)."""
    
    proposal = db.query(GeneratedProposal).filter_by(id=proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404)
    
    return {
        "id": proposal_id,
        "content": proposal.full_content,
        "sent_to_count": proposal.sent_to_count,
        "open_count": proposal.open_count,
        "conversion": proposal.conversion
    }

# ============================================================
# COMPETITOR INTELLIGENCE
# ============================================================

@router.post("/competitors/{deal_id}/detect")
async def detect_competitors(
    deal_id: str,
    transcript_text: str,
    source: str = "call_transcript",
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Detect competitor mentions in transcript."""
    
    detector = CompetitorDetector(db)
    mentions = await detector.detect_competitors_in_transcript(
        deal_id=deal_id,
        transcript_text=transcript_text,
        source=source
    )
    
    return {
        "deal_id": deal_id,
        "competitors_detected": [
            {
                "name": m.competitor_name,
                "confidence": m.confidence,
                "context": m.context
            }
            for m in mentions
        ]
    }

@router.get("/competitors/{deal_id}/positioning")
async def get_competitor_positioning(
    deal_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get positioning against detected competitors."""
    
    detector = CompetitorDetector(db)
    positioning = await detector.get_competitive_positioning(deal_id)
    
    return {
        "deal_id": deal_id,
        "positioning": positioning
    }

@router.post("/competitors/{deal_id}/campaign/{competitor_name}")
async def create_displacement_campaign(
    deal_id: str,
    competitor_name: str,
    target_person_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    background_tasks: BackgroundTasks
):
    """Create campaign to displace competitor."""
    
    detector = CompetitorDetector(db)
    campaign_plan = await detector.build_displacement_campaign(deal_id, competitor_name)
    
    if not campaign_plan:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    # Create campaign (async)
    campaign = EmailCampaign(
        deal_id=deal_id,
        campaign_type="competitive_displacement",
        campaign_name=f"Displace {competitor_name}",
        target_person_id=target_person_id,
        email_sequence=campaign_plan["campaign_sequence"],
        status="active"
    )
    db.add(campaign)
    db.commit()
    
    # Schedule emails
    background_tasks.add_task(schedule_campaign_emails, campaign.id)
    
    return {
        "campaign_id": campaign.id,
        "competitor": competitor_name,
        "emails_scheduled": len(campaign_plan["campaign_sequence"])
    }

# ============================================================
# CAMPAIGN ORCHESTRATION
# ============================================================

@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get campaign status + performance."""
    
    campaign = db.query(EmailCampaign).filter_by(id=campaign_id).first()
    
    return {
        "id": campaign_id,
        "name": campaign.campaign_name,
        "type": campaign.campaign_type,
        "status": campaign.status,
        "emails_sent": campaign.emails_sent,
        "emails_opened": campaign.emails_opened,
        "open_rate": (campaign.emails_opened / campaign.emails_sent * 100) if campaign.emails_sent > 0 else 0,
        "conversions": campaign.conversions
    }

@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Pause active campaign."""
    
    campaign = db.query(EmailCampaign).filter_by(id=campaign_id).first()
    campaign.status = "paused"
    db.commit()
    
    return {"status": "paused"}
```

---

## 5. CELERY TASKS

**File**: `backend/app/tasks/engagement.py`

```python
from celery import shared_task
from datetime import datetime, timedelta
from backend.app.database import SessionLocal
from backend.app.models.engagement import EmailCampaign, CampaignEmail
from backend.app.services.email import send_email
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def send_campaign_email(self, campaign_email_id: str):
    """Send individual campaign email at optimal time."""
    try:
        db = SessionLocal()
        
        email = db.query(CampaignEmail).filter_by(id=campaign_email_id).first()
        if not email:
            return {"status": "email_not_found"}
        
        # Send email
        result = send_email(
            to=email.target_email,
            subject=email.email_subject,
            body=email.email_body
        )
        
        email.actual_send_time = datetime.utcnow()
        db.commit()
        
        logger.info(f"Sent email {campaign_email_id}")
        return {"status": "sent"}
    
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        self.retry(countdown=300, exc=exc, max_retries=3)

@celery_app.task(bind=True, max_retries=2)
def retrain_send_time_model_weekly(self):
    """Retrain send-time model with latest email data (weekly)."""
    try:
        from backend.app.ml.send_time_trainer import train_send_time_model
        
        logger.info("Retraining send-time model...")
        
        new_model = train_send_time_model()
        auc_score = new_model.evaluate()
        
        if auc_score >= 0.75:  # Send-time threshold
            new_model.save()
            logger.info(f"New model AUC: {auc_score}. Deployed.")
            return {"status": "deployed", "auc": auc_score}
        else:
            logger.warning(f"Model AUC {auc_score} < 0.75. Not deploying.")
            return {"status": "not_deployed"}
    
    except Exception as exc:
        logger.error(f"Model retraining failed: {exc}")
        self.retry(countdown=3600, exc=exc)
```

---

## 6. FRONTEND COMPONENTS

### EmailCampaignBuilder.tsx (300 lines)

```typescript
import React, { useState } from 'react';
import { Card, Button, Select, TextInput, Textarea } from '@tremor/react';
import { SendTimeOptimizer } from './SendTimeOptimizer';

export const EmailCampaignBuilder: React.FC = () => {
  const [campaignType, setCampaignType] = useState('followup');
  const [targetPerson, setTargetPerson] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [selectedSendTime, setSelectedSendTime] = useState('');

  const handleBuild = async () => {
    const response = await fetch('/api/v1/engagement/campaigns', {
      method: 'POST',
      body: JSON.stringify({
        campaign_type: campaignType,
        target_person_id: targetPerson,
        email_subject: subject,
        email_body: body,
        scheduled_send_time: selectedSendTime
      })
    });
    
    const result = await response.json();
    console.log('Campaign created:', result);
  };

  return (
    <div className="space-y-4 p-6">
      <Card>
        <h2 className="text-lg font-bold mb-4">Email Campaign Builder</h2>
        
        <Select
          value={campaignType}
          onValueChange={setCampaignType}
          placeholder="Campaign Type"
        >
          <option value="followup">Follow-up</option>
          <option value="competitive_displacement">Competitive Displacement</option>
          <option value="reengagement">Re-engagement</option>
        </Select>
        
        <TextInput
          placeholder="Target Person ID"
          value={targetPerson}
          onChange={(e) => setTargetPerson(e.target.value)}
        />
        
        {/* Send-time optimizer */}
        {targetPerson && (
          <SendTimeOptimizer
            personId={targetPerson}
            onSelect={setSelectedSendTime}
          />
        )}
        
        <TextInput
          placeholder="Email Subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
        
        <Textarea
          placeholder="Email Body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        
        <Button onClick={handleBuild}>Create Campaign</Button>
      </Card>
    </div>
  );
};
```

### ProposalGenerator.tsx (250 lines)

```typescript
import React, { useState } from 'react';
import { Card, Button, TextInput, Textarea, Badge } from '@tremor/react';

export const ProposalGenerator: React.FC<{dealId: string}> = ({dealId}) => {
  const [loading, setLoading] = useState(false);
  const [dealName, setDealName] = useState('');
  const [company, setCompany] = useState('');
  const [useCase, setUseCase] = useState('');
  const [budget, setBudget] = useState('');
  const [generatedProposal, setGeneratedProposal] = useState<any>(null);

  const handleGenerate = async () => {
    setLoading(true);
    
    const response = await fetch('/api/v1/engagement/proposals/generate', {
      method: 'POST',
      body: JSON.stringify({
        deal_id: dealId,
        deal_name: dealName,
        company: company,
        use_case: useCase,
        budget: parseFloat(budget)
      })
    });
    
    const result = await response.json();
    setGeneratedProposal(result);
    setLoading(false);
  };

  return (
    <div className="space-y-4 p-6">
      <Card>
        <h2 className="text-lg font-bold mb-4">AI Proposal Generator</h2>
        
        <TextInput
          placeholder="Deal Name"
          value={dealName}
          onChange={(e) => setDealName(e.target.value)}
        />
        
        <TextInput
          placeholder="Company"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
        />
        
        <Textarea
          placeholder="Use Case / Pain Points"
          value={useCase}
          onChange={(e) => setUseCase(e.target.value)}
        />
        
        <TextInput
          placeholder="Budget ($)"
          type="number"
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
        />
        
        <Button
          onClick={handleGenerate}
          disabled={loading || !dealName || !company}
        >
          {loading ? 'Generating...' : 'Generate Proposal (2 min)'}
        </Button>
      </Card>
      
      {generatedProposal && (
        <Card>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold">{generatedProposal.title}</h3>
              <Badge>{generatedProposal.generation_time_seconds.toFixed(1)}s</Badge>
            </div>
            
            <div className="prose max-w-none">
              <h4>Executive Summary</h4>
              <p>{generatedProposal.sections.executive_summary}</p>
            </div>
            
            <Button onClick={() => window.open(`/proposals/${generatedProposal.proposal_id}/download`)}>
              Download PDF
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};
```

---

## 7. IMPLEMENTATION TIMELINE

**Week 9-10**: SendTimeOptimizer
- [ ] Database schema + migrations
- [ ] Email open events ingestion
- [ ] SendTimeOptimizer service (300 lines)
- [ ] ML model training (XGBoost)
- [ ] API endpoint + tests

**Week 11-12**: ProposalGenerator
- [ ] Proposal templates CRUD
- [ ] ProposalGenerator service (400 lines)
- [ ] Claude API integration
- [ ] PDF export
- [ ] Frontend component + testing

**Week 13**: CompetitorDetector
- [ ] Competitor intelligence tables
- [ ] CompetitorDetector service (250 lines)
- [ ] Displacement campaign builder
- [ ] API endpoints

**Week 14**: Integration + Testing
- [ ] Campaign orchestration engine
- [ ] End-to-end testing (3+ scenarios)
- [ ] Performance testing (100 concurrent users)
- [ ] UAT with power users (5-10 deals)

---

## 8. SUCCESS CRITERIA

**Technical**:
- [ ] All 3 services complete + tested
- [ ] Send-time model accuracy 75%+
- [ ] Proposal generation < 2 minutes
- [ ] API response time < 200ms p95
- [ ] 99%+ uptime

**Product**:
- [ ] Email open rate +45% (A/B test)
- [ ] Close rate +5-8% (tracked via proposals)
- [ ] Displacement campaigns 2-5% conversion
- [ ] Team using generator on 50%+ deals

---

**Phase 28 Architecture Ready** ✅

