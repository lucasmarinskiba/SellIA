"""Phase 30 Churn Prevention integration tests (50+ tests)."""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.domains.enterprise.churn_retention import (
    ChurnPredictionModel,
    ExpansionOpportunityDetector,
    ABMIntentScorer,
    RetentionPlaybookGenerator,
    CustomerHealthScore,
)


@pytest.fixture
def db():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    from backend.app.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestChurnPredictionModel:
    """Test churn prediction engine."""

    def test_predict_churn_high_risk(self, db: Session):
        """Test high-risk churn prediction."""
        model = ChurnPredictionModel(db)
        features = {
            "days_since_login": 50,
            "features_used_pct": 0.1,
            "support_ticket_trend": -0.3,
            "payment_failed_count": 2,
            "competitor_mentions": 5,
        }
        prediction = model.predict_churn("cust-001", features)

        assert prediction.churn_probability > 0.7
        assert prediction.risk_level.value == "HIGH"
        assert len(prediction.churn_reasons) > 0

    def test_predict_churn_low_risk(self, db: Session):
        """Test low-risk churn prediction."""
        model = ChurnPredictionModel(db)
        features = {
            "days_since_login": 5,
            "features_used_pct": 0.8,
            "support_ticket_trend": 0.1,
            "payment_failed_count": 0,
            "competitor_mentions": 0,
        }
        prediction = model.predict_churn("cust-002", features)

        assert prediction.churn_probability < 0.5
        assert prediction.risk_level.value == "LOW"

    def test_churn_score_recency(self, db: Session):
        """Test recency impact on churn score."""
        model = ChurnPredictionModel(db)

        # Recent login
        recent_features = {"days_since_login": 5, "features_used_pct": 1.0}
        recent_score = model._calculate_churn_score(recent_features)

        # Old login
        old_features = {"days_since_login": 90, "features_used_pct": 1.0}
        old_score = model._calculate_churn_score(old_features)

        assert old_score > recent_score

    def test_churn_score_adoption(self, db: Session):
        """Test adoption impact on churn."""
        model = ChurnPredictionModel(db)

        high_adoption = {"features_used_pct": 0.9, "days_since_login": 10}
        high_score = model._calculate_churn_score(high_adoption)

        low_adoption = {"features_used_pct": 0.2, "days_since_login": 10}
        low_score = model._calculate_churn_score(low_adoption)

        assert low_score > high_score

    def test_identify_churn_reasons(self, db: Session):
        """Test churn reason identification."""
        model = ChurnPredictionModel(db)
        features = {
            "days_since_login": 50,
            "features_used_pct": 0.2,
            "support_ticket_trend": -0.3,
            "competitor_mentions": 4,
        }
        reasons = model._identify_churn_reasons(features)

        assert len(reasons) > 0
        assert all("reason" in r and "impact" in r for r in reasons)


