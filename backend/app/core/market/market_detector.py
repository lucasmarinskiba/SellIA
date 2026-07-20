"""Market Detector — Auto-detect business type, industry, business model."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class Industry(str, Enum):
    REAL_ESTATE = "real_estate"
    COMMERCE = "commerce"
    SERVICES = "services"
    FINANCE = "finance"
    LABOR = "labor"
    MANUFACTURING = "manufacturing"
    DIGITAL_PRODUCTS = "digital_products"
    OTHER = "other"


class BusinessModel(str, Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    HYBRID = "hybrid"
    SUBSCRIPTION = "subscription"
    MARKETPLACE = "marketplace"


class BuyerMotivation(str, Enum):
    NEED = "need"
    DESIRE = "desire"
    LUXURY = "luxury"
    INVESTMENT = "investment"


@dataclass
class MarketProfile:
    """Market profile for vendor."""
    industry: Industry
    business_model: BusinessModel
    buyer_motivation: BuyerMotivation
    market_type: str
    keywords: list[str]
    confidence_score: float
    recommended_agents: list[str]
    recommended_rules_file: str


class MarketDetector:
    """Auto-detect market type from vendor inputs."""

    INDUSTRY_KEYWORDS = {
        Industry.REAL_ESTATE: ["propiedad", "inmueble", "casa", "apartamento", "terreno", "alquiler", "venta inmobiliaria", "agente"],
        Industry.COMMERCE: ["producto", "venta", "tienda", "ecommerce", "mercado"],
        Industry.SERVICES: ["servicio", "consultoría", "asesoría", "coaching"],
        Industry.FINANCE: ["inversión", "crédito", "finanzas", "trading", "criptomoneda"],
        Industry.LABOR: ["empleado", "contratación", "reclutamiento", "freelance"],
        Industry.MANUFACTURING: ["manufactura", "producción", "fábrica", "industrial"],
        Industry.DIGITAL_PRODUCTS: ["software", "app", "SaaS", "curso", "membresía"],
    }

    BUSINESS_MODEL_KEYWORDS = {
        BusinessModel.PHYSICAL: ["producto físico", "envío", "inventario"],
        BusinessModel.DIGITAL: ["descargable", "acceso instantáneo", "software"],
        BusinessModel.SERVICE: ["servicio", "consultoría", "por hora"],
        BusinessModel.SUBSCRIPTION: ["mensual", "suscripción", "anual"],
        BusinessModel.MARKETPLACE: ["marketplace", "plataforma", "comisión"],
    }

    MOTIVATION_KEYWORDS = {
        BuyerMotivation.NEED: ["esencial", "necesario", "urgente", "problema"],
        BuyerMotivation.DESIRE: ["quiero", "me gustaría", "interesante"],
        BuyerMotivation.LUXURY: ["premium", "exclusivo", "lujo"],
        BuyerMotivation.INVESTMENT: ["inversión", "retorno", "ganancia"],
    }

    @staticmethod
    def detect_market(user_input: str, company_data: Optional[Dict[str, Any]] = None) -> MarketProfile:
        input_text = user_input.lower()
        if company_data:
            input_text += f" {company_data.get('business_name', '')} {company_data.get('description', '')}".lower()

        industry_scores = {}
        for ind, keywords in MarketDetector.INDUSTRY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in input_text)
            if score > 0:
                industry_scores[ind] = score

        industry = max(industry_scores, key=industry_scores.get, default=Industry.OTHER)
        industry_confidence = min(industry_scores.get(industry, 0) / 10.0, 1.0)

        model_scores = {}
        for model, keywords in MarketDetector.BUSINESS_MODEL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in input_text)
            if score > 0:
                model_scores[model] = score

        business_model = max(model_scores, key=model_scores.get, default=BusinessModel.HYBRID)
        model_confidence = min(model_scores.get(business_model, 0) / 10.0, 1.0)

        motivation_scores = {}
        for motiv, keywords in MarketDetector.MOTIVATION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in input_text)
            if score > 0:
                motivation_scores[motiv] = score

        motivation = max(motivation_scores, key=motivation_scores.get, default=BuyerMotivation.NEED)

        market_type = MarketDetector._determine_market_type(industry, input_text)
        recommended_agents = MarketDetector._recommend_agents(industry, business_model)
        rules_file = MarketDetector._get_rules_file(industry)
        keywords = [kw for kw in re.findall(r'\b\w{3,}\b', input_text) if len(kw) > 3][:10]
        confidence = (industry_confidence + model_confidence) / 2

        return MarketProfile(
            industry=industry,
            business_model=business_model,
            buyer_motivation=motivation,
            market_type=market_type,
            keywords=keywords,
            confidence_score=confidence,
            recommended_agents=recommended_agents,
            recommended_rules_file=rules_file,
        )

    @staticmethod
    def _determine_market_type(industry: Industry, text: str) -> str:
        if "empresa" in text or "corporativo" in text or "b2b" in text:
            return "B2B"
        elif "directo" in text or "d2c" in text or "consumidor" in text:
            return "D2C"
        return "B2C"

    @staticmethod
    def _recommend_agents(industry: Industry, model: BusinessModel) -> list[str]:
        agents = ["sellIA_base"]
        if industry == Industry.REAL_ESTATE:
            agents.extend(["realEstate_leadScorer", "realEstate_propertyAnalyzer", "realEstate_negotiator"])
        elif industry == Industry.COMMERCE:
            agents.extend(["commerce_prospector", "commerce_advisor", "commerce_negotiator"])
        elif industry == Industry.SERVICES:
            agents.extend(["services_qualifier", "services_deliveryCoordinator"])
        elif industry == Industry.FINANCE:
            agents.extend(["finance_advisor", "finance_riskAssessor"])
        elif industry == Industry.DIGITAL_PRODUCTS:
            agents.extend(["digital_converter", "digital_retention"])
        return agents

    @staticmethod
    def _get_rules_file(industry: Industry) -> str:
        rules_map = {
            Industry.REAL_ESTATE: "backend/app/core/market/rules/real_estate.yaml",
            Industry.COMMERCE: "backend/app/core/market/rules/commerce.yaml",
            Industry.SERVICES: "backend/app/core/market/rules/services.yaml",
            Industry.FINANCE: "backend/app/core/market/rules/finance.yaml",
            Industry.LABOR: "backend/app/core/market/rules/labor.yaml",
            Industry.MANUFACTURING: "backend/app/core/market/rules/manufacturing.yaml",
            Industry.DIGITAL_PRODUCTS: "backend/app/core/market/rules/digital.yaml",
        }
        return rules_map.get(industry, "backend/app/core/market/rules/default.yaml")
