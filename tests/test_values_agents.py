"""
Comprehensive test suite for Block A: Values + Respect Agents

Tests:
1. VirtueAgent (honesty, integrity, respect, transparency)
2. ValuesAlignmentAgent (value extraction, alignment scoring)
3. EthicalFramework (dark patterns, FOMO, scarcity, testimonials, pricing)
4. AuthenticityEngine (personality, tone, stories, vulnerability, growth)
"""

import pytest
from backend.app.core.agents.virtue_agent import VirtueAgent, HonestySeverity
from backend.app.core.agents.values_alignment_agent import ValuesAlignmentAgent, ValueType
from backend.app.core.agents.ethical_framework import EthicalFramework, DarkPatternType
from backend.app.core.agents.authenticity_engine import AuthenticityEngine


# ============================================================================
# VIRTUE AGENT TESTS
# ============================================================================

class TestVirtueAgent:
    """Test honesty, integrity, respect, transparency enforcement."""

    def test_validate_honesty_no_violations(self):
        """Test claim that passes honesty validation."""
        claim = "This tool helps you save time on admin tasks"
        product_data = {"verified_helpful": True}

        is_honest, details = VirtueAgent.validate_honesty(claim, product_data)

        assert is_honest is True
        assert len(details["violations"]) == 0

    def test_validate_honesty_prohibited_claim(self):
        """Test detection of prohibited claims."""
        claim = "This is a risk-free guarantee"
        product_data = {}

        is_honest, details = VirtueAgent.validate_honesty(claim, product_data)

        assert is_honest is False
        assert len(details["violations"]) > 0
        assert details["violations"][0]["severity"] == HonestySeverity.CRITICAL

    def test_validate_honesty_unverified_superlative(self):
        """Test detection of unverified superlatives."""
        claim = "We are the best solution in market"
        product_data = {"verified_best": False}

        is_honest, details = VirtueAgent.validate_honesty(claim, product_data)

        assert len(details["warnings"]) > 0

    def test_check_integrity_delivery_match(self):
        """Test integrity check when promise matches delivery."""
        promise = "We deliver in 3 days"
        delivery = {"quality_score": 0.95, "delivered_features": ["feature_a"]}
        timeline = {}

        is_integral, details = VirtueAgent.check_integrity(promise, delivery, timeline)

        assert is_integral is True

    def test_check_integrity_missing_features(self):
        """Test integrity check when features are missing."""
        promise = "Full feature set"
        delivery = {
            "quality_score": 0.8,
            "promised_features": ["feature_a", "feature_b", "feature_c"],
            "delivered_features": ["feature_a", "feature_b"],
        }
        timeline = {}

        is_integral, details = VirtueAgent.check_integrity(promise, delivery, timeline)

        assert is_integral is False
        assert "feature_c" in str(details["gaps"])

    def test_enforce_respect_framework_no_dark_patterns(self):
        """Test respect check with honest message."""
        message = "This tool can help you organize your work better"
        audience = {}

        is_respectful, details = VirtueAgent.enforce_respect_framework(
            audience, message, "sales"
        )

        assert is_respectful is True

    def test_enforce_respect_framework_dark_pattern_detected(self):
        """Test respect check detects dark patterns."""
        message = "Last chance! Only 3 spots left! Act now or miss out forever!"
        audience = {"verified_scarcity": False}

        is_respectful, details = VirtueAgent.enforce_respect_framework(
            audience, message, "sales"
        )

        assert is_respectful is False
        assert len(details["violations"]) > 0

    def test_check_transparency_all_required_disclosed(self):
        """Test transparency check when all required items disclosed."""
        message = "Trial ends on Dec 31. Full pricing: $99/mo + $15 setup. Note: works best with X browser"
        product = {"trial": True}
        must_disclose = ["trial_length", "pricing", "limitations"]

        is_transparent, details = VirtueAgent.check_transparency(
            message, product, must_disclose
        )

        assert is_transparent is True
        assert len(details["missing"]) == 0

    def test_check_transparency_missing_items(self):
        """Test transparency check when items missing."""
        message = "This is a great product"
        product = {"trial": True}
        must_disclose = ["trial_length", "pricing", "limitations"]

        is_transparent, details = VirtueAgent.check_transparency(
            message, product, must_disclose
        )

        assert is_transparent is False
        assert len(details["missing"]) > 0

    def test_virtue_score_calculation(self):
        """Test overall virtue score calculation."""
        claim = "Try free for 7 days. Then $29/month. Full feature set included."
        product = {
            "verified_helpful": True,
            "highly_predictable": False,
            "timeline": {},
        }
        delivery = {"quality_score": 0.9, "delivered_features": ["a", "b"]}
        audience = {}

        result = VirtueAgent.score_virtue(claim, product, delivery, audience)

        assert "virtue_score" in result
        assert 0 <= result["virtue_score"] <= 100
        assert isinstance(result["passed"], bool)


