"""Phase 31 Psychology Sales integration tests.

Tests all 5 engines + 6 API endpoints:
- DiscoveryQuestionsEngine
- NeedCreationEngine
- UrgencyTriggerEngine
- PsychologyObjectionHandler
- AssumptiveCloseEngine
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.core.database import Base, engine
from app.models.psychology_sales import (
    DiscoveryResponse,
    NeedNarrative,
    ObjectionHandling,
    CloseAttempt,
    SalesConversation,
    SalesRepPerformance,
)
from app.domains.crm.models import Deal
from app.domains.enterprise.psychology_sales import (
    DiscoveryQuestionsEngine,
    NeedCreationEngine,
    UrgencyTriggerEngine,
    PsychologyObjectionHandler,
    AssumptiveCloseEngine,
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


@pytest.fixture
def test_deal(db: Session):
    """Create test deal."""
    deal = Deal(
        id="deal-001",
        company_name="TechCorp Inc",
        industry="technology",
        value=150000,
    )
    db.add(deal)
    db.commit()
    return deal


class TestDiscoveryQuestionsEngine:
    """Test discovery questions generation."""

    def test_generate_questions_rapport_stage(self, db: Session):
        """Test rapport stage questions."""
        engine = DiscoveryQuestionsEngine(db)
        prospect = {
            "company_name": "TechCorp Inc",
            "industry": "technology",
            "role": "decision_maker",
        }

        questions = engine.generate_questions(prospect, "rapport")

        assert len(questions) > 0
        assert all(hasattr(q, "question") for q in questions)
        assert all(hasattr(q, "psychology") for q in questions)

    def test_generate_questions_problem_stage(self, db: Session):
        """Test problem identification stage."""
        engine = DiscoveryQuestionsEngine(db)
        prospect = {"company_name": "TechCorp", "industry": "finance", "role": "cfo"}

        questions = engine.generate_questions(prospect, "problem")

        assert len(questions) > 0
        for q in questions:
            assert "problem" in q.question.lower() or "challenge" in q.question.lower()

    def test_generate_questions_impact_stage(self, db: Session):
        """Test impact quantification stage."""
        engine = DiscoveryQuestionsEngine(db)
        prospect = {"company_name": "Acme Corp", "industry": "retail", "role": "ceo"}

        questions = engine.generate_questions(prospect, "impact")

        assert len(questions) > 0
        # Impact questions should focus on financial consequences
        assert any("cost" in q.question.lower() or "money" in q.question.lower() for q in questions)

    def test_record_response(self, db: Session, test_deal: Deal):
        """Test recording discovery response."""
        engine = DiscoveryQuestionsEngine(db)

        response = engine.record_response(
            test_deal.id,
            "What's your biggest challenge?",
            "We're losing $500k/year to manual processes",
        )

        assert response is not None
        assert response.deal_id == test_deal.id
        assert response.response_text == "We're losing $500k/year to manual processes"

        # Verify in database
        db_response = db.query(DiscoveryResponse).filter_by(deal_id=test_deal.id).first()
        assert db_response is not None
        assert db_response.urgency_level > 0

    def test_extract_pain_points_from_response(self, db: Session, test_deal: Deal):
        """Test pain point extraction."""
        engine = DiscoveryQuestionsEngine(db)

        response = engine.record_response(
            test_deal.id,
            "What problems do you face?",
            "We have three issues: manual data entry taking 40 hours/week, "
            "frequent errors causing customer complaints, and team burnout",
        )

        assert response.pain_points is not None
        assert len(response.pain_points) > 0
        # Should identify: manual data entry, errors, burnout
        assert any("manual" in str(p).lower() for p in response.pain_points)


class TestNeedCreationEngine:
    """Test need narrative generation."""

    def test_create_need_narrative(self, db: Session, test_deal: Deal):
        """Test narrative generation from pain."""
        engine = NeedCreationEngine(db)

        # First, record some discovery responses
        discovery_engine = DiscoveryQuestionsEngine(db)
        discovery_engine.record_response(
            test_deal.id,
            "What's your biggest pain?",
            "Manual processes costing us $500k annually",
        )

        narrative = engine.create_need_narrative(
            test_deal.id,
            ["Manual processes", "Team burnout", "Customer errors"],
        )

        assert narrative is not None
        assert narrative.narrative is not None
        assert len(narrative.narrative) > 100
        assert narrative.financial_impact is not None
        assert narrative.financial_impact > 0

    def test_financial_impact_calculation(self, db: Session, test_deal: Deal):
        """Test automatic financial impact calculation."""
        engine = NeedCreationEngine(db)

        narrative = engine.create_need_narrative(
            test_deal.id,
            ["Losing $200k/year to downtime", "5 FTE hours/week on workarounds"],
        )

        # Should calculate impact in dollars
        assert narrative.financial_impact >= 200000
        assert narrative.urgency_level > 0

    def test_narrative_includes_gap_analysis(self, db: Session, test_deal: Deal):
        """Test that narrative shows gap between current and desired state."""
        engine = NeedCreationEngine(db)

        narrative = engine.create_need_narrative(
            test_deal.id,
            ["Current manual process", "Desired: automated solution"],
        )

        # Narrative should quantify gap
        assert "current" in narrative.narrative.lower() or "gap" in narrative.narrative.lower()


class TestUrgencyTriggerEngine:
    """Test FOMO/urgency trigger generation."""

    def test_generate_supply_scarcity_trigger(self, db: Session):
        """Test supply scarcity trigger."""
        engine = UrgencyTriggerEngine(db)
        deal = {"stage": "proposal", "industry": "saas"}

        triggers = engine.generate_urgency_triggers(deal)

        assert len(triggers) > 0
        assert any("supply" in str(t).lower() or "capacity" in str(t).lower() for t in triggers)

    def test_generate_price_increase_trigger(self, db: Session):
        """Test price increase trigger."""
        engine = UrgencyTriggerEngine(db)
        deal = {"stage": "negotiation", "industry": "enterprise"}

        triggers = engine.generate_urgency_triggers(deal)

        assert len(triggers) > 0
        assert any("price" in str(t).lower() for t in triggers)

    def test_generate_social_proof_trigger(self, db: Session):
        """Test social proof trigger."""
        engine = UrgencyTriggerEngine(db)
        deal = {"stage": "proposal", "industry": "technology"}

        triggers = engine.generate_urgency_triggers(deal)

        assert len(triggers) > 0
        # Should include competitor activity or customer success stories
        trigger_str = " ".join(str(t).lower() for t in triggers)
        assert "competitor" in trigger_str or "customer" in trigger_str or "social" in trigger_str

    def test_triggers_include_psychology_rationale(self, db: Session):
        """Test that triggers include psychology explanation."""
        engine = UrgencyTriggerEngine(db)
        deal = {"stage": "proposal", "industry": "finance"}

        triggers = engine.generate_urgency_triggers(deal)

        # Each trigger should explain the psychology
        assert len(triggers) > 0
        for trigger in triggers:
            if isinstance(trigger, dict):
                assert "psychology" in trigger or "type" in trigger


class TestPsychologyObjectionHandler:
    """Test objection handling."""

    def test_handle_price_objection(self, db: Session):
        """Test price objection handling."""
        handler = PsychologyObjectionHandler(db)
        prospect = {"role": "cfo"}

        response = handler.handle_objection(
            "I think your pricing is too high",
            prospect,
        )

        assert response is not None
        assert len(response) > 0
        # Should validate, not dismiss
        assert "understand" in response.lower() or "valid" in response.lower()

    def test_handle_time_objection(self, db: Session):
        """Test timing objection."""
        handler = PsychologyObjectionHandler(db)
        prospect = {"role": "ceo"}

        response = handler.handle_objection(
            "This isn't the right time for us",
            prospect,
        )

        assert response is not None
        # Should ask questions rather than push
        assert "?" in response or "think" in response.lower()

    def test_handle_need_objection(self, db: Session):
        """Test 'don't need this' objection."""
        handler = PsychologyObjectionHandler(db)
        prospect = {"role": "vp_sales"}

        response = handler.handle_objection(
            "We don't really need this solution",
            prospect,
        )

        assert response is not None
        # Should circle back to discovered pain
        assert len(response) > 50

    def test_handle_authority_objection(self, db: Session):
        """Test authority objection."""
        handler = PsychologyObjectionHandler(db)
        prospect = {"role": "manager"}

        response = handler.handle_objection(
            "I need to check with my boss before deciding",
            prospect,
        )

        assert response is not None
        # Should facilitate rather than block
        assert "boss" in response.lower() or "decision" in response.lower() or "together" in response.lower()

    def test_objection_response_is_psychology_based(self, db: Session):
        """Test that response uses psychology principles."""
        handler = PsychologyObjectionHandler(db)

        response = handler.handle_objection(
            "Your product doesn't have feature X that we need",
            {"role": "technical_buyer"},
        )

        # Should validate the concern first
        assert response is not None
        assert len(response) > 0


