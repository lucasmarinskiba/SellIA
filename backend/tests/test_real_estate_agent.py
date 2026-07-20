"""Unit tests for real estate agent orchestrator.

Tests cover:
- Property analysis
- Lead scoring for real estate
- Negotiation strategies
- Pricing recommendations
- Legal compliance
- Market intelligence
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.real_estate.real_estate_orchestrator import (
    RealEstateOrchestrator,
    PropertyAnalysis,
    LeadProfile,
    NegotiationContext,
)


class TestPropertyAnalysis:
    """Test property analysis capabilities."""

    @pytest.mark.asyncio
    async def test_analyze_property_basic(self):
        """Test basic property analysis."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "address": "123 Main St",
            "square_meters": 150,
            "bedrooms": 3,
            "bathrooms": 2,
            "year_built": 2015,
            "neighborhood": "Downtown",
            "property_type": "house",
            "condition": "excellent"
        }

        analysis = await orchestrator.analyze_property(property_data)

        assert analysis is not None
        assert hasattr(analysis, 'valuation')
        assert hasattr(analysis, 'market_competitiveness')
        assert hasattr(analysis, 'investment_potential')

    @pytest.mark.asyncio
    async def test_estimate_property_value(self):
        """Test property valuation estimation."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "address": "456 Oak Ave",
            "square_meters": 200,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 2010,
            "condition": "good"
        }

        valuation = await orchestrator.estimate_value(property_data)

        assert isinstance(valuation, (int, float))
        assert valuation > 0

    @pytest.mark.asyncio
    async def test_compare_with_market_comps(self):
        """Test comparing property with market comparables."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "address": "789 Pine Rd",
            "square_meters": 180,
            "bedrooms": 3,
            "bathrooms": 2,
            "neighborhood": "Suburbs"
        }

        comparison = await orchestrator.compare_with_comps(property_data)

        assert "price_per_sqm" in comparison
        assert "market_position" in comparison
        assert "value_relative_to_market" in comparison

    @pytest.mark.asyncio
    async def test_identify_property_issues(self):
        """Test identifying potential property issues."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "square_meters": 100,
            "age": 50,
            "condition": "needs_repair",
            "foundation_issues": True,
            "roof_age": 25
        }

        issues = await orchestrator.identify_issues(property_data)

        assert isinstance(issues, list)
        if len(issues) > 0:
            assert all(isinstance(i, str) for i in issues)

    @pytest.mark.asyncio
    async def test_investment_potential_analysis(self):
        """Test analyzing investment potential."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "purchase_price": 300000,
            "square_meters": 200,
            "bedrooms": 3,
            "neighborhood": "Emerging",
            "rental_income_potential": 1500
        }

        investment_analysis = await orchestrator.analyze_investment(property_data)

        assert "roi_potential" in investment_analysis
        assert "cash_flow_projection" in investment_analysis
        assert "appreciation_forecast" in investment_analysis


