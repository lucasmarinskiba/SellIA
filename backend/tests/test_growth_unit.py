"""Comprehensive unit tests for ALL 11 Growth Engines.

NO database required. Uses mocking for ALL external dependencies.
Covers business logic not already well-tested in test_growth.py (integration).
"""

import uuid
import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

# Models
from app.domains.growth.models import (
    LeadMagnet, LeadMagnetFormat,
    InboundLead, InboundLeadSource, NurturingStage,
    SocialProofItem, SocialProofType, SocialProofStatus,
    UgcRequest, UgcRequestStatus,
    ValueSequence, ValueSequenceEnrollment,
)

# Engines
from app.domains.growth.inbound_engine import InboundGrowthEngine
from app.domains.growth.lead_magnet_funnel import LeadMagnetEngine
from app.domains.growth.viral_referral import ViralReferralEngine
from app.domains.growth.social_proof import SocialProofEngine
from app.domains.growth.ugc_collector import UGCCollector
from app.domains.growth.value_outreach import ValueFirstOutreach
from app.domains.growth.comment_responder import CommentResponder
from app.domains.growth.content_syndication import ContentSyndicationEngine
from app.domains.growth.seo_pipeline import SEOPipeline
from app.domains.growth.voice_note_engine import VoiceNoteEngine
from app.domains.growth.warm_lead_detector import WarmLeadDetector


# ========== Helpers ==========

