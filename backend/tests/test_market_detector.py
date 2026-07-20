"""Unit tests for market_detector.py — Auto-detect business type, industry, business model.

Tests cover:
- Industry detection from keywords
- Business model classification
- Buyer motivation analysis
- Confidence scoring
- Recommended agents selection
- Edge cases and malformed inputs
"""

import pytest
from typing import Dict, Any
from app.core.market.market_detector import (
    MarketDetector,
    MarketProfile,
    Industry,
    BusinessModel,
    BuyerMotivation,
)


class TestMarketDetection:
    """Test market detection capabilities."""

    def test_detect_real_estate_market(self):
        """Test detection of real estate market."""
        result = MarketDetector.detect_market(
            "Vendo propiedades inmobiliarias de lujo en Miami",
            company_data={"business_name": "Premium Real Estate"}
        )

        assert result.industry == Industry.REAL_ESTATE
        assert result.confidence_score > 0.5
        assert isinstance(result.keywords, list)
        assert isinstance(result.recommended_agents, list)

    def test_detect_ecommerce_market(self):
        """Test detection of e-commerce market."""
        result = MarketDetector.detect_market(
            "Tienda online de productos electrónicos con envío rápido",
            company_data={"business_name": "TechStore"}
        )

        assert result.industry == Industry.COMMERCE
        assert result.confidence_score > 0.3
        assert result.business_model in [
            BusinessModel.PHYSICAL,
            BusinessModel.MARKETPLACE
        ]

    def test_detect_services_market(self):
        """Test detection of services market."""
        result = MarketDetector.detect_market(
            "Ofrecemos servicios de consultoría empresarial y asesoría"
        )

        assert result.industry == Industry.SERVICES
        assert result.business_model == BusinessModel.SERVICE

    def test_detect_digital_products_market(self):
        """Test detection of digital products market."""
        result = MarketDetector.detect_market(
            "Vendemos cursos online y membresías de software"
        )

        assert result.industry == Industry.DIGITAL_PRODUCTS
        assert result.business_model == BusinessModel.DIGITAL

    def test_detect_finance_market(self):
        """Test detection of finance/investment market."""
        result = MarketDetector.detect_market(
            "Plataforma de inversión en criptomonedas y trading"
        )

        assert result.industry == Industry.FINANCE

    def test_detect_labor_market(self):
        """Test detection of labor/recruitment market."""
        result = MarketDetector.detect_market(
            "Reclutamiento de empleados y servicios freelance"
        )

        assert result.industry == Industry.LABOR

    def test_business_model_physical_products(self):
        """Test detection of physical business model."""
        result = MarketDetector.detect_market(
            "Producto físico con envío rápido e inventario"
        )

        assert result.business_model == BusinessModel.PHYSICAL

    def test_business_model_subscription(self):
        """Test detection of subscription business model."""
        result = MarketDetector.detect_market(
            "Suscripción mensual con renovación anual automática"
        )

        assert result.business_model == BusinessModel.SUBSCRIPTION

    def test_business_model_marketplace(self):
        """Test detection of marketplace business model."""
        result = MarketDetector.detect_market(
            "Plataforma marketplace con comisión por transacción"
        )

        assert result.business_model == BusinessModel.MARKETPLACE

    def test_buyer_motivation_need(self):
        """Test detection of 'need' buyer motivation."""
        result = MarketDetector.detect_market(
            "Solución esencial y urgente para problemas empresariales"
        )

        assert result.buyer_motivation == BuyerMotivation.NEED

    def test_buyer_motivation_desire(self):
        """Test detection of 'desire' buyer motivation."""
        result = MarketDetector.detect_market(
            "Me gustaría obtener un interesante producto"
        )

        assert result.buyer_motivation == BuyerMotivation.DESIRE

    def test_buyer_motivation_luxury(self):
        """Test detection of 'luxury' buyer motivation."""
        result = MarketDetector.detect_market(
            "Productos premium exclusivos de lujo"
        )

        assert result.buyer_motivation == BuyerMotivation.LUXURY

    def test_buyer_motivation_investment(self):
        """Test detection of 'investment' buyer motivation."""
        result = MarketDetector.detect_market(
            "Oportunidad de inversión con retorno de ganancias"
        )

        assert result.buyer_motivation == BuyerMotivation.INVESTMENT

    def test_with_company_data_enrichment(self):
        """Test market detection enriched with company data."""
        company_data = {
            "business_name": "Inmobiliaria Global",
            "description": "Venta y alquiler de propiedades"
        }
        result = MarketDetector.detect_market(
            "Mercado inmobiliario",
            company_data=company_data
        )

        assert result.industry == Industry.REAL_ESTATE
        assert result.confidence_score >= 0.5

    def test_default_to_other_industry(self):
        """Test default industry assignment when no keywords match."""
        result = MarketDetector.detect_market("xyz abc def ghijk")

        assert result.industry == Industry.OTHER
        assert result.confidence_score < 0.5

    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        result_lower = MarketDetector.detect_market("propiedad casa apartamento")
        result_upper = MarketDetector.detect_market("PROPIEDAD CASA APARTAMENTO")
        result_mixed = MarketDetector.detect_market("Propiedad Casa Apartamento")

        assert result_lower.industry == Industry.REAL_ESTATE
        assert result_upper.industry == Industry.REAL_ESTATE
        assert result_mixed.industry == Industry.REAL_ESTATE

    def test_market_profile_structure(self):
        """Test that MarketProfile contains all expected fields."""
        result = MarketDetector.detect_market("Vendo propiedades inmobiliarias")

        assert hasattr(result, 'industry')
        assert hasattr(result, 'business_model')
        assert hasattr(result, 'buyer_motivation')
        assert hasattr(result, 'market_type')
        assert hasattr(result, 'keywords')
        assert hasattr(result, 'confidence_score')
        assert hasattr(result, 'recommended_agents')
        assert hasattr(result, 'recommended_rules_file')

    def test_keywords_populated(self):
        """Test that keywords list is populated."""
        result = MarketDetector.detect_market("Vendo productos en tienda online")

        assert len(result.keywords) > 0
        assert all(isinstance(kw, str) for kw in result.keywords)

    def test_recommended_agents_populated(self):
        """Test that recommended agents list is populated."""
        result = MarketDetector.detect_market("Vendo propiedades inmobiliarias")

        assert len(result.recommended_agents) > 0
        assert all(isinstance(agent, str) for agent in result.recommended_agents)

    def test_confidence_score_range(self):
        """Test that confidence score is between 0 and 1."""
        result = MarketDetector.detect_market("Vendo productos")

        assert 0 <= result.confidence_score <= 1

    def test_hybrid_business_model(self):
        """Test detection of hybrid business model."""
        result = MarketDetector.detect_market(
            "Servicio digital con producto físico"
        )

        assert result.business_model == BusinessModel.HYBRID

    def test_empty_input(self):
        """Test handling of empty input."""
        result = MarketDetector.detect_market("")

        assert isinstance(result, MarketProfile)
        assert result.industry == Industry.OTHER

    def test_none_company_data(self):
        """Test handling of None company data."""
        result = MarketDetector.detect_market("Vendo propiedades", company_data=None)

        assert result.industry == Industry.REAL_ESTATE

    def test_empty_company_data(self):
        """Test handling of empty company data dict."""
        result = MarketDetector.detect_market("Vendo propiedades", company_data={})

        assert result.industry == Industry.REAL_ESTATE

    def test_multiple_keywords_matching(self):
        """Test when multiple keywords from different industries match."""
        result = MarketDetector.detect_market(
            "Software para gestionar propiedades y créditos financieros"
        )

        # Should pick the industry with highest match count
        assert isinstance(result.industry, Industry)
        assert result.confidence_score >= 0

    def test_special_characters_handling(self):
        """Test handling of special characters in input."""
        result = MarketDetector.detect_market(
            "¡Vendo propiedades! @casa #inmueble &apartamento"
        )

        assert result.industry == Industry.REAL_ESTATE

    def test_manufacturing_detection(self):
        """Test detection of manufacturing industry."""
        result = MarketDetector.detect_market(
            "Fábrica de producción industrial y manufactura"
        )

        assert result.industry == Industry.MANUFACTURING

    def test_recommended_rules_file_populated(self):
        """Test that recommended rules file is set."""
        result = MarketDetector.detect_market("Vendo propiedades inmobiliarias")

        assert isinstance(result.recommended_rules_file, str)
        assert len(result.recommended_rules_file) > 0

    def test_market_type_field_populated(self):
        """Test that market_type field is populated."""
        result = MarketDetector.detect_market("Vendo productos en tienda")

        assert isinstance(result.market_type, str)
        assert len(result.market_type) > 0


class TestMarketDetectionEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_input(self):
        """Test handling of very long input strings."""
        long_input = "propiedad " * 1000
        result = MarketDetector.detect_market(long_input)

        assert result.industry == Industry.REAL_ESTATE

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        result = MarketDetector.detect_market(
            "Vendo propiedades inmobiliarias ñ é ü"
        )

        assert isinstance(result, MarketProfile)

    def test_repeated_keywords(self):
        """Test handling of repeated keywords."""
        result = MarketDetector.detect_market(
            "propiedad propiedad propiedad inmueble inmueble"
        )

        assert result.industry == Industry.REAL_ESTATE
        assert result.confidence_score > 0.5

    def test_mixed_industries(self):
        """Test market with keywords from multiple industries."""
        result = MarketDetector.detect_market(
            "Vendo propiedades inmobiliarias y servicios de consultoría"
        )

        # Should pick the primary industry
        assert result.industry in [Industry.REAL_ESTATE, Industry.SERVICES]

    def test_numbers_in_input(self):
        """Test handling of numbers in input."""
        result = MarketDetector.detect_market(
            "Vendo 100 propiedades inmobiliarias por 500000"
        )

        assert result.industry == Industry.REAL_ESTATE

    def test_url_in_input(self):
        """Test handling of URLs in input."""
        result = MarketDetector.detect_market(
            "Vendo propiedades en https://example.com"
        )

        assert result.industry == Industry.REAL_ESTATE

    def test_whitespace_variations(self):
        """Test handling of various whitespace."""
        result = MarketDetector.detect_market(
            "propiedad  \n  inmueble \t casa"
        )

        assert result.industry == Industry.REAL_ESTATE
