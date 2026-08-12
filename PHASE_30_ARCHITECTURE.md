# Phase 30 - Retention: Churn Prevention + Intent ABM Architecture

**Duration**: 5 weeks (Weeks 25-29)  
**Team Size**: 1 backend engineer + 1 ML engineer  
**Expected Impact**: -30% churn, +50-80% warm pipeline  
**Prerequisites**: Phase 27-29 (deal intelligence, email, voice, playbooks)

---

## STRATEGIC OVERVIEW

Phase 30 implements 2 customer retention systems:

1. **Churn Prediction Engine** - ML model predicts customer churn risk (0-100 score)
2. **Intent-Based Account Scoring** - Identify expansion opportunities + at-risk accounts

Both systems feed into automated win-back campaigns + account team routing.

---

## 1. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND (React 19)                     │
│  Churn Risk Dashboard | Account Health | ABM Pipeline   │
│  Win-back Campaign Manager | LTV Forecasts              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              API LAYER (FastAPI)                        │
│  /api/v1/retention/churn-risk/{customer_id}             │
│  /api/v1/retention/expansion/{account_id}               │
│  /api/v1/retention/winback/{customer_id}                │
│  /api/v1/retention/accounts (intent scoring)            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          BUSINESS LOGIC (Python Services)               │
│  ChurnPredictor (ML model + risk scoring)               │
│  ExpansionOpportunityFinder (expansion triggers)        │
│  WinBackOrchestrator (retention campaigns)              │
│  IntentScorer (account health + ABM scoring)            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           DATA LAYER (PostgreSQL + Redis)               │
│  customer_health | churn_risk_scores | expansion_opps   │
│  account_intent_signals | winback_campaigns             │
│  customer_lifecycle | retention_metrics                 │
└─────────────────────────────────────────────────────────┘
```

---

## 2. DATABASE SCHEMA

### Retention Tables

```sql
CREATE SCHEMA retention;

-- ============================================================
-- CUSTOMER HEALTH & CHURN PREDICTION
-- ============================================================

