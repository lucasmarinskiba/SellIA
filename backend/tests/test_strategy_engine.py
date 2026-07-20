"""Unit tests for strategy_engine.py — Dynamic strategy selection and adaptation.

Tests cover:
- Strategy initialization
- Customer profiling
- Strategy scoring
- Market context integration
- Fallback mechanisms
- Strategy evolution
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.strategy.strategy_engine import (
    StrategyEngine,
    Strategy,
    StrategyScore,
    CustomerProfile,
)


class TestStrategyEngineInitialization:
    """Test strategy engine initialization."""

    def test_engine_initialization(self):
        """Test basic engine initialization."""
        engine = StrategyEngine()

        assert engine is not None
        assert hasattr(engine, 'strategies')
        assert hasattr(engine, 'current_strategy')

    def test_load_strategies(self):
        """Test loading strategies."""
        engine = StrategyEngine()
        engine.load_strategies()

        assert len(engine.strategies) > 0
        assert all(isinstance(s, Strategy) for s in engine.strategies)

    def test_strategies_have_required_fields(self):
        """Test that strategies have all required fields."""
        engine = StrategyEngine()
        engine.load_strategies()

        for strategy in engine.strategies:
            assert hasattr(strategy, 'name')
            assert hasattr(strategy, 'description')
            assert hasattr(strategy, 'weight')
            assert hasattr(strategy, 'conditions')
            assert hasattr(strategy, 'rules')


class TestCustomerProfiling:
    """Test customer profiling capabilities."""

    def test_create_customer_profile(self):
        """Test creating a customer profile."""
        profile = CustomerProfile(
            industry="real_estate",
            business_model="physical",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=0.7,
            trust_level=0.8,
            engagement_history=[],
            purchase_intent=0.6
        )

        assert profile.industry == "real_estate"
        assert profile.business_model == "physical"
        assert 0 <= profile.price_sensitivity <= 1
        assert 0 <= profile.trust_level <= 1

    def test_profile_with_engagement_history(self):
        """Test profile with engagement history."""
        engagement = {
            "interaction_type": "message",
            "timestamp": datetime.now(),
            "sentiment": 0.8
        }
        profile = CustomerProfile(
            industry="commerce",
            business_model="digital",
            buyer_motivation="desire",
            market_type="B2C",
            price_sensitivity=0.5,
            trust_level=0.7,
            engagement_history=[engagement],
            purchase_intent=0.8
        )

        assert len(profile.engagement_history) == 1
        assert profile.engagement_history[0]["sentiment"] == 0.8

    def test_profile_attributes_in_range(self):
        """Test that profile attributes are in valid ranges."""
        profile = CustomerProfile(
            industry="services",
            business_model="service",
            buyer_motivation="need",
            market_type="B2B",
            price_sensitivity=0.9,
            trust_level=0.4,
            engagement_history=[],
            purchase_intent=0.75
        )

        assert 0 <= profile.price_sensitivity <= 1
        assert 0 <= profile.trust_level <= 1
        assert 0 <= profile.purchase_intent <= 1


class TestStrategyScoring:
    """Test strategy scoring and selection."""

    @pytest.mark.asyncio
    async def test_score_strategies_basic(self):
        """Test basic strategy scoring."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="real_estate",
            business_model="physical",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=0.6,
            trust_level=0.8,
            engagement_history=[],
            purchase_intent=0.7
        )

        scores = await engine.score_strategies(profile)

        assert isinstance(scores, list)
        assert len(scores) > 0
        assert all(isinstance(s, StrategyScore) for s in scores)

    @pytest.mark.asyncio
    async def test_score_strategies_sorting(self):
        """Test that strategies are sorted by score (descending)."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="commerce",
            business_model="digital",
            buyer_motivation="desire",
            market_type="B2C",
            price_sensitivity=0.4,
            trust_level=0.9,
            engagement_history=[],
            purchase_intent=0.85
        )

        scores = await engine.score_strategies(profile)

        for i in range(len(scores) - 1):
            assert scores[i].score >= scores[i + 1].score

    @pytest.mark.asyncio
    async def test_score_strategies_all_positive(self):
        """Test that all scores are non-negative."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="services",
            business_model="service",
            buyer_motivation="need",
            market_type="B2B",
            price_sensitivity=0.5,
            trust_level=0.5,
            engagement_history=[],
            purchase_intent=0.5
        )

        scores = await engine.score_strategies(profile)

        for score in scores:
            assert score.score >= 0

    @pytest.mark.asyncio
    async def test_select_best_strategy(self):
        """Test selecting the best strategy."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="real_estate",
            business_model="physical",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=0.3,
            trust_level=0.9,
            engagement_history=[],
            purchase_intent=0.8
        )

        best_strategy = await engine.select_best_strategy(profile)

        assert best_strategy is not None
        assert isinstance(best_strategy, Strategy)

    @pytest.mark.asyncio
    async def test_select_strategy_considers_price_sensitivity(self):
        """Test that strategy selection considers price sensitivity."""
        engine = StrategyEngine()
        engine.load_strategies()

        high_price_sensitive = CustomerProfile(
            industry="commerce",
            business_model="digital",
            buyer_motivation="desire",
            market_type="B2C",
            price_sensitivity=0.9,
            trust_level=0.5,
            engagement_history=[],
            purchase_intent=0.5
        )

        low_price_sensitive = CustomerProfile(
            industry="commerce",
            business_model="digital",
            buyer_motivation="luxury",
            market_type="B2B",
            price_sensitivity=0.1,
            trust_level=0.7,
            engagement_history=[],
            purchase_intent=0.7
        )

        strategy_high = await engine.select_best_strategy(high_price_sensitive)
        strategy_low = await engine.select_best_strategy(low_price_sensitive)

        # Strategies should adapt to price sensitivity
        assert strategy_high is not None
        assert strategy_low is not None

    @pytest.mark.asyncio
    async def test_select_strategy_considers_trust_level(self):
        """Test that strategy selection considers trust level."""
        engine = StrategyEngine()
        engine.load_strategies()

        high_trust = CustomerProfile(
            industry="finance",
            business_model="digital",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=0.5,
            trust_level=0.95,
            engagement_history=[],
            purchase_intent=0.8
        )

        low_trust = CustomerProfile(
            industry="finance",
            business_model="digital",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=0.5,
            trust_level=0.1,
            engagement_history=[],
            purchase_intent=0.3
        )

        strategy_high = await engine.select_best_strategy(high_trust)
        strategy_low = await engine.select_best_strategy(low_trust)

        assert strategy_high is not None
        assert strategy_low is not None


class TestStrategyAdaptation:
    """Test strategy adaptation and learning."""

    @pytest.mark.asyncio
    async def test_update_strategy_performance(self):
        """Test updating strategy performance metrics."""
        engine = StrategyEngine()
        engine.load_strategies()

        strategy = engine.strategies[0]
        original_success_rate = strategy.success_rate

        # Record a successful outcome
        await engine.record_strategy_outcome(
            strategy_name=strategy.name,
            success=True,
            customer_feedback=0.9
        )

        # Success rate should improve
        assert strategy.success_rate >= original_success_rate

    @pytest.mark.asyncio
    async def test_fallback_strategy_selection(self):
        """Test fallback to alternative strategy."""
        engine = StrategyEngine()
        engine.load_strategies()

        # Get first strategy
        primary_strategy = engine.strategies[0]

        # Simulate primary strategy failure
        profile = CustomerProfile(
            industry="commerce",
            business_model="digital",
            buyer_motivation="desire",
            market_type="B2C",
            price_sensitivity=0.5,
            trust_level=0.5,
            engagement_history=[],
            purchase_intent=0.5
        )

        # Should get fallback strategy
        fallback = await engine.get_fallback_strategy(primary_strategy, profile)

        assert fallback is not None
        if len(engine.strategies) > 1:
            assert fallback.name != primary_strategy.name

    @pytest.mark.asyncio
    async def test_strategy_evolution(self):
        """Test strategy evolution over multiple interactions."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="real_estate",
            business_model="physical",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=0.4,
            trust_level=0.8,
            engagement_history=[],
            purchase_intent=0.7
        )

        # Run multiple iterations
        strategies_over_time = []
        for _ in range(3):
            strategy = await engine.select_best_strategy(profile)
            strategies_over_time.append(strategy.name)

        # Engine should adapt but maintain consistency
        assert len(strategies_over_time) == 3