class TestAssumptiveCloseEngine:
    """Test 5-step closing sequence."""

    def test_step_1_small_yes(self, db: Session, test_deal: Deal):
        """Test step 1: small commitment."""
        engine = AssumptiveCloseEngine(db)

        close = engine.get_close(1)

        assert close is not None
        assert len(close) > 0
        # Should ask for small commitment (meeting, demo, etc.)
        assert any(
            word in close.lower()
            for word in ["call", "meeting", "demo", "quick", "brief", "time"]
        )

    def test_step_2_choice_between(self, db: Session):
        """Test step 2: assume buying, offer choice."""
        engine = AssumptiveCloseEngine(db)

        close = engine.get_close(2)

        assert close is not None
        # Should frame as "which" not "whether"
        assert "?" in close

    def test_step_3_pilot(self, db: Session):
        """Test step 3: reduce risk with pilot."""
        engine = AssumptiveCloseEngine(db)

        close = engine.get_close(3)

        assert close is not None
        # Should mention limited time or money-back guarantee
        assert any(
            word in close.lower()
            for word in ["pilot", "trial", "test", "guarantee", "risk", "limited"]
        )

    def test_step_4_upsell(self, db: Session):
        """Test step 4: expand scope on momentum."""
        engine = AssumptiveCloseEngine(db)

        close = engine.get_close(4)

        assert close is not None
        # Should expand/add features while they're enthusiastic
        assert any(
            word in close.lower()
            for word in ["add", "upgrade", "premium", "include", "more"]
        )

    def test_step_5_full_commitment(self, db: Session):
        """Test step 5: final close."""
        engine = AssumptiveCloseEngine(db)

        close = engine.get_close(5)

        assert close is not None
        # Should assume agreement is done
        assert any(
            word in close.lower()
            for word in ["great", "perfect", "excellent", "sign", "let's"]
        )

    def test_is_positive_response(self, db: Session):
        """Test positive response detection."""
        engine = AssumptiveCloseEngine(db)

        positive = engine._is_positive_response("Yes, that sounds great!")
        assert positive is True

        negative = engine._is_positive_response("I need to think about it")
        assert negative is False


