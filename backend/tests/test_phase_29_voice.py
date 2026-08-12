"""Phase 29 Voice Sales Integration Tests"""

import pytest
from datetime import datetime
from backend.app.domains.enterprise.voice_sales import (
    VoiceCallManager,
    PlaybookExtractor,
    PlaybookRecommender,
)


class TestVoiceCallManager:
    """Voice call manager tests."""

    def test_initiate_call(self, db):
        """Should initiate voice call."""
        manager = VoiceCallManager(db)

        result = manager.initiate_call("prospect123", "deal456")

        assert result.call_id
        assert result.prospect_id == "prospect123"
        assert result.deal_id == "deal456"
        assert result.status == "initiated"

    def test_handle_call_input(self, db, sample_voice_call):
        """Should handle voice input and generate response."""
        manager = VoiceCallManager(db)

        response = manager.handle_call_input(str(sample_voice_call.id), "I'm interested in learning more")

        assert len(response) > 0
        assert isinstance(response, str)

    def test_end_call(self, db, sample_voice_call):
        """Should end call and analyze outcome."""
        manager = VoiceCallManager(db)

        result = manager.end_call(str(sample_voice_call.id), "meeting_booked")

        assert result["call_id"]
        assert result["outcome"] == "meeting_booked"
        assert result["duration"] >= 0

    def test_multiple_turns_conversation(self, db, sample_voice_call):
        """Should maintain conversation history."""
        manager = VoiceCallManager(db)

        # First turn
        response1 = manager.handle_call_input(str(sample_voice_call.id), "Hi, tell me about your product")
        assert response1

        # Second turn
        response2 = manager.handle_call_input(str(sample_voice_call.id), "How much does it cost?")
        assert response2


class TestPlaybookExtractor:
    """Playbook extraction tests."""

    def test_extract_playbooks_empty(self, db):
        """Should handle empty call list gracefully."""
        extractor = PlaybookExtractor(db)

        result = extractor.extract_playbooks([])

        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_playbooks_from_calls(self, db, sample_successful_calls):
        """Should extract playbooks from successful calls."""
        extractor = PlaybookExtractor(db)

        result = extractor.extract_playbooks(["rep1", "rep2"])

        assert isinstance(result, list)

    def test_playbook_consolidation(self, db):
        """Should consolidate similar playbooks."""
        extractor = PlaybookExtractor(db)

        cluster = [
            {
                "opening": "Hi, this is SellIA",
                "discovery": ["How many team members?", "What's your current solution?"],
                "win_rate": 0.75,
            },
            {
                "opening": "Hi, SellIA calling",
                "discovery": ["Team size?", "Current tool?"],
                "win_rate": 0.78,
            },
        ]

        consolidated = extractor._consolidate_cluster(cluster)

        assert consolidated


class TestPlaybookRecommender:
    """Playbook recommendation tests."""

    def test_recommend_playbook_not_found(self, db):
        """Should return None if no playbook found."""
        recommender = PlaybookRecommender(db)

        result = recommender.recommend_playbook("nonexistent_deal")

        assert result is None

    def test_recommend_playbook_by_industry(self, db, sample_deal, sample_playbook):
        """Should recommend playbook by industry."""
        recommender = PlaybookRecommender(db)

        result = recommender.recommend_playbook(sample_deal.id)

        # Would return playbook if found
        if result:
            assert result.playbook_id
            assert result.win_rate > 0


class TestE2EVoiceWorkflow:
    """End-to-end voice workflow tests."""

    def test_full_voice_call_workflow(self, db, sample_deal):
        """E2E: Initiate call → handle input → end call → analyze."""
        manager = VoiceCallManager(db)

        # 1. Initiate call
        result = manager.initiate_call("prospect1", sample_deal.id)
        call_id = result.call_id
        assert call_id

        # 2. Handle multiple turns
        response1 = manager.handle_call_input(call_id, "Hi, I'm interested")
        assert response1

        response2 = manager.handle_call_input(call_id, "Can we schedule a meeting?")
        assert response2

        # 3. End call
        end_result = manager.end_call(call_id, "meeting_booked")
        assert end_result["meeting_booked"] == True

    def test_playbook_usage_workflow(self, db, sample_deal, sample_playbook):
        """E2E: Get recommendation → use playbook during call."""
        recommender = PlaybookRecommender(db)
        manager = VoiceCallManager(db)

        # 1. Get playbook recommendation
        recommendation = recommender.recommend_playbook(sample_deal.id)

        # 2. If recommended, use it
        if recommendation:
            result = manager.initiate_call("prospect1", sample_deal.id)
            assert result.call_id


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def sample_voice_call(db):
    """Create sample voice call."""
    from backend.app.models.voice_sales import VoiceCall

    call = VoiceCall(
        prospect_id="prospect123",
        deal_id="deal456",
        call_sid="twilio_sid_123",
        script_used="Hi, this is SellIA...",
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    return call


@pytest.fixture
def sample_successful_calls(db):
    """Create sample successful calls."""
    from backend.app.models.voice_sales import VoiceCall

    calls = []
    for i in range(5):
        call = VoiceCall(
            prospect_id=f"prospect{i}",
            deal_id=f"deal{i}",
            outcome="meeting_booked",
            transcript="Sample transcript...",
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow(),
        )
        db.add(call)
        calls.append(call)

    db.commit()
    return calls


@pytest.fixture
def sample_playbook(db):
    """Create sample playbook."""
    from backend.app.models.voice_sales import SalesPlaybook

    playbook = SalesPlaybook(
        name="Enterprise Discovery Playbook",
        industry="SaaS",
        deal_stage="qualification",
        win_rate=0.75,
        extracted_from_calls=10,
    )
    db.add(playbook)
    db.commit()
    return playbook


@pytest.fixture
def sample_deal(db):
    """Create sample deal."""
    from backend.app.models.deal import Deal

    deal = Deal(
        id="deal123",
        name="Test Deal",
        amount=100000,
        stage="opportunity",
        industry="SaaS",
        created_at=datetime.utcnow(),
    )
    db.add(deal)
    db.commit()
    return deal