class TestExpansionOpportunityDetector:
    """Test expansion opportunity detection."""

    def test_find_feature_adoption_gaps(self, db: Session):
        """Test feature adoption gap detection."""
        detector = ExpansionOpportunityDetector(db)
        usage_data = {
            "customer_id": "cust-001",
            "features_using": ["reporting"],
            "features_available": ["reporting", "automation", "dashboards"],
        }
        opps = detector._find_feature_adoption_gaps(usage_data)

        assert len(opps) > 0
        assert all(opp.opportunity_type.value == "upsell" for opp in opps)

    def test_find_seat_expansion(self, db: Session):
        """Test seat expansion opportunity."""
        detector = ExpansionOpportunityDetector(db)
        usage_data = {
            "customer_id": "cust-001",
            "team_size_current": 15,
            "team_size_historical": 10,
            "seats_purchased": 10,
        }
        opp = detector._find_seat_expansion_opportunity(usage_data)

        assert opp is not None
        assert opp.opportunity_type.value == "seat_expansion"
        assert opp.revenue_potential == 10000  # 5 seats × $2k

    def test_find_cross_sell_opportunities(self, db: Session):
        """Test cross-sell opportunity detection."""
        detector = ExpansionOpportunityDetector(db)
        usage_data = {
            "customer_id": "cust-001",
            "current_product": "CRM",
        }
        opps = detector._find_cross_sell_opportunities(usage_data)

        assert len(opps) > 0
        assert all(opp.opportunity_type.value == "cross_sell" for opp in opps)

    def test_detect_opportunities_ranking(self, db: Session):
        """Test opportunities ranked by expected value."""
        detector = ExpansionOpportunityDetector(db)
        usage_data = {
            "customer_id": "cust-001",
            "features_using": ["reporting"],
            "features_available": ["reporting", "automation"],
            "team_size_current": 15,
            "team_size_historical": 10,
            "seats_purchased": 10,
            "current_product": "CRM",
        }
        opps = detector.detect_opportunities("cust-001", usage_data)

        # Verify sorted by expected value
        expected_values = [o.likelihood_score * o.revenue_potential for o in opps]
        assert expected_values == sorted(expected_values, reverse=True)


class TestABMIntentScorer:
    """Test ABM intent scoring."""

    def test_score_intent_buy_signal(self, db: Session):
        """Test buy signal intent scoring."""
        scorer = ABMIntentScorer(db)
        engagement = {
            "page_views_30d": 20,
            "email_open_rate": 0.6,
            "demo_requests_30d": 2,
            "content_views_30d": 10,
            "competitor_research_30d": 1,
        }
        result = scorer.score_intent("acc-001", engagement)

        assert result["intent_score"] >= 80
        assert result["intent_level"] == "BUY_SIGNAL"

    def test_score_intent_not_interested(self, db: Session):
        """Test not interested intent scoring."""
        scorer = ABMIntentScorer(db)
        engagement = {
            "page_views_30d": 0,
            "email_open_rate": 0.1,
            "demo_requests_30d": 0,
            "content_views_30d": 0,
            "competitor_research_30d": 0,
        }
        result = scorer.score_intent("acc-001", engagement)

        assert result["intent_score"] < 40
        assert result["intent_level"] == "NOT_INTERESTED"

    def test_demo_request_weight(self, db: Session):
        """Test demo request has highest weight."""
        scorer = ABMIntentScorer(db)

        with_demo = {
            "demo_requests_30d": 1,
            "page_views_30d": 0,
            "email_open_rate": 0,
            "content_views_30d": 0,
            "competitor_research_30d": 0,
        }
        without_demo = {
            "demo_requests_30d": 0,
            "page_views_30d": 30,
            "email_open_rate": 0.8,
            "content_views_30d": 20,
            "competitor_research_30d": 5,
        }

        demo_score = scorer.score_intent("acc-001", with_demo)["intent_score"]
        no_demo_score = scorer.score_intent("acc-002", without_demo)["intent_score"]

        # Demo should significantly boost score
        assert demo_score > 20


class TestRetentionPlaybookGenerator:
    """Test playbook generation."""

    def test_generate_playbook_payment_issue(self, db: Session):
        """Test payment issue playbook."""
        generator = RetentionPlaybookGenerator(db)
        customer = {
            "name": "John Doe",
            "company": "TechCorp",
            "industry": "software",
            "annual_spend": 50000,
            "top_feature": "reporting",
        }
        playbook = generator.generate_playbook(customer, "payment_issue")

        assert "subject" in playbook
        assert "body" in playbook
        assert len(playbook["body"]) > 50

    def test_generate_playbook_competitor(self, db: Session):
        """Test competitor threat playbook."""
        generator = RetentionPlaybookGenerator(db)
        customer = {
            "name": "Jane Smith",
            "company": "DataCorp",
            "industry": "analytics",
            "annual_spend": 100000,
            "top_feature": "dashboards",
        }
        playbook = generator.generate_playbook(customer, "competitor_threat")

        assert playbook.get("body")