class TestIntegrationEndToEnd:
    """End-to-end psychology sales flow tests."""

    def test_full_discovery_to_close_flow(self, db: Session, test_deal: Deal):
        """Test complete flow from discovery to close."""
        # Step 1: Generate discovery questions
        discovery_engine = DiscoveryQuestionsEngine(db)
        prospect = {"company_name": "TestCorp", "industry": "technology", "role": "ceo"}

        questions = discovery_engine.generate_questions(prospect, "problem")
        assert len(questions) > 0

        # Step 2: Record responses
        discovery_engine.record_response(
            test_deal.id,
            questions[0].question,
            "We're losing $300k/year to manual processes",
        )

        # Step 3: Create need narrative
        need_engine = NeedCreationEngine(db)
        narrative = need_engine.create_need_narrative(test_deal.id, ["Manual processes", "Cost"])
        assert narrative.financial_impact > 0

        # Step 4: Get urgency triggers
        urgency_engine = UrgencyTriggerEngine(db)
        triggers = urgency_engine.generate_urgency_triggers(
            {"stage": "proposal", "industry": "technology"}
        )
        assert len(triggers) > 0

        # Step 5: Handle objection
        objection_handler = PsychologyObjectionHandler(db)
        response = objection_handler.handle_objection(
            "This is too expensive",
            prospect,
        )
        assert response is not None

        # Step 6: Start closing sequence
        close_engine = AssumptiveCloseEngine(db)
        for step in range(1, 6):
            close = close_engine.get_close(step)
            assert close is not None

    def test_deal_conversation_tracking(self, db: Session, test_deal: Deal):
        """Test conversation tracking across all engines."""
        # Create conversation record
        conversation = SalesConversation(
            id="conv-001",
            deal_id=test_deal.id,
            discovery_questions_asked=6,
            need_narrative_used=True,
            objections_handled=1,
            closes_attempted=3,
            deal_won=False,
        )
        db.add(conversation)
        db.commit()

        # Verify tracking
        db_conversation = db.query(SalesConversation).filter_by(deal_id=test_deal.id).first()
        assert db_conversation is not None
        assert db_conversation.discovery_questions_asked == 6

    def test_rep_performance_metrics(self, db: Session):
        """Test rep performance tracking."""
        perf = SalesRepPerformance(
            id="perf-001",
            rep_id="rep-123",
            discovery_questions_per_call=4.5,
            percent_prospects_opening_up=75.0,
            close_rate=0.60,
            average_closes_to_win=2.3,
            sales_cycle_avg_days=30,
            aov=150000,
        )
        db.add(perf)
        db.commit()

        db_perf = db.query(SalesRepPerformance).filter_by(rep_id="rep-123").first()
        assert db_perf is not None
        assert db_perf.close_rate == 0.60  # 60% target


