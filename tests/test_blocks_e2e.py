"""
End-to-End Test Suite for SellIA Brain v3

Tests complete pipelines across all blocks:
- Block A: Values + Respect
- Block B: Comment Responses
- Block C: Growth
- Block D: Performance
"""

import pytest
from backend.app.core.sellias_brain_v3 import SellIABrainV3


class TestE2EValidateSalesMessage:
    """E2E test: Validate sales message."""

    def test_good_message_all_validations_pass(self):
        """Test message that passes all ethical checks."""
        brain = SellIABrainV3()

        message = "Try free for 14 days (no credit card required). After trial, $29/month."
        product = {"verified_free_trial": True}
        delivery = {"quality_score": 0.95}
        audience = {"values": ["financial", "privacy"]}

        result = brain.validate_sales_message(message, product, delivery, audience)

        assert result["message_approved"] is True
        assert result["scores"]["virtue"] >= 70
        assert result["scores"]["ethics"] >= 70

    def test_bad_message_fails_validation(self):
        """Test message with ethical issues."""
        brain = SellIABrainV3()

        message = "Last chance! Guaranteed results! Risk-free!"
        product = {}
        delivery = {"quality_score": 0.5}
        audience = {}

        result = brain.validate_sales_message(message, product, delivery, audience)

        assert result["message_approved"] is False
        assert len(result["recommendations"]) > 0


class TestE2ECommentResponse:
    """E2E test: Generate ethical comment response."""

    def test_generate_response_to_praise(self):
        """Test response to positive comment."""
        brain = SellIABrainV3()

        comment = "Love your product! Life-changing!"
        author = {"followers": 1000, "engagement_rate": 0.05}
        post = {"type": "product_showcase"}
        product = {"pricing": {"base_price": 29}}

        response = brain.generate_comment_response(
            comment, author, post, product
        )

        assert response["response_text"]
        assert response["ethics_approved"] is True
        assert len(response["response_text"]) > 10

    def test_generate_response_to_question(self):
        """Test response to question."""
        brain = SellIABrainV3()

        comment = "Does this work with Shopify?"
        author = {"followers": 100}
        post = {"type": "question"}
        product = {"integrations": ["shopify"]}

        response = brain.generate_comment_response(
            comment, author, post, product
        )

        assert "shopify" in response["response_text"].lower() or "yes" in response["response_text"].lower()
        assert response["ethics_approved"] is True

    def test_generate_response_values_alignment(self):
        """Test response respects user values."""
        brain = SellIABrainV3()

        comment = "I care about privacy and sustainability"
        author = {
            "follower": 500,
            "values": ["privacy", "environmental"],
        }
        post = {"type": "question"}
        product = {
            "pricing": {"base_price": 29},
            "eco_friendly": True,
        }

        response = brain.generate_comment_response(
            comment, author, post, product
        )

        assert response["values_aligned"] is True


class TestE2EGrowthPlanning:
    """E2E test: Growth strategy planning."""

    def test_bootstrap_growth_plan(self):
        """Test bootstrap growth plan generation."""
        brain = SellIABrainV3()

        result = brain.plan_growth_strategy(
            current_customers=0,
            product_category="ecommerce",
            target_month_1=50,
        )

        assert result["strategy_type"]
        assert result["bootstrap_plan"]
        assert result["month_1_target"] == 50
        assert result["recommendations"]

    def test_viral_coefficient_exponential(self):
        """Test viral coefficient for exponential growth."""
        brain = SellIABrainV3()

        result = brain.plan_growth_strategy(
            current_customers=10,
            product_category="service",
            target_month_1=100,
        )

        assert "viral_coefficient" in result
        assert "exponential_growth" in result


class TestE2ESystemHealth:
    """E2E test: System monitoring."""

    def test_system_status_complete(self):
        """Test complete system status report."""
        brain = SellIABrainV3()

        status = brain.get_system_status()

        assert status["version"] == "3.0.0"
        assert status["status"] == "production_ready"
        assert status["initialized"] is True
        assert "health" in status
        assert "features_enabled" in status


class TestE2EIntegration:
    """Full integration test."""

    def test_complete_sales_workflow(self):
        """Test complete sales workflow."""
        brain = SellIABrainV3()

        # Step 1: Plan growth
        growth_plan = brain.plan_growth_strategy(0, "ecommerce", 50)
        assert growth_plan["month_1_target"] == 50

        # Step 2: Validate message
        message = "Try free for 14 days. No credit card. $29/month after."
        validation = brain.validate_sales_message(
            message,
            {"verified_free_trial": True},
            {"quality_score": 0.9},
            {"values": ["financial"]}
        )
        assert validation["message_approved"] is True

        # Step 3: Generate response to comment
        response = brain.generate_comment_response(
            "Interested! How does it work?",
            {"followers": 100},
            {"type": "question"},
            {"pricing": {"base_price": 29}},
        )
        assert response["ethics_approved"] is True

        # Step 4: Check system health
        health = brain.monitor_system_health()
        assert health["status"] == "healthy"

        print("✓ Complete sales workflow test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
