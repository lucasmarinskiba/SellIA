"""Enrich leads with additional data based on business model."""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .lead_generator import Lead, LeadQuality
from app.domains.business_intelligence.business_model_detector import BusinessProfile

logger = logging.getLogger(__name__)


class LeadEnricher:
    """Enrich leads with context-specific data"""

    def enrich_lead(self, lead: Lead, business: BusinessProfile) -> Lead:
        """Add business-relevant data to lead"""

        if business.model.value == "physical_store":
            return self._enrich_local_lead(lead, business)
        elif business.model.value == "online_only":
            return self._enrich_ecommerce_lead(lead, business)
        elif business.model.value == "service_at_home":
            return self._enrich_service_lead(lead, business)
        elif business.model.value == "b2b_consulting":
            return self._enrich_b2b_lead(lead, business)
        else:
            return self._enrich_generic_lead(lead, business)

    def _enrich_local_lead(self, lead: Lead, business: BusinessProfile) -> Lead:
        """Enrich for local store"""
        lead.raw_data.update({
            "relevance_score": 0.8,
            "preferred_contact": "whatsapp",
            "opening_hours": "9AM-8PM",
            "typical_budget": business.average_ticket_size or 200,
            "purchase_cycle": "1-7 days",
            "pain_points": ["convenience", "location", "hours"],
            "offers_that_work": ["loyalty program", "opening hours extended", "delivery"],
            "enriched_at": datetime.utcnow().isoformat()
        })
        lead.enriched = True
        return lead

    def _enrich_ecommerce_lead(self, lead: Lead, business: BusinessProfile) -> Lead:
        """Enrich for e-commerce"""
        lead.raw_data.update({
            "relevance_score": 0.75,
            "preferred_contact": "email",
            "search_intent": "high",
            "cart_abandonment_likely": True,
            "personalization_needed": True,
            "typical_budget": lead.estimated_budget or 100,
            "purchase_cycle": "1-30 days",
            "pain_points": ["shipping cost", "delivery time", "returns"],
            "offers_that_work": ["free shipping", "discount", "guarantee"],
            "enriched_at": datetime.utcnow().isoformat()
        })
        lead.enriched = True
        return lead

    def _enrich_service_lead(self, lead: Lead, business: BusinessProfile) -> Lead:
        """Enrich for service at home"""
        lead.raw_data.update({
            "relevance_score": 0.9,
            "preferred_contact": "whatsapp",
            "urgency": "high",
            "immediate_need": True,
            "typical_budget": business.average_ticket_size or 500,
            "purchase_cycle": "1-3 days",
            "decision_speed": "fast",
            "pain_points": ["time availability", "trust", "price"],
            "offers_that_work": ["same day service", "24/7 availability", "guarantees"],
            "enriched_at": datetime.utcnow().isoformat()
        })
        lead.quality = LeadQuality.HOT
        lead.enriched = True
        return lead

    def _enrich_b2b_lead(self, lead: Lead, business: BusinessProfile) -> Lead:
        """Enrich for B2B"""
        lead.raw_data.update({
            "relevance_score": 0.85,
            "preferred_contact": "email",
            "decision_makers": 3,
            "approval_required": True,
            "budget_cycle": "quarterly_or_annual",
            "purchase_cycle": "30-90 days",
            "typical_budget": lead.estimated_budget or 10000,
            "pain_points": ["roi", "implementation", "support"],
            "offers_that_work": ["demo", "trial", "references"],
            "requires_proposal": True,
            "enriched_at": datetime.utcnow().isoformat()
        })
        lead.enriched = True
        return lead

    def _enrich_generic_lead(self, lead: Lead, business: BusinessProfile) -> Lead:
        """Generic enrichment"""
        lead.raw_data.update({
            "relevance_score": 0.5,
            "preferred_contact": lead.contact_method,
            "typical_budget": business.average_ticket_size or 500,
            "enriched_at": datetime.utcnow().isoformat()
        })
        lead.enriched = True
        return lead

    def enrich_batch(self, leads: list[Lead], business: BusinessProfile) -> list[Lead]:
        """Enrich multiple leads"""
        return [self.enrich_lead(lead, business) for lead in leads]