# ============================================================================
# VALUES ALIGNMENT AGENT TESTS
# ============================================================================

class TestValuesAlignmentAgent:
    """Test user value extraction and alignment scoring."""

    def test_extract_user_values_from_profile(self):
        """Test value extraction from user profile."""
        user_profile = {
            "description": "I love sustainable products and value my time",
            "bio": "Environmental advocate, busy professional",
        }

        values = ValuesAlignmentAgent.extract_user_values(
            user_profile, [], []
        )

        assert "values" in values
        assert len(values["primary_values"]) > 0
        assert ValueType.ENVIRONMENTAL.value in values["primary_values"] or \
               ValueType.TIME.value in values["primary_values"]

    def test_extract_user_values_from_behavior(self):
        """Test value extraction from behavior history."""
        behavior = [
            {"action": "Searched for eco-friendly products"},
            {"action": "Bought premium tool for productivity"},
        ]

        values = ValuesAlignmentAgent.extract_user_values({}, behavior, [])

        assert len(values["primary_values"]) > 0

    def test_extract_user_values_from_feedback(self):
        """Test value extraction from user feedback."""
        feedback = [
            "I care about privacy and data protection",
            "I want to learn and grow my skills",
        ]

        values = ValuesAlignmentAgent.extract_user_values({}, [], feedback)

        assert ValueType.PRIVACY.value in values["values"]
        assert ValueType.GROWTH.value in values["values"]

    def test_score_recommendation_alignment_high(self):
        """Test high alignment recommendation."""
        recommendation = {
            "description": "Save money with automation and eco-friendly approach",
            "features": "Sustainable production, 40% cost reduction",
        }
        user_values = {
            "primary_values": [ValueType.FINANCIAL.value, ValueType.ENVIRONMENTAL.value],
            "secondary_values": [],
        }

        result = ValuesAlignmentAgent.score_recommendation_alignment(
            recommendation, user_values
        )

        assert result["alignment_score"] >= 70
        assert result["passed"] is True

    def test_score_recommendation_alignment_low(self):
        """Test low alignment recommendation."""
        recommendation = {
            "description": "Premium pricing with heavy data tracking",
            "features": "Comprehensive analytics, collects all user data",
        }
        user_values = {
            "primary_values": [ValueType.FINANCIAL.value, ValueType.PRIVACY.value],
            "secondary_values": [],
        }

        result = ValuesAlignmentAgent.score_recommendation_alignment(
            recommendation, user_values
        )

        assert result["alignment_score"] < 60
        assert result["passed"] is False

    def test_detect_conflicts_sales_vs_values(self):
        """Test conflict detection between sales goal and user values."""
        recommendation = {
            "description": "Requires 2-year contract with automatic renewal",
            "terms": "Cannot cancel easily",
        }
        user_values = {
            "primary_values": [ValueType.INDEPENDENCE.value],
            "secondary_values": [],
        }

        result = ValuesAlignmentAgent.detect_conflicts(
            recommendation, user_values, "close_sale"
        )

        assert result["conflicts_detected"] is True

    def test_learn_alignment_good_prediction(self):
        """Test learning when prediction matched reality."""
        result = ValuesAlignmentAgent.learn_alignment(
            "rec_123",
            {"values": {}},
            actual_satisfaction=0.85,
            actual_value_alignment=0.8,
        )

        assert "learnings" in result


# ============================================================================
# ETHICAL FRAMEWORK TESTS
# ============================================================================

