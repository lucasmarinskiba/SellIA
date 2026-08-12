"""Phase 30 Churn Prevention API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.domains.enterprise.churn_retention import (
    ChurnPredictionModel,
    ExpansionOpportunityDetector,
    ABMIntentScorer,
    RetentionPlaybookGenerator,
    CustomerHealthScore,
)

router = APIRouter(prefix="/api/v1/churn", tags=["churn-retention"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================


class ChurnPredictionRequest(BaseModel):
    customer_id: str


class ChurnPredictionResponse(BaseModel):
    customer_id: str
    churn_probability: float
    risk_level: str
    churn_reasons: List[dict]
    predicted_churn_date: str
    retention_offer: str


class ExpansionOpportunitiesRequest(BaseModel):
    customer_id: str


class ExpansionOpportunitiesResponse(BaseModel):
    customer_id: str
    opportunities: List[dict]


class ABMIntentRequest(BaseModel):
    account_id: str


class ABMIntentResponse(BaseModel):
    account_id: str
    intent_score: int
    intent_level: str
    top_signals: List[dict]
    trending: str


class RetentionCampaignRequest(BaseModel):
    customer_id: str
    churn_reason: str


class RetentionCampaignResponse(BaseModel):
    campaign_id: str
    message: str
    offer: str
    executive_message: Optional[str]


class HealthScoreRequest(BaseModel):
    customer_id: str


class HealthScoreResponse(BaseModel):
    customer_id: str
    health_score: int
    health_level: str
    churn_risk: str
    churn_probability: float
    expansion_potential: float
    expansion_opportunities: int
    abm_intent_score: int
    abm_intent_level: str
    trending: str
    recommended_action: str


# ============================================================
# ENDPOINTS
# ============================================================


@router.post("/predictions/{customer_id}", response_model=ChurnPredictionResponse)
def predict_churn(customer_id: str, db: Session = Depends(get_db)):
    """Get churn prediction for customer."""
    try:
        from backend.app.models.deal import Deal

        deal = db.query(Deal).filter(Deal.id == customer_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Mock features (in production: query actual engagement data)
        features = {
            "days_since_login": 25,
            "features_used_pct": 0.45,
            "support_ticket_trend": -0.1,
            "payment_failed_count": 0,
            "competitor_mentions": 2,
        }

        model = ChurnPredictionModel(db)
        prediction = model.predict_churn(customer_id, features)

        return ChurnPredictionResponse(
            customer_id=prediction.customer_id,
            churn_probability=prediction.churn_probability,
            risk_level=prediction.risk_level.value,
            churn_reasons=prediction.churn_reasons,
            predicted_churn_date=prediction.predicted_churn_date,
            retention_offer=prediction.retention_offer,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expansion-opportunities/{customer_id}", response_model=ExpansionOpportunitiesResponse)
def get_expansion_opportunities(customer_id: str, db: Session = Depends(get_db)):
    """Get expansion opportunities for customer."""
    try:
        from backend.app.models.deal import Deal

        deal = db.query(Deal).filter(Deal.id == customer_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Mock usage data
        usage_data = {
            "customer_id": customer_id,
            "features_using": ["reporting", "analytics"],
            "features_available": ["reporting", "analytics", "automation", "custom_dashboards"],
            "team_size_current": 12,
            "team_size_historical": 10,
            "seats_purchased": 10,
            "current_product": "Analytics",
        }

        detector = ExpansionOpportunityDetector(db)
        opportunities = detector.detect_opportunities(customer_id, usage_data)

        return ExpansionOpportunitiesResponse(
            customer_id=customer_id,
            opportunities=[
                {
                    "type": opp.opportunity_type.value,
                    "feature": opp.adjacent_feature,
                    "revenue_potential": opp.revenue_potential,
                    "likelihood": opp.likelihood_score,
                    "message": opp.recommended_message,
                }
                for opp in opportunities
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/abm-intent/{account_id}", response_model=ABMIntentResponse)
def get_abm_intent(account_id: str, db: Session = Depends(get_db)):
    """Get ABM intent score for account."""
    try:
        from backend.app.models.deal import Deal

        deal = db.query(Deal).filter(Deal.id == account_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Account not found")

        # Mock engagement data
        engagement_data = {
            "page_views_30d": 15,
            "email_open_rate": 0.55,
            "demo_requests_30d": 1,
            "content_views_30d": 8,
            "competitor_research_30d": 2,
            "engagement_score_current": 65,
            "engagement_score_previous": 50,
        }

        scorer = ABMIntentScorer(db)
        intent = scorer.score_intent(account_id, engagement_data)

        return ABMIntentResponse(
            account_id=account_id,
            intent_score=intent["intent_score"],
            intent_level=intent["intent_level"],
            top_signals=intent["top_signals"],
            trending=intent["trending"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/retention-campaign/{customer_id}", response_model=RetentionCampaignResponse)
def launch_retention_campaign(
    customer_id: str,
    request: RetentionCampaignRequest,
    db: Session = Depends(get_db),
):
    """Launch retention campaign for at-risk customer."""
    try:
        from backend.app.models.deal import Deal
        import uuid

        deal = db.query(Deal).filter(Deal.id == customer_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Mock customer data
        customer = {
            "name": "John Doe",
            "company": deal.company_name,
            "industry": getattr(deal, "industry", "technology"),
            "annual_spend": getattr(deal, "value", 50000),
            "top_feature": "Analytics",
        }

        generator = RetentionPlaybookGenerator(db)
        playbook = generator.generate_playbook(customer, request.churn_reason)

        return RetentionCampaignResponse(
            campaign_id=str(uuid.uuid4()),
            message=playbook.get("body", ""),
            offer=playbook.get("offer", ""),
            executive_message=playbook.get("executive", None),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/healthcheck/{customer_id}", response_model=HealthScoreResponse)
def get_customer_health(customer_id: str, db: Session = Depends(get_db)):
    """Get comprehensive customer health scorecard."""
    try:
        from backend.app.models.deal import Deal

        deal = db.query(Deal).filter(Deal.id == customer_id).first()
        if not deal:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Mock features
        features = {
            "days_since_login": 25,
            "features_used_pct": 0.45,
            "support_ticket_trend": -0.1,
            "payment_failed_count": 0,
            "competitor_mentions": 2,
            "customer_id": customer_id,
            "features_using": ["reporting"],
            "features_available": ["reporting", "automation"],
            "team_size_current": 12,
            "team_size_historical": 10,
            "seats_purchased": 10,
            "current_product": "Analytics",
            "page_views_30d": 15,
            "email_open_rate": 0.55,
            "demo_requests_30d": 1,
            "content_views_30d": 8,
            "competitor_research_30d": 2,
            "engagement_score_current": 65,
            "engagement_score_previous": 50,
        }

        churn_model = ChurnPredictionModel(db)
        expansion_detector = ExpansionOpportunityDetector(db)
        abm_scorer = ABMIntentScorer(db)

        health_calculator = CustomerHealthScore(db, churn_model, expansion_detector, abm_scorer)
        health = health_calculator.calculate_health(customer_id, features)

        return HealthScoreResponse(
            customer_id=customer_id,
            health_score=health["health_score"],
            health_level=health["health_level"],
            churn_risk=health["churn_risk"],
            churn_probability=health["churn_probability"],
            expansion_potential=health["expansion_potential"],
            expansion_opportunities=health["expansion_opportunities"],
            abm_intent_score=health["abm_intent_score"],
            abm_intent_level=health["abm_intent_level"],
            trending=health["trending"],
            recommended_action=health["recommended_action"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