class TestRealEstateLeadScoring:
    """Test lead scoring specific to real estate."""

    @pytest.mark.asyncio
    async def test_score_real_estate_lead(self):
        """Test scoring a real estate lead."""
        orchestrator = RealEstateOrchestrator()

        lead_data = {
            "budget": 500000,
            "timeline": "3_months",
            "property_type_preference": "house",
            "location_preference": "downtown",
            "engagement_level": 0.8,
            "previous_purchases": 1
        }

        score = await orchestrator.score_lead(lead_data)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_identify_buyer_profile(self):
        """Test identifying buyer profile characteristics."""
        orchestrator = RealEstateOrchestrator()

        lead_data = {
            "budget": 750000,
            "family_size": 4,
            "commute_preference": "public_transit",
            "investment_intent": True,
            "timeline": "immediate"
        }

        profile = await orchestrator.identify_buyer_profile(lead_data)

        assert profile is not None
        assert "buyer_type" in profile
        assert "motivation" in profile
        assert "key_priorities" in profile

    @pytest.mark.asyncio
    async def test_property_recommendations(self):
        """Test recommending properties for a lead."""
        orchestrator = RealEstateOrchestrator()

        lead_data = {
            "budget": 400000,
            "bedrooms": 3,
            "location": "suburbs",
            "property_type": "house",
            "commute_distance": 20
        }

        available_properties = [
            {
                "id": 1,
                "price": 380000,
                "bedrooms": 3,
                "location": "suburbs",
                "distance_from_commute": 18
            },
            {
                "id": 2,
                "price": 450000,
                "bedrooms": 4,
                "location": "suburbs",
                "distance_from_commute": 25
            },
            {
                "id": 3,
                "price": 420000,
                "bedrooms": 3,
                "location": "downtown",
                "distance_from_commute": 5
            }
        ]

        recommendations = await orchestrator.recommend_properties(
            lead_data,
            available_properties
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_lead_readiness_assessment(self):
        """Test assessing if lead is ready to purchase."""
        orchestrator = RealEstateOrchestrator()

        lead_data = {
            "mortgage_preapproval": True,
            "viewed_properties": 5,
            "made_offers": 0,
            "timeline": "immediate",
            "budget_confirmed": True
        }

        readiness = await orchestrator.assess_readiness(lead_data)

        assert 0 <= readiness <= 1


class TestNegotiationStrategies:
    """Test negotiation strategy selection and execution."""

    @pytest.mark.asyncio
    async def test_select_negotiation_strategy(self):
        """Test selecting appropriate negotiation strategy."""
        orchestrator = RealEstateOrchestrator()

        context = NegotiationContext(
            property_price=500000,
            buyer_offer=450000,
            buyer_motivation="investment",
            seller_motivation="quick_sale",
            market_conditions="buyer_favored"
        )

        strategy = await orchestrator.select_negotiation_strategy(context)

        assert strategy is not None
        assert hasattr(strategy, 'name')
        assert hasattr(strategy, 'tactics')

    @pytest.mark.asyncio
    async def test_generate_counter_offer(self):
        """Test generating counter-offer."""
        orchestrator = RealEstateOrchestrator()

        negotiation_data = {
            "list_price": 500000,
            "buyer_offer": 420000,
            "comparable_sales": [480000, 495000, 505000],
            "days_on_market": 30,
            "seller_flexibility": "medium"
        }

        counter_offer = await orchestrator.generate_counter_offer(negotiation_data)

        assert isinstance(counter_offer, (int, float))
        assert counter_offer > negotiation_data["buyer_offer"]
        assert counter_offer <= negotiation_data["list_price"]

    @pytest.mark.asyncio
    async def test_identify_negotiation_leverage(self):
        """Test identifying negotiation leverage points."""
        orchestrator = RealEstateOrchestrator()

        context = {
            "buyer_has_financing": True,
            "buyer_timeline": "urgent",
            "property_days_on_market": 90,
            "competing_offers": 0,
            "property_condition": "excellent"
        }

        leverage = await orchestrator.identify_leverage(context)

        assert isinstance(leverage, dict)
        assert "buyer_advantages" in leverage
        assert "seller_advantages" in leverage

    @pytest.mark.asyncio
    async def test_negotiation_suggestions(self):
        """Test generating negotiation suggestions."""
        orchestrator = RealEstateOrchestrator()

        context = {
            "current_offer": 420000,
            "asking_price": 500000,
            "property_value": 480000,
            "negotiation_rounds": 2,
            "buyer_motivation": "need"
        }

        suggestions = await orchestrator.get_negotiation_suggestions(context)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0


class TestPricingRecommendations:
    """Test pricing recommendation engine."""

    @pytest.mark.asyncio
    async def test_recommend_listing_price(self):
        """Test recommending listing price for property."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "square_meters": 200,
            "bedrooms": 4,
            "bathrooms": 3,
            "year_built": 2015,
            "condition": "excellent",
            "neighborhood": "premium",
            "recent_sales_comps": [480000, 490000, 500000, 510000]
        }

        recommendation = await orchestrator.recommend_listing_price(property_data)

        assert isinstance(recommendation, dict)
        assert "suggested_price" in recommendation
        assert "price_range" in recommendation
        assert "confidence" in recommendation

    @pytest.mark.asyncio
    async def test_dynamic_pricing_adjustment(self):
        """Test dynamic pricing adjustment based on market."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "current_price": 500000,
            "days_on_market": 45,
            "market_conditions": "cooling",
            "inventory_level": "high",
            "interest_from_buyers": 2
        }

        adjusted_price = await orchestrator.adjust_price_dynamically(property_data)

        assert isinstance(adjusted_price, (int, float))
        # Price should adjust based on market conditions
        assert adjusted_price > 0

    @pytest.mark.asyncio
    async def test_price_optimization_for_market(self):
        """Test optimizing price based on market dynamics."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "estimated_value": 500000,
            "market_absorption_rate": 0.8,
            "inventory_level": 120,
            "days_to_sell_typical": 45
        }

        optimization = await orchestrator.optimize_for_market(property_data)

        assert "recommended_price" in optimization
        assert "expected_sale_time" in optimization
        assert "marketing_strategy" in optimization


class TestLegalCompliance:
    """Test legal compliance checking."""

    @pytest.mark.asyncio
    async def test_verify_title_status(self):
        """Test verifying property title status."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "property_id": "prop_123",
            "address": "123 Main St"
        }

        title_status = await orchestrator.verify_title(property_data)

        assert "is_clear" in title_status
        assert "liens" in title_status
        assert "encumbrances" in title_status

    @pytest.mark.asyncio
    async def test_check_zoning_compliance(self):
        """Test checking zoning compliance."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "address": "456 Oak Ave",
            "intended_use": "residential",
            "current_use": "residential"
        }

        zoning = await orchestrator.check_zoning(property_data)

        assert "is_compliant" in zoning
        assert "zoning_type" in zoning
        assert "allowed_uses" in zoning

    @pytest.mark.asyncio
    async def test_identify_required_disclosures(self):
        """Test identifying required disclosures."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "property_type": "house",
            "year_built": 1980,
            "has_lead_paint": True,
            "natural_hazard_zone": True
        }

        disclosures = await orchestrator.identify_disclosures(property_data)

        assert isinstance(disclosures, list)
        assert len(disclosures) > 0
        assert "lead_paint" in disclosures or "Lead Paint Disclosure" in str(disclosures)

    @pytest.mark.asyncio
    async def test_legal_document_preparation(self):
        """Test preparing legal documents."""
        orchestrator = RealEstateOrchestrator()

        transaction_data = {
            "seller": "John Doe",
            "buyer": "Jane Smith",
            "property_address": "789 Pine Rd",
            "purchase_price": 450000,
            "closing_date": "2024-08-15"
        }

        documents = await orchestrator.prepare_documents(transaction_data)

        assert isinstance(documents, list)
        assert len(documents) > 0