class TestEthicalFramework:
    """Test dark pattern detection and ethical boundaries."""

    def test_detect_dark_patterns_false_urgency(self):
        """Test detection of false urgency patterns."""
        message = "Hurry! Last chance! Act now before it's gone!"

        result = EthicalFramework.detect_dark_patterns(message)

        assert len(result["patterns_detected"]) > 0
        assert result["max_severity"] in ["high", "critical"]
        assert result["safe_to_send"] is False

    def test_detect_dark_patterns_fake_scarcity(self):
        """Test detection of fake scarcity patterns."""
        message = "Only 3 left in stock! Exclusive offer!"

        result = EthicalFramework.detect_dark_patterns(message)

        assert len(result["patterns_detected"]) > 0

    def test_detect_dark_patterns_confirmshaming(self):
        """Test detection of confirm shaming."""
        message = "Click 'I want to save money' or 'Make me poor'"

        result = EthicalFramework.detect_dark_patterns(message)

        assert any(p["pattern_type"] == DarkPatternType.CONFIRMSHAMING.value
                   for p in result["patterns_detected"])
        assert result["safe_to_send"] is False

    def test_check_fomo_abuse_legitimate(self):
        """Test FOMO check with legitimate deadline."""
        message = "Event registration closes December 15"
        context = {"verified_end_date": True}

        result = EthicalFramework.check_fomo_abuse(message, context)

        assert result.get("legitimate") is True

    def test_check_fomo_abuse_manipulative(self):
        """Test FOMO check with manipulative FOMO."""
        message = "Everyone is buying this! Last chance! Don't miss out!"
        context = {"verified_limited_spots": False}

        result = EthicalFramework.check_fomo_abuse(message, context)

        assert result.get("legitimate") is False

    def test_validate_scarcity_verified(self):
        """Test scarcity validation when inventory is low."""
        claim = "Only 5 items left"
        product_data = {
            "current_inventory": 4,
            "low_inventory_threshold": 10,
        }

        result = EthicalFramework.validate_scarcity(claim, product_data)

        assert result["scarcity_verified"] is True
        assert result["safe_to_claim"] is True

    def test_validate_scarcity_false(self):
        """Test scarcity validation when claim is false."""
        claim = "Only 5 left"
        product_data = {
            "current_inventory": 10000,
            "low_inventory_threshold": 100,
        }

        result = EthicalFramework.validate_scarcity(claim, product_data)

        assert result["scarcity_verified"] is False
        assert result["safe_to_claim"] is False

    def test_validate_testimonials_verified(self):
        """Test testimonial validation with verified purchase."""
        testimonials = [
            {
                "reviewer_name": "John Doe",
                "verified_purchase": True,
                "text": "This product really helped me save 10 hours a week",
                "reviewer_role": "customer",
            }
        ]
        product_data = {}

        result = EthicalFramework.validate_testimonials(testimonials, product_data)

        assert result["valid"] >= 1

    def test_validate_testimonials_unverified(self):
        """Test detection of unverified testimonials."""
        testimonials = [
            {
                "reviewer_name": "Anonymous",
                "verified_purchase": False,
                "text": "Best product ever!!!",
                "reviewer_role": "customer",
            }
        ]
        product_data = {}

        result = EthicalFramework.validate_testimonials(testimonials, product_data)

        assert result["flagged"] > 0

    def test_check_pricing_honesty_hidden_fees(self):
        """Test pricing honesty check detects hidden fees."""
        pricing = {
            "base_price": 99,
            "setup_fee": 20,
            "setup_fee_disclosed": False,
            "tax": 15,
            "tax_disclosed": True,
            "final_price_clear": False,
        }

        result = EthicalFramework.check_pricing_honesty(pricing)

        assert result["price_honest"] is False
        assert "setup" in str(result["hidden_fees"]).lower()

    def test_check_pricing_honesty_full_transparency(self):
        """Test pricing honesty when fully transparent."""
        pricing = {
            "base_price": 99,
            "setup_fee": 20,
            "setup_fee_disclosed": True,
            "tax": 15,
            "tax_disclosed": True,
            "final_price_clear": True,
        }

        result = EthicalFramework.check_pricing_honesty(pricing)

        assert result["price_honest"] is True

    def test_ethical_score_calculation(self):
        """Test overall ethical score."""
        message = "Try free for 14 days. Full pricing $49/mo + $10 setup. Limited offer."
        product_data = {
            "current_inventory": 100,
            "pricing": {"base_price": 49, "setup_fee": 10},
        }

        result = EthicalFramework.ethical_score(message, product_data, {})

        assert 0 <= result["ethical_score"] <= 100
        assert isinstance(result["passed"], bool)


# ============================================================================
# AUTHENTICITY ENGINE TESTS
# ============================================================================