def mock_db():
    """Create a mocked AsyncSession."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    db.delete = AsyncMock()
    return db


def make_uuid():
    return uuid.uuid4()


# ========== 1. InboundGrowthEngine ==========

class TestInboundGrowthEngine:
    """Light tests for get_dashboard_metrics date math (integration tests cover the rest)."""

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics_date_math(self):
        """Verify get_dashboard_metrics computes week_ago correctly and aggregates results."""
        db = mock_db()
        engine = InboundGrowthEngine(db)

        # Mock scalar results for each execute call
        scalars = [
            MagicMock(scalar=lambda: 5),    # leads this week
            MagicMock(scalar=lambda: 20),   # total organic leads
            MagicMock(scalar=lambda: 2),    # total conversions
            MagicMock(scalar=lambda: 3),    # active campaigns
            MagicMock(all=lambda: [(InboundLeadSource.SEO, 10), (InboundLeadSource.SOCIAL_POST, 10)]),
        ]

        async def side_effect(*args, **kwargs):
            return scalars.pop(0)

        db.execute.side_effect = side_effect

        metrics = await engine.get_dashboard_metrics(make_uuid())

        assert metrics["leads_this_week"] == 5
        assert metrics["total_organic_leads"] == 20
        assert metrics["total_conversions"] == 2
        assert metrics["conversion_rate"] == 10.0  # (2/20)*100
        assert metrics["active_campaigns"] == 3
        assert metrics["period"] == "last_7_days"
        assert "sources_breakdown" in metrics


# ========== 2. LeadMagnetEngine ==========

class TestLeadMagnetEngine:
    @pytest.mark.asyncio
    async def test_generate_lead_magnet_with_mocked_ai(self):
        """Test generate_lead_magnet when AI returns valid JSON."""
        db = mock_db()
        engine = LeadMagnetEngine(db)

        ai_json = json.dumps({
            "title": "Guía Secreta",
            "description": "Descubre todo",
            "sections": ["Intro", "Cuerpo"],
            "key_takeaways": ["Tip 1", "Tip 2"],
            "preview_text": "Preview",
            "cta": "Descarga ya",
        })

        with patch("app.domains.growth.lead_magnet_funnel.generate_raw_ai_response", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = ai_json
            magnet = await engine.generate_lead_magnet(
                business_id=make_uuid(),
                topic="Marketing",
                magnet_format=LeadMagnetFormat.CHEAT_SHEET,
            )

        assert isinstance(magnet, LeadMagnet)
        assert magnet.title == "Guía Secreta"
        assert magnet.format == LeadMagnetFormat.CHEAT_SHEET
        db.add.assert_called()
        db.commit.assert_called()
        db.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_deliver_lead_magnet_allowed(self):
        """Test deliver_lead_magnet when fatigue allows contact."""
        db = mock_db()
        engine = LeadMagnetEngine(db)

        magnet = MagicMock(spec=LeadMagnet)
        magnet.id = make_uuid()
        magnet.business_id = make_uuid()
        magnet.delivery_message = "¡Aquí tienes tu guía!"
        magnet.delivery_channel = "whatsapp"
        magnet.times_delivered = 0

        with patch.object(engine, "_get_magnet", new_callable=AsyncMock, return_value=magnet), \
             patch.object(engine.fatigue, "can_contact_now", new_callable=AsyncMock, return_value={"allowed": True}), \
             patch("app.domains.channels.services.send_outbound_message", new_callable=AsyncMock) as mock_send, \
             patch("app.core.events.event_bus.emit", new_callable=AsyncMock) as mock_event:

            result = await engine.deliver_lead_magnet(magnet.id, make_uuid())

        assert result["status"] == "delivered"
        assert magnet.times_delivered == 1
        mock_send.assert_called_once()
        args, kwargs = mock_event.call_args
        assert args[0] == "lead_magnet.delivered"
        assert isinstance(args[1], dict)

    @pytest.mark.asyncio
    async def test_deliver_lead_magnet_blocked_by_fatigue(self):
        """Test deliver_lead_magnet when fatigue blocks contact."""
        db = mock_db()
        engine = LeadMagnetEngine(db)

        magnet = MagicMock(spec=LeadMagnet)
        magnet.id = make_uuid()
        magnet.business_id = make_uuid()
        magnet.delivery_channel = "whatsapp"

        with patch.object(engine, "_get_magnet", new_callable=AsyncMock, return_value=magnet), \
             patch.object(engine.fatigue, "can_contact_now", new_callable=AsyncMock, return_value={"allowed": False, "reason": "too_soon"}):

            result = await engine.deliver_lead_magnet(magnet.id, make_uuid())

        assert result["status"] == "blocked"
        assert result["reason"] == "too_soon"

    @pytest.mark.asyncio
    async def test_track_conversion(self):
        """Test track_conversion increments metrics and emits event."""
        db = mock_db()
        engine = LeadMagnetEngine(db)

        magnet = MagicMock(spec=LeadMagnet)
        magnet.id = make_uuid()
        magnet.business_id = make_uuid()
        magnet.times_delivered = 10
        magnet.times_converted = 2
        magnet.conversion_rate = 20.0

        with patch.object(engine, "_get_magnet", new_callable=AsyncMock, return_value=magnet), \
             patch("app.core.events.event_bus.emit", new_callable=AsyncMock) as mock_event:

            result = await engine.track_conversion(magnet.id, make_uuid())

        assert result is magnet
        assert magnet.times_converted == 3
        assert magnet.conversion_rate == 30.0  # (3/10)*100
        args, kwargs = mock_event.call_args
        assert args[0] == "lead_magnet.converted"
        assert isinstance(args[1], dict)


# ========== 3. ViralReferralEngine ==========

class TestViralReferralEngine:
    @pytest.mark.asyncio
    async def test_calculate_viral_coefficient_zero_division(self):
        """Test calculate_viral_coefficient handles zero referrers and zero signups."""
        db = mock_db()
        engine = ViralReferralEngine(db)

        # All counts return 0
        mock_result = MagicMock()
        mock_result.scalar = lambda: 0
        db.execute.return_value = mock_result

        result = await engine.calculate_viral_coefficient(make_uuid())

        assert result["unique_referrers"] == 0
        assert result["total_signups"] == 0
        assert result["total_conversions"] == 0
        assert result["signups_per_referrer"] == 0
        assert result["conversion_rate"] == 0
        assert result["k_factor"] == 0
        assert result["exponential_growth"] is False
        assert result["k_interpretation"] == "sub_linear"


# ========== 4. SocialProofEngine ==========

class TestSocialProofEngine:
    @pytest.mark.parametrize("text,expected_sentiment", [
        ("Excelente servicio, genial y recomiendo mucho", pytest.approx(1.0, abs=0.1)),
        ("Malo, horrible y terrible producto", pytest.approx(-1.0, abs=0.1)),
        ("El producto llegó tarde pero funciona bien", pytest.approx(0.0, abs=0.5)),
        ("Sin comentarios especiales", 0.0),
    ])
    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, text, expected_sentiment):
        """Test _analyze_sentiment pure logic with various inputs."""
        db = mock_db()
        engine = SocialProofEngine(db)
        score = await engine._analyze_sentiment(text)
        assert score == expected_sentiment or abs(score - expected_sentiment) < 0.2

    @pytest.mark.asyncio
    async def test_request_review_sent_immediately(self):
        """Test request_review sends immediately when delay_hours <= 0."""
        db = mock_db()
        engine = SocialProofEngine(db)

        # No existing review
        mock_existing = MagicMock()
        mock_existing.scalar_one_or_none = lambda: None
        db.execute.return_value = mock_existing

        with patch.object(engine, "_generate_review_request", new_callable=AsyncMock, return_value="¿Nos dejas una review?"), \
             patch("app.domains.channels.services.send_outbound_message", new_callable=AsyncMock) as mock_send:

            result = await engine.request_review(
                business_id=make_uuid(),
                order_id=make_uuid(),
                conversation_id=make_uuid(),
                channel="whatsapp",
                delay_hours=0,
            )

        assert result["status"] == "sent"
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_inject_into_message_with_proof(self):
        """Test inject_into_message appends testimonial when proof exists."""
        db = mock_db()
        engine = SocialProofEngine(db)

        proof_item = MagicMock(spec=SocialProofItem)
        proof_item.content = "Me encantó el servicio, super recomendado"
        proof_item.customer_name = "Ana"
        proof_item.usage_count = 0
        proof_item.last_used_at = None

        with patch.object(engine, "get_social_proof_wall", new_callable=AsyncMock, return_value=[proof_item]):
            result = await engine.inject_into_message(make_uuid(), "Hola, tenemos una oferta")

        assert "Me encantó el servicio" in result
        assert "Ana" in result
        assert proof_item.usage_count == 1
        assert proof_item.last_used_at is not None
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_inject_into_message_no_proof(self):
        """Test inject_into_message returns original message when no proof exists."""
        db = mock_db()
        engine = SocialProofEngine(db)

        with patch.object(engine, "get_social_proof_wall", new_callable=AsyncMock, return_value=[]):
            result = await engine.inject_into_message(make_uuid(), "Hola, tenemos una oferta")

        assert result == "Hola, tenemos una oferta"


# ========== 5. UGCCollector ==========

class TestUGCCollector:
    @pytest.mark.asyncio
    async def test_request_ugc_new(self):
        """Test request_ugc creates a new request when none exists."""
        db = mock_db()
        engine = UGCCollector(db)

        mock_existing = MagicMock()
        mock_existing.scalar_one_or_none = lambda: None
        db.execute.return_value = mock_existing

        with patch.object(engine, "_generate_ugc_request", new_callable=AsyncMock, return_value="¿Nos mandas una foto?"):
            result = await engine.request_ugc(
                business_id=make_uuid(),
                order_id=make_uuid(),
                conversation_id=make_uuid(),
                content_type="lifestyle_photo",
            )

        assert isinstance(result, UgcRequest)
        assert result.status == UgcRequestStatus.PENDING
        db.add.assert_called()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_send_ugc_request_allowed(self):
        """Test send_ugc_request delivers message when fatigue allows."""
        db = mock_db()
        engine = UGCCollector(db)

        ugc_req = MagicMock(spec=UgcRequest)
        ugc_req.id = make_uuid()
        ugc_req.business_id = make_uuid()
        ugc_req.conversation_id = make_uuid()
        ugc_req.status = UgcRequestStatus.PENDING
        ugc_req.request_message = "¿Nos mandas una foto?"

        db.get.return_value = ugc_req

        with patch.object(engine.fatigue, "can_contact_now", new_callable=AsyncMock, return_value={"allowed": True}), \
             patch("app.domains.channels.services.send_outbound_message", new_callable=AsyncMock) as mock_send:

            result = await engine.send_ugc_request(ugc_req.id)

        assert result["status"] == "sent"
        assert ugc_req.status == UgcRequestStatus.SENT
        mock_send.assert_called_once()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_send_ugc_request_blocked(self):
        """Test send_ugc_request is blocked by fatigue."""
        db = mock_db()
        engine = UGCCollector(db)

        ugc_req = MagicMock(spec=UgcRequest)
        ugc_req.id = make_uuid()
        ugc_req.business_id = make_uuid()
        ugc_req.conversation_id = make_uuid()
        ugc_req.status = UgcRequestStatus.PENDING

        db.get.return_value = ugc_req

        with patch.object(engine.fatigue, "can_contact_now", new_callable=AsyncMock, return_value={"allowed": False}):
            result = await engine.send_ugc_request(ugc_req.id)

        assert result["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_collect_submission(self):
        """Test collect_submission updates request and emits event."""
        db = mock_db()
        engine = UGCCollector(db)

        ugc_req = MagicMock(spec=UgcRequest)
        ugc_req.id = make_uuid()
        ugc_req.business_id = make_uuid()
        ugc_req.conversation_id = make_uuid()
        ugc_req.order_id = make_uuid()
        ugc_req.status = UgcRequestStatus.SENT
        ugc_req.social_proof_id = None

        db.get.return_value = ugc_req

        with patch("app.core.events.event_bus.emit", new_callable=AsyncMock) as mock_event:
            result = await engine.collect_submission(
                request_id=ugc_req.id,
                media_urls=["https://example.com/photo.jpg"],
                response_text="Acá va mi foto!",
            )

        assert result is ugc_req
        assert ugc_req.status == UgcRequestStatus.RECEIVED
        assert len(ugc_req.response_media_urls) == 1
        args, kwargs = mock_event.call_args
        assert args[0] == "ugc.submitted"
        assert isinstance(args[1], dict)
        db.commit.assert_called()


# ========== 6. ValueFirstOutreach ==========

class TestValueFirstOutreach:
    @pytest.mark.asyncio
    async def test_create_educational_sequence(self):
        """Test create_educational_sequence with mocked AI message generation."""
        db = mock_db()
        engine = ValueFirstOutreach(db)

        mock_messages = [
            {"order": 1, "content": "Tip 1", "delay_hours": 24, "type": "value"},
            {"order": 2, "content": "Tip 2", "delay_hours": 48, "type": "value"},
        ]

        with patch.object(engine, "_generate_sequence_messages", new_callable=AsyncMock, return_value=mock_messages):
            result = await engine.create_educational_sequence(
                business_id=make_uuid(),
                name="Test Sequence",
                topic="Marketing",
                message_count=2,
                total_duration_days=3,
            )

        assert isinstance(result, ValueSequence)
        assert result.name == "Test Sequence"
        assert result.topic == "Marketing"
        assert result.message_count == 2
        assert len(result.messages) == 2
        db.add.assert_called()
        db.commit.assert_called()

    def test_fallback_messages(self):
        """Test _fallback_messages pure logic."""
        db = mock_db()
        engine = ValueFirstOutreach(db)

        messages = engine._fallback_messages("ventas", 3, 24)

        assert len(messages) == 3
        assert messages[0]["order"] == 1
        assert "ventas" in messages[0]["content"]
        assert messages[2]["type"] == "soft_cta"

        # Test truncation when count < 3
        messages_two = engine._fallback_messages("marketing", 2, 12)
        assert len(messages_two) == 2

    @pytest.mark.asyncio
    async def test_send_next_message_success(self):
        """Test send_next_message delivers the next value message."""
        db = mock_db()
        engine = ValueFirstOutreach(db)

        seq = MagicMock(spec=ValueSequence)
        seq.id = make_uuid()
        seq.message_count = 3
        seq.messages = [
            {"order": 1, "content": "Mensaje 1", "delay_hours": 24},
            {"order": 2, "content": "Mensaje 2", "delay_hours": 48},
        ]

        enrollment = MagicMock(spec=ValueSequenceEnrollment)
        enrollment.id = make_uuid()
        enrollment.status = "active"
        enrollment.current_step = 0
        enrollment.business_id = make_uuid()
        enrollment.conversation_id = make_uuid()
        enrollment.messages_sent = 0

        db.get.return_value = enrollment

        with patch.object(engine, "_get_sequence", new_callable=AsyncMock, return_value=seq), \
             patch.object(engine.fatigue, "can_contact_now", new_callable=AsyncMock, return_value={"allowed": True}), \
             patch("app.domains.channels.services.send_outbound_message", new_callable=AsyncMock) as mock_send:

            result = await engine.send_next_message(enrollment.id)

        assert result["status"] == "sent"
        assert result["step"] == 1
        assert enrollment.current_step == 1
        assert enrollment.messages_sent == 1
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_next_message_blocked(self):
        """Test send_next_message is blocked by fatigue."""
        db = mock_db()
        engine = ValueFirstOutreach(db)

        seq = MagicMock(spec=ValueSequence)
        seq.id = make_uuid()
        seq.message_count = 3
        seq.messages = [{"order": 1, "content": "Mensaje 1"}]

        enrollment = MagicMock(spec=ValueSequenceEnrollment)
        enrollment.id = make_uuid()
        enrollment.status = "active"
        enrollment.current_step = 0
        enrollment.business_id = make_uuid()
        enrollment.conversation_id = make_uuid()

        db.get.return_value = enrollment

        with patch.object(engine, "_get_sequence", new_callable=AsyncMock, return_value=seq), \
             patch.object(engine.fatigue, "can_contact_now", new_callable=AsyncMock, return_value={"allowed": False}):
            result = await engine.send_next_message(enrollment.id)

        assert result["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_send_next_message_completes_sequence(self):
        """Test send_next_message completes sequence when all messages sent."""
        db = mock_db()
        engine = ValueFirstOutreach(db)

        seq = MagicMock(spec=ValueSequence)
        seq.id = make_uuid()
        seq.message_count = 2
        seq.messages = [
            {"order": 1, "content": "M1"},
            {"order": 2, "content": "M2"},
        ]
        seq.times_completed = 0

        enrollment = MagicMock(spec=ValueSequenceEnrollment)
        enrollment.id = make_uuid()
        enrollment.status = "active"
        enrollment.current_step = 2  # Already at last step
        enrollment.business_id = make_uuid()
        enrollment.conversation_id = make_uuid()

        db.get.return_value = enrollment

        with patch.object(engine, "_get_sequence", new_callable=AsyncMock, return_value=seq):
            result = await engine.send_next_message(enrollment.id)

        assert result["status"] == "completed"
        assert enrollment.status == "completed"
        assert enrollment.completed_at is not None


# ========== 7. CommentResponder ==========

class TestCommentResponder:
    @pytest.mark.parametrize("comment_text,expected_action", [
        ("cuanto cuesta? quiero comprar", "reply_and_dm"),
        ("gracias por el tip, muy util", "value_reply_and_dm"),
        ("me gusta", "reply_only"),
        ("hola", "skip"),
    ])
    @pytest.mark.asyncio
    async def test_process_comment_intents(self, comment_text, expected_action):
        """Test process_comment routes different comment types to correct handlers."""
        db = mock_db()
        engine = CommentResponder(db)

        with patch.object(engine, "_generate_public_reply", new_callable=AsyncMock, return_value="¡Gracias!"), \
             patch.object(engine, "_generate_dm_message", new_callable=AsyncMock, return_value="Te escribo por DM"), \
             patch.object(engine, "_capture_comment_lead", new_callable=AsyncMock, return_value=MagicMock(id=make_uuid())), \
             patch("app.domains.growth.comment_responder.generate_raw_ai_response", new_callable=AsyncMock) as mock_ai, \
             patch("app.core.events.event_bus.emit", new_callable=AsyncMock) as mock_event:

            result = await engine.process_comment(
                business_id=make_uuid(),
                platform="instagram",
                post_id="post123",
                comment_id="c456",
                author_username="testuser",
                comment_text=comment_text,
            )

        assert result["action"] == expected_action
        if expected_action in ("reply_and_dm", "value_reply_and_dm"):
            assert "public_reply" in result
            assert "dm_message" in result
            assert "lead_id" in result

    @pytest.mark.asyncio
    async def test_capture_comment_lead(self):
        """Test _capture_comment_lead creates lead and emits event."""
        db = mock_db()
        engine = CommentResponder(db)

        with patch("app.core.events.event_bus.emit", new_callable=AsyncMock) as mock_event:
            lead = await engine._capture_comment_lead(
                business_id=make_uuid(),
                platform="instagram",
                username="testuser",
                post_id="post123",
                source_detail="high_intent",
            )

        assert isinstance(lead, InboundLead)
        assert lead.source_type == InboundLeadSource.COMMENT_DM
        assert "instagram" in lead.source_detail
        assert lead.contact_info["username"] == "testuser"
        args, kwargs = mock_event.call_args
        assert args[0] == "inbound.lead_captured"
        assert isinstance(args[1], dict)


# ========== 8. ContentSyndicationEngine ==========

class TestContentSyndicationEngine:
    @pytest.mark.asyncio
    async def test_syndicate_content(self):
        """Test syndicate_content adapts source for multiple platforms."""
        db = mock_db()
        engine = ContentSyndicationEngine(db)

        source = MagicMock()
        source.meta_data = {"title": "Cómo vender sin vender"}
        source.text_content = "Contenido largo del blog post..."
        db.get.return_value = source

        with patch.object(engine, "_adapt_for_platform", new_callable=AsyncMock) as mock_adapt:
            mock_adapt.side_effect = [
                {"carousel_slides": [], "caption": "IG caption"},
                {"hook": "Hook!", "script": "Script"},
                {"post": "LinkedIn post"},
            ]

            result = await engine.syndicate_content(
                business_id=make_uuid(),
                source_content_id=make_uuid(),
                platforms=["instagram", "tiktok", "linkedin"],
            )

        assert "platforms" in result
        assert result["platforms_scheduled"] == 3
        assert "instagram" in result["platforms"]
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_adapt_instagram(self):
        """Test _adapt_instagram with mocked AI response."""
        db = mock_db()
        engine = ContentSyndicationEngine(db)

        ai_response = json.dumps({
            "carousel_slides": [{"slide": 1, "title": "T1", "text": "Txt"}],
            "caption": "Caption",
            "hashtags": ["#tag1"],
            "cta": "CTA",
        })

        with patch("app.domains.growth.content_syndication.generate_raw_ai_response", new_callable=AsyncMock, return_value=ai_response):
            result = await engine._adapt_instagram(make_uuid(), "Title", "Body text")

        assert result["carousel_slides"][0]["slide"] == 1
        assert result["hashtags"] == ["#tag1"]

    @pytest.mark.asyncio
    async def test_adapt_tiktok(self):
        """Test _adapt_tiktok with mocked AI response."""
        db = mock_db()
        engine = ContentSyndicationEngine(db)

        ai_response = json.dumps({
            "hook": "No hagas esto",
            "script": "Guion completo",
            "on_screen_text": ["0:03 ERROR"],
            "sound_suggestion": "Trending",
            "cta": "Comenta",
        })

        with patch("app.domains.growth.content_syndication.generate_raw_ai_response", new_callable=AsyncMock, return_value=ai_response):
            result = await engine._adapt_tiktok(make_uuid(), "Title", "Body text")

        assert "hook" in result
        assert result["hook"] == "No hagas esto"

    @pytest.mark.asyncio
    async def test_adapt_linkedin(self):
        """Test _adapt_linkedin with mocked AI response."""
        db = mock_db()
        engine = ContentSyndicationEngine(db)

        ai_response = json.dumps({
            "post": "Post profesional",
            "hashtags": ["#negocios"],
        })

        with patch("app.domains.growth.content_syndication.generate_raw_ai_response", new_callable=AsyncMock, return_value=ai_response):
            result = await engine._adapt_linkedin(make_uuid(), "Title", "Body text")

        assert "post" in result

    @pytest.mark.asyncio
    async def test_adapt_whatsapp_status(self):
        """Test _adapt_whatsapp_status with mocked AI response."""
        db = mock_db()
        engine = ContentSyndicationEngine(db)

        ai_response = json.dumps({
            "status_text": "💡 Tip del día",
            "cta": "Respondé para más",
        })

        with patch("app.domains.growth.content_syndication.generate_raw_ai_response", new_callable=AsyncMock, return_value=ai_response):
            result = await engine._adapt_whatsapp_status(make_uuid(), "Title", "Body text")

        assert result["status_text"] == "💡 Tip del día"

    @pytest.mark.asyncio
    async def test_adapt_email(self):
        """Test _adapt_email with mocked AI response."""
        db = mock_db()
        engine = ContentSyndicationEngine(db)

        ai_response = json.dumps({
            "subject": "Subject line",
            "preview": "Preview",
            "body": "<h1>Title</h1>",
            "cta": "CTA",
            "ps": "P.S.",
        })

        with patch("app.domains.growth.content_syndication.generate_raw_ai_response", new_callable=AsyncMock, return_value=ai_response):
            result = await engine._adapt_email(make_uuid(), "Title", "Body text")

        assert result["subject"] == "Subject line"


# ========== 9. SEOPipeline ==========

class TestSEOPipeline:
    @pytest.mark.asyncio
    async def test_generate_blog_post(self):
        """Test generate_blog_post with mocked AI (2 calls: article + meta)."""
        db = mock_db()
        engine = SEOPipeline(db)

        article_json = json.dumps({
            "title": "Cómo vender sin vender",
            "body": "Contenido del artículo...",
            "headers": [{"level": 2, "text": "Intro"}],
            "related_keywords": ["marketing organico"],
            "snippet_answer": "Vender sin vender es...",
        })
        meta_json = json.dumps({
            "meta_description": "Descubre cómo vender sin vender",
            "schema_markup": "{}",
        })

        def mock_content_factory(**kwargs):
            m = MagicMock()
            for k, v in kwargs.items():
                setattr(m, k, v)
            return m

        with patch("app.domains.growth.seo_pipeline.GeneratedContent", side_effect=mock_content_factory), \
             patch("app.domains.growth.seo_pipeline.generate_raw_ai_response", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = [article_json, meta_json]
            result = await engine.generate_blog_post(
                business_id=make_uuid(),
                keyword="vender sin vender",
            )

        assert result.content_type == "blog_post"
        assert result.status == "completed"
        assert result.meta_data["title"] == "Cómo vender sin vender"
        assert mock_ai.call_count == 2
        db.add.assert_called()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_generate_guide(self):
        """Test generate_guide with mocked AI."""
        db = mock_db()
        engine = SEOPipeline(db)

        guide_json = json.dumps({
            "title": "Guía completa: SEO para emprendedores",
            "body": "Paso 1... Paso 2...",
            "headers": [{"level": 2, "text": "Paso 1"}],
            "related_keywords": ["seo local"],
            "snippet_answer": "SEO es...",
        })

        def mock_content_factory(**kwargs):
            m = MagicMock()
            for k, v in kwargs.items():
                setattr(m, k, v)
            return m

        with patch("app.domains.growth.seo_pipeline.GeneratedContent", side_effect=mock_content_factory), \
             patch("app.domains.growth.seo_pipeline.generate_raw_ai_response", new_callable=AsyncMock, return_value=guide_json):
            result = await engine.generate_guide(
                business_id=make_uuid(),
                topic="SEO para emprendedores",
            )

        assert result.content_type == "guide"
        assert result.meta_data["difficulty"] == "beginner"
        db.add.assert_called()

    @pytest.mark.asyncio
    async def test_generate_content_batch(self):
        """Test generate_content_batch delegates to generate_blog_post."""
        db = mock_db()
        engine = SEOPipeline(db)

        mock_content = MagicMock()
        mock_content.content_type = "blog_post"

        with patch.object(engine, "generate_blog_post", new_callable=AsyncMock, return_value=mock_content) as mock_gen:
            results = await engine.generate_content_batch(
                business_id=make_uuid(),
                keywords=["keyword1", "keyword2"],
            )

        assert len(results) == 2
        assert mock_gen.call_count == 2


# ========== 10. VoiceNoteEngine ==========

class TestVoiceNoteEngine:
    @pytest.mark.asyncio
    async def test_generate_welcome_voice_note_ai_success(self):
        """Test generate_welcome_voice_note returns AI script when available."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value="Che Juan, cómo andás? Mirá..."):
            result = await engine.generate_welcome_voice_note(make_uuid(), "Juan", "instagram")

        assert result == "Che Juan, cómo andás? Mirá..."

    @pytest.mark.asyncio
    async def test_generate_welcome_voice_note_fallback(self):
        """Test generate_welcome_voice_note falls back when AI returns None."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value=None):
            result = await engine.generate_welcome_voice_note(make_uuid(), "Juan", "instagram")

        assert "Juan" in result
        assert "Gracias por escribirme" in result

    @pytest.mark.asyncio
    async def test_generate_value_voice_note_ai_success(self):
        """Test generate_value_voice_note returns AI script."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value="Che Ana, te cuento algo..."):
            result = await engine.generate_value_voice_note(make_uuid(), "Ana", "Marketing", "Documenta tus procesos")

        assert result == "Che Ana, te cuento algo..."

    @pytest.mark.asyncio
    async def test_generate_value_voice_note_fallback(self):
        """Test generate_value_voice_note falls back when AI returns None."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value=None):
            result = await engine.generate_value_voice_note(make_uuid(), "Ana", "Marketing", "Documenta tus procesos")

        assert "Ana" in result
        assert "Documenta tus procesos" in result

    @pytest.mark.asyncio
    async def test_generate_soft_close_voice_note_ai_success(self):
        """Test generate_soft_close_voice_note returns AI script."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value="Che Pedro, si querés charlamos..."):
            result = await engine.generate_soft_close_voice_note(make_uuid(), "Pedro", "Curso de Ventas")

        assert result == "Che Pedro, si querés charlamos..."

    @pytest.mark.asyncio
    async def test_generate_soft_close_voice_note_fallback(self):
        """Test generate_soft_close_voice_note falls back when AI returns None."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value=None):
            result = await engine.generate_soft_close_voice_note(make_uuid(), "Pedro", "Curso de Ventas")

        assert "Pedro" in result
        assert "charlemos 10 minutos" in result

    @pytest.mark.asyncio
    async def test_generate_referral_voice_note_ai_success(self):
        """Test generate_referral_voice_note returns AI script."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value="Che María, te jodo con una cosita..."):
            result = await engine.generate_referral_voice_note(make_uuid(), "María", "CODE123")

        assert result == "Che María, te jodo con una cosita..."

    @pytest.mark.asyncio
    async def test_generate_referral_voice_note_fallback(self):
        """Test generate_referral_voice_note falls back when AI returns None."""
        db = mock_db()
        engine = VoiceNoteEngine(db)

        with patch("app.domains.growth.voice_note_engine.generate_raw_ai_response", new_callable=AsyncMock, return_value=None):
            result = await engine.generate_referral_voice_note(make_uuid(), "María", "CODE123")

        assert "María" in result
        assert "CODE123" in result


