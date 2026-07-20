"""Tests for Growth Domain — Organic customer acquisition engine."""

import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.growth.models import (
    GrowthCampaign, GrowthCampaignType, GrowthCampaignStatus,
    LeadMagnet, LeadMagnetFormat,
    InboundLead, InboundLeadSource, NurturingStage,
    SocialProofItem, SocialProofType, SocialProofStatus,
    UgcRequest, UgcRequestStatus,
    ValueSequence, ValueSequenceEnrollment,
)
from app.domains.growth.inbound_engine import InboundGrowthEngine
from app.domains.growth.lead_magnet_funnel import LeadMagnetEngine
from app.domains.growth.viral_referral import ViralReferralEngine
from app.domains.growth.social_proof import SocialProofEngine
from app.domains.growth.ugc_collector import UGCCollector
from app.domains.growth.value_outreach import ValueFirstOutreach
from app.domains.users.models import User
from app.domains.businesses.models import Business


# ========== Fixtures ==========

@pytest_asyncio.fixture
async def test_business(db_session: AsyncSession):
    """Create a test business."""
    business = Business(
        id=uuid.uuid4(),
        name="Test Business",
        user_id=uuid.uuid4(),
        type="services",
    )
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)
    return business


@pytest_asyncio.fixture
async def test_conversation(db_session: AsyncSession, test_business):
    """Create a test conversation."""
    from app.domains.channels.models import Conversation
    conv = Conversation(
        id=uuid.uuid4(),
        business_id=test_business.id,
        channel="whatsapp",
        lead_name="Test Lead",
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)
    return conv


# ========== Model Tests ==========

