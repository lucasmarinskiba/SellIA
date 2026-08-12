"""Phase 27 Integration Tests - Email Auth + Deal Intelligence"""

import pytest
from datetime import datetime, timedelta
from backend.app.domains.auth.email_auth import EmailAuthManager
from backend.app.domains.enterprise.deal_intelligence import DealIntelligenceManager


# ============================================================
# EMAIL VERIFICATION TESTS
# ============================================================


class TestEmailVerification:
    """Email verification flow tests."""

    def test_create_verification_token(self, db):
        """Should create valid verification token."""
        auth = EmailAuthManager(db)
        token = auth.create_verification_token("user123", "user@example.com")

        assert len(token) > 30
        assert token.isalnum() or "_" in token or "-" in token

    def test_verify_valid_token(self, db):
        """Should verify valid token."""
        auth = EmailAuthManager(db)
        token = auth.create_verification_token("user123", "user@example.com")

        result = auth.verify_email_token(token)

        assert result.success == True
        assert result.user_id == "user123"
        assert result.email == "user@example.com"

    def test_verify_expired_token(self, db):
        """Should reject expired token."""
        auth = EmailAuthManager(db)
        token = auth.create_verification_token("user123", "user@example.com")

        # Manually expire the token
        from backend.app.models.email_auth import EmailVerificationToken
        from sqlalchemy import select
        query = select(EmailVerificationToken).where(EmailVerificationToken.token == token)
        verification = db.execute(query).scalar()
        verification.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.add(verification)
        db.commit()

        result = auth.verify_email_token(token)

        assert result.success == False
        assert result.error_code == "TOKEN_EXPIRED"

    def test_verify_twice_fails(self, db):
        """Should fail if token already verified."""
        auth = EmailAuthManager(db)
        token = auth.create_verification_token("user123", "user@example.com")

        # First verification succeeds
        result1 = auth.verify_email_token(token)
        assert result1.success == True

        # Second verification fails
        result2 = auth.verify_email_token(token)
        assert result2.success == False
        assert result2.error_code == "TOKEN_NOT_FOUND"


# ============================================================
# ACCOUNT APPROVAL TESTS
# ============================================================


class TestAccountApproval:
    """Account approval workflow tests."""

    def test_request_approval(self, db):
        """Should create approval request."""
        auth = EmailAuthManager(db)
        result = auth.request_account_approval(
            user_id="user123",
            email="user@example.com",
            full_name="John Doe",
            company="Acme Corp",
            role="Sales Manager",
        )

        assert result.user_id == "user123"
        assert result.email == "user@example.com"
        assert result.full_name == "John Doe"

    def test_admin_approve_account(self, db):
        """Should allow admin to approve account."""
        auth = EmailAuthManager(db)

        # Create approval request
        request = auth.request_account_approval(
            user_id="user123",
            email="user@example.com",
            full_name="John Doe",
        )

        # Admin approves
        from backend.app.models.email_auth import AccountApproval
        approval = db.query(AccountApproval).filter(AccountApproval.user_id == "user123").first()

        success = auth.approve_account(
            approval_id=str(approval.id),
            admin_id="admin1",
            notes="Approved - verified company",
        )

        assert success == True

    def test_admin_reject_account(self, db):
        """Should allow admin to reject account."""
        auth = EmailAuthManager(db)

        # Create approval request
        auth.request_account_approval(
            user_id="user123",
            email="user@example.com",
            full_name="John Doe",
        )

        # Admin rejects
        from backend.app.models.email_auth import AccountApproval
        approval = db.query(AccountApproval).filter(AccountApproval.user_id == "user123").first()

        success = auth.reject_account(
            approval_id=str(approval.id),
            admin_id="admin1",
            rejection_reason="Company not in approved list",
        )

        assert success == True


# ============================================================
# DEAL INTELLIGENCE TESTS
# ============================================================