class TestMarketIntelligence:
    """Test market intelligence gathering."""

    @pytest.mark.asyncio
    async def test_analyze_market_trends(self):
        """Test analyzing market trends."""
        orchestrator = RealEstateOrchestrator()

        market_data = {
            "location": "downtown",
            "property_type": "residential",
            "time_period": "last_12_months"
        }

        trends = await orchestrator.analyze_market_trends(market_data)

        assert "price_trend" in trends
        assert "inventory_trend" in trends
        assert "days_on_market_trend" in trends

    @pytest.mark.asyncio
    async def test_neighborhood_analysis(self):
        """Test neighborhood analysis."""
        orchestrator = RealEstateOrchestrator()

        neighborhood_data = {
            "neighborhood": "Downtown",
            "metrics": ["schools", "amenities", "safety", "appreciation"]
        }

        analysis = await orchestrator.analyze_neighborhood(neighborhood_data)

        assert "school_ratings" in analysis or "schools" in str(analysis)
        assert "walkability" in analysis or "amenities" in str(analysis)
        assert "safety_score" in analysis or "safety" in str(analysis)

    @pytest.mark.asyncio
    async def test_investment_market_conditions(self):
        """Test assessing investment market conditions."""
        orchestrator = RealEstateOrchestrator()

        conditions = await orchestrator.assess_investment_conditions()

        assert "buyer_market_index" in conditions
        assert "seller_market_index" in conditions
        assert "market_outlook" in conditions

    @pytest.mark.asyncio
    async def test_competitive_listing_analysis(self):
        """Test analyzing competitive listings."""
        orchestrator = RealEstateOrchestrator()

        property_data = {
            "address": "123 Main St",
            "square_meters": 200,
            "bedrooms": 3,
            "listing_price": 500000
        }

        competition = await orchestrator.analyze_competition(property_data)

        assert "comparable_listings" in competition
        assert "market_position" in competition
        assert "pricing_strategy" in competition


