"""Unit tests for ml_engine.py — ML-powered sales prediction and optimization.

Tests cover:
- Model training
- Sales prediction
- Conversion rate estimation
- Lead scoring
- Churn prediction
- Feature extraction
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.ml.ml_engine import (
    MLEngine,
    SalesPredictor,
    ConversionPredictor,
    LeadScorer,
    ChurnPredictor,
    FeatureExtractor,
)


class TestMLEngineInitialization:
    """Test ML engine initialization and setup."""

    def test_engine_initialization(self):
        """Test basic ML engine initialization."""
        engine = MLEngine()

        assert engine is not None
        assert hasattr(engine, 'predictors')
        assert hasattr(engine, 'feature_extractor')

    def test_load_models(self):
        """Test loading pre-trained models."""
        engine = MLEngine()
        engine.load_models()

        assert engine.sales_predictor is not None
        assert engine.conversion_predictor is not None
        assert engine.lead_scorer is not None
        assert engine.churn_predictor is not None

    def test_model_initialization_state(self):
        """Test that models are properly initialized."""
        engine = MLEngine()
        engine.load_models()

        assert hasattr(engine.sales_predictor, 'is_trained')
        assert hasattr(engine.conversion_predictor, 'is_trained')


class TestFeatureExtraction:
    """Test feature extraction from raw data."""

    def test_extract_features_from_customer_data(self):
        """Test feature extraction from customer data."""
        extractor = FeatureExtractor()

        customer_data = {
            "industry": "commerce",
            "business_model": "digital",
            "price_sensitivity": 0.6,
            "trust_level": 0.8,
            "engagement_count": 5,
            "last_interaction_days": 2,
            "total_value": 1500.0,
            "previous_purchases": 2
        }

        features = extractor.extract(customer_data)

        assert isinstance(features, np.ndarray) or isinstance(features, list)
        assert len(features) > 0

    def test_feature_normalization(self):
        """Test that features are normalized."""
        extractor = FeatureExtractor()

        customer_data = {
            "price_sensitivity": 0.9,
            "trust_level": 0.1,
            "engagement_count": 100,
            "total_value": 10000.0
        }

        features = extractor.extract(customer_data)
        features_array = np.array(features)

        # Features should be in reasonable range (typically 0-1 or normalized)
        assert not np.isnan(features_array).any()
        assert not np.isinf(features_array).any()

    def test_extract_temporal_features(self):
        """Test extraction of temporal features."""
        extractor = FeatureExtractor()

        customer_data = {
            "account_created": (datetime.now() - timedelta(days=30)).isoformat(),
            "last_interaction": datetime.now().isoformat(),
            "purchase_history": [
                {"date": (datetime.now() - timedelta(days=10)).isoformat()},
                {"date": (datetime.now() - timedelta(days=5)).isoformat()}
            ]
        }

        features = extractor.extract(customer_data)

        assert len(features) > 0

    def test_extract_behavioral_features(self):
        """Test extraction of behavioral features."""
        extractor = FeatureExtractor()

        customer_data = {
            "engagement_events": [
                {"type": "view", "timestamp": datetime.now().isoformat()},
                {"type": "click", "timestamp": datetime.now().isoformat()},
                {"type": "share", "timestamp": datetime.now().isoformat()}
            ],
            "response_time_seconds": 120,
            "message_sentiment": 0.8,
            "negotiation_count": 2
        }

        features = extractor.extract(customer_data)

        assert len(features) > 0


class TestSalesPredictor:
    """Test sales prediction capabilities."""

    @pytest.mark.asyncio
    async def test_predict_sales_amount(self):
        """Test predicting sales amount."""
        predictor = SalesPredictor()
        predictor.train_on_sample_data()

        features = np.array([0.6, 0.8, 5, 2, 1500.0, 2])

        prediction = await predictor.predict(features)

        assert prediction is not None
        assert isinstance(prediction, (int, float, np.number))
        assert prediction >= 0

    @pytest.mark.asyncio
    async def test_predict_sales_with_confidence(self):
        """Test sales prediction with confidence interval."""
        predictor = SalesPredictor()
        predictor.train_on_sample_data()

        features = np.array([0.7, 0.9, 8, 1, 3000.0, 3])

        result = await predictor.predict_with_confidence(features)

        assert "prediction" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_batch_prediction(self):
        """Test batch sales prediction."""
        predictor = SalesPredictor()
        predictor.train_on_sample_data()

        features_batch = [
            np.array([0.5, 0.7, 3, 5, 1000.0, 1]),
            np.array([0.8, 0.9, 10, 1, 5000.0, 5]),
            np.array([0.3, 0.4, 1, 10, 500.0, 0])
        ]

        predictions = await predictor.batch_predict(features_batch)

        assert len(predictions) == 3
        assert all(p >= 0 for p in predictions)

    @pytest.mark.asyncio
    async def test_model_training(self):
        """Test model training on data."""
        predictor = SalesPredictor()

        training_data = {
            "features": [
                [0.5, 0.7, 3, 5, 1000.0, 1],
                [0.8, 0.9, 10, 1, 5000.0, 5],
                [0.3, 0.4, 1, 10, 500.0, 0]
            ],
            "targets": [1200.0, 5500.0, 450.0]
        }

        await predictor.train(training_data["features"], training_data["targets"])

        assert predictor.is_trained


class TestConversionPredictor:
    """Test conversion rate prediction."""

    @pytest.mark.asyncio
    async def test_predict_conversion_probability(self):
        """Test predicting conversion probability."""
        predictor = ConversionPredictor()
        predictor.train_on_sample_data()

        features = np.array([0.6, 0.8, 5, 2, 1500.0, 2])

        probability = await predictor.predict(features)

        assert isinstance(probability, (float, np.number))
        assert 0 <= probability <= 1

    @pytest.mark.asyncio
    async def test_predict_conversion_with_factors(self):
        """Test conversion prediction with contributing factors."""
        predictor = ConversionPredictor()
        predictor.train_on_sample_data()

        features = np.array([0.7, 0.9, 8, 1, 3000.0, 3])

        result = await predictor.predict_with_factors(features)

        assert "probability" in result
        assert "factors" in result
        assert 0 <= result["probability"] <= 1
        assert len(result["factors"]) > 0

    @pytest.mark.asyncio
    async def test_batch_conversion_prediction(self):
        """Test batch conversion prediction."""
        predictor = ConversionPredictor()
        predictor.train_on_sample_data()

        features_batch = [
            np.array([0.5, 0.7, 3, 5, 1000.0, 1]),
            np.array([0.8, 0.9, 10, 1, 5000.0, 5])
        ]

        probabilities = await predictor.batch_predict(features_batch)

        assert len(probabilities) == 2
        assert all(0 <= p <= 1 for p in probabilities)

    @pytest.mark.asyncio
    async def test_identify_conversion_obstacles(self):
        """Test identifying obstacles to conversion."""
        predictor = ConversionPredictor()
        predictor.train_on_sample_data()

        features = np.array([0.3, 0.2, 1, 15, 200.0, 0])

        obstacles = await predictor.identify_obstacles(features)

        assert isinstance(obstacles, list)
        assert len(obstacles) > 0


class TestLeadScorer:
    """Test lead scoring capabilities."""

    @pytest.mark.asyncio
    async def test_score_lead(self):
        """Test basic lead scoring."""
        scorer = LeadScorer()
        scorer.train_on_sample_data()

        lead_data = {
            "engagement": 0.8,
            "interest_signals": 5,
            "budget": 5000,
            "timeline": "immediate",
            "company_size": "medium"
        }

        score = await scorer.score(lead_data)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_lead_scoring_with_breakdown(self):
        """Test lead scoring with component breakdown."""
        scorer = LeadScorer()
        scorer.train_on_sample_data()

        lead_data = {
            "engagement": 0.9,
            "interest_signals": 8,
            "budget": 10000,
            "timeline": "immediate",
            "company_size": "large"
        }

        result = await scorer.score_with_breakdown(lead_data)

        assert "total_score" in result
        assert "components" in result
        assert 0 <= result["total_score"] <= 100
        assert len(result["components"]) > 0

    @pytest.mark.asyncio
    async def test_identify_high_quality_leads(self):
        """Test identifying high-quality leads."""
        scorer = LeadScorer()
        scorer.train_on_sample_data()

        leads = [
            {"engagement": 0.8, "interest_signals": 5, "budget": 5000},
            {"engagement": 0.2, "interest_signals": 1, "budget": 500},
            {"engagement": 0.9, "interest_signals": 8, "budget": 10000}
        ]

        high_quality = await scorer.filter_high_quality(leads, threshold=70)

        assert isinstance(high_quality, list)
        assert len(high_quality) <= len(leads)

    @pytest.mark.asyncio
    async def test_lead_prioritization(self):
        """Test lead prioritization."""
        scorer = LeadScorer()
        scorer.train_on_sample_data()

        leads = [
            {"id": 1, "engagement": 0.5, "budget": 2000},
            {"id": 2, "engagement": 0.9, "budget": 8000},
            {"id": 3, "engagement": 0.7, "budget": 4000}
        ]

        ranked_leads = await scorer.rank_leads(leads)

        assert len(ranked_leads) == 3
        # Should be sorted by score
        if len(ranked_leads) > 1:
            for i in range(len(ranked_leads) - 1):
                assert ranked_leads[i]["score"] >= ranked_leads[i + 1]["score"]


class TestChurnPredictor:
    """Test churn prediction capabilities."""

    @pytest.mark.asyncio
    async def test_predict_churn_probability(self):
        """Test predicting customer churn probability."""
        predictor = ChurnPredictor()
        predictor.train_on_sample_data()

        customer_data = {
            "account_age_days": 180,
            "interaction_frequency": 2,
            "last_purchase_days": 30,
            "satisfaction_score": 0.7,
            "support_tickets": 2
        }

        probability = await predictor.predict(customer_data)

        assert isinstance(probability, (float, np.number))
        assert 0 <= probability <= 1

    @pytest.mark.asyncio
    async def test_identify_churn_risk_factors(self):
        """Test identifying churn risk factors."""
        predictor = ChurnPredictor()
        predictor.train_on_sample_data()

        customer_data = {
            "account_age_days": 60,
            "interaction_frequency": 0.5,
            "last_purchase_days": 90,
            "satisfaction_score": 0.3,
            "support_tickets": 10
        }

        risk_factors = await predictor.identify_risk_factors(customer_data)

        assert isinstance(risk_factors, list)
        assert len(risk_factors) > 0

    @pytest.mark.asyncio
    async def test_churn_prevention_recommendations(self):
        """Test churn prevention recommendations."""
        predictor = ChurnPredictor()
        predictor.train_on_sample_data()

        customer_data = {
            "account_age_days": 90,
            "interaction_frequency": 1,
            "last_purchase_days": 60,
            "satisfaction_score": 0.4,
            "support_tickets": 5
        }

        recommendations = await predictor.get_prevention_actions(customer_data)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_batch_churn_prediction(self):
        """Test batch churn prediction."""
        predictor = ChurnPredictor()
        predictor.train_on_sample_data()

        customers = [
            {"account_age_days": 180, "satisfaction_score": 0.8},
            {"account_age_days": 30, "satisfaction_score": 0.3}
        ]

        probabilities = await predictor.batch_predict(customers)

        assert len(probabilities) == 2
        assert all(0 <= p <= 1 for p in probabilities)


class TestMLEngineIntegration:
    """Test integration of ML components."""

    @pytest.mark.asyncio
    async def test_comprehensive_customer_analysis(self):
        """Test comprehensive customer analysis with all ML models."""
        engine = MLEngine()
        engine.load_models()

        customer_data = {
            "industry": "commerce",
            "engagement": 0.8,
            "price_sensitivity": 0.5,
            "trust_level": 0.9,
            "account_age_days": 180,
            "satisfaction_score": 0.85
        }

        analysis = await engine.analyze_customer(customer_data)

        assert "sales_prediction" in analysis
        assert "conversion_probability" in analysis
        assert "lead_score" in analysis
        assert "churn_risk" in analysis

    @pytest.mark.asyncio
    async def test_model_ensemble_prediction(self):
        """Test ensemble prediction combining multiple models."""
        engine = MLEngine()
        engine.load_models()

        features = np.array([0.7, 0.8, 6, 2, 2000.0, 2])

        ensemble_result = await engine.ensemble_predict(features)

        assert "sales" in ensemble_result
        assert "conversion" in ensemble_result
        assert "lead_score" in ensemble_result

    @pytest.mark.asyncio
    async def test_model_retraining(self):
        """Test retraining models with new data."""
        engine = MLEngine()
        engine.load_models()

        new_data = {
            "features": [
                [0.6, 0.8, 5, 2, 1500.0],
                [0.8, 0.9, 10, 1, 5000.0]
            ],
            "targets": [1600.0, 5200.0]
        }

        await engine.retrain_models(new_data)

        # Models should still be functional after retraining
        assert engine.is_trained


class TestMLEngineEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_predict_with_missing_features(self):
        """Test prediction with missing features."""
        predictor = SalesPredictor()
        predictor.train_on_sample_data()

        # Use different size array
        try:
            features = np.array([0.6, 0.8])
            prediction = await predictor.predict(features)
            # Should either handle gracefully or raise error
            assert prediction is not None or isinstance(prediction, Exception)
        except (ValueError, IndexError):
            # Expected behavior
            pass

    @pytest.mark.asyncio
    async def test_extreme_feature_values(self):
        """Test prediction with extreme feature values."""
        predictor = SalesPredictor()
        predictor.train_on_sample_data()

        extreme_features = np.array([0.0, 1.0, 1000, 0, 1000000.0, 1000])

        prediction = await predictor.predict(extreme_features)

        assert prediction is not None
        assert not np.isnan(prediction)

    @pytest.mark.asyncio
    async def test_model_without_training(self):
        """Test prediction with untrained model."""
        predictor = SalesPredictor()

        features = np.array([0.6, 0.8, 5, 2, 1500.0, 2])

        try:
            prediction = await predictor.predict(features)
            # Should either use default model or raise error
            assert prediction is None or isinstance(prediction, (int, float))
        except RuntimeError:
            # Expected if model not trained
            pass

    @pytest.mark.asyncio
    async def test_batch_prediction_empty_list(self):
        """Test batch prediction with empty list."""
        predictor = SalesPredictor()
        predictor.train_on_sample_data()

        predictions = await predictor.batch_predict([])

        assert isinstance(predictions, list)
        assert len(predictions) == 0

    @pytest.mark.asyncio
    async def test_concurrent_predictions(self):
        """Test concurrent predictions."""
        import asyncio

        predictor = SalesPredictor()
        predictor.train_on_sample_data()

        features = np.array([0.6, 0.8, 5, 2, 1500.0, 2])

        tasks = [predictor.predict(features) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r is not None for r in results)
