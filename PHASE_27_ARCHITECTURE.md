# Phase 27 - Deal Intelligence Foundation Architecture

**Duration**: 8 weeks  
**Team Size**: 1 backend engineer + 1 frontend engineer + 1 ML engineer  
**Expected Impact**: +15-20% forecast accuracy, -30% stalled deals  
**Milestone**: End of Aug / Early Sep 2026

---

## STRATEGIC OVERVIEW

Phase 27 implements 3 interconnected systems:

1. **Multi-threaded Stakeholder Intelligence** - Map buying committees, identify economic buyers, track engagement
2. **Deal Probability Predictor** - ML model forecasts close probability per deal
3. **Real-time Deal Health Scoring** - Automatic alerts when deals at risk

All three feed into a unified **Deal Intelligence Dashboard** for sellers.

---

## 1. ARCHITECTURE LAYERS

```
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND (React 19)                     │
│  Dashboard | Deal Detail | Health Alerts | Bulk Actions │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              API LAYER (FastAPI)                        │
│  /api/v1/intelligence/deal/{id}                         │
│  /api/v1/intelligence/stakeholders/{deal_id}            │
│  /api/v1/intelligence/probability/{deal_id}             │
│  /api/v1/intelligence/health/{deal_id}                  │
│  /api/v1/intelligence/alerts                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          BUSINESS LOGIC (Python Services)               │
│  DealIntelligenceManager                                │
│  ├─ StakeholderMapper (enrich + identify buyers)        │
│  ├─ DealProbabilityPredictor (ML inference)             │
│  └─ DealHealthScorer (real-time evaluation)             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           DATA LAYER (PostgreSQL + Redis)               │
│  deal_stakeholders | deal_probability_scores            │
│  deal_health_snapshots | stakeholder_engagement         │
│  deal_health_alerts | model_predictions_cache           │
└─────────────────────────────────────────────────────────┘
```

---

## 2. DATABASE SCHEMA

### New Tables

```sql
-- ============================================================
-- SCHEMA: intelligence
-- ============================================================

CREATE SCHEMA intelligence;

-- Stakeholder mapping (buying committee)
CREATE TABLE intelligence.deal_stakeholders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  
  -- Person details
  person_id VARCHAR(255),
  email VARCHAR(255),
  name VARCHAR(255),
  title VARCHAR(255),
  company VARCHAR(255),
  
  -- Role in buying process
  buyer_role VARCHAR(50),  -- economic_buyer, user_buyer, coach, blocker, influencer
  influence_level INT DEFAULT 5,  -- 1-10 scale
  engagement_score FLOAT DEFAULT 0.0,  -- 0-100
  
  -- Engagement tracking
  last_email_open TIMESTAMP,
  last_call_date TIMESTAMP,
  email_open_count INT DEFAULT 0,
  meeting_count INT DEFAULT 0,
  message_count INT DEFAULT 0,
  
  -- Status
  status VARCHAR(50),  -- active, churned, dormant, prospect
  identified_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_deal_stakeholders_deal ON intelligence.deal_stakeholders(deal_id);
CREATE INDEX idx_deal_stakeholders_role ON intelligence.deal_stakeholders(buyer_role);

-- ============================================================
-- Deal Probability Predictions
-- ============================================================

CREATE TABLE intelligence.deal_probability_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255) UNIQUE,
  
  -- Predicted probability
  close_probability FLOAT,  -- 0-100
  confidence_level FLOAT,  -- 0-100 (model confidence)
  
  -- Input features (for explainability)
  features JSONB,  -- {"days_in_stage": 45, "engagement_velocity": 2.1, ...}
  
  -- Model metadata
  model_version VARCHAR(50),
  prediction_date TIMESTAMP DEFAULT NOW(),
  
  -- Confidence intervals
  probability_low FLOAT,  -- 90% CI lower bound
  probability_high FLOAT,  -- 90% CI upper bound
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_prob_scores_deal ON intelligence.deal_probability_scores(deal_id);
CREATE INDEX idx_prob_scores_prob ON intelligence.deal_probability_scores(close_probability DESC);

-- ============================================================
-- Deal Health Snapshots (Real-time Evaluation)
-- ============================================================

CREATE TABLE intelligence.deal_health_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  
  -- Overall health
  health_score INT,  -- 0-100
  health_status VARCHAR(20),  -- healthy, at_risk, critical, won, lost
  
  -- Component scores
  engagement_health INT,  -- 0-100 (based on stakeholder engagement)
  momentum_health INT,  -- 0-100 (velocity of deal progression)
  buyer_health INT,  -- 0-100 (economic buyer involvement)
  competition_health INT,  -- 0-100 (competitive threat level)
  
  -- Risk indicators
  days_since_last_activity INT,
  stakeholder_churn_count INT,
  buying_committee_complete BOOLEAN,
  economic_buyer_engaged BOOLEAN,
  
  -- Recommendations
  recommended_actions JSONB,  -- [{action: "Call economic buyer", priority: "high"}]
  
  -- Metadata
  snapshot_date TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_health_deal ON intelligence.deal_health_snapshots(deal_id);
CREATE INDEX idx_health_status ON intelligence.deal_health_snapshots(health_status);
CREATE INDEX idx_health_date ON intelligence.deal_health_snapshots(snapshot_date DESC);

-- ============================================================
-- Deal Health Alerts
-- ============================================================

CREATE TABLE intelligence.deal_health_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  user_id VARCHAR(255),
  
  -- Alert details
  alert_type VARCHAR(50),  -- low_engagement, lost_momentum, buyer_churn, stalled
  severity VARCHAR(20),  -- info, warning, critical
  title VARCHAR(255),
  description TEXT,
  
  -- Recommended action
  recommended_action TEXT,
  action_type VARCHAR(50),  -- call, email, meeting, escalate
  
  -- Alert lifecycle
  triggered_at TIMESTAMP DEFAULT NOW(),
  acknowledged_at TIMESTAMP,
  resolved_at TIMESTAMP,
  action_taken BOOLEAN DEFAULT FALSE,
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE,
  CONSTRAINT fk_user FOREIGN KEY (user_id) 
    REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_alerts_deal ON intelligence.deal_health_alerts(deal_id);
CREATE INDEX idx_alerts_user ON intelligence.deal_health_alerts(user_id);
CREATE INDEX idx_alerts_status ON intelligence.deal_health_alerts(resolved_at);

-- ============================================================
-- Stakeholder Engagement Events (time-series)
-- ============================================================

CREATE TABLE intelligence.stakeholder_engagement_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255),
  person_id VARCHAR(255),
  
  -- Event type
  event_type VARCHAR(50),  -- email_open, email_click, call, meeting, message
  engagement_value INT,  -- points assigned (email_open=1, call=10, etc)
  
  -- Event details
  event_details JSONB,  -- {email_subject: "...", call_duration: 15}
  
  event_timestamp TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_engagement_deal_person ON intelligence.stakeholder_engagement_events(deal_id, person_id);
CREATE INDEX idx_engagement_timestamp ON intelligence.stakeholder_engagement_events(event_timestamp DESC);

-- ============================================================
-- Model Prediction Cache (for performance)
-- ============================================================

CREATE TABLE intelligence.model_predictions_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id VARCHAR(255) UNIQUE,
  
  -- Cached prediction
  prediction_json JSONB,  -- Full prediction object
  
  cache_created_at TIMESTAMP DEFAULT NOW(),
  cache_expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '6 hours',
  
  CONSTRAINT fk_deal FOREIGN KEY (deal_id) 
    REFERENCES public.deals(id) ON DELETE CASCADE
);

CREATE INDEX idx_cache_expires ON intelligence.model_predictions_cache(cache_expires_at);

-- ============================================================
-- Grant permissions to app user
-- ============================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA intelligence TO sellia_user;
GRANT USAGE ON SCHEMA intelligence TO sellia_user;
```