CREATE TABLE retention.customer_health (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id VARCHAR(255) UNIQUE,
  
  -- Core metrics
  arr FLOAT,  -- Annual Recurring Revenue
  mrr FLOAT,  -- Monthly Recurring Revenue
  net_retention_rate FLOAT,  -- 100% = no churn
  
  -- Engagement metrics
  active_users INT,
  monthly_active_users INT,
  feature_adoption_score FLOAT,  -- 0-100
  support_ticket_volume INT,
  nps_score INT,  -- Net Promoter Score (-100 to 100)
  
  -- Usage patterns
  days_since_last_login INT,
  avg_monthly_login_count INT,
  feature_usage_breadth INT,  -- How many features used
  
  -- Financial health
  payment_failures INT,
  days_overdue INT,
  expansion_potential FLOAT,  -- 0-100 (likelihood to expand)
  
  -- Health status
  health_score FLOAT,  -- 0-100
  health_status VARCHAR(20),  -- healthy, at_risk, critical
  
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_customer FOREIGN KEY (customer_id) 
    REFERENCES public.customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_health_customer ON retention.customer_health(customer_id);
CREATE INDEX idx_health_status ON retention.customer_health(health_status);
CREATE INDEX idx_health_score ON retention.customer_health(health_score DESC);

-- Churn risk predictions
CREATE TABLE retention.churn_risk_predictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id VARCHAR(255),
  
  -- Prediction
  churn_probability FLOAT,  -- 0-100
  churn_risk_score FLOAT,  -- 0-100 (inverse of health)
  confidence_level FLOAT,  -- 0-1
  
  -- Risk factors (top 3)
  top_risk_factors JSONB,  -- [{factor: "no logins in 30d", impact: 25}]
  
  -- Recommended actions
  recommended_actions JSONB,  -- [{action: "executive check-in", urgency: "high"}]
  
  -- Model metadata
  model_version VARCHAR(50),
  prediction_date TIMESTAMP DEFAULT NOW(),
  churn_probability_low FLOAT,  -- 90% CI
  churn_probability_high FLOAT,
  
  CONSTRAINT fk_customer FOREIGN KEY (customer_id) 
    REFERENCES public.customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_churn_risk_customer ON retention.churn_risk_predictions(customer_id);
CREATE INDEX idx_churn_risk_prob ON retention.churn_risk_predictions(churn_probability DESC);

-- ============================================================
-- EXPANSION OPPORTUNITIES
-- ============================================================

CREATE TABLE retention.expansion_opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id VARCHAR(255),
  account_id VARCHAR(255),
  
  -- Opportunity details
  opportunity_type VARCHAR(50),  -- upsell, cross_sell, migration
  feature_gap VARCHAR(255),  -- "Missing X feature, could add $Y MRR"
  estimated_new_arr FLOAT,  -- Expected revenue if closed
  expansion_probability FLOAT,  -- 0-100
  
  -- Triggers
  trigger_reason VARCHAR(200),  -- "Usage of feature X increasing"
  trigger_confidence FLOAT,  -- 0-100
  
  -- Campaign
  campaign_status VARCHAR(50),  -- not_started, in_progress, completed, lost
  campaign_started TIMESTAMP,
  campaign_closed TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_customer FOREIGN KEY (customer_id) 
    REFERENCES public.customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_expansion_customer ON retention.expansion_opportunities(customer_id);
CREATE INDEX idx_expansion_type ON retention.expansion_opportunities(opportunity_type);

-- ============================================================
-- ACCOUNT INTENT SIGNALS (ABM)
-- ============================================================

CREATE TABLE retention.account_intent_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id VARCHAR(255),
  
  -- Intent signal
  signal_type VARCHAR(50),  -- expansion_signal, churn_signal, upgrade_interest
  signal_strength FLOAT,  -- 0-100
  
  -- Source
  detection_source VARCHAR(50),  -- usage_pattern, support_ticket, feature_request, billing
  signal_details VARCHAR(500),
  
  -- Timeline
  detected_at TIMESTAMP DEFAULT NOW(),
  last_observed TIMESTAMP,
  signal_frequency INT,  -- How many times detected
  
  CONSTRAINT fk_account FOREIGN KEY (account_id) 
    REFERENCES public.accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_intent_account ON retention.account_intent_signals(account_id);
CREATE INDEX idx_intent_type ON retention.account_intent_signals(signal_type);
CREATE INDEX idx_intent_strength ON retention.account_intent_signals(signal_strength DESC);

-- ============================================================
-- WIN-BACK CAMPAIGNS
-- ============================================================

CREATE TABLE retention.winback_campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id VARCHAR(255),
  
  -- Campaign details
  campaign_type VARCHAR(50),  -- churn_prevention, win_back, re_engagement
  trigger_reason VARCHAR(200),  -- "Churn risk 85%, no logins 60 days"
  
  -- Sequence
  email_sequence JSONB,  -- [{day: 0, subject: "...", body: "..."}, ...]
  executive_outreach_enabled BOOLEAN DEFAULT TRUE,
  
  -- Tracking
  started_at TIMESTAMP DEFAULT NOW(),
  ended_at TIMESTAMP,
  status VARCHAR(50),  -- active, paused, completed, successful, failed
  
  -- Results
  emails_sent INT DEFAULT 0,
  emails_opened INT DEFAULT 0,
  email_click_rate FLOAT,
  outreach_calls INT DEFAULT 0,
  calls_connected INT DEFAULT 0,
  
  -- Outcome
  customer_retained BOOLEAN,
  revenue_retained FLOAT,  -- ARR saved
  
  CONSTRAINT fk_customer FOREIGN KEY (customer_id) 
    REFERENCES public.customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_winback_customer ON retention.winback_campaigns(customer_id);
CREATE INDEX idx_winback_status ON retention.winback_campaigns(status);

-- ============================================================
-- CUSTOMER LIFECYCLE
-- ============================================================

CREATE TABLE retention.customer_lifecycle_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id VARCHAR(255),
  
  -- Event
  event_type VARCHAR(50),  -- onboarded, feature_adopted, churn_risk_detected, churned, reactivated
  event_details JSONB,
  
  event_timestamp TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_customer FOREIGN KEY (customer_id) 
    REFERENCES public.customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_lifecycle_customer ON retention.customer_lifecycle_events(customer_id);
CREATE INDEX idx_lifecycle_timestamp ON retention.customer_lifecycle_events(event_timestamp DESC);

-- ============================================================
-- Grants
-- ============================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA retention TO sellia_user;
```

---

## 3. CHURN PREDICTION ENGINE

**File**: `backend/app/services/retention/churn_predictor.py` (350 lines)

```python
from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
import joblib
from sqlalchemy import select
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

@dataclass
class ChurnPrediction:
    """Churn risk assessment."""
    churn_probability: float  # 0-100
    churn_risk_score: float  # 0-100 (inverse)
    confidence: float  # 0-1
    risk_factors: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]

