"""Test market detection."""

import pytest
from app.core.market import MarketDetector, Industry, BusinessModel, BuyerMotivation


def test_detect_real_estate_market():
    """Test real estate market detection."""
    input_text = "Vendo apartamento de 2 dormitorios en Buenos Aires, necesito comprador rápido"
    profile = MarketDetector.detect_market(input_text)
    
    assert profile.industry == Industry.REAL_ESTATE
    assert profile.confidence_score > 0.5


def test_detect_commerce_market():
    """Test commerce market detection."""
    input_text = "Tengo tienda de ropa en Shopify, vendo productos de moda online"
    profile = MarketDetector.detect_market(input_text)
    
    assert profile.industry == Industry.COMMERCE
    assert profile.business_model == BusinessModel.DIGITAL


def test_detect_services_market():
    """Test services market detection."""
    input_text = "Soy consultor de marketing digital, ofrezco coaching a empresas"
    profile = MarketDetector.detect_market(input_text)
    
    assert profile.industry == Industry.SERVICES


def test_detect_market_type_b2b():
    """Test B2B market type detection."""
    input_text = "Vendemos software de contabilidad a empresas grandes"
    profile = MarketDetector.detect_market(input_text)
    
    assert profile.market_type == "B2B"


def test_detect_buyer_motivation():
    """Test buyer motivation detection."""
    input_text = "Necesito resolver urgentemente mi problema de inventario"
    profile = MarketDetector.detect_market(input_text)
    
    assert profile.buyer_motivation == BuyerMotivation.NEED


def test_agent_recommendations():
    """Test agent pool recommendations."""
    input_text = "Vendo propiedades inmobiliarias en Buenos Aires"
    profile = MarketDetector.detect_market(input_text)
    
    assert "realEstate_leadScorer" in profile.recommended_agents
    assert "sellIA_base" in profile.recommended_agents


def test_rules_file_mapping():
    """Test rules file mapping."""
    input_text = "Vendo bienes raíces"
    profile = MarketDetector.detect_market(input_text)
    
    assert "real_estate.yaml" in profile.recommended_rules_file
