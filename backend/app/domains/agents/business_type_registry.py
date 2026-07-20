"""Business-Type-Aware Agent & Tool Registry.

Determina qué agentes autónomos y qué herramientas del ReAct orchestrator
son relevantes según el tipo específico de negocio (BusinessContext).
"""

from typing import Dict, List, Set, Optional
from app.domains.business_context.models import BusinessType


# ═══════════════════════════════════════════════════════════════════════════
# Agent relevance by business type
# ═══════════════════════════════════════════════════════════════════════════

AGENT_RELEVANCE: Dict[BusinessType, Dict[str, int]] = {
    # Format: {agent_slug: priority_score (0-100)}
    # Agents not listed are considered irrelevant (score 0)

    BusinessType.PHYSICAL_PRODUCTS: {
        "market_analyst": 90,
        "financial_planner": 80,
        "acquisition_strategist": 85,
        "landing_builder": 95,
        "ad_copywriter": 90,
        "investor_pitch": 30,
        "kpi_architect": 70,
        "app_builder": 20,
        "crm_builder": 60,
        "music_agent": 40,
        "brand_visual": 95,
        "viral_video": 85,
        "customer_service": 80,
        "lead_qualifier": 85,
        "auto_responder": 75,
    },
    BusinessType.DIGITAL_PRODUCTS: {
        "market_analyst": 85,
        "financial_planner": 80,
        "acquisition_strategist": 90,
        "landing_builder": 95,
        "ad_copywriter": 85,
        "investor_pitch": 50,
        "kpi_architect": 75,
        "app_builder": 60,
        "crm_builder": 70,
        "music_agent": 30,
        "brand_visual": 80,
        "viral_video": 70,
        "customer_service": 85,
        "lead_qualifier": 90,
        "auto_responder": 80,
    },
    BusinessType.SERVICES: {
        "market_analyst": 80,
        "financial_planner": 85,
        "acquisition_strategist": 90,
        "landing_builder": 70,
        "ad_copywriter": 75,
        "investor_pitch": 40,
        "kpi_architect": 60,
        "app_builder": 30,
        "crm_builder": 80,
        "music_agent": 20,
        "brand_visual": 60,
        "viral_video": 50,
        "customer_service": 90,
        "lead_qualifier": 95,
        "auto_responder": 85,
    },
    BusinessType.CONSULTING: {
        "market_analyst": 95,
        "financial_planner": 90,
        "acquisition_strategist": 85,
        "landing_builder": 60,
        "ad_copywriter": 70,
        "investor_pitch": 60,
        "kpi_architect": 70,
        "app_builder": 40,
        "crm_builder": 90,
        "music_agent": 10,
        "brand_visual": 50,
        "viral_video": 40,
        "customer_service": 85,
        "lead_qualifier": 95,
        "auto_responder": 80,
    },
    BusinessType.SOFTWARE: {
        "market_analyst": 90,
        "financial_planner": 85,
        "acquisition_strategist": 95,
        "landing_builder": 80,
        "ad_copywriter": 75,
        "investor_pitch": 80,
        "kpi_architect": 85,
        "app_builder": 70,
        "crm_builder": 60,
        "music_agent": 10,
        "brand_visual": 70,
        "viral_video": 60,
        "customer_service": 90,
        "lead_qualifier": 95,
        "auto_responder": 85,
    },
    BusinessType.FOOD_BEVERAGE: {
        "market_analyst": 80,
        "financial_planner": 75,
        "acquisition_strategist": 85,
        "landing_builder": 90,
        "ad_copywriter": 90,
        "investor_pitch": 20,
        "kpi_architect": 60,
        "app_builder": 20,
        "crm_builder": 50,
        "music_agent": 30,
        "brand_visual": 85,
        "viral_video": 90,
        "customer_service": 85,
        "lead_qualifier": 80,
        "auto_responder": 75,
    },
    BusinessType.FASHION_BEAUTY: {
        "market_analyst": 85,
        "financial_planner": 70,
        "acquisition_strategist": 90,
        "landing_builder": 95,
        "ad_copywriter": 95,
        "investor_pitch": 30,
        "kpi_architect": 65,
        "app_builder": 20,
        "crm_builder": 55,
        "music_agent": 40,
        "brand_visual": 98,
        "viral_video": 95,
        "customer_service": 80,
        "lead_qualifier": 85,
        "auto_responder": 70,
    },
    BusinessType.HEALTH_WELLNESS: {
        "market_analyst": 80,
        "financial_planner": 75,
        "acquisition_strategist": 85,
        "landing_builder": 85,
        "ad_copywriter": 85,
        "investor_pitch": 30,
        "kpi_architect": 65,
        "app_builder": 30,
        "crm_builder": 70,
        "music_agent": 30,
        "brand_visual": 80,
        "viral_video": 75,
        "customer_service": 90,
        "lead_qualifier": 85,
        "auto_responder": 80,
    },
    BusinessType.HOME_DECOR: {
        "market_analyst": 75,
        "financial_planner": 70,
        "acquisition_strategist": 80,
        "landing_builder": 90,
        "ad_copywriter": 85,
        "investor_pitch": 20,
        "kpi_architect": 60,
        "app_builder": 20,
        "crm_builder": 50,
        "music_agent": 20,
        "brand_visual": 90,
        "viral_video": 75,
        "customer_service": 80,
        "lead_qualifier": 75,
        "auto_responder": 70,
    },
    BusinessType.HANDCRAFT: {
        "market_analyst": 70,
        "financial_planner": 65,
        "acquisition_strategist": 80,
        "landing_builder": 85,
        "ad_copywriter": 80,
        "investor_pitch": 20,
        "kpi_architect": 55,
        "app_builder": 20,
        "crm_builder": 50,
        "music_agent": 25,
        "brand_visual": 85,
        "viral_video": 70,
        "customer_service": 85,
        "lead_qualifier": 75,
        "auto_responder": 70,
    },
    BusinessType.OTHER: {
        "market_analyst": 70,
        "financial_planner": 70,
        "acquisition_strategist": 75,
        "landing_builder": 70,
        "ad_copywriter": 70,
        "investor_pitch": 40,
        "kpi_architect": 60,
        "app_builder": 40,
        "crm_builder": 60,
        "music_agent": 30,
        "brand_visual": 70,
        "viral_video": 60,
        "customer_service": 75,
        "lead_qualifier": 75,
        "auto_responder": 70,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Tool relevance by business type (for ReAct orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

TOOL_RELEVANCE: Dict[BusinessType, Dict[str, int]] = {
    BusinessType.PHYSICAL_PRODUCTS: {
        "SearchProducts": 100,
        "GetCustomerHistory": 90,
        "CheckInventory": 100,
        "RetrieveKnowledge": 80,
        "RetrieveDocuments": 70,
        "SearchMemory": 85,
        "ScheduleMeeting": 60,
    },
    BusinessType.DIGITAL_PRODUCTS: {
        "SearchProducts": 100,
        "GetCustomerHistory": 90,
        "CheckInventory": 30,  # Digital has infinite stock
        "RetrieveKnowledge": 95,
        "RetrieveDocuments": 90,
        "SearchMemory": 85,
        "ScheduleMeeting": 50,
    },
    BusinessType.SERVICES: {
        "SearchProducts": 60,  # Services are not "products"
        "GetCustomerHistory": 95,
        "CheckInventory": 10,
        "RetrieveKnowledge": 90,
        "RetrieveDocuments": 80,
        "SearchMemory": 90,
        "ScheduleMeeting": 100,
    },
    BusinessType.CONSULTING: {
        "SearchProducts": 50,
        "GetCustomerHistory": 95,
        "CheckInventory": 5,
        "RetrieveKnowledge": 100,
        "RetrieveDocuments": 90,
        "SearchMemory": 90,
        "ScheduleMeeting": 100,
    },
    BusinessType.SOFTWARE: {
        "SearchProducts": 80,  # SaaS plans/features
        "GetCustomerHistory": 95,
        "CheckInventory": 20,
        "RetrieveKnowledge": 100,
        "RetrieveDocuments": 95,
        "SearchMemory": 90,
        "ScheduleMeeting": 70,
    },
    BusinessType.FOOD_BEVERAGE: {
        "SearchProducts": 100,
        "GetCustomerHistory": 85,
        "CheckInventory": 90,
        "RetrieveKnowledge": 75,
        "RetrieveDocuments": 60,
        "SearchMemory": 80,
        "ScheduleMeeting": 40,
    },
    BusinessType.FASHION_BEAUTY: {
        "SearchProducts": 100,
        "GetCustomerHistory": 85,
        "CheckInventory": 95,
        "RetrieveKnowledge": 75,
        "RetrieveDocuments": 65,
        "SearchMemory": 80,
        "ScheduleMeeting": 50,
    },
    BusinessType.HEALTH_WELLNESS: {
        "SearchProducts": 90,
        "GetCustomerHistory": 90,
        "CheckInventory": 70,
        "RetrieveKnowledge": 95,
        "RetrieveDocuments": 85,
        "SearchMemory": 85,
        "ScheduleMeeting": 80,
    },
    BusinessType.HOME_DECOR: {
        "SearchProducts": 100,
        "GetCustomerHistory": 80,
        "CheckInventory": 90,
        "RetrieveKnowledge": 70,
        "RetrieveDocuments": 65,
        "SearchMemory": 75,
        "ScheduleMeeting": 40,
    },
    BusinessType.HANDCRAFT: {
        "SearchProducts": 95,
        "GetCustomerHistory": 80,
        "CheckInventory": 85,
        "RetrieveKnowledge": 70,
        "RetrieveDocuments": 60,
        "SearchMemory": 75,
        "ScheduleMeeting": 50,
    },
    BusinessType.OTHER: {
        "SearchProducts": 80,
        "GetCustomerHistory": 85,
        "CheckInventory": 60,
        "RetrieveKnowledge": 80,
        "RetrieveDocuments": 70,
        "SearchMemory": 80,
        "ScheduleMeeting": 60,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Prompt adaptations by business type
# ═══════════════════════════════════════════════════════════════════════════

BUSINESS_TYPE_PROMPT_ADAPTATIONS: Dict[BusinessType, str] = {
    BusinessType.PHYSICAL_PRODUCTS: (
        "You are assisting a business that sells PHYSICAL PRODUCTS. "
        "Focus on: inventory management, shipping options, product photography, "
        "size/specs questions, returns policy, and in-stock availability. "
        "Always mention delivery times and shipping costs when relevant."
    ),
    BusinessType.DIGITAL_PRODUCTS: (
        "You are assisting a business that sells DIGITAL PRODUCTS (ebooks, courses, templates, software). "
        "Focus on: instant delivery, download links, license keys, refund policy for digital goods, "
        "access duration, and device compatibility. No shipping questions."
    ),
    BusinessType.SERVICES: (
        "You are assisting a SERVICE-BASED business. "
        "Focus on: booking appointments, service descriptions, pricing packages, "
        "availability, duration, location (in-person vs remote), and qualifications. "
        "Always guide toward scheduling a consultation or booking."
    ),
    BusinessType.CONSULTING: (
        "You are assisting a CONSULTING or COACHING business. "
        "Focus on: expertise areas, methodology, case studies, session structure, "
        "pricing models (hourly/packages), and ROI. Guide toward discovery calls."
    ),
    BusinessType.SOFTWARE: (
        "You are assisting a SOFTWARE or SaaS business. "
        "Focus on: features, integrations, pricing tiers, free trials, onboarding, "
        "technical support, API docs, and security. Guide toward demos or signups."
    ),
    BusinessType.FOOD_BEVERAGE: (
        "You are assisting a FOOD & BEVERAGE business (restaurant, café, delivery). "
        "Focus on: menu items, ingredients, dietary restrictions, delivery radius, "
        "pickup options, hours, reservations, and hygiene standards."
    ),
    BusinessType.FASHION_BEAUTY: (
        "You are assisting a FASHION or BEAUTY business. "
        "Focus on: sizing guides, colors, materials, skin types, trends, "
        "styling advice, return/exchange policy, and seasonal collections."
    ),
    BusinessType.HEALTH_WELLNESS: (
        "You are assisting a HEALTH & WELLNESS business. "
        "Focus on: programs, schedules, trainer/doctor qualifications, "
        "contraindications, personalized plans, and progress tracking. "
        "Be empathetic and avoid medical claims."
    ),
    BusinessType.HOME_DECOR: (
        "You are assisting a HOME DECOR or FURNITURE business. "
        "Focus on: dimensions, materials, assembly, delivery options for large items, "
        "room compatibility, color matching, and warranty."
    ),
    BusinessType.HANDCRAFT: (
        "You are assisting a HANDCRAFT or ARTISAN business. "
        "Focus on: craftsmanship, materials, customization options, "
        "production time, uniqueness, and the story behind each piece. "
        "Emphasize handmade quality and exclusivity."
    ),
    BusinessType.OTHER: (
        "You are assisting a business. Adapt your approach based on the products/services offered."
    ),
}


class BusinessTypeRegistry:
    """Registry that provides business-type-aware configurations."""

    @staticmethod
    def get_relevant_agents(business_type: BusinessType, min_priority: int = 50) -> List[str]:
        """Return agent slugs relevant for this business type, sorted by priority."""
        scores = AGENT_RELEVANCE.get(business_type, AGENT_RELEVANCE[BusinessType.OTHER])
        filtered = {k: v for k, v in scores.items() if v >= min_priority}
        return sorted(filtered.keys(), key=lambda k: filtered[k], reverse=True)

    @staticmethod
    def get_agent_priority(business_type: BusinessType, agent_slug: str) -> int:
        """Get priority score (0-100) for an agent on a given business type."""
        scores = AGENT_RELEVANCE.get(business_type, AGENT_RELEVANCE[BusinessType.OTHER])
        return scores.get(agent_slug, 0)

    @staticmethod
    def get_relevant_tools(business_type: BusinessType, min_priority: int = 30) -> List[str]:
        """Return tool names relevant for this business type, sorted by priority."""
        scores = TOOL_RELEVANCE.get(business_type, TOOL_RELEVANCE[BusinessType.OTHER])
        filtered = {k: v for k, v in scores.items() if v >= min_priority}
        return sorted(filtered.keys(), key=lambda k: filtered[k], reverse=True)

    @staticmethod
    def get_tool_priority(business_type: BusinessType, tool_name: str) -> int:
        """Get priority score (0-100) for a tool on a given business type."""
        scores = TOOL_RELEVANCE.get(business_type, TOOL_RELEVANCE[BusinessType.OTHER])
        return scores.get(tool_name, 0)

    @staticmethod
    def get_prompt_adaptation(business_type: BusinessType) -> str:
        """Get the prompt adaptation text for a business type."""
        return BUSINESS_TYPE_PROMPT_ADAPTATIONS.get(
            business_type, BUSINESS_TYPE_PROMPT_ADAPTATIONS[BusinessType.OTHER]
        )

    @staticmethod
    def is_agent_relevant(business_type: BusinessType, agent_slug: str, threshold: int = 50) -> bool:
        """Check if an agent is relevant enough for this business type."""
        return BusinessTypeRegistry.get_agent_priority(business_type, agent_slug) >= threshold

    @staticmethod
    def is_tool_relevant(business_type: BusinessType, tool_name: str, threshold: int = 30) -> bool:
        """Check if a tool is relevant enough for this business type."""
        return BusinessTypeRegistry.get_tool_priority(business_type, tool_name) >= threshold