class TestAuthenticityEngine:
    """Test personality consistency, tone authenticity, story validation."""

    def test_check_personality_consistency_aligned(self):
        """Test personality consistency when aligned."""
        message = "We built this because we struggled with the same problem"
        personality = {
            "archetype": "founder",
            "secondary_archetypes": ["expert"],
        }

        result = AuthenticityEngine.check_personality_consistency(
            message, [], personality
        )

        assert result["alignment_with_declared"] >= 70

    def test_check_personality_consistency_misaligned(self):
        """Test personality consistency when misaligned."""
        message = "Our sophisticated algorithmic approach leverages paradigm-shifting synergies"
        personality = {
            "archetype": "founder",
        }

        result = AuthenticityEngine.check_personality_consistency(
            message, [], personality
        )

        assert result["alignment_with_declared"] < 70

    def test_check_tone_authenticity_casual(self):
        """Test tone authenticity for casual expectation."""
        message = "Honestly, I totally get it. Yeah, we had the same problem"
        expected_tone = "casual"

        result = AuthenticityEngine.check_tone_authenticity(message, expected_tone)

        assert result["tone_match"] is True
        assert result["authenticity_score"] >= 60

    def test_check_tone_authenticity_corporate_detected(self):
        """Test detection of corporate language."""
        message = "We seek to leverage synergies to optimize your paradigm"
        expected_tone = "casual"

        result = AuthenticityEngine.check_tone_authenticity(message, expected_tone)

        assert len(result["corporate_language_detected"]) > 0
        assert result["tone_match"] is False

    def test_check_vulnerability_shows_admission(self):
        """Test vulnerability showing weakness."""
        message = "I struggled with this for years before finding the solution"

        result = AuthenticityEngine.check_vulnerability(message)

        assert result["shows_vulnerability"] is True
        assert result["vulnerability_score"] > 0

    def test_check_vulnerability_no_admission(self):
        """Test message with no vulnerability."""
        message = "This is perfect and works great for everyone"

        result = AuthenticityEngine.check_vulnerability(message)

        assert result["shows_vulnerability"] is False
        assert result["vulnerability_score"] == 0

    def test_check_growth_mindset_present(self):
        """Test growth mindset detection."""
        message = "We've evolved our approach and learned so much from customer feedback"

        result = AuthenticityEngine.check_growth_mindset(message)

        assert result["growth_mindset"] is True

    def test_check_growth_mindset_absent(self):
        """Test absence of growth mindset."""
        message = "We are perfect and have never needed to change anything"

        result = AuthenticityEngine.check_growth_mindset(message)

        assert result["growth_mindset"] is False

    def test_authenticity_score_calculation(self):
        """Test overall authenticity score."""
        message = "I struggled with this, but learned a ton. We're always improving based on feedback"
        personality = {
            "archetype": "founder",
            "tone": "warm",
        }

        result = AuthenticityEngine.authenticity_score(
            message, personality, []
        )

        assert 0 <= result["authenticity_score"] <= 100
        assert isinstance(result["passed"], bool)

    def test_authenticity_score_corporate_language(self):
        """Test authenticity score penalizes corporate language."""
        message = "We leverage synergies to optimize paradigm shifts"
        personality = {"archetype": "founder", "tone": "casual"}

        result = AuthenticityEngine.authenticity_score(
            message, personality, []
        )

        assert result["authenticity_score"] < 60


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestValuesAgentsIntegration:
    """Integration tests for all value agents working together."""

    def test_complete_virtue_check_flow(self):
        """Test complete virtue check flow."""
        message = "This tool will definitely solve all your problems with a 30-day money-back guarantee"
        product = {"verified_guarantee": False}
        delivery = {"quality_score": 0.8}

        virtue_result = VirtueAgent.score_virtue(
            message, product, delivery, {}
        )

        assert virtue_result["virtue_score"] < 80
        assert not virtue_result["passed"]
        assert len(virtue_result["violations"]) > 0

    def test_complete_alignment_check_flow(self):
        """Test complete alignment check flow."""
        # User values privacy and financial savings
        user_values = ValuesAlignmentAgent.extract_user_values(
            {"description": "I care about privacy and want to save money"},
            [],
            []
        )

        # Recommendation aligns perfectly
        recommendation = {
            "description": "Affordable solution with privacy-first design",
            "features": "No data tracking, low cost",
        }

        alignment = ValuesAlignmentAgent.score_recommendation_alignment(
            recommendation, user_values
        )

        assert alignment["passed"] is True

    def test_complete_ethical_check_flow(self):
        """Test complete ethical check flow."""
        message = "Last chance today! Only 2 spots left at premium pricing!"
        product_data = {
            "current_inventory": 100,
            "pricing": {"base_price": 299},
        }

        result = EthicalFramework.ethical_score(message, product_data, {})

        assert result["ethical_score"] < 70
        assert not result["passed"]

    def test_complete_authenticity_check_flow(self):
        """Test complete authenticity check flow."""
        message = "I really struggled with this problem for years. Then I discovered this approach..."
        personality = {"archetype": "founder", "tone": "warm"}

        result = AuthenticityEngine.authenticity_score(
            message, personality, []
        )

        assert result["authenticity_score"] >= 60
        assert result["passed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
