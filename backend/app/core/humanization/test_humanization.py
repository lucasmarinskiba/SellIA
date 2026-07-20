"""
Phase 10: Humanization — Comprehensive Test Suite (400L)

Tests for:
- Tone engine (10 tones across markets)
- Empathy layer (emotion detection, empathetic responses)
- Personalization (name usage, history, preferences)
- Response builder (combining components)
- A/B testing (variant selection, winner determination)
- End-to-end humanization
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from tone_engine import (
    ToneEngine,
    ToneType,
    Market,
    Industry,
    ToneProfile,
)
from empathy_layer import (
    EmpathyLayer,
    EmotionalState,
    EmpathyResponse,
)
from personalization import (
    PersonalizationEngine,
    BuyerProfile,
    PersonalizationContext,
    PersonalizationLevel,
)
from response_builder import (
    ResponseBuilder,
    CTAType,
)
from a_b_testing import (
    ABTestingEngine,
    ExperimentType,
)


class TestToneEngine(unittest.TestCase):
    """Tests for ToneEngine"""

    def setUp(self):
        self.engine = ToneEngine()

    def test_initialization(self):
        """Test engine initializes with all profiles"""
        self.assertGreater(len(self.engine.TONE_REGISTRY), 0)

    def test_get_tone_profile_exact_match(self):
        """Test getting exact tone profile"""
        profile = self.engine.get_tone_profile(
            ToneType.FORMAL,
            Market.LATIN_AMERICA,
            Industry.REAL_ESTATE,
        )
        self.assertIsNotNone(profile)
        self.assertEqual(profile.tone_type, ToneType.FORMAL)

    def test_get_tone_profile_fallback(self):
        """Test fallback when exact match not found"""
        profile = self.engine.get_tone_profile(
            ToneType.CASUAL,
            Market.LATIN_AMERICA,  # Not in casual profiles
            Industry.REAL_ESTATE,
        )
        # Should fallback to something
        self.assertIsNotNone(profile)

    def test_suggest_tone_high_urgency(self):
        """Test tone suggestion for high urgency"""
        tone = self.engine.suggest_tone(
            buyer_sentiment="positive",
            buyer_urgency="high",
            market=Market.USA,
            industry=Industry.ECOMMERCE,
        )
        self.assertEqual(tone, ToneType.URGENT)

    def test_suggest_tone_negative_sentiment(self):
        """Test tone suggestion for negative sentiment"""
        tone = self.engine.suggest_tone(
            buyer_sentiment="negative",
            buyer_urgency="low",
            market=Market.USA,
            industry=Industry.SERVICES,
        )
        self.assertEqual(tone, ToneType.EMPATHETIC)

    def test_apply_tone_modifies_message(self):
        """Test that tone application modifies message"""
        profile = self.engine.get_tone_profile(
            ToneType.FORMAL,
            Market.LATIN_AMERICA,
            Industry.REAL_ESTATE,
        )
        result = self.engine.apply_tone("Hey, this is cool!", profile)

        self.assertIsNotNone(result)
        self.assertIn("toned_message", result)
        self.assertIn("modifications", result)

    def test_measure_tone_match(self):
        """Test tone matching score"""
        profile = self.engine.get_tone_profile(
            ToneType.CASUAL,
            Market.USA,
            Industry.ECOMMERCE,
        )
        score = self.engine.measure_tone_match(
            "Hey! This is totally awesome! 🚀",
            profile,
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Casual text should score high with casual profile
        self.assertGreater(score, 0.5)

    def test_get_all_tones(self):
        """Test getting all available tones"""
        tones = self.engine.get_all_tones()
        self.assertGreater(len(tones), 0)
        self.assertIn("tone", tones[0])
        self.assertIn("formality", tones[0])


class TestEmpathyLayer(unittest.TestCase):
    """Tests for EmpathyLayer"""

    def setUp(self):
        self.layer = EmpathyLayer()

    def test_detect_confidence(self):
        """Test detecting confident emotional state"""
        signal = self.layer.detect_emotion("I'm ready to buy, let's do it!", "en")
        self.assertEqual(signal.emotional_state, EmotionalState.CONFIDENT)
        self.assertGreater(signal.confidence, 0.7)

    def test_detect_hesitant(self):
        """Test detecting hesitant state"""
        signal = self.layer.detect_emotion("I need to think about this", "en")
        self.assertEqual(signal.emotional_state, EmotionalState.HESITANT)

    def test_detect_frustrated(self):
        """Test detecting frustrated state"""
        signal = self.layer.detect_emotion("This is frustrating, nothing works", "en")
        self.assertEqual(signal.emotional_state, EmotionalState.FRUSTRATED)

    def test_detect_urgent(self):
        """Test detecting urgent state"""
        signal = self.layer.detect_emotion("I need this ASAP, today only", "en")
        self.assertEqual(signal.emotional_state, EmotionalState.URGENT)
        self.assertGreaterEqual(signal.urgency_level, 8)

    def test_spanish_detection(self):
        """Test emotion detection in Spanish"""
        signal = self.layer.detect_emotion("Estoy frustrado con esto", "es")
        self.assertEqual(signal.emotional_state, EmotionalState.FRUSTRATED)

    def test_generate_empathetic_response(self):
        """Test generating empathetic response"""
        signal = self.layer.detect_emotion("I'm not sure about this", "en")
        response = self.layer.generate_empathetic_response(signal, "en")

        self.assertIsNotNone(response)
        self.assertIn("response", response)
        self.assertIn("emotional_state", response)
        self.assertIn("response_type", response)

    def test_handle_objection(self):
        """Test handling specific objections"""
        result = self.layer.handle_objection("It's too expensive", "en")
        self.assertEqual(result["objection_type"], "price")
        self.assertIn("response", result)

    def test_handle_objection_competitor(self):
        """Test handling competitor objection"""
        result = self.layer.handle_objection("We already use a competitor", "en")
        self.assertEqual(result["objection_type"], "competitor")

    def test_build_urgency_empathetically(self):
        """Test building urgency without being pushy"""
        result = self.layer.build_urgency_empathetically("limited_spots", "en")
        self.assertIn("message", result)
        self.assertEqual(result["urgency_type"], "limited_spots")


class TestPersonalizationEngine(unittest.TestCase):
    """Tests for PersonalizationEngine"""

    def setUp(self):
        self.engine = PersonalizationEngine()

    def test_create_buyer_profile(self):
        """Test creating buyer profile"""
        profile = self.engine.create_buyer_profile(
            buyer_id="buyer_123",
            name="John Doe",
            company="Acme Corp",
            industry="saas",
            role="CTO",
        )
        self.assertEqual(profile.name, "John Doe")
        self.assertEqual(profile.first_name, "John")
        self.assertEqual(profile.company, "Acme Corp")
        self.assertEqual(profile.industry, "saas")

    def test_infer_industry_real_estate(self):
        """Test inferring real estate industry"""
        industry = self.engine.infer_industry(company_name="Luxury Realty Inc")
        self.assertEqual(industry, "real_estate")

    def test_infer_industry_saas(self):
        """Test inferring SaaS industry"""
        industry = self.engine.infer_industry(company_name="CloudSoft Platform")
        self.assertEqual(industry, "saas")

    def test_infer_industry_ecommerce(self):
        """Test inferring e-commerce industry"""
        industry = self.engine.infer_industry(company_name="Online Shop Store")
        self.assertEqual(industry, "ecommerce")

    def test_personalize_message_light(self):
        """Test light personalization"""
        profile = self.engine.create_buyer_profile(
            buyer_id="buyer_123",
            name="Jane",
        )
        context = PersonalizationContext(
            buyer_profile=profile,
            message_type="initial",
            personalization_level=PersonalizationLevel.LIGHT,
        )
        result = self.engine.personalize_message(
            "Check out our new product",
            profile,
            context,
            "en",
        )
        self.assertIn("Jane", result["personalized_message"])

    def test_personalize_message_deep(self):
        """Test deep personalization"""
        profile = self.engine.create_buyer_profile(
            buyer_id="buyer_123",
            name="Jane Smith",
            company="Tech Corp",
            industry="saas",
            role="VP of Sales",
        )
        profile.past_purchases = [
            {"product": "Premium Plan", "date": "2024-01-15"}
        ]
        context = PersonalizationContext(
            buyer_profile=profile,
            message_type="follow_up",
            personalization_level=PersonalizationLevel.DEEP,
        )
        result = self.engine.personalize_message(
            "I wanted to follow up on our conversation",
            profile,
            context,
            "en",
        )
        # Should include various personalization elements
        self.assertGreater(len(result["personalization_elements"]), 1)

    def test_detect_urgency_from_profile(self):
        """Test urgency detection from profile"""
        profile = self.engine.create_buyer_profile(
            buyer_id="buyer_123",
            name="John",
            is_vip=True,
        )
        urgency = self.engine.detect_urgency_from_profile(profile)
        self.assertGreaterEqual(urgency, 6)  # VIP gets high urgency

    def test_extract_buyer_preferences(self):
        """Test extracting buyer preferences"""
        profile = self.engine.create_buyer_profile(
            buyer_id="buyer_123",
            name="John",
            role="Executive",
            industry="saas",
        )
        prefs = self.engine.extract_buyer_preferences(profile)
        self.assertIn("tone", prefs)
        self.assertEqual(prefs["tone"], "professional")


class TestResponseBuilder(unittest.TestCase):
    """Tests for ResponseBuilder"""

    def setUp(self):
        self.builder = ResponseBuilder()

    def test_build_response_complete(self):
        """Test building complete response"""
        result = self.builder.build_response(
            base_message="Our product can help your business grow faster",
            tone_type="friendly",
            emotional_state="curious",
            buyer_name="John",
            cta_type=CTAType.SOFT,
            language="en",
        )
        self.assertIn("response", result)
        self.assertIn("humanness_score", result)
        self.assertGreater(result["humanness_score"], 0.0)

    def test_build_response_with_social_proof(self):
        """Test building response with social proof"""
        result = self.builder.build_response(
            base_message="Try our platform",
            tone_type="casual",
            emotional_state="confident",
            cta_type=CTAType.BENEFIT,
            social_proof_data={
                "count": "500",
                "percent": "85",
                "audience": "B2B companies",
                "timeframe": "30 days",
            },
            language="en",
        )
        self.assertIn("social_proof", result["components"])

    def test_cta_strength_calculation(self):
        """Test CTA strength calculation"""
        soft_strength = self.builder._calculate_cta_strength(CTAType.SOFT, "message")
        direct_strength = self.builder._calculate_cta_strength(CTAType.DIRECT, "message")
        scarcity_strength = self.builder._calculate_cta_strength(CTAType.SCARCITY, "message")

        self.assertLess(soft_strength, direct_strength)
        self.assertLess(direct_strength, scarcity_strength)

    def test_humanness_score_calculation(self):
        """Test humanness score is calculated"""
        score = self.builder._calculate_humanness(
            "Hey! I think you might really enjoy this. It's awesome and I'd love to hear what you think.",
            "casual",
            "en",
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_optimize_for_sms(self):
        """Test SMS optimization"""
        long_response = "This is a very long message " * 50
        result = self.builder.optimize_for_platform(
            long_response,
            "sms",
        )
        self.assertLessEqual(len(result["optimized_response"]), 160)

    def test_validate_response_good(self):
        """Test validation of good response"""
        response = "Hey John! I think this could really work for you. What do you think?"
        result = self.builder.validate_response(response, "casual", "en")
        self.assertTrue(result["is_valid"])

    def test_validate_response_bad(self):
        """Test validation catches issues"""
        response = "x"  # Too short
        result = self.builder.validate_response(response, "casual", "en")
        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["issues"]), 0)


class TestABTestingEngine(unittest.TestCase):
    """Tests for A/B Testing Engine"""

    def setUp(self):
        self.engine = ABTestingEngine()

    def test_create_test(self):
        """Test creating A/B test"""
        test = self.engine.create_test(
            test_name="Tone Test",
            test_type=ExperimentType.TONE,
            control_message="Hey, check this out",
            treatment_messages=[
                {"name": "Formal", "message": "I'd like to introduce this opportunity"},
            ],
            hypothesis="Casual tone converts better",
        )
        self.assertIsNotNone(test)
        self.assertEqual(test.test_type, ExperimentType.TONE)

    def test_select_variant(self):
        """Test variant selection"""
        test = self.engine.create_test(
            test_name="Simple Test",
            test_type=ExperimentType.TONE,
            control_message="Control",
            treatment_messages=[{"name": "Treatment", "message": "Treatment"}],
            hypothesis="Test",
        )
        variant = self.engine.select_variant(test.test_id)
        self.assertIsNotNone(variant)

    def test_record_events(self):
        """Test recording events"""
        test = self.engine.create_test(
            test_name="Event Test",
            test_type=ExperimentType.TONE,
            control_message="Control",
            treatment_messages=[{"name": "Treatment", "message": "Treatment"}],
            hypothesis="Test",
        )
        control = test.control_variant

        # Record events
        self.engine.record_event(test.test_id, control.variant_id, "sent")
        self.engine.record_event(test.test_id, control.variant_id, "opened")
        self.engine.record_event(test.test_id, control.variant_id, "clicked")

        # Check counts
        self.assertEqual(control.sent_count, 1)
        self.assertEqual(control.open_count, 1)
        self.assertEqual(control.click_count, 1)

    def test_analyze_test_inconclusive(self):
        """Test analysis for inconclusive results"""
        test = self.engine.create_test(
            test_name="Inconclusive Test",
            test_type=ExperimentType.TONE,
            control_message="Control",
            treatment_messages=[{"name": "Treatment", "message": "Treatment"}],
            hypothesis="Test",
        )
        # Add minimal events
        for _ in range(10):
            self.engine.record_event(test.test_id, test.control_variant.variant_id, "sent")

        analysis = self.engine.analyze_test(test.test_id)
        self.assertIn("status", analysis)

    def test_humanness_feedback(self):
        """Test recording humanness feedback"""
        test = self.engine.create_test(
            test_name="Humanness Test",
            test_type=ExperimentType.HUMANNESS,
            control_message="Control",
            treatment_messages=[{"name": "Treatment", "message": "Treatment"}],
            hypothesis="Test humanness",
        )
        control = test.control_variant
        success = self.engine.record_humanness_feedback(test.test_id, control.variant_id, 0.85)
        self.assertTrue(success)
        self.assertGreater(control.humanness_score, 0.5)

    def test_create_preset_test(self):
        """Test creating test from preset"""
        test = self.engine.create_preset_test(
            "formal_vs_casual",
            "Control message",
        )
        self.assertIsNotNone(test)
        self.assertEqual(test.test_type, ExperimentType.TONE)


class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        self.tone_engine = ToneEngine()
        self.empathy_layer = EmpathyLayer()
        self.personalization_engine = PersonalizationEngine()
        self.response_builder = ResponseBuilder()

    def test_build_human_message_flow(self):
        """Test complete flow to build human message"""
        # Create buyer profile
        buyer = self.personalization_engine.create_buyer_profile(
            buyer_id="buyer_123",
            name="Alice Johnson",
            company="Tech Startup",
            industry="saas",
        )

        # Detect emotion
        emotion = self.empathy_layer.detect_emotion("This sounds interesting, tell me more", "en")

        # Get tone
        tone = self.tone_engine.suggest_tone(
            buyer_sentiment="positive",
            buyer_urgency="low",
            market=Market.USA,
            industry=Industry.SAAS,
        )

        # Personalize
        context = PersonalizationContext(
            buyer_profile=buyer,
            message_type="follow_up",
        )
        personalized = self.personalization_engine.personalize_message(
            "Our platform can help you scale faster",
            buyer,
            context,
            "en",
        )

        # Build response
        response = self.response_builder.build_response(
            base_message=personalized["personalized_message"],
            tone_type=tone.value,
            emotional_state=emotion.emotional_state.value,
            buyer_name=buyer.first_name,
            language="en",
        )

        # Verify
        self.assertIn("response", response)
        self.assertGreater(response["humanness_score"], 0.5)
        self.assertTrue(response["personalization_score"] > 0)


if __name__ == "__main__":
    unittest.main()
