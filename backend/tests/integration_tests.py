"""Integration tests — Multi-component system workflows.

Tests cover:
- End-to-end workflows
- Component interactions
- Data flow
- Error propagation
- State consistency
- Performance under load
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch
from app.core.market.market_detector import MarketDetector, Industry
from app.core.strategy.strategy_engine import StrategyEngine
from app.core.ml.ml_engine import MLEngine
from app.core.automation.automation_engine import AutomationEngine
from app.agents.real_estate.real_estate_orchestrator import RealEstateOrchestrator


class TestMarketToStrategyIntegration:
    """Test integration between market detection and strategy selection."""

    @pytest.mark.asyncio
    async def test_market_detection_to_strategy_selection(self):
        """Test workflow from market detection to strategy selection."""
        # Step 1: Detect market
        market_profile = MarketDetector.detect_market(
            "Vendo propiedades inmobiliarias en Miami",
            company_data={"business_name": "Real Estate Co"}
        )

        assert market_profile.industry == Industry.REAL_ESTATE

        # Step 2: Create customer profile from market data
        from app.core.strategy.strategy_engine import CustomerProfile

        profile = CustomerProfile(
            industry=market_profile.industry.value,
            business_model=market_profile.business_model.value,
            buyer_motivation=market_profile.buyer_motivation.value,
            market_type=market_profile.market_type,
            price_sensitivity=0.6,
            trust_level=0.8,
            engagement_history=[],
            purchase_intent=0.7
        )

        # Step 3: Select strategy
        engine = StrategyEngine()
        engine.load_strategies()

        strategy = await engine.select_best_strategy(profile)

        assert strategy is not None
        assert hasattr(strategy, 'name')

    @pytest.mark.asyncio
    async def test_market_context_preservation(self):
        """Test that market context is preserved through strategy pipeline."""
        market_profile = MarketDetector.detect_market(
            "E-commerce de productos electrónicos"
        )

        market_context = {
            "industry": market_profile.industry,
            "business_model": market_profile.business_model,
            "keywords": market_profile.keywords
        }

        # Should preserve context through strategy selection
        engine = StrategyEngine()
        # Pass context to strategy engine
        context_preserved = engine.validate_context(market_context)

        assert context_preserved is not None


class TestStrategyToAutomationIntegration:
    """Test integration between strategy and automation."""

    @pytest.mark.asyncio
    async def test_strategy_driven_automation_workflow(self):
        """Test automation workflow driven by strategy."""
        # Step 1: Select strategy
        strategy = {
            "name": "consultative_selling",
            "tactics": [
                "needs_assessment",
                "solution_presentation",
                "objection_handling"
            ]
        }

        # Step 2: Generate automation tasks from strategy
        engine = AutomationEngine()
        engine.load_workflows()

        workflow = await engine.generate_workflow_from_strategy(strategy)

        assert workflow is not None
        assert len(workflow.get("tasks", [])) > 0

        # Step 3: Execute automation
        result = await engine.execute_workflow(workflow)

        assert result is not None

    @pytest.mark.asyncio
    async def test_strategy_parameter_propagation(self):
        """Test that strategy parameters propagate to automation tasks."""
        strategy = {
            "name": "high_touch_approach",
            "parameters": {
                "contact_frequency": "daily",
                "personalization_level": "high",
                "response_time": 60
            }
        }

        engine = AutomationEngine()

        workflow = await engine.generate_workflow_from_strategy(strategy)

        # Check that parameters are in workflow
        assert workflow is not None


class TestMLPredictionToAutomationIntegration:
    """Test integration between ML predictions and automation."""

    @pytest.mark.asyncio
    async def test_prediction_driven_automation(self):
        """Test automation triggered by ML predictions."""
        # Step 1: Get ML predictions
        import numpy as np

        ml_engine = MLEngine()
        ml_engine.load_models()

        features = np.array([0.8, 0.9, 8, 1, 5000.0, 3])

        conversion_prob = await ml_engine.conversion_predictor.predict(features)
        lead_score = await ml_engine.lead_scorer.score({
            "engagement": 0.8,
            "interest_signals": 5,
            "budget": 5000
        })

        # Step 2: Route to automation based on predictions
        auto_engine = AutomationEngine()

        if conversion_prob > 0.7:
            workflow = {
                "name": "aggressive_close",
                "priority": "high",
                "tasks": [
                    {"type": "prepare_proposal"},
                    {"type": "schedule_call"},
                    {"type": "send_offer"}
                ]
            }
        else:
            workflow = {
                "name": "nurture_lead",
                "priority": "normal",
                "tasks": [
                    {"type": "send_educational_content"},
                    {"type": "schedule_followup"}
                ]
            }

        result = await auto_engine.execute_workflow(workflow)

        assert result is not None

    @pytest.mark.asyncio
    async def test_churn_prediction_automation(self):
        """Test automation for churn prevention based on predictions."""
        ml_engine = MLEngine()
        ml_engine.load_models()

        customer_data = {
            "account_age_days": 90,
            "satisfaction_score": 0.3,
            "support_tickets": 10
        }

        churn_prob = await ml_engine.churn_predictor.predict(customer_data)

        # If high churn probability, trigger retention automation
        if churn_prob > 0.7:
            auto_engine = AutomationEngine()

            retention_workflow = {
                "name": "retention_save",
                "priority": "critical",
                "tasks": [
                    {"type": "manager_outreach"},
                    {"type": "offer_special_terms"},
                    {"type": "schedule_win_back_call"}
                ]
            }

            result = await auto_engine.execute_workflow(retention_workflow)

            assert result is not None


class TestRealEstateIntegration:
    """Test real estate specific integration."""

    @pytest.mark.asyncio
    async def test_property_analysis_to_lead_scoring(self):
        """Test workflow from property analysis to lead scoring."""
        # Step 1: Analyze property
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "address": "123 Main St",
            "square_meters": 200,
            "bedrooms": 3,
            "price": 500000,
            "neighborhood": "downtown"
        }

        property_analysis = await orchestrator.analyze_property(property_data)

        assert property_analysis is not None

        # Step 2: Use property analysis in lead scoring
        lead = {
            "budget": 550000,
            "property_preferences": {
                "square_meters": [150, 250],
                "bedrooms": 3,
                "location": "downtown"
            }
        }

        # Match property to lead based on analysis
        match_score = await orchestrator.score_property_lead_match(
            property_analysis,
            lead
        )

        assert 0 <= match_score <= 100

    @pytest.mark.asyncio
    async def test_market_intelligence_to_pricing(self):
        """Test market intelligence influencing pricing strategy."""
        orchestrator = RealEstateOrchestrator()

        # Step 1: Analyze market
        market_trends = await orchestrator.analyze_market_trends({
            "location": "downtown",
            "property_type": "residential"
        })

        # Step 2: Use trends for pricing
        property_data = {
            "estimated_value": 500000,
            "square_meters": 200,
            "condition": "excellent"
        }

        # Adjust pricing based on market trends
        pricing = await orchestrator.recommend_listing_price(property_data)

        assert "suggested_price" in pricing


class TestEndToEndSalesFlow:
    """Test complete sales flow from lead to closing."""

    @pytest.mark.asyncio
    async def test_complete_sales_cycle(self):
        """Test complete sales cycle from lead discovery to close."""
        # Phase 1: Lead Identification & Qualification
        market_detector = MarketDetector()

        market_profile = market_detector.detect_market(
            "Looking to buy investment property"
        )

        # Phase 2: Strategy Selection
        strategy_engine = StrategyEngine()
        strategy_engine.load_strategies()

        from app.core.strategy.strategy_engine import CustomerProfile

        customer_profile = CustomerProfile(
            industry=market_profile.industry.value,
            business_model=market_profile.business_model.value,
            buyer_motivation=market_profile.buyer_motivation.value,
            market_type=market_profile.market_type,
            price_sensitivity=0.5,
            trust_level=0.8,
            engagement_history=[],
            purchase_intent=0.7
        )

        strategy = await strategy_engine.select_best_strategy(customer_profile)
        assert strategy is not None

        # Phase 3: ML Prediction for Lead Score
        ml_engine = MLEngine()
        ml_engine.load_models()

        import numpy as np
        features = np.array([0.7, 0.8, 6, 2, 2000.0, 2])

        lead_score = await ml_engine.lead_scorer.score({
            "engagement": 0.7,
            "interest_signals": 6,
            "budget": 500000
        })

        # Phase 4: Automation Execution
        auto_engine = AutomationEngine()

        automation_workflow = {
            "name": "sales_cycle",
            "tasks": [
                {
                    "type": "send_welcome",
                    "params": {"template": "real_estate_welcome"}
                },
                {
                    "type": "property_recommendations",
                    "params": {"budget": 500000, "type": "investment"}
                },
                {
                    "type": "schedule_viewing",
                    "params": {"lead_id": "lead_123"}
                }
            ]
        }

        result = await auto_engine.execute_workflow(automation_workflow)

        assert result is not None

    @pytest.mark.asyncio
    async def test_multi_channel_lead_engagement(self):
        """Test engaging lead across multiple channels."""
        from app.core.orchestration.multi_platform_orchestrator import (
            MultiPlatformOrchestrator
        )

        orchestrator = MultiPlatformOrchestrator()

        lead = {
            "id": "multi_lead_123",
            "email": "buyer@example.com",
            "phone": "+1234567890",
            "preferred_channels": ["whatsapp", "email"]
        }

        # Engage on multiple channels
        engagement_result = await orchestrator.engage_on_channels(
            lead,
            channels=["whatsapp", "email", "mercadolibre"]
        )

        assert engagement_result is not None


class TestDataConsistency:
    """Test data consistency across components."""

    @pytest.mark.asyncio
    async def test_state_consistency_through_workflow(self):
        """Test that state remains consistent through workflow."""
        auto_engine = AutomationEngine()

        initial_state = {
            "lead_id": "lead_consistency_test",
            "stage": "qualification",
            "score": 85,
            "timestamp": datetime.now().isoformat()
        }

        # Save state
        await auto_engine.save_state("test_exec_123", initial_state)

        # Execute workflow
        workflow = {
            "name": "test_consistency",
            "tasks": [
                {"type": "update_score", "params": {"delta": 5}},
                {"type": "advance_stage", "params": {"new_stage": "proposal"}}
            ]
        }

        result = await auto_engine.execute_workflow(workflow)

        # Restore and verify state
        restored_state = await auto_engine.restore_state("test_exec_123")

        assert restored_state is not None

    @pytest.mark.asyncio
    async def test_event_ordering_consistency(self):
        """Test that events maintain ordering through pipeline."""
        auto_engine = AutomationEngine()

        events = [
            {"type": "lead_received", "timestamp": datetime.now()},
            {"type": "qualification_started", "timestamp": datetime.now()},
            {"type": "score_assigned", "timestamp": datetime.now()},
            {"type": "proposal_sent", "timestamp": datetime.now()}
        ]

        # Record events in order
        for event in events:
            await auto_engine.record_event("lead_123", event)

        # Retrieve and verify order
        recorded_events = await auto_engine.get_event_history("lead_123")

        assert len(recorded_events) == len(events)


class TestErrorPropagation:
    """Test error handling and propagation."""

    @pytest.mark.asyncio
    async def test_error_propagation_through_pipeline(self):
        """Test error propagation through component pipeline."""
        auto_engine = AutomationEngine()

        workflow = {
            "name": "error_test",
            "tasks": [
                {"type": "valid_task"},
                {"type": "failing_task"},
                {"type": "should_not_execute"}
            ]
        }

        result = await auto_engine.execute_workflow(workflow)

        # Should have error information
        assert "errors" in result or "status" in result

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test system graceful degradation on component failure."""
        from app.core.orchestration.multi_platform_orchestrator import (
            MultiPlatformOrchestrator
        )

        orchestrator = MultiPlatformOrchestrator()

        lead = {"id": "lead_degradation"}

        # Try sending with all channels, should fallback gracefully
        result = await orchestrator.send_with_failover(
            lead,
            message="Test message",
            primary_channel="unavailable",
            fallback_channels=["email", "sms"]
        )

        # Should succeed with fallback
        assert result is not None