class ChurnPredictor:
    """Predict customer churn risk."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.ml_model = ChurnModel()
    
    async def predict_churn_risk(self, customer_id: str) -> ChurnPrediction:
        """Predict churn probability for customer."""
        
        # Check cache
        cached = await self._get_cached_prediction(customer_id)
        if cached:
            return cached
        
        # Extract features
        features = await self._extract_customer_features(customer_id)
        
        # Run inference
        prediction = self.ml_model.predict(features)
        
        # Extract risk factors
        risk_factors = await self._identify_risk_factors(customer_id, features)
        
        # Generate recommendations
        actions = await self._generate_retention_actions(
            customer_id=customer_id,
            churn_prob=prediction["probability"],
            risk_factors=risk_factors
        )
        
        # Store prediction
        await self._store_prediction(
            customer_id=customer_id,
            prediction=prediction,
            risk_factors=risk_factors,
            actions=actions
        )
        
        return ChurnPrediction(
            churn_probability=prediction["probability"],
            churn_risk_score=100 - prediction["probability"],
            confidence=prediction["confidence"],
            risk_factors=risk_factors,
            recommended_actions=actions
        )
    
    async def _extract_customer_features(self, customer_id: str) -> Dict[str, Any]:
        """Extract features for churn prediction."""
        
        # Get customer health
        health = self.db.query(CustomerHealth).filter_by(
            customer_id=customer_id
        ).first()
        
        if not health:
            return {}
        
        # Calculate features
        features = {
            "arr": health.arr,
            "mrr": health.mrr,
            "net_retention_rate": health.net_retention_rate,
            "active_users": health.active_users,
            "days_since_last_login": health.days_since_last_login,
            "feature_adoption_score": health.feature_adoption_score,
            "support_ticket_volume": health.support_ticket_volume,
            "nps_score": health.nps_score,
            "monthly_active_users": health.monthly_active_users,
            "payment_failures": health.payment_failures,
            "days_overdue": health.days_overdue,
            "feature_usage_breadth": health.feature_usage_breadth
        }
        
        return features
    
    async def _identify_risk_factors(
        self,
        customer_id: str,
        features: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify top risk factors contributing to churn."""
        
        risk_factors = []
        
        # Factor 1: Inactivity
        if features.get("days_since_last_login", 999) > 30:
            risk_factors.append({
                "factor": f"No logins in {features['days_since_last_login']} days",
                "impact": 25,
                "severity": "high"
            })
        
        # Factor 2: Low engagement
        if features.get("feature_adoption_score", 100) < 30:
            risk_factors.append({
                "factor": "Low feature adoption (only using 20% of features)",
                "impact": 20,
                "severity": "high"
            })
        
        # Factor 3: Payment issues
        if features.get("payment_failures", 0) > 2:
            risk_factors.append({
                "factor": f"{features['payment_failures']} failed payments",
                "impact": 25,
                "severity": "critical"
            })
        
        # Factor 4: Low NPS
        if features.get("nps_score", 0) < 20:
            risk_factors.append({
                "factor": f"Low NPS score ({features['nps_score']})",
                "impact": 15,
                "severity": "high"
            })
        
        # Factor 5: Declining usage
        if features.get("monthly_active_users", 0) < 5:
            risk_factors.append({
                "factor": "Only 3 monthly active users (declining)",
                "impact": 20,
                "severity": "medium"
            })
        
        return sorted(risk_factors, key=lambda x: x["impact"], reverse=True)[:3]
    
    async def _generate_retention_actions(
        self,
        customer_id: str,
        churn_prob: float,
        risk_factors: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate recommended retention actions."""
        
        actions = []
        
        if churn_prob > 80:
            actions.append({
                "action": "Executive check-in call",
                "urgency": "critical",
                "description": "VP-level conversation to understand pain points",
                "timeline": "Within 24 hours"
            })
        
        if any("payment" in rf["factor"] for rf in risk_factors):
            actions.append({
                "action": "Review payment method",
                "urgency": "high",
                "description": "Help customer update payment info, offer payment plan",
                "timeline": "Within 24 hours"
            })
        
        if any("No logins" in rf["factor"] for rf in risk_factors):
            actions.append({
                "action": "Personalized onboarding follow-up",
                "urgency": "high",
                "description": "Send feature walkthrough, schedule training",
                "timeline": "Within 48 hours"
            })
        
        if churn_prob > 50:
            actions.append({
                "action": "Launch win-back campaign",
                "urgency": "high",
                "description": "Email sequence + account manager outreach",
                "timeline": "Immediate"
            })
        
        return actions
    
    async def _get_cached_prediction(self, customer_id: str) -> ChurnPrediction:
        """Get cached prediction if fresh."""
        
        query = select(ChurnRiskPrediction).where(
            ChurnRiskPrediction.customer_id == customer_id
        ).order_by(ChurnRiskPrediction.prediction_date.desc()).limit(1)
        
        pred = self.db.execute(query).scalar()
        
        if pred:
            # Cache fresh for 7 days
            if (datetime.utcnow() - pred.prediction_date).days < 7:
                return ChurnPrediction(
                    churn_probability=pred.churn_probability,
                    churn_risk_score=100 - pred.churn_probability,
                    confidence=pred.confidence_level,
                    risk_factors=pred.top_risk_factors or [],
                    recommended_actions=pred.recommended_actions or []
                )
        
        return None
    
    async def _store_prediction(
        self,
        customer_id: str,
        prediction: Dict,
        risk_factors: List,
        actions: List
    ):
        """Store prediction in database."""
        
        pred = ChurnRiskPrediction(
            customer_id=customer_id,
            churn_probability=prediction["probability"],
            confidence_level=prediction["confidence"],
            top_risk_factors=risk_factors,
            recommended_actions=actions,
            model_version=self.ml_model.version,
            churn_probability_low=prediction["probability_low"],
            churn_probability_high=prediction["probability_high"]
        )
        
        self.db.add(pred)
        self.db.commit()

class ChurnModel:
    """Trained churn prediction model (XGBoost)."""
    
    def __init__(self):
        self.version = "1.0.0"
        import joblib
        self.model = joblib.load("/app/models/churn_prediction_v1.0.0.pkl")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict churn probability.
        
        Returns:
        {
            "probability": 72.5,  # 0-100
            "confidence": 0.88,   # 0-1
            "probability_low": 65.2,
            "probability_high": 79.8
        }
        """
        
        import numpy as np
        
        # Feature extraction
        X = np.array([
            features.get("arr", 10000),
            features.get("net_retention_rate", 100),
            features.get("days_since_last_login", 0),
            features.get("feature_adoption_score", 50),
            features.get("support_ticket_volume", 0),
            features.get("nps_score", 0),
            features.get("monthly_active_users", 10),
            features.get("payment_failures", 0),
            features.get("days_overdue", 0),
            features.get("feature_usage_breadth", 5)
        ]).reshape(1, -1)
        
        # Predict
        prob = self.model.predict_proba(X)[0][1] * 100
        confidence = min(max(prob / 100, 0.6), 0.95)
        
        # CI
        margin = 5 * (1 - confidence)
        
        return {
            "probability": round(prob, 1),
            "confidence": round(confidence, 2),
            "probability_low": max(0, round(prob - margin, 1)),
            "probability_high": min(100, round(prob + margin, 1))
        }
```

---

## 4. EXPANSION OPPORTUNITY FINDER

**File**: `backend/app/services/retention/expansion_finder.py` (250 lines)

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExpansionOpportunity:
    """Identified expansion opportunity."""
    opportunity_type: str  # upsell, cross_sell
    feature_gap: str
    estimated_new_arr: float
    expansion_probability: float

class ExpansionOpportunityFinder:
    """Identify expansion opportunities in customer accounts."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def find_expansion_opportunities(self, customer_id: str) -> List[ExpansionOpportunity]:
        """Identify upsell/cross-sell opportunities."""
        
        # Get customer health
        health = self.db.query(CustomerHealth).filter_by(
            customer_id=customer_id
        ).first()
        
        if not health:
            return []
        
        opportunities = []
        
        # Trigger 1: Growing user count
        if health.active_users > health.monthly_active_users * 1.2:
            opps = await self._upsell_higher_tier(customer_id, health)
            opportunities.extend(opps)
        
        # Trigger 2: High feature usage breadth
        if health.feature_usage_breadth > 8:
            opps = await self._cross_sell_premium_features(customer_id, health)
            opportunities.extend(opps)
        
        # Trigger 3: Strong NPS
        if health.nps_score > 60:
            opps = await self._expansion_from_advocate(customer_id, health)
            opportunities.extend(opps)
        
        # Store opportunities
        for opp in opportunities:
            db_opp = ExpansionOpportunity(
                customer_id=customer_id,
                opportunity_type=opp["type"],
                feature_gap=opp["gap"],
                estimated_new_arr=opp["arr"],
                expansion_probability=opp["probability"],
                trigger_reason=opp["reason"],
                campaign_status="not_started"
            )
            self.db.add(db_opp)
        
        self.db.commit()
        return opportunities
    
    async def _upsell_higher_tier(
        self,
        customer_id: str,
        health
    ) -> List[Dict[str, Any]]:
        """Upsell to higher tier plan."""
        
        # ARR growth needed
        growth_needed = health.active_users * 1000  # Estimate $1k per user
        
        return [{
            "type": "upsell",
            "gap": f"Growing from {health.active_users} to {health.active_users + 10} users",
            "arr": min(growth_needed - health.arr, 50000),
            "probability": 65,
            "reason": "30% user growth in last 90 days"
        }]
    
    async def _cross_sell_premium_features(
        self,
        customer_id: str,
        health
    ) -> List[Dict[str, Any]]:
        """Cross-sell premium features."""
        
        return [
            {
                "type": "cross_sell",
                "gap": "Advanced analytics add-on ($5k/year)",
                "arr": 5000,
                "probability": 55,
                "reason": "Using 9/10 core features, ready for analytics"
            },
            {
                "type": "cross_sell",
                "gap": "Custom integrations ($3k/year)",
                "arr": 3000,
                "probability": 45,
                "reason": "High API usage indicates integration needs"
            }
        ]
    
    async def _expansion_from_advocate(
        self,
        customer_id: str,
        health
    ) -> List[Dict[str, Any]]:
        """Expansion opportunities from promoters."""
        
        return [{
            "type": "expansion",
            "gap": "Multi-team license ($20k/year)",
            "arr": 20000,
            "probability": 75,
            "reason": f"NPS {health.nps_score}, strong advocate"
        }]
```

---

## 5. INTENT-BASED ABM SCORING

**File**: `backend/app/services/retention/intent_scorer.py` (200 lines)

```python
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func, select
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

class IntentScorer:
    """Score accounts based on intent signals (ABM)."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def score_account_intent(self, account_id: str) -> Dict[str, Any]:
        """Calculate ABM intent score for account."""
        
        # Collect all intent signals
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        query = select(AccountIntentSignal).where(
            (AccountIntentSignal.account_id == account_id) &
            (AccountIntentSignal.detected_at >= thirty_days_ago)
        )
        
        signals = self.db.execute(query).scalars().all()
        
        # Calculate scores by signal type
        expansion_score = sum(
            s.signal_strength for s in signals 
            if s.signal_type == "expansion_signal"
        ) / len([s for s in signals if s.signal_type == "expansion_signal"]) if signals else 0
        
        churn_score = sum(
            s.signal_strength for s in signals 
            if s.signal_type == "churn_signal"
        ) / len([s for s in signals if s.signal_type == "churn_signal"]) if signals else 0
        
        # Overall intent score (0-100)
        # Weight: 70% expansion, 30% inverse of churn
        intent_score = (expansion_score * 0.7) + ((100 - churn_score) * 0.3)
        
        # Determine priority
        if intent_score > 75:
            priority = "high"
        elif intent_score > 50:
            priority = "medium"
        else:
            priority = "low"
        
        return {
            "account_id": account_id,
            "intent_score": round(intent_score, 1),
            "expansion_signals": expansion_score,
            "churn_risk": churn_score,
            "priority": priority,
            "signal_count": len(signals),
            "signals": [
                {
                    "type": s.signal_type,
                    "strength": s.signal_strength,
                    "source": s.detection_source,
                    "details": s.signal_details
                }
                for s in signals[:5]
            ]
        }
    
    async def detect_intent_signals(
        self,
        account_id: str,
        signal_type: str,
        source: str,
        details: str
    ):
        """Record detected intent signal."""
        
        # Check if similar signal exists
        query = select(AccountIntentSignal).where(
            (AccountIntentSignal.account_id == account_id) &
            (AccountIntentSignal.signal_type == signal_type) &
            (AccountIntentSignal.detection_source == source)
        ).order_by(AccountIntentSignal.detected_at.desc()).limit(1)
        
        existing = self.db.execute(query).scalar()
        
        if existing:
            # Update existing signal
            existing.signal_frequency += 1
            existing.last_observed = datetime.utcnow()
            existing.signal_strength = min(existing.signal_strength + 5, 100)
        else:
            # Create new signal
            signal = AccountIntentSignal(
                account_id=account_id,
                signal_type=signal_type,
                signal_strength=60.0,
                detection_source=source,
                signal_details=details,
                signal_frequency=1
            )
            self.db.add(signal)
        
        self.db.commit()
```

---

## 6. WIN-BACK ORCHESTRATOR

**File**: `backend/app/services/retention/winback_orchestrator.py` (200 lines)

```python
from typing import Dict, Any
from datetime import datetime, timedelta
from backend.app.database import get_db
import logging

logger = logging.getLogger(__name__)

class WinBackOrchestrator:
    """Orchestrate win-back campaigns for at-risk customers."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def launch_winback_campaign(
        self,
        customer_id: str,
        churn_probability: float,
        risk_factors: list
    ) -> Dict[str, Any]:
        """Launch automated win-back campaign."""
        
        # Determine campaign type
        if churn_probability > 80:
            campaign_type = "churn_prevention"  # Still have them
        elif churn_probability > 60:
            campaign_type = "retention"
        else:
            campaign_type = "reengagement"
        
        # Build email sequence
        email_sequence = self._build_email_sequence(
            campaign_type=campaign_type,
            risk_factors=risk_factors
        )
        
        # Create campaign
        campaign = WinBackCampaign(
            customer_id=customer_id,
            campaign_type=campaign_type,
            trigger_reason=f"Churn risk {churn_probability:.0f}%, {risk_factors[0]['factor']}",
            email_sequence=email_sequence,
            status="active",
            executive_outreach_enabled=(churn_probability > 80)
        )
        
        self.db.add(campaign)
        self.db.commit()
        
        # Schedule first email
        await self._schedule_campaign_email(campaign.id, 0)
        
        return {
            "campaign_id": campaign.id,
            "type": campaign_type,
            "emails_scheduled": len(email_sequence),
            "executive_outreach": campaign.executive_outreach_enabled
        }
    
    def _build_email_sequence(
        self,
        campaign_type: str,
        risk_factors: list
    ) -> list:
        """Build email sequence based on risk factors."""
        
        if campaign_type == "churn_prevention":
            return [
                {
                    "day": 0,
                    "subject": "We notice you haven't been using SellIA recently",
                    "body": "Let's discuss how to get more value from your investment..."
                },
                {
                    "day": 2,
                    "subject": "Quick wins you might be missing",
                    "body": "Here are 3 features used by similar companies to drive..."
                },
                {
                    "day": 5,
                    "subject": "Your VP should see this ROI story",
                    "body": "Case study: $250k savings in first year..."
                }
            ]
        elif campaign_type == "retention":
            return [
                {
                    "day": 0,
                    "subject": "Let's make SellIA work better for you",
                    "body": "Quick check-in to see if we're solving your core needs..."
                },
                {
                    "day": 3,
                    "subject": "Training: Get 10x more value",
                    "body": "30-min session on advanced features..."
                }
            ]
        else:
            return [
                {
                    "day": 0,
                    "subject": "Welcome back to SellIA!",
                    "body": "A lot has changed since you last logged in..."
                },
                {
                    "day": 4,
                    "subject": "Your team is missing out",
                    "body": "Best practices from customers like you..."
                }
            ]
    
    async def _schedule_campaign_email(self, campaign_id: str, sequence_index: int):
        """Schedule email to be sent."""
        
        from backend.app.tasks.retention import send_winback_email
        
        campaign = self.db.query(WinBackCampaign).filter_by(id=campaign_id).first()
        
        if not campaign or sequence_index >= len(campaign.email_sequence):
            return
        
        email_config = campaign.email_sequence[sequence_index]
        send_time = datetime.utcnow() + timedelta(days=email_config["day"])
        
        send_winback_email.apply_async(
            args=[campaign_id, sequence_index],
            eta=send_time
        )
```

---

## 7. API ENDPOINTS

```python
@router.get("/retention/churn-risk/{customer_id}")
async def get_churn_risk(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get churn risk prediction + recommendations."""
    
    predictor = ChurnPredictor(db)
    prediction = await predictor.predict_churn_risk(customer_id)
    
    return {
        "customer_id": customer_id,
        "churn_probability": prediction.churn_probability,
        "churn_risk_score": prediction.churn_risk_score,
        "confidence": prediction.confidence,
        "risk_factors": prediction.risk_factors,
        "recommended_actions": prediction.recommended_actions
    }

@router.get("/retention/expansion/{account_id}")
async def get_expansion_opportunities(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get expansion opportunities for account."""
    
    finder = ExpansionOpportunityFinder(db)
    opportunities = await finder.find_expansion_opportunities(account_id)
    
    return {
        "account_id": account_id,
        "opportunities": [
            {
                "type": o.opportunity_type,
                "gap": o.feature_gap,
                "estimated_arr": o.estimated_new_arr,
                "probability": o.expansion_probability
            }
            for o in opportunities
        ],
        "total_potential_arr": sum(o.estimated_new_arr for o in opportunities)
    }

@router.get("/retention/accounts")
async def get_account_intent_scores(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    limit: int = 50
):
    """Get top accounts by intent score (ABM prioritization)."""
    
    query = select(AccountIntentSignal).order_by(
        AccountIntentSignal.signal_strength.desc()
    ).limit(limit)
    
    signals = db.execute(query).scalars().all()
    
    # Group by account, calculate scores
    accounts = {}
    for signal in signals:
        if signal.account_id not in accounts:
            scorer = IntentScorer(db)
            accounts[signal.account_id] = await scorer.score_account_intent(
                signal.account_id
            )
    
    return {
        "accounts": list(accounts.values())
    }

@router.post("/retention/winback/{customer_id}")
async def launch_winback_campaign(
    customer_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Launch win-back campaign for at-risk customer."""
    
    predictor = ChurnPredictor(db)
    prediction = await predictor.predict_churn_risk(customer_id)
    
    if prediction.churn_probability < 50:
        raise HTTPException(status_code=400, detail="Customer not at risk")
    
    orchestrator = WinBackOrchestrator(db)
    result = await orchestrator.launch_winback_campaign(
        customer_id=customer_id,
        churn_probability=prediction.churn_probability,
        risk_factors=prediction.risk_factors
    )
    
    return result
```

---

## 8. FRONTEND COMPONENTS

### ChurnRiskDashboard.tsx

```typescript
export const ChurnRiskDashboard: React.FC = () => {
  const [riskLevel, setRiskLevel] = useState('');
  const [topCustomers, setTopCustomers] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/v1/retention/churn-risk?limit=20')
      .then(r => r.json())
      .then(data => setTopCustomers(data.at_risk_customers));
  }, []);

  return (
    <div className="space-y-4 p-6">
      <Card>
        <h2 className="text-lg font-bold">Churn Risk Dashboard</h2>
        
        <div className="grid grid-cols-3 gap-4 my-4">
          <Stat>
            <p>Critical Risk (>80%)</p>
            <p className="text-2xl font-bold text-red-600">
              {topCustomers.filter(c => c.churn_prob > 80).length}
            </p>
          </Stat>
          <Stat>
            <p>High Risk (50-80%)</p>
            <p className="text-2xl font-bold text-yellow-600">
              {topCustomers.filter(c => c.churn_prob > 50).length}
            </p>
          </Stat>
          <Stat>
            <p>Potential ARR at Risk</p>
            <p className="text-2xl font-bold">${(topCustomers.reduce((s, c) => s + (c.arr || 0), 0) / 1000).toFixed(0)}k</p>
          </Stat>
        </div>
        
        <Table>
          <thead>
            <tr>
              <th>Customer</th>
              <th>Churn Risk</th>
              <th>Top Risk Factor</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {topCustomers.map(c => (
              <tr key={c.customer_id}>
                <td>{c.customer_name}</td>
                <td><Badge color={c.churn_prob > 80 ? 'red' : 'yellow'}>{c.churn_prob}%</Badge></td>
                <td>{c.risk_factors[0]?.factor}</td>
                <td>
                  <Button onClick={() => launchWinback(c.customer_id)}>
                    Launch Campaign
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </div>
  );
};
```

---

## 9. IMPLEMENTATION TIMELINE

**Week 25**: Churn Prediction
- [ ] Database schema
- [ ] ChurnPredictor service (350 lines)
- [ ] ML model training (XGBoost)
- [ ] API endpoints

**Week 26**: Expansion Finder
- [ ] ExpansionOpportunityFinder (250 lines)
- [ ] Opportunity detection logic
- [ ] Campaign triggering

**Week 27**: Intent Scoring + ABM
- [ ] IntentScorer service (200 lines)
- [ ] Account intent signals
- [ ] ABM dashboard

**Week 28**: Win-Back Orchestrator
- [ ] WinBackOrchestrator (200 lines)
- [ ] Campaign email sequences
- [ ] Automated executive outreach

**Week 29**: Frontend + Testing
- [ ] ChurnRiskDashboard component
- [ ] ExpansionOpportunities view
- [ ] E2E testing + UAT

---

## 10. SUCCESS CRITERIA

**Technical**:
- [ ] Churn model AUC 0.82+
- [ ] All APIs < 200ms p95
- [ ] Dashboard loads < 2s
- [ ] 99%+ uptime

**Product**:
- [ ] Churn reduction -30%
- [ ] Expansion pipeline +50-80% warm
- [ ] Win-back campaign 25%+ conversion
- [ ] LTV increase +20-25%

---

**Phase 30 Architecture Complete** ✅

**Phase 27-30 Full Cycle Ready** ✅