class TestRealEstateIntegration:
    """Test integration of real estate features."""

    @pytest.mark.asyncio
    async def test_end_to_end_property_transaction(self):
        """Test complete property transaction workflow."""
        orchestrator = RealEstateOrchestrator()

        # Step 1: Analyze property
        property_data = {
            "address": "123 Main St",
            "square_meters": 200,
            "bedrooms": 3,
            "price": 500000
        }
        property_analysis = await orchestrator.analyze_property(property_data)
        assert property_analysis is not None

        # Step 2: Score lead
        lead_data = {
            "budget": 550000,
            "timeline": "2_months",
            "property_type_preference": "house"
        }
        lead_score = await orchestrator.score_lead(lead_data)
        assert 0 <= lead_score <= 100

        # Step 3: Recommend properties
        recommendations = await orchestrator.recommend_properties(
            lead_data,
            [property_data]
        )
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_market_to_transaction_workflow(self):
        """Test workflow from market analysis to transaction."""
        orchestrator = RealEstateOrchestrator()

        # Analyze market
        market_trends = await orchestrator.analyze_market_trends({
            "location": "downtown",
            "property_type": "residential"
        })
        assert market_trends is not None

        # Prepare pricing strategy
        property_data = {
            "estimated_value": 500000,
            "square_meters": 200
        }
        pricing = await orchestrator.recommend_listing_price(property_data)
        assert pricing is not None

        # Prepare for transaction
        transaction = {
            "seller": "Test Seller",
            "buyer": "Test Buyer",
            "property_address": "downtown location"
        }
        docs = await orchestrator.prepare_documents(transaction)
        assert len(docs) > 0


class TestRealEstateEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_analyze_luxury_property(self):
        """Test analyzing luxury property."""
        orchestrator = RealEstateOrchestrator()

        luxury_property = {
            "price": 5000000,
            "square_meters": 500,
            "bedrooms": 5,
            "amenities": ["pool", "gym", "wine_cellar", "theater"],
            "location": "premium"
        }

        analysis = await orchestrator.analyze_property(luxury_property)
        assert analysis is not None

    @pytest.mark.asyncio
    async def test_analyze_distressed_property(self):
        """Test analyzing distressed property."""
        orchestrator = RealEstateOrchestrator()

        distressed_property = {
            "price": 150000,
            "condition": "needs_major_repair",
            "square_meters": 120,
            "age": 80,
            "issues": ["foundation", "roof", "plumbing"]
        }

        analysis = await orchestrator.analyze_property(distressed_property)
        assert analysis is not None

    @pytest.mark.asyncio
    async def test_commercial_property_analysis(self):
        """Test analyzing commercial property."""
        orchestrator = RealEstateOrchestrator()

        commercial = {
            "property_type": "commercial",
            "square_meters": 1000,
            "price": 2000000,
            "cap_rate": 0.07,
            "noi": 140000
        }

        analysis = await orchestrator.analyze_property(commercial)
        assert analysis is not None