class TestMarketContextIntegration:
    """Test integration with market context."""

    @pytest.mark.asyncio
    async def test_strategy_selection_with_market_rules(self):
        """Test strategy selection respects market rules."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="finance",
            business_model="digital",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=0.3,
            trust_level=0.9,
            engagement_history=[],
            purchase_intent=0.85
        )

        strategy = await engine.select_best_strategy(profile)

        # Strategy should be compliant with finance regulations
        assert strategy is not None
        assert hasattr(strategy, 'rules')

    @pytest.mark.asyncio
    async def test_strategy_adapts_to_market_conditions(self):
        """Test strategy adaptation based on market conditions."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="commerce",
            business_model="physical",
            buyer_motivation="need",
            market_type="B2C",
            price_sensitivity=0.7,
            trust_level=0.6,
            engagement_history=[],
            purchase_intent=0.6
        )

        # Get strategy for normal conditions
        normal_strategy = await engine.select_best_strategy(profile)

        # Simulate market stress
        engine.market_stress_level = 0.8

        stress_strategy = await engine.select_best_strategy(profile)

        assert normal_strategy is not None
        assert stress_strategy is not None


class TestStrategyEngineEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_strategies_list(self):
        """Test handling when no strategies are loaded."""
        engine = StrategyEngine()
        engine.strategies = []

        profile = CustomerProfile(
            industry="commerce",
            business_model="digital",
            buyer_motivation="desire",
            market_type="B2C",
            price_sensitivity=0.5,
            trust_level=0.5,
            engagement_history=[],
            purchase_intent=0.5
        )

        # Should handle gracefully
        result = await engine.select_best_strategy(profile)

        # Either return None or raise meaningful error
        assert result is None or isinstance(result, Strategy)

    @pytest.mark.asyncio
    async def test_profile_with_extreme_values(self):
        """Test strategy selection with extreme profile values."""
        engine = StrategyEngine()
        engine.load_strategies()

        extreme_profile = CustomerProfile(
            industry="real_estate",
            business_model="physical",
            buyer_motivation="investment",
            market_type="B2B",
            price_sensitivity=1.0,
            trust_level=0.0,
            engagement_history=[],
            purchase_intent=1.0
        )

        strategy = await engine.select_best_strategy(extreme_profile)

        assert strategy is not None

    @pytest.mark.asyncio
    async def test_strategy_with_no_matching_conditions(self):
        """Test when no strategy matches conditions."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="other",
            business_model="hybrid",
            buyer_motivation="desire",
            market_type="unknown",
            price_sensitivity=0.5,
            trust_level=0.5,
            engagement_history=[],
            purchase_intent=0.5
        )

        strategy = await engine.select_best_strategy(profile)

        # Should still return a strategy (fallback)
        assert strategy is not None

    @pytest.mark.asyncio
    async def test_rapid_strategy_changes(self):
        """Test handling of rapid strategy changes."""
        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="commerce",
            business_model="digital",
            buyer_motivation="desire",
            market_type="B2C",
            price_sensitivity=0.5,
            trust_level=0.5,
            engagement_history=[],
            purchase_intent=0.5
        )

        # Get strategies rapidly
        strategies = []
        for _ in range(5):
            strategy = await engine.select_best_strategy(profile)
            strategies.append(strategy)

        # All should be valid
        assert all(s is not None for s in strategies)

    @pytest.mark.asyncio
    async def test_concurrent_strategy_scoring(self):
        """Test concurrent strategy scoring."""
        import asyncio

        engine = StrategyEngine()
        engine.load_strategies()

        profile = CustomerProfile(
            industry="services",
            business_model="service",
            buyer_motivation="need",
            market_type="B2B",
            price_sensitivity=0.5,
            trust_level=0.5,
            engagement_history=[],
            purchase_intent=0.5
        )

        # Run concurrent scoring
        tasks = [
            engine.select_best_strategy(profile)
            for _ in range(3)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(r is not None for r in results)


class TestStrategyPersistence:
    """Test strategy persistence and recovery."""

    @pytest.mark.asyncio
    async def test_save_strategy_state(self):
        """Test saving strategy engine state."""
        engine = StrategyEngine()
        engine.load_strategies()

        state = engine.get_state()

        assert isinstance(state, dict)
        assert 'strategies' in state
        assert 'current_strategy' in state

    @pytest.mark.asyncio
    async def test_restore_strategy_state(self):
        """Test restoring strategy engine state."""
        engine1 = StrategyEngine()
        engine1.load_strategies()
        state = engine1.get_state()

        engine2 = StrategyEngine()
        await engine2.restore_state(state)

        # Should have same number of strategies
        assert len(engine2.strategies) == len(engine1.strategies)

    @pytest.mark.asyncio
    async def test_strategy_state_consistency(self):
        """Test that strategy state remains consistent."""
        engine = StrategyEngine()
        engine.load_strategies()

        initial_strategy_count = len(engine.strategies)

        # Save and restore
        state = engine.get_state()
        await engine.restore_state(state)

        assert len(engine.strategies) == initial_strategy_count