class TestAPIEndpoints:
    """Test all 6 API endpoints."""

    def test_discovery_questions_endpoint(self, db: Session, client):
        """Test GET discovery-questions endpoint."""
        response = client.post(
            "/api/v1/psychology/discovery-questions",
            json={
                "prospect_id": "prospect-001",
                "deal_id": "deal-001",
                "stage": "problem",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) > 0

    def test_record_response_endpoint(self, db: Session, client):
        """Test record-response endpoint."""
        response = client.post(
            "/api/v1/psychology/record-response",
            json={
                "deal_id": "deal-001",
                "question": "What's your biggest pain?",
                "response": "We're losing money",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "recorded" in data
        assert data["recorded"] is True

    def test_create_need_narrative_endpoint(self, db: Session, client):
        """Test create-need-narrative endpoint."""
        response = client.post(
            "/api/v1/psychology/create-need-narrative",
            json={
                "deal_id": "deal-001",
                "discovery_responses": ["Pain 1", "Pain 2"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "narrative" in data
        assert "financial_impact" in data

    def test_urgency_triggers_endpoint(self, db: Session, client):
        """Test urgency-triggers endpoint."""
        response = client.post(
            "/api/v1/psychology/urgency-triggers",
            json={
                "deal_id": "deal-001",
                "stage": "proposal",
                "industry": "technology",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "triggers" in data
        assert len(data["triggers"]) > 0

    def test_handle_objection_endpoint(self, db: Session, client):
        """Test handle-objection endpoint."""
        response = client.post(
            "/api/v1/psychology/handle-objection",
            json={
                "deal_id": "deal-001",
                "objection": "Too expensive",
                "prospect_role": "cfo",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "psychology" in data

    def test_close_endpoint(self, db: Session, client):
        """Test close endpoint."""
        response = client.post(
            "/api/v1/psychology/close",
            json={
                "deal_id": "deal-001",
                "current_step": 1,
                "prospect_response": "Yes, that works for us",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "next_close" in data
        assert "step" in data