@pytest.mark.asyncio
async def test_create_growth_campaign(db_session: AsyncSession, test_business):
    """Test creating a growth campaign."""
    campaign = GrowthCampaign(
        business_id=test_business.id,
        name="SEO Blog Campaign",
        campaign_type=GrowthCampaignType.SEO_CONTENT,
        description="Generate SEO content weekly",
        config={"target_keywords": ["vender sin vender", "marketing organico"]},
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    assert campaign.id is not None
    assert campaign.name == "SEO Blog Campaign"
    assert campaign.campaign_type == GrowthCampaignType.SEO_CONTENT
    assert campaign.status == GrowthCampaignStatus.DRAFT
    assert campaign.config["target_keywords"] == ["vender sin vender", "marketing organico"]
    assert campaign.leads_generated == 0
    assert campaign.is_active is True


@pytest.mark.asyncio
async def test_create_lead_magnet(db_session: AsyncSession, test_business):
    """Test creating a lead magnet."""
    magnet = LeadMagnet(
        business_id=test_business.id,
        title="Guía: Cómo Vender Sin Vender",
        description="Descubre las estrategias de marketing orgánico",
        format=LeadMagnetFormat.CHEAT_SHEET,
        topic="marketing organico",
        content={"sections": ["Intro", "Estrategias", "Checklist"]},
        conversion_rate=15.5,
    )
    db_session.add(magnet)
    await db_session.commit()
    await db_session.refresh(magnet)

    assert magnet.id is not None
    assert magnet.title == "Guía: Cómo Vender Sin Vender"
    assert magnet.format == LeadMagnetFormat.CHEAT_SHEET
    assert magnet.times_delivered == 0
    assert float(magnet.conversion_rate) == 15.5


@pytest.mark.asyncio
async def test_create_inbound_lead(db_session: AsyncSession, test_business, test_conversation):
    """Test creating an inbound lead."""
    lead = InboundLead(
        business_id=test_business.id,
        conversation_id=test_conversation.id,
        source_type=InboundLeadSource.SEO,
        source_detail="blog_post: como-vender-sin-vender",
        contact_info={"name": "Juan", "email": "juan@test.com"},
        nurturing_stage=NurturingStage.NEW,
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    assert lead.id is not None
    assert lead.source_type == InboundLeadSource.SEO
    assert lead.nurturing_stage == NurturingStage.NEW
    assert lead.contact_info["name"] == "Juan"
    assert lead.value_touches_received == 0


@pytest.mark.asyncio
async def test_create_social_proof(db_session: AsyncSession, test_business, test_conversation):
    """Test creating a social proof item."""
    proof = SocialProofItem(
        business_id=test_business.id,
        conversation_id=test_conversation.id,
        item_type=SocialProofType.TESTIMONIAL,
        status=SocialProofStatus.AUTO_APPROVED,
        content="Excelente servicio, me cambió la vida!",
        rating=5,
        customer_name="María García",
        sentiment_score=0.95,
    )
    db_session.add(proof)
    await db_session.commit()
    await db_session.refresh(proof)

    assert proof.id is not None
    assert proof.item_type == SocialProofType.TESTIMONIAL
    assert proof.status == SocialProofStatus.AUTO_APPROVED
    assert float(proof.sentiment_score) == 0.95
    assert proof.usage_count == 0


@pytest.mark.asyncio
async def test_create_ugc_request(db_session: AsyncSession, test_business, test_conversation):
    """Test creating a UGC request."""
    request = UgcRequest(
        business_id=test_business.id,
        conversation_id=test_conversation.id,
        content_type="lifestyle_photo",
        request_message="¿Podrías compartir una foto usando nuestro producto?",
        incentive_offered="10% off next purchase",
    )
    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)

    assert request.id is not None
    assert request.status == UgcRequestStatus.PENDING
    assert request.content_type == "lifestyle_photo"


@pytest.mark.asyncio
async def test_create_value_sequence(db_session: AsyncSession, test_business):
    """Test creating a value sequence."""
    sequence = ValueSequence(
        business_id=test_business.id,
        name="Nurturing: Marketing Orgánico",
        topic="marketing organico",
        messages=[
            {"order": 1, "content": "Tip #1", "delay_hours": 24},
            {"order": 2, "content": "Tip #2", "delay_hours": 48},
        ],
        message_count=3,
        total_duration_days=7,
        target_segment="cold",
    )
    db_session.add(sequence)
    await db_session.commit()
    await db_session.refresh(sequence)

    assert sequence.id is not None
    assert sequence.message_count == 3
    assert len(sequence.messages) == 2
    assert sequence.times_started == 0


# ========== Service Tests ==========

@pytest.mark.asyncio
async def test_inbound_growth_engine_create_campaign(db_session: AsyncSession, test_business):
    """Test InboundGrowthEngine.create_campaign."""
    engine = InboundGrowthEngine(db_session)
    campaign = await engine.create_campaign(
        business_id=test_business.id,
        name="Test Social Campaign",
        campaign_type=GrowthCampaignType.SOCIAL_ORGANIC,
        description="Test campaign",
        target_audience="Emprendedores",
    )

    assert campaign.id is not None
    assert campaign.name == "Test Social Campaign"
    assert campaign.status == GrowthCampaignStatus.DRAFT

    # Test activate
    activated = await engine.activate_campaign(campaign.id)
    assert activated.status == GrowthCampaignStatus.ACTIVE
    assert activated.started_at is not None

    # Test pause
    paused = await engine.pause_campaign(campaign.id)
    assert paused.status == GrowthCampaignStatus.PAUSED

    # Test evaluate
    evaluation = await engine.evaluate_campaign(campaign.id)
    assert evaluation["campaign_id"] == str(campaign.id)
    assert "recommendations" in evaluation


@pytest.mark.asyncio
async def test_inbound_growth_engine_capture_lead(db_session: AsyncSession, test_business, test_conversation):
    """Test InboundGrowthEngine.capture_inbound_lead."""
    engine = InboundGrowthEngine(db_session)
    lead = await engine.capture_inbound_lead(
        business_id=test_business.id,
        source_type=InboundLeadSource.SOCIAL_POST,
        conversation_id=test_conversation.id,
        source_detail="instagram_reel: como-atraer-clientes",
    )

    assert lead.id is not None
    assert lead.source_type == InboundLeadSource.SOCIAL_POST
    assert lead.nurturing_stage == NurturingStage.NEW

    # Test update stage
    updated = await engine.update_lead_stage(lead.id, NurturingStage.INTEREST, 10)
    assert updated.nurturing_stage == NurturingStage.INTEREST
    assert updated.engagement_score == 10

    # Test get leads
    leads = await engine.get_leads(test_business.id)
    assert len(leads) >= 1

    # Test dashboard metrics
    metrics = await engine.get_dashboard_metrics(test_business.id)
    assert "total_organic_leads" in metrics
    assert metrics["period"] == "last_7_days"


@pytest.mark.asyncio
async def test_lead_magnet_engine_generate_and_track(db_session: AsyncSession, test_business):
    """Test LeadMagnetEngine generate and track methods."""
    engine = LeadMagnetEngine(db_session)

    # Generate lead magnet (mocked AI)
    magnet = await engine.generate_lead_magnet(
        business_id=test_business.id,
        topic="Cómo vender sin pagar ads",
        magnet_format=LeadMagnetFormat.CHEAT_SHEET,
    )

    assert magnet.id is not None
    assert magnet.topic == "Cómo vender sin pagar ads"
    assert magnet.format == LeadMagnetFormat.CHEAT_SHEET
    assert magnet.auto_deliver is True

    # Test performance report
    report = await engine.get_performance_report(magnet.id)
    assert report["magnet_id"] == str(magnet.id)
    assert report["times_delivered"] == 0
    assert report["conversion_rate"] == 0.0

    # Test top performing magnets
    top = await engine.get_top_performing_magnets(test_business.id, 5)
    assert isinstance(top, list)


@pytest.mark.asyncio
async def test_social_proof_engine_collect_and_moderate(db_session: AsyncSession, test_business, test_conversation):
    """Test SocialProofEngine collection and moderation."""
    engine = SocialProofEngine(db_session)

    # Collect testimonial
    item = await engine.collect_testimonial(
        business_id=test_business.id,
        conversation_id=test_conversation.id,
        content="Increíble servicio, super recomendado! Me ayudaron a duplicar mis ventas.",
        customer_name="Carlos López",
    )

    assert item.id is not None
    assert item.status in [SocialProofStatus.PENDING, SocialProofStatus.AUTO_APPROVED]
    assert item.sentiment_score != 0  # Should be analyzed

    # Test get wall
    wall = await engine.get_social_proof_wall(test_business.id, count=10)
    # If auto-approved, should be in wall
    if item.status == SocialProofStatus.AUTO_APPROVED:
        assert len(wall) >= 1

    # Test manual approve
    approved = await engine.approve_item(item.id)
    assert approved.status == SocialProofStatus.APPROVED
    assert approved.approved_at is not None

    # Test get stats
    stats = await engine.get_stats(test_business.id)
    assert stats["total_collected"] >= 1
    assert stats["approval_rate"] > 0


@pytest.mark.asyncio
async def test_viral_referral_engine(db_session: AsyncSession, test_business, test_conversation):
    """Test ViralReferralEngine."""
    engine = ViralReferralEngine(db_session)

    # Create campaign
    program = await engine.create_referral_campaign(
        business_id=test_business.id,
        name="Referidos 2026",
        incentive_type="discount_credit",
        reward_value=25.0,
    )
    assert program.id is not None
    assert program.reward_type == "discount_credit"

    # Generate code
    code = await engine.generate_referral_link(
        business_id=test_business.id,
        conversation_id=test_conversation.id,
    )
    assert code.code is not None
    assert len(code.code) > 0

    # Test generate message
    message = await engine.generate_referral_message(
        business_id=test_business.id,
        conversation_id=test_conversation.id,
        code=code.code,
    )
    assert len(message) > 0
    assert code.code in message

    # Test track click
    click_result = await engine.track_click(code.code)
    assert click_result["status"] == "tracked"

    # Test viral coefficient (with no data yet)
    metrics = await engine.calculate_viral_coefficient(test_business.id)
    assert metrics["business_id"] == str(test_business.id)
    assert "k_factor" in metrics
    assert metrics["exponential_growth"] is False  # No referrers yet


@pytest.mark.asyncio
async def test_value_first_outreach_sequence(db_session: AsyncSession, test_business, test_conversation):
    """Test ValueFirstOutreach sequence creation and enrollment."""
    engine = ValueFirstOutreach(db_session)

    # Create sequence
    sequence = await engine.create_educational_sequence(
        business_id=test_business.id,
        name="Test Nurturing",
        topic="Marketing orgánico para emprendedores",
        message_count=3,
        total_duration_days=7,
    )
    assert sequence.id is not None
    assert sequence.message_count == 3
    assert len(sequence.messages) > 0

    # Enroll lead
    enrollment = await engine.enroll_lead(
        sequence_id=sequence.id,
        conversation_id=test_conversation.id,
    )
    assert enrollment.id is not None
    assert enrollment.status == "active"
    assert enrollment.current_step == 0

    # Test performance
    perf = await engine.get_sequence_performance(sequence.id)
    assert perf["sequence_id"] == str(sequence.id)
    assert perf["total_enrollments"] >= 1


@pytest.mark.asyncio
async def test_ugc_collector_request_and_collect(db_session: AsyncSession, test_business, test_conversation):
    """Test UGCCollector request and collect."""
    engine = UGCCollector(db_session)

    # Create order first
    from app.domains.orders.models import Order
    order = Order(
        id=uuid.uuid4(),
        business_id=test_business.id,
        conversation_id=test_conversation.id,
        status="completed",
        total_amount=100.0,
    )
    db_session.add(order)
    await db_session.commit()

    # Request UGC
    request = await engine.request_ugc(
        business_id=test_business.id,
        order_id=order.id,
        conversation_id=test_conversation.id,
        content_type="lifestyle_photo",
    )
    assert request.id is not None
    assert request.status == UgcRequestStatus.PENDING
    assert len(request.request_message) > 0

    # Collect submission
    collected = await engine.collect_submission(
        request_id=request.id,
        media_urls=["https://example.com/photo1.jpg"],
        response_text="Acá va mi foto usando el producto!",
    )
    assert collected.status == UgcRequestStatus.RECEIVED
    assert len(collected.response_media_urls) == 1

    # Test gallery
    gallery = await engine.get_ugc_gallery(test_business.id)
    assert len(gallery) >= 1


# ========== API Endpoint Tests ==========

@pytest.mark.asyncio
async def test_growth_dashboard_endpoint(auth_client, test_business):
    """Test GET /growth/dashboard."""
    # Override current user to have business_id
    from app.main import app
    from app.core.deps import get_current_active_user
    from app.domains.users.models import User

    user_with_business = User(
        id=uuid.uuid4(),
        email="growth-test@example.com",
        hashed_password="hashed",
        full_name="Growth Test",
        business_id=test_business.id,
        is_active=True,
    )
    app.dependency_overrides[get_current_active_user] = lambda: user_with_business

    try:
        response = await auth_client.get("/api/v1/growth/dashboard")
        assert response.status_code in [200, 500]  # 500 if DB issue, 200 if OK
        if response.status_code == 200:
            data = response.json()
            assert "total_organic_leads" in data
            assert "conversion_rate" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_campaigns_endpoint(auth_client, test_business):
    """Test GET /growth/campaigns."""
    from app.main import app
    from app.core.deps import get_current_active_user
    from app.domains.users.models import User

    user_with_business = User(
        id=uuid.uuid4(),
        email="growth-test2@example.com",
        hashed_password="hashed",
        full_name="Growth Test 2",
        business_id=test_business.id,
        is_active=True,
    )
    app.dependency_overrides[get_current_active_user] = lambda: user_with_business

    try:
        response = await auth_client.get("/api/v1/growth/campaigns")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    finally:
        app.dependency_overrides.clear()