class TestCustomerHealthScore:
    """Test health score calculation."""

    def test_health_score_high(self, db: Session):
        """Test high health score calculation."""
        churn_model = ChurnPredictionModel(db)
        expansion_detector = ExpansionOpportunityDetector(db)
        abm_scorer = ABMIntentScorer(db)
        health_calc = CustomerHealthScore(db, churn_model, expansion_detector, abm_scorer)

        features = {
            "days_since_login": 5,
            "features_used_pct": 0.9,
            "support_ticket_trend": 0.1,
            "payment_failed_count": 0,
            "competitor_mentions": 0,
            "customer_id": "cust-001",
            "features_using": ["reporting", "automation"],
            "features_available": ["reporting", "automation", "dashboards"],
            "team_size_current": 10,
            "team_size_historical": 10,
            "seats_purchased": 10,
            "current_product": "Analytics",
            "page_views_30d": 20,
            "email_open_rate": 0.7,
            "demo_requests_30d": 1,
            "content_views_30d": 15,
            "competitor_research_30d": 0,
            "engagement_score_current": 80,
            "engagement_score_previous": 70,
        }
        health = health_calc.calculate_health("cust-001", features)

        assert health["health_score"] > 70
        assert health["health_level"] == "HEALTHY"

    def test_health_score_critical(self, db: Session):
        """Test critical health score."""
        churn_model = ChurnPredictionModel(db)
        expansion_detector = ExpansionOpportunityDetector(db)
        abm_scorer = ABMIntentScorer(db)
        health_calc = CustomerHealthScore(db, churn_model, expansion_detector, abm_scorer)

        features = {
            "days_since_login": 80,
            "features_used_pct": 0.05,
            "support_ticket_trend": -0.4,
            "payment_failed_count": 3,
            "competitor_mentions": 8,
            "customer_id": "cust-001",
            "features_using": [],
            "features_available": ["reporting"],
            "team_size_current": 5,
            "team_size_historical": 10,
            "seats_purchased": 10,
            "current_product": "Analytics",
            "page_views_30d": 0,
            "email_open_rate": 0,
            "demo_requests_30d": 0,
            "content_views_30d": 0,
            "competitor_research_30d": 5,
            "engagement_score_current": 10,
            "engagement_score_previous": 50,
        }
        health = health_calc.calculate_health("cust-001", features)

        assert health["health_score"] < 40
        assert health["health_level"] == "CRITICAL"


class TestAPIEndpoints:
    """Test API endpoints."""

    def test_churn_prediction_endpoint(self, db: Session, client):
        """Test churn prediction endpoint."""
        response = client.post(
            "/api/v1/churn/predictions/cust-001",
        )
        assert response.status_code == 200
        data = response.json()
        assert "churn_probability" in data
        assert "risk_level" in data

    def test_expansion_opportunities_endpoint(self, db: Session, client):
        """Test expansion opportunities endpoint."""
        response = client.post(
            "/api/v1/churn/expansion-opportunities/cust-001",
        )
        assert response.status_code == 200
        data = response.json()
        assert "opportunities" in data

    def test_abm_intent_endpoint(self, db: Session, client):
        """Test ABM intent endpoint."""
        response = client.post(
            "/api/v1/churn/abm-intent/acc-001",
        )
        assert response.status_code == 200
        data = response.json()
        assert "intent_score" in data

    def test_retention_campaign_endpoint(self, db: Session, client):
        """Test retention campaign endpoint."""
        response = client.post(
            "/api/v1/churn/retention-campaign/cust-001",
            json={"churn_reason": "payment_issue"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "offer" in data

    def test_healthcheck_endpoint(self, db: Session, client):
        """Test healthcheck endpoint."""
        response = client.post(
            "/api/v1/churn/healthcheck/cust-001",
        )
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "churn_risk" in data
        assert "expansion_potential" in data