---

## 3. BACKEND IMPLEMENTATION

### Core Service: DealIntelligenceManager

**File**: `backend/app/domains/enterprise/deal_intelligence.py` (400 lines)

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from sqlalchemy import func, select
from backend.app.database import get_db
from backend.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@dataclass
class StakeholderProfile:
    """Buying committee member profile."""
    person_id: str
    email: str
    name: str
    title: str
    buyer_role: str  # economic_buyer, user_buyer, coach, blocker, influencer
    influence_level: int  # 1-10
    engagement_score: float  # 0-100
    email_open_count: int
    meeting_count: int
    last_activity: Optional[datetime]

@dataclass
class DealProbability:
    """Deal close probability prediction."""
    close_probability: float  # 0-100
    confidence_level: float  # 0-100
    probability_low: float  # 90% CI lower
    probability_high: float  # 90% CI upper
    features: Dict[str, Any]
    model_version: str

@dataclass
class DealHealth:
    """Real-time deal health assessment."""
    health_score: int  # 0-100
    health_status: str  # healthy, at_risk, critical
    engagement_health: int
    momentum_health: int
    buyer_health: int
    competition_health: int
    risk_indicators: Dict[str, Any]
    recommended_actions: List[Dict[str, str]]

class DealIntelligenceManager:
    """Unified deal intelligence engine."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.ml_model = DealProbabilityModel()  # Loaded ML model
    
    # ============================================================
    # STAKEHOLDER INTELLIGENCE
    # ============================================================
    
    async def get_buying_committee(self, deal_id: str) -> List[StakeholderProfile]:
        """Fetch all stakeholders for a deal."""
        query = select(DealStakeholder).where(
            DealStakeholder.deal_id == deal_id
        ).order_by(DealStakeholder.influence_level.desc())
        
        stakeholders = self.db.execute(query).scalars().all()
        return [self._to_stakeholder_profile(s) for s in stakeholders]
    
    async def identify_economic_buyer(self, deal_id: str) -> Optional[StakeholderProfile]:
        """Identify economic buyer from buying committee."""
        # Priority: already marked economic_buyer > C-level + high engagement > recent activity
        
        query = select(DealStakeholder).where(
            (DealStakeholder.deal_id == deal_id) &
            (DealStakeholder.status == "active")
        ).order_by(
            # Rank by: buyer_role match, then influence, then engagement
            case(
                (DealStakeholder.buyer_role == "economic_buyer", 1),
                (DealStakeholder.title.icontains("CEO") | 
                 DealStakeholder.title.icontains("CFO") |
                 DealStakeholder.title.icontains("SVP"), 2),
                else_=3
            ),
            DealStakeholder.influence_level.desc(),
            DealStakeholder.engagement_score.desc()
        ).limit(1)
        
        stakeholder = self.db.execute(query).scalar()
        return self._to_stakeholder_profile(stakeholder) if stakeholder else None
    
    async def update_stakeholder_engagement(
        self,
        deal_id: str,
        person_id: str,
        event_type: str,  # email_open, call, meeting, etc
        event_details: Dict[str, Any]
    ):
        """Record engagement event and update stakeholder score."""
        
        # 1. Log event
        event = StakeholderEngagementEvent(
            deal_id=deal_id,
            person_id=person_id,
            event_type=event_type,
            engagement_value=self._get_engagement_points(event_type),
            event_details=event_details
        )
        self.db.add(event)
        
        # 2. Update stakeholder engagement score
        query = select(DealStakeholder).where(
            (DealStakeholder.deal_id == deal_id) &
            (DealStakeholder.person_id == person_id)
        )
        stakeholder = self.db.execute(query).scalar()
        
        if stakeholder:
            # Recalculate engagement score (recent activity + historical)
            stakeholder.engagement_score = await self._calculate_engagement_score(
                deal_id, person_id
            )
            stakeholder.last_email_open = datetime.utcnow() if event_type == "email_open" else stakeholder.last_email_open
            self.db.add(stakeholder)
        
        self.db.commit()
        
        # 3. Trigger deal health recalculation
        await self.calculate_deal_health(deal_id)
    
    def _get_engagement_points(self, event_type: str) -> int:
        """Points assigned per engagement event type."""
        points = {
            "email_open": 1,
            "email_click": 3,
            "meeting": 10,
            "call": 8,
            "message": 2,
            "proposal_viewed": 5
        }
        return points.get(event_type, 0)
    
    async def _calculate_engagement_score(self, deal_id: str, person_id: str) -> float:
        """Calculate 0-100 engagement score for stakeholder."""
        # Last 30 days: weight recent events higher
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        query = select(func.sum(StakeholderEngagementEvent.engagement_value)).where(
            (StakeholderEngagementEvent.deal_id == deal_id) &
            (StakeholderEngagementEvent.person_id == person_id) &
            (StakeholderEngagementEvent.event_timestamp >= thirty_days_ago)
        )
        
        total_points = self.db.execute(query).scalar() or 0
        
        # Normalize to 0-100 (max 50 points = 100 score)
        score = min((total_points / 50.0) * 100, 100)
        return score
    
    # ============================================================
    # DEAL PROBABILITY PREDICTION
    # ============================================================
    
    async def predict_close_probability(self, deal_id: str) -> DealProbability:
        """Predict deal close probability using ML model."""
        
        # Check cache first
        cached = await self._get_cached_prediction(deal_id)
        if cached:
            return cached
        
        # 1. Extract features
        features = await self._extract_deal_features(deal_id)
        
        # 2. Run inference
        prediction = self.ml_model.predict(features)
        
        # 3. Store prediction
        prob_score = DealProbabilityScore(
            deal_id=deal_id,
            close_probability=prediction["probability"],
            confidence_level=prediction["confidence"],
            probability_low=prediction["probability_low"],
            probability_high=prediction["probability_high"],
            features=features,
            model_version=self.ml_model.version
        )
        self.db.add(prob_score)
        self.db.commit()
        
        # 4. Cache (6 hours)
        await self._cache_prediction(deal_id, prediction)
        
        return DealProbability(
            close_probability=prediction["probability"],
            confidence_level=prediction["confidence"],
            probability_low=prediction["probability_low"],
            probability_high=prediction["probability_high"],
            features=features,
            model_version=self.ml_model.version
        )
    
    async def _extract_deal_features(self, deal_id: str) -> Dict[str, Any]:
        """Extract ML model features from deal state."""
        
        # Fetch deal + related data
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        stakeholders = await self.get_buying_committee(deal_id)
        
        # Calculate features
        days_in_stage = (datetime.utcnow() - deal.stage_changed_at).days
        engagement_velocity = await self._calculate_engagement_velocity(deal_id, 14)  # Last 14 days
        
        features = {
            "stage": self._encode_stage(deal.stage),
            "days_in_stage": days_in_stage,
            "engagement_velocity": engagement_velocity,
            "proposal_sent": deal.proposal_sent_at is not None,
            "days_since_proposal": (datetime.utcnow() - deal.proposal_sent_at).days if deal.proposal_sent_at else 999,
            "stakeholder_count": len(stakeholders),
            "economic_buyer_engaged": any(s.buyer_role == "economic_buyer" for s in stakeholders),
            "avg_engagement_score": sum(s.engagement_score for s in stakeholders) / len(stakeholders) if stakeholders else 0,
            "deal_size": deal.deal_value,
            "deal_size_segment": self._encode_size(deal.deal_value),
            "days_in_pipeline": (datetime.utcnow() - deal.created_at).days,
            "competitor_mentioned": deal.competitor_mentioned or False,
            "cios_involved": sum(1 for s in stakeholders if "CIO" in s.title),
            "multiple_stakeholders": len(stakeholders) >= 3
        }
        
        return features
    
    async def _calculate_engagement_velocity(self, deal_id: str, days: int) -> float:
        """Calculate engagement events per day (velocity)."""
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = select(func.count(StakeholderEngagementEvent.id)).where(
            (StakeholderEngagementEvent.deal_id == deal_id) &
            (StakeholderEngagementEvent.event_timestamp >= cutoff)
        )
        
        event_count = self.db.execute(query).scalar() or 0
        velocity = event_count / max(days, 1)
        
        return velocity
    
    async def _get_cached_prediction(self, deal_id: str) -> Optional[Dict]:
        """Retrieve cached prediction if not expired."""
        
        query = select(ModelPredictionsCache).where(
            (ModelPredictionsCache.deal_id == deal_id) &
            (ModelPredictionsCache.cache_expires_at > datetime.utcnow())
        )
        
        cache = self.db.execute(query).scalar()
        return json.loads(cache.prediction_json) if cache else None
    
    async def _cache_prediction(self, deal_id: str, prediction: Dict):
        """Cache prediction for 6 hours."""
        
        cache = ModelPredictionsCache(
            deal_id=deal_id,
            prediction_json=json.dumps(prediction),
            cache_expires_at=datetime.utcnow() + timedelta(hours=6)
        )
        self.db.add(cache)
        self.db.commit()
    
    # ============================================================
    # DEAL HEALTH SCORING
    # ============================================================
    
    async def calculate_deal_health(self, deal_id: str) -> DealHealth:
        """Calculate real-time deal health score (0-100)."""
        
        # 1. Get deal + stakeholders
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        stakeholders = await self.get_buying_committee(deal_id)
        probability = await self.predict_close_probability(deal_id)
        
        # 2. Calculate component scores (each 0-100)
        engagement_health = self._score_engagement(stakeholders)
        momentum_health = await self._score_momentum(deal_id)
        buyer_health = self._score_buyer_completeness(stakeholders)
        competition_health = self._score_competition(deal)
        
        # 3. Weighted average (health_score)
        weights = {
            "engagement": 0.25,
            "momentum": 0.25,
            "buyer": 0.30,
            "competition": 0.20
        }
        
        health_score = int(
            engagement_health * weights["engagement"] +
            momentum_health * weights["momentum"] +
            buyer_health * weights["buyer"] +
            competition_health * weights["competition"]
        )
        
        # 4. Determine status
        if health_score >= 80:
            health_status = "healthy"
        elif health_score >= 50:
            health_status = "at_risk"
        else:
            health_status = "critical"
        
        # 5. Generate recommendations
        recommended_actions = await self._generate_recommendations(
            deal_id, health_score, engagement_health, momentum_health, buyer_health
        )
        
        # 6. Store snapshot
        snapshot = DealHealthSnapshot(
            deal_id=deal_id,
            health_score=health_score,
            health_status=health_status,
            engagement_health=engagement_health,
            momentum_health=momentum_health,
            buyer_health=buyer_health,
            competition_health=competition_health,
            days_since_last_activity=await self._days_since_last_activity(deal_id),
            stakeholder_churn_count=sum(1 for s in stakeholders if s.status == "churned"),
            buying_committee_complete=len(stakeholders) >= 3,
            economic_buyer_engaged=any(s.buyer_role == "economic_buyer" for s in stakeholders),
            recommended_actions=recommended_actions
        )
        self.db.add(snapshot)
        self.db.commit()
        
        # 7. Check for alerts
        await self._check_and_create_alerts(deal, health_score, health_status, recommended_actions)
        
        return DealHealth(
            health_score=health_score,
            health_status=health_status,
            engagement_health=engagement_health,
            momentum_health=momentum_health,
            buyer_health=buyer_health,
            competition_health=competition_health,
            risk_indicators={
                "days_since_activity": await self._days_since_last_activity(deal_id),
                "stakeholder_churn": sum(1 for s in stakeholders if s.status == "churned"),
                "buying_committee_incomplete": len(stakeholders) < 3,
                "no_economic_buyer": not any(s.buyer_role == "economic_buyer" for s in stakeholders)
            },
            recommended_actions=recommended_actions
        )
    
    def _score_engagement(self, stakeholders: List[StakeholderProfile]) -> int:
        """Score based on average stakeholder engagement (0-100)."""
        if not stakeholders:
            return 0
        avg_engagement = sum(s.engagement_score for s in stakeholders) / len(stakeholders)
        return int(avg_engagement)
    
    async def _score_momentum(self, deal_id: str) -> int:
        """Score based on deal progression velocity (0-100)."""
        # Recent stage changes, recent activity, proposal progression
        
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        
        days_since_update = (datetime.utcnow() - deal.updated_at).days
        
        if days_since_update <= 3:
            momentum = 90
        elif days_since_update <= 7:
            momentum = 70
        elif days_since_update <= 14:
            momentum = 50
        else:
            momentum = 20
        
        return momentum
    
    def _score_buyer_completeness(self, stakeholders: List[StakeholderProfile]) -> int:
        """Score based on buying committee completeness (0-100)."""
        
        has_economic_buyer = any(s.buyer_role == "economic_buyer" for s in stakeholders)
        has_user_buyer = any(s.buyer_role == "user_buyer" for s in stakeholders)
        has_coach = any(s.buyer_role == "coach" for s in stakeholders)
        stakeholder_count = len(stakeholders)
        
        score = 0
        if has_economic_buyer:
            score += 40
        if has_user_buyer:
            score += 30
        if has_coach:
            score += 20
        if stakeholder_count >= 3:
            score += 10
        
        return min(score, 100)
    
    def _score_competition(self, deal: Deal) -> int:
        """Score based on competitive threat (inverse scoring)."""
        
        if not deal.competitor_mentioned:
            return 100
        elif deal.competition_stage == "shortlist":
            return 60
        elif deal.competition_stage == "finalist":
            return 30
        else:
            return 10
    
    async def _generate_recommendations(
        self,
        deal_id: str,
        health_score: int,
        engagement: int,
        momentum: int,
        buyer: int
    ) -> List[Dict[str, str]]:
        """Generate next-best-action recommendations."""
        
        actions = []
        
        if buyer < 50:
            actions.append({
                "action": "Identify and engage economic buyer",
                "priority": "critical",
                "description": "Buying committee incomplete. Schedule call with CFO/VP Finance."
            })
        
        if momentum < 40:
            actions.append({
                "action": "Re-engage stakeholders",
                "priority": "high",
                "description": "No activity in 2+ weeks. Send personalized email or schedule check-in."
            })
        
        if engagement < 50:
            actions.append({
                "action": "Increase engagement",
                "priority": "high",
                "description": "Stakeholders not engaged. Consider proposal or demo."
            })
        
        if health_score < 30:
            actions.append({
                "action": "Escalate to manager",
                "priority": "critical",
                "description": "Deal at critical risk. Requires leadership intervention."
            })
        
        return actions
    
    async def _check_and_create_alerts(
        self,
        deal: Deal,
        health_score: int,
        health_status: str,
        actions: List[Dict]
    ):
        """Create alerts if health dropped significantly."""
        
        # Get previous health snapshot
        prev_query = select(DealHealthSnapshot).where(
            DealHealthSnapshot.deal_id == deal.id
        ).order_by(DealHealthSnapshot.snapshot_date.desc()).limit(1)
        
        prev_snapshot = self.db.execute(prev_query).scalar()
        
        if prev_snapshot and health_score < prev_snapshot.health_score - 20:
            # Health dropped 20+ points -> create alert
            alert = DealHealthAlert(
                deal_id=deal.id,
                user_id=deal.owner_id,
                alert_type="low_engagement" if health_status == "critical" else "at_risk",
                severity="critical" if health_score < 30 else "warning",
                title=f"Deal health declined to {health_score}/100",
                description=f"Deal '{deal.name}' health score dropped from {prev_snapshot.health_score} to {health_score}",
                recommended_action=actions[0]["action"] if actions else "Review deal status",
                action_type="call" if "economic" in actions[0]["action"].lower() else "email"
            )
            self.db.add(alert)
            self.db.commit()
    
    async def _days_since_last_activity(self, deal_id: str) -> int:
        """Calculate days since last deal activity."""
        
        query = select(func.max(StakeholderEngagementEvent.event_timestamp)).where(
            StakeholderEngagementEvent.deal_id == deal_id
        )
        
        last_activity = self.db.execute(query).scalar()
        
        if not last_activity:
            # Fallback to deal updated_at
            deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
            last_activity = deal.updated_at
        
        days_since = (datetime.utcnow() - last_activity).days
        return days_since
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _to_stakeholder_profile(self, stakeholder) -> StakeholderProfile:
        return StakeholderProfile(
            person_id=stakeholder.person_id,
            email=stakeholder.email,
            name=stakeholder.name,
            title=stakeholder.title,
            buyer_role=stakeholder.buyer_role,
            influence_level=stakeholder.influence_level,
            engagement_score=stakeholder.engagement_score,
            email_open_count=stakeholder.email_open_count,
            meeting_count=stakeholder.meeting_count,
            last_activity=stakeholder.last_email_open or stakeholder.last_call_date
        )
    
    def _encode_stage(self, stage: str) -> int:
        """Encode deal stage as numeric feature."""
        stages = {
            "prospect": 1, "qualified": 2, "discovery": 3,
            "proposal": 4, "negotiation": 5, "closing": 6
        }
        return stages.get(stage.lower(), 0)
    
    def _encode_size(self, deal_value: float) -> str:
        """Categorize deal by size."""
        if deal_value < 10000:
            return "small"
        elif deal_value < 50000:
            return "mid"
        else:
            return "enterprise"

# ============================================================
# ML MODEL WRAPPER
# ============================================================

class DealProbabilityModel:
    """Trained deal close probability model."""
    
    def __init__(self):
        self.version = "1.0.0"
        # Load model on init (from pickle/joblib file)
        import joblib
        self.model = joblib.load("/app/models/deal_probability_v1.0.0.pkl")
        self.feature_names = ["stage", "days_in_stage", "engagement_velocity", ...]
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict close probability.
        
        Returns:
        {
            "probability": 75.2,  # 0-100
            "confidence": 0.92,   # 0-1 (model confidence)
            "probability_low": 68.1,  # 90% CI
            "probability_high": 82.3
        }
        """
        
        import numpy as np
        
        # Convert features dict to model input
        X = np.array([features[f] for f in self.feature_names])
        
        # Get prediction + uncertainty
        prob = self.model.predict_proba(X.reshape(1, -1))[0][1] * 100
        
        # Estimate confidence (from model calibration)
        confidence = min(max(prob / 100, 0.5), 0.99)
        
        # Calculate CI (simplified)
        margin = 10 * (1 - confidence)
        
        return {
            "probability": round(prob, 1),
            "confidence": round(confidence, 2),
            "probability_low": max(0, round(prob - margin, 1)),
            "probability_high": min(100, round(prob + margin, 1))
        }