# ========== 11. WarmLeadDetector ==========

class TestWarmLeadDetector:
    @pytest.mark.parametrize(
        "messages,engagement_score,expected_score,expected_details",
        [
            # No messages → score 0
            ([], 0, 0, []),
            # 2 messages recent, no keywords → score low (1 new_reply + 1 multiple_messages)
            ([
                {"direction": "inbound", "created_at": datetime.now(timezone.utc) - timedelta(minutes=30), "content": "hola"},
                {"direction": "inbound", "created_at": datetime.now(timezone.utc), "content": "todo bien"},
            ], 0, 2, ["new_reply", "multiple_messages"]),
            # 3 messages recent, last has price + buy keywords → score high
            ([
                {"direction": "inbound", "created_at": datetime.now(timezone.utc) - timedelta(minutes=30), "content": "hola"},
                {"direction": "inbound", "created_at": datetime.now(timezone.utc) - timedelta(minutes=10), "content": "ok"},
                {"direction": "inbound", "created_at": datetime.now(timezone.utc), "content": "cuanto cuesta? me interesa comprar"},
            ], 0, 8, ["new_reply", "high_message_frequency", "price_inquiry", "buying_intent_keywords"]),
            # Old messages → score low (no messages within since window)
            ([{"direction": "inbound", "created_at": datetime.now(timezone.utc) - timedelta(days=10), "content": "hola"}], 0, 0, []),
        ],
    )
    @pytest.mark.asyncio
    async def test_analyze_warming_signals(self, messages, engagement_score, expected_score, expected_details):
        """Test _analyze_warming_signals with various scenarios."""
        db = mock_db()
        engine = WarmLeadDetector(db)

        lead = MagicMock(spec=InboundLead)
        lead.id = make_uuid()
        lead.business_id = make_uuid()
        lead.engagement_score = engagement_score
        lead.conversation_id = make_uuid()

        conv = MagicMock()
        conv.id = lead.conversation_id

        since = datetime.now(timezone.utc) - timedelta(hours=24)

        # Build mock message objects
        mock_msgs = []
        for i, m in enumerate(messages):
            msg = MagicMock()
            msg.direction = m["direction"]
            msg.created_at = m["created_at"]
            msg.content = m["content"]
            msg.id = make_uuid()
            mock_msgs.append(msg)

        # Track calls to return appropriate mock per query
        call_history = []
        recent_msgs = [m for m in mock_msgs if m.created_at >= since]
        recent_msgs.sort(key=lambda m: m.created_at, reverse=True)

        def execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()

            if len(call_history) == 0:
                # First call: last inbound message
                call_history.append("last")
                mock_result.scalar_one_or_none = lambda: recent_msgs[0] if recent_msgs else None
                return mock_result

            if len(call_history) == 1 and call_history[0] == "last" and recent_msgs:
                # Second call: previous inbound message (only if last exists)
                call_history.append("prev")
                if len(recent_msgs) > 1:
                    last = recent_msgs[0]
                    prev_candidates = [m for m in recent_msgs if m.created_at < last.created_at]
                    mock_result.scalar_one_or_none = lambda: prev_candidates[0] if prev_candidates else None
                else:
                    mock_result.scalar_one_or_none = lambda: None
                return mock_result

            # Final call: message count
            call_history.append("count")
            count = sum(1 for m in mock_msgs if m.created_at >= since and m.direction == "inbound")
            mock_result.scalar = lambda: count
            return mock_result

        db.execute.side_effect = execute_side_effect

        signals = await engine._analyze_warming_signals(lead, conv, since)

        assert signals["score"] == expected_score
        for detail in expected_details:
            assert detail in signals["details"]

    @pytest.mark.asyncio
    async def test_scan_for_warming_leads(self):
        """Test scan_for_warming_leads finds leads and emits events."""
        db = mock_db()
        engine = WarmLeadDetector(db)

        lead = MagicMock(spec=InboundLead)
        lead.id = make_uuid()
        lead.business_id = make_uuid()
        lead.engagement_score = 25
        lead.nurturing_stage = NurturingStage.AWARENESS
        lead.conversation_id = make_uuid()

        conv = MagicMock()
        conv.id = lead.conversation_id

        # Mock the join query result
        mock_result = MagicMock()
        mock_result.all = lambda: [(lead, conv)]
        db.execute.return_value = mock_result

        with patch.object(engine, "_analyze_warming_signals", new_callable=AsyncMock, return_value={"score": 5, "details": ["price_inquiry"]}), \
             patch("app.domains.growth.warm_lead_detector.event_bus.emit", new_callable=AsyncMock) as mock_event:

            results = await engine.scan_for_warming_leads(make_uuid(), lookback_hours=24)

        assert len(results) == 1
        assert results[0]["warming_score"] == 5
        mock_event.assert_called()