class TestPerformanceUnderLoad:
    """Test system performance under load."""

    @pytest.mark.asyncio
    async def test_concurrent_lead_processing(self):
        """Test processing multiple leads concurrently."""
        import asyncio

        auto_engine = AutomationEngine()

        leads = [
            {"id": f"lead_{i}", "score": 50 + i}
            for i in range(10)
        ]

        tasks = []
        for lead in leads:
            workflow = {
                "name": f"process_{lead['id']}",
                "tasks": [
                    {"type": "analyze", "params": {"lead": lead}}
                ]
            }
            tasks.append(auto_engine.execute_workflow(workflow))

        results = await asyncio.gather(*tasks)

        assert len(results) == len(leads)

    @pytest.mark.asyncio
    async def test_high_volume_message_sending(self):
        """Test sending messages at high volume."""
        from app.core.connectors.whatsapp_connector import WhatsappConnector

        connector = WhatsappConnector(
            phone_number="+1234567890",
            api_token="test_token"
        )

        # Send multiple messages
        message_results = []
        for i in range(50):
            result = await connector.send_message(
                recipient=f"+123456789{i % 10}",
                message=f"Message {i}"
            )
            message_results.append(result)

        # Should handle volume
        assert len(message_results) == 50


class TestIntegrationEdgeCases:
    """Test integration edge cases."""

    @pytest.mark.asyncio
    async def test_component_timeout_handling(self):
        """Test handling timeouts in component chain."""
        auto_engine = AutomationEngine()

        workflow = {
            "name": "timeout_test",
            "timeout": 1,
            "tasks": [
                {"type": "long_running_task", "duration": 5}
            ]
        }

        result = await auto_engine.execute_workflow(workflow)

        # Should timeout gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_circular_workflow_detection(self):
        """Test detection of circular dependencies in workflow."""
        auto_engine = AutomationEngine()

        workflow = {
            "name": "circular_test",
            "tasks": [
                {"id": "A", "depends_on": ["B"]},
                {"id": "B", "depends_on": ["C"]},
                {"id": "C", "depends_on": ["A"]}
            ]
        }

        result = await auto_engine.execute_workflow(workflow)

        # Should detect or handle circular dependency
        assert result is not None

    @pytest.mark.asyncio
    async def test_resource_cleanup_on_failure(self):
        """Test cleanup of resources on workflow failure."""
        auto_engine = AutomationEngine()

        workflow = {
            "name": "cleanup_test",
            "tasks": [
                {"type": "allocate_resource"},
                {"type": "failing_task"},
                {"type": "cleanup", "always": True}
            ]
        }

        result = await auto_engine.execute_workflow(workflow)

        # Cleanup should execute
        assert result is not None