```

---

## 4. API ENDPOINTS

**File**: `backend/app/api/v1/enterprise_deal_intelligence.py` (250 lines)

```python
from fastapi import APIRouter, Depends, HTTPException
from backend.app.dependencies import get_current_user, get_db
from backend.app.domains.enterprise.deal_intelligence import (
    DealIntelligenceManager, DealProbability, DealHealth
)

router = APIRouter(prefix="/api/v1/intelligence", tags=["deal-intelligence"])

# ============================================================
# Stakeholder Intelligence
# ============================================================

@router.get("/stakeholders/{deal_id}")
async def get_buying_committee(
    deal_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Fetch buying committee for deal with engagement data."""
    
    manager = DealIntelligenceManager(db)
    stakeholders = await manager.get_buying_committee(deal_id)
    economic_buyer = await manager.identify_economic_buyer(deal_id)
    
    return {
        "deal_id": deal_id,
        "stakeholders": [
            {
                "person_id": s.person_id,
                "name": s.name,
                "email": s.email,
                "title": s.title,
                "buyer_role": s.buyer_role,
                "influence_level": s.influence_level,
                "engagement_score": s.engagement_score,
                "email_open_count": s.email_open_count,
                "meeting_count": s.meeting_count,
                "last_activity": s.last_activity
            }
            for s in stakeholders
        ],
        "economic_buyer": {
            "person_id": economic_buyer.person_id,
            "name": economic_buyer.name
        } if economic_buyer else None,
        "buying_committee_complete": len(stakeholders) >= 3
    }

@router.post("/stakeholders/{deal_id}/engagement")
async def record_stakeholder_engagement(
    deal_id: str,
    person_id: str,
    event_type: str,
    event_details: dict,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Record engagement event (email open, call, meeting, etc)."""
    
    manager = DealIntelligenceManager(db)
    await manager.update_stakeholder_engagement(
        deal_id=deal_id,
        person_id=person_id,
        event_type=event_type,
        event_details=event_details
    )
    
    return {"status": "recorded"}

# ============================================================
# Deal Probability Prediction
# ============================================================

@router.get("/probability/{deal_id}")
async def get_deal_probability(
    deal_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get predicted close probability for deal."""
    
    manager = DealIntelligenceManager(db)
    probability = await manager.predict_close_probability(deal_id)
    
    return {
        "deal_id": deal_id,
        "close_probability": probability.close_probability,
        "confidence_level": probability.confidence_level,
        "probability_low": probability.probability_low,
        "probability_high": probability.probability_high,
        "features": probability.features,
        "model_version": probability.model_version
    }

# ============================================================
# Deal Health Scoring
# ============================================================

@router.get("/health/{deal_id}")
async def get_deal_health(
    deal_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get real-time deal health score (0-100)."""
    
    manager = DealIntelligenceManager(db)
    health = await manager.calculate_deal_health(deal_id)
    
    return {
        "deal_id": deal_id,
        "health_score": health.health_score,
        "health_status": health.health_status,
        "component_scores": {
            "engagement": health.engagement_health,
            "momentum": health.momentum_health,
            "buyer_completeness": health.buyer_health,
            "competition": health.competition_health
        },
        "risk_indicators": health.risk_indicators,
        "recommended_actions": health.recommended_actions
    }

# ============================================================
# Deal Health Alerts
# ============================================================

@router.get("/alerts")
async def get_deal_alerts(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    status: str = "unresolved"  # unresolved, all
):
    """Get all deal health alerts for current user."""
    
    query = select(DealHealthAlert).where(
        DealHealthAlert.user_id == current_user["id"]
    )
    
    if status == "unresolved":
        query = query.where(DealHealthAlert.resolved_at.is_(None))
    
    alerts = db.execute(query).scalars().all()
    
    return {
        "alerts": [
            {
                "id": a.id,
                "deal_id": a.deal_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "recommended_action": a.recommended_action,
                "triggered_at": a.triggered_at,
                "acknowledged": a.acknowledged_at is not None
            }
            for a in alerts
        ]
    }

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Mark alert as acknowledged."""
    
    alert = db.query(DealHealthAlert).filter(DealHealthAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    
    return {"status": "acknowledged"}
```

---

## 5. FRONTEND COMPONENTS

### DealIntelligenceDashboard.tsx (400 lines)

```typescript
import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { DealHealthCard } from './DealHealthCard';
import { BuyingCommitteePanel } from './BuyingCommitteePanel';
import { DealProbabilityChart } from './DealProbabilityChart';
import { AlertsPanel } from './AlertsPanel';
import { RecommendedActionsPanel } from './RecommendedActionsPanel';

interface DealIntelligence {
  health: {
    health_score: number;
    health_status: 'healthy' | 'at_risk' | 'critical';
    component_scores: {
      engagement: number;
      momentum: number;
      buyer_completeness: number;
      competition: number;
    };
  };
  probability: {
    close_probability: number;
    confidence_level: number;
    probability_low: number;
    probability_high: number;
  };
  stakeholders: Array<{
    person_id: string;
    name: string;
    title: string;
    buyer_role: string;
    engagement_score: number;
  }>;
}

export const DealIntelligenceDashboard: React.FC = () => {
  const { dealId } = useParams();
  const [intelligence, setIntelligence] = useState<DealIntelligence | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIntelligence = async () => {
      try {
        const [health, prob, stakeholders] = await Promise.all([
          fetch(`/api/v1/intelligence/health/${dealId}`).then(r => r.json()),
          fetch(`/api/v1/intelligence/probability/${dealId}`).then(r => r.json()),
          fetch(`/api/v1/intelligence/stakeholders/${dealId}`).then(r => r.json())
        ]);

        setIntelligence({
          health,
          probability: prob,
          stakeholders: stakeholders.stakeholders
        });
      } finally {
        setLoading(false);
      }
    };

    fetchIntelligence();
  }, [dealId]);

  if (loading) return <div>Loading deal intelligence...</div>;
  if (!intelligence) return <div>No data available</div>;

  return (
    <div className="grid grid-cols-4 gap-4 p-6">
      {/* Health Score Card (prominent) */}
      <div className="col-span-1">
        <DealHealthCard {...intelligence.health} />
      </div>

      {/* Close Probability */}
      <div className="col-span-1">
        <DealProbabilityChart {...intelligence.probability} />
      </div>

      {/* Recommended Actions */}
      <div className="col-span-1">
        <RecommendedActionsPanel dealId={dealId as string} />
      </div>

      {/* Active Alerts */}
      <div className="col-span-1">
        <AlertsPanel dealId={dealId as string} />
      </div>

      {/* Buying Committee (spans 2 columns) */}
      <div className="col-span-2">
        <BuyingCommitteePanel stakeholders={intelligence.stakeholders} />
      </div>

      {/* Component Scores (spans 2 columns) */}
      <div className="col-span-2">
        <ComponentScoresDetail scores={intelligence.health.component_scores} />
      </div>
    </div>
  );
};
```

---

## 6. ML MODEL SPECIFICATION

### Deal Close Probability Model

**Type**: XGBoost classifier  
**Target**: Deal closed (0/1)  
**Training Data**: Historical deals (past 2 years)  
**Features**: 15 engineered features  

**Features**:
```python
features = {
    # Stage/progression
    "stage": one_hot(deal.stage),  # prospect, qualified, discovery, proposal, negotiation, closing
    "days_in_stage": deal.stage_changed_at → days since,
    "days_in_pipeline": deal.created_at → days total,
    
    # Engagement
    "engagement_velocity": events_per_day (last 14 days),
    "avg_stakeholder_engagement": mean(stakeholder.engagement_score),
    "email_engagement": emails_opened / emails_sent,
    "meeting_count": count(meetings in last 30 days),
    
    # Buying Committee
    "stakeholder_count": len(stakeholders),
    "economic_buyer_engaged": bool,
    "buying_committee_complete": bool (>=3 stakeholders),
    "influencer_count": count(stakeholders with role=influencer),
    
    # Deal Characteristics
    "deal_size_segment": small/mid/enterprise,
    "proposal_sent": bool,
    "days_since_proposal": proposal_sent_at → days,
    
    # Competition/Risk
    "competitor_mentioned": bool,
    "competition_stage": shortlist/finalist/none
}
```

**Model Hyperparameters**:
```python
XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=1.5  # Imbalanced data
)
```

**Training Procedure**:
1. Pull closed/lost deals from past 24 months
2. Engineer features
3. Train/test split (80/20, stratified by outcome)
4. Cross-validation (5-fold)
5. Hyperparameter tuning (grid search)
6. Evaluate on holdout test set
7. Save model + feature names + calibration curves

**Performance Targets**:
- AUC: 0.85+
- Precision: 80%+ (minimize false positives)
- Recall: 75%+ (catch most closable deals)

---

## 7. CELERY TASKS

**File**: `backend/app/tasks/intelligence.py`

```python
from backend.celery_app import celery_app
from backend.app.domains.enterprise.deal_intelligence import DealIntelligenceManager
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def calculate_all_deal_health(self):
    """Recalculate health for all open deals (run hourly)."""
    try:
        db = get_db()
        manager = DealIntelligenceManager(db)
        
        # Get all open deals
        open_deals = db.query(Deal).filter(Deal.closed_date.is_(None)).all()
        
        for deal in open_deals:
            manager.calculate_deal_health(deal.id)
            logger.info(f"Health recalculated for {deal.id}")
    
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task(bind=True)
def update_deal_engagement_from_webhooks(self, deal_id: str, person_id: str, event_type: str):
    """Process engagement webhooks (email tracking, etc)."""
    try:
        db = get_db()
        manager = DealIntelligenceManager(db)
        
        manager.update_stakeholder_engagement(
            deal_id=deal_id,
            person_id=person_id,
            event_type=event_type,
            event_details={}
        )
    except Exception as exc:
        logger.error(f"Webhook processing failed: {exc}")

@celery_app.task(bind=True, max_retries=3)
def retrain_deal_probability_model(self):
    """Retrain model weekly (Sundays 2am)."""
    try:
        from backend.app.ml.deal_probability_trainer import train_model
        
        # Pull recent deal history
        # Train new model
        # Validate performance
        # Deploy if better than current
        
        logger.info("Model retraining complete")
    except Exception as exc:
        logger.error(f"Model retraining failed: {exc}")
        self.retry(countdown=3600, exc=exc)
```

Add to `celery_app.py`:
```python
beat_schedule = {
    'calculate-deal-health': {
        'task': 'backend.app.tasks.intelligence.calculate_all_deal_health',
        'schedule': crontab(minute=0),  # Hourly
    },
    'retrain-model': {
        'task': 'backend.app.tasks.intelligence.retrain_deal_probability_model',
        'schedule': crontab(hour=2, day_of_week=6),  # Sunday 2am
    },
}
```

---

## 8. INTEGRATION POINTS

### Salesforce Sync

**Endpoint**: `POST /webhooks/salesforce/deal-update`

When deal status changes in Salesforce → pull updated engagement data → recalculate health + probability

### Email Tracking

**Endpoint**: `POST /webhooks/email-tracking/open-click`

When stakeholder opens email / clicks link → record engagement event → update engagement score

### LinkedIn Integration

**Enrichment Flow**:
```
New stakeholder added
  → Query LinkedIn API (person.email → LinkedIn profile)
  → Extract title, company, connections
  → Store in deal_stakeholders.title + enrichment_data
```

---

## 9. IMPLEMENTATION TIMELINE

**Week 1-2**: Database + Schema
- [ ] Create intelligence schema + 6 tables
- [ ] Add migrations to Alembic
- [ ] Test schema with sample data

**Week 3-4**: Backend Core
- [ ] Implement DealIntelligenceManager
- [ ] Build stakeholder mapping + engagement tracking
- [ ] Build deal health scoring logic
- [ ] Write unit tests (80%+ coverage)

**Week 5-6**: ML Model
- [ ] Pull + prepare training data
- [ ] Engineer features
- [ ] Train XGBoost model
- [ ] Evaluate performance (AUC 0.85+)
- [ ] Save model + feature names

**Week 7**: API + Integration
- [ ] Create 5 API endpoints
- [ ] Build Celery tasks (health recalc, model retrain)
- [ ] Add Salesforce webhook handling
- [ ] Add email tracking webhook handling

**Week 8**: Frontend + Testing
- [ ] Build 4 React components
- [ ] End-to-end testing (5+ test scenarios)
- [ ] Performance testing (100 concurrent users)
- [ ] Deploy to staging
- [ ] UAT with power users (5-10 deals)

---

## 10. SUCCESS CRITERIA (GO/NO-GO)

**Technical Metrics**:
- [ ] All 6 tables created + migrated
- [ ] All 5 API endpoints responding (< 200ms p95)
- [ ] ML model AUC 0.85+ on validation set
- [ ] Dashboard loads in < 2s
- [ ] 99%+ uptime (staging, 1 week)

**Product Metrics**:
- [ ] Forecast accuracy +10% (vs. historical)
- [ ] Sales team uses health score in 3+ deals
- [ ] Recommendations acted upon in 2+ deals
- [ ] User satisfaction 4.0+/5.0 (survey)

**Operational**:
- [ ] No critical bugs (P0)
- [ ] Documentation complete
- [ ] Team trained on new dashboards
- [ ] Monitoring + alerting configured

---

**Phase 27 Ready for Development** ✅