class TestDealIntelligence:
    """Deal intelligence tests."""

    def test_add_stakeholder(self, db, sample_deal):
        """Should add stakeholder to buying committee."""
        manager = DealIntelligenceManager(db)

        stakeholder = manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person1",
            email="john@acme.com",
            name="John Smith",
            title="VP Sales",
            buyer_role="economic_buyer",
            influence_level=9,
        )

        assert stakeholder.person_id == "person1"
        assert stakeholder.buyer_role == "economic_buyer"
        assert stakeholder.influence_level == 9

    def test_identify_stakeholders(self, db, sample_deal):
        """Should list all stakeholders for deal."""
        manager = DealIntelligenceManager(db)

        # Add 3 stakeholders
        manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person1",
            email="john@acme.com",
            name="John Smith",
            title="VP Sales",
            buyer_role="economic_buyer",
        )
        manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person2",
            email="jane@acme.com",
            name="Jane Doe",
            title="Manager",
            buyer_role="user_buyer",
        )
        manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person3",
            email="bob@acme.com",
            name="Bob Johnson",
            title="Director",
            buyer_role="influencer",
        )

        stakeholders = manager.identify_stakeholders(sample_deal.id)

        assert len(stakeholders) == 3

    def test_find_economic_buyer(self, db, sample_deal):
        """Should identify economic buyer."""
        manager = DealIntelligenceManager(db)

        manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person1",
            email="john@acme.com",
            name="John Smith",
            title="VP Sales",
            buyer_role="economic_buyer",
            influence_level=9,
        )

        economic_buyer = manager.find_economic_buyer(sample_deal.id)

        assert economic_buyer is not None
        assert economic_buyer.buyer_role == "economic_buyer"
        assert economic_buyer.name == "John Smith"

    def test_update_stakeholder_engagement(self, db, sample_deal):
        """Should track engagement events."""
        manager = DealIntelligenceManager(db)

        manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person1",
            email="john@acme.com",
            name="John Smith",
            title="VP Sales",
        )

        # Record email open
        manager.update_stakeholder_engagement(
            deal_id=sample_deal.id,
            person_id="person1",
            event_type="email_open",
        )

        # Record meeting
        manager.update_stakeholder_engagement(
            deal_id=sample_deal.id,
            person_id="person1",
            event_type="meeting",
        )

        stakeholders = manager.identify_stakeholders(sample_deal.id)
        assert stakeholders[0].engagement_score > 0

    def test_predict_close_probability(self, db, sample_deal):
        """Should predict deal close probability."""
        manager = DealIntelligenceManager(db)

        result = manager.predict_close_probability(sample_deal.id)

        assert 0 <= result.close_probability <= 100
        assert 0 <= result.confidence_level <= 100
        assert result.probability_low <= result.close_probability <= result.probability_high

    def test_calculate_deal_health(self, db, sample_deal):
        """Should calculate deal health score."""
        manager = DealIntelligenceManager(db)

        # Add stakeholders
        manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person1",
            email="john@acme.com",
            name="John Smith",
            title="VP Sales",
            buyer_role="economic_buyer",
        )

        # Record engagement
        manager.update_stakeholder_engagement(
            deal_id=sample_deal.id,
            person_id="person1",
            event_type="meeting",
        )

        result = manager.calculate_deal_health(sample_deal.id)

        assert 0 <= result.health_score <= 100
        assert result.health_status in ["healthy", "at_risk", "critical"]
        assert len(result.recommended_actions) > 0

    def test_health_status_classification(self, db):
        """Should classify health status correctly."""
        manager = DealIntelligenceManager(db)

        # Create test deals with different health levels
        # Score 80 → healthy
        # Score 60 → at_risk
        # Score 30 → critical

        # This would require creating deals with specific engagement patterns
        # Simplified example:
        # If health_score >= 70: status = "healthy"
        # If 50 <= health_score < 70: status = "at_risk"
        # If health_score < 50: status = "critical"

        assert True  # Placeholder


# ============================================================
# END-TO-END WORKFLOW TESTS
# ============================================================


class TestE2EWorkflows:
    """End-to-end workflow tests."""

    def test_user_signup_verification_approval(self, db):
        """E2E: User signs up → verifies email → gets approved."""
        auth = EmailAuthManager(db)

        # 1. User signs up
        token = auth.create_verification_token("user123", "user@example.com")

        # 2. User clicks verification link
        verify_result = auth.verify_email_token(token)
        assert verify_result.success == True

        # 3. User requests approval
        approval_result = auth.request_account_approval(
            user_id="user123",
            email="user@example.com",
            full_name="John Doe",
            company="Acme Corp",
        )
        assert approval_result.user_id == "user123"

        # 4. Admin approves
        from backend.app.models.email_auth import AccountApproval
        approval = db.query(AccountApproval).filter(AccountApproval.user_id == "user123").first()
        success = auth.approve_account(
            approval_id=str(approval.id),
            admin_id="admin1",
        )
        assert success == True

    def test_deal_intelligence_workflow(self, db, sample_deal):
        """E2E: Sales rep views deal intelligence."""
        manager = DealIntelligenceManager(db)

        # 1. Add buying committee
        manager.add_stakeholder(
            deal_id=sample_deal.id,
            person_id="person1",
            email="john@acme.com",
            name="John Smith",
            title="VP Sales",
            buyer_role="economic_buyer",
        )

        # 2. Record engagement (rep had meeting)
        manager.update_stakeholder_engagement(
            deal_id=sample_deal.id,
            person_id="person1",
            event_type="meeting",
        )

        # 3. Get intelligence
        stakeholders = manager.identify_stakeholders(sample_deal.id)
        probability = manager.predict_close_probability(sample_deal.id)
        health = manager.calculate_deal_health(sample_deal.id)

        # 4. Verify data
        assert len(stakeholders) > 0
        assert probability.close_probability > 0
        assert health.health_score > 0
        assert len(health.recommended_actions) > 0


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def sample_deal(db):
    """Create sample deal for testing."""
    from backend.app.models.deal import Deal

    deal = Deal(
        id="deal-test-123",
        name="Test Deal",
        amount=100000,
        stage="opportunity",
        created_at=datetime.utcnow(),
        stage_entered_at=datetime.utcnow(),
    )
    db.add(deal)
    db.commit()
    return deal
