"""
Phase 8: Advanced Negotiation Engine
Dynamic pricing, contract optimization, strategy selection
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.domains.agents.negotiation_engine import (
    NegotiationEngine,
    CompanySize,
    NegotiationStrategy,
)
from app.domains.crm.crm_adapter import CRMAdapterFactory, CRMType

router = APIRouter(tags=["negotiation"])
negotiation_engine = NegotiationEngine()

logger = logging.getLogger(__name__)


@router.post("/negotiate/dynamic-pricing")
async def calculate_dynamic_pricing(
    intent_score: float = Query(..., ge=0.0, le=1.0, description="Lead intent 0-1"),
    company_size: str = Query("smb", description="startup|smb|mid_market|enterprise"),
    prospect_budget: Optional[float] = Query(None, description="Prospect budget in USD"),
    expansion_potential: float = Query(0.5, ge=0.0, le=1.0),
    competitor_price: Optional[float] = Query(None, description="Competitor price for comparison"),
) -> Dict[str, Any]:
    """
    Calculate optimal pricing based on intent, company size, budget, expansion.

    Returns:
    - Recommended price
    - Discount percentage allowed
    - Legal review requirement
    - Competitor advantage analysis
    """
    try:
        company_size_enum = CompanySize[company_size.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid company_size. Must be one of: {[e.value for e in CompanySize]}",
        )

    pricing = await negotiation_engine.calculate_dynamic_pricing(
        intent_score=intent_score,
        company_size=company_size_enum,
        prospect_budget=prospect_budget,
        expansion_potential=expansion_potential,
        competitor_price=competitor_price,
    )

    return {
        "status": "success",
        "pricing": pricing,
        "timestamp": datetime.utcnow().isoformat(),
        "@context": "https://schema.org",
        "@type": "PriceSpecification",
    }


@router.post("/negotiate/pricing-tiers")
async def generate_pricing_tiers(
    final_price: float = Query(..., description="Final negotiated price"),
    company_size: str = Query("smb", description="startup|smb|mid_market|enterprise"),
) -> Dict[str, Any]:
    """
    Generate 3-tier pricing options (Standard, Professional, Enterprise).
    Each tier includes features, support level, implementation timeline.
    """
    try:
        company_size_enum = CompanySize[company_size.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid company_size")

    tiers = await negotiation_engine.generate_pricing_tiers(
        final_price=final_price,
        company_size=company_size_enum,
    )

    return {
        "status": "success",
        "pricing_tiers": [
            {
                "name": tier.name,
                "annual_price": tier.annual_price,
                "monthly_price": tier.monthly_price,
                "features": tier.features,
                "support_level": tier.support_level,
                "implementation_days": tier.implementation_days,
                "payment_terms": tier.payment_terms,
            }
            for tier in tiers
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/negotiate/contract-terms")
async def optimize_contract_terms(
    industry: str = Query(..., description="Industry (saas, enterprise, finance, etc)"),
    company_size: str = Query("smb"),
    annual_price: float = Query(...),
    preferred_duration_months: Optional[int] = Query(None),
) -> Dict[str, Any]:
    """
    Optimize contract terms for industry and company size.

    Returns:
    - Recommended contract duration
    - Payment schedule
    - Support level
    - SLA uptime commitment
    - Training hours
    - Legal review requirement
    """
    try:
        company_size_enum = CompanySize[company_size.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid company_size")

    prospect_prefs = (
        {"preferred_duration_months": preferred_duration_months}
        if preferred_duration_months
        else None
    )

    terms = await negotiation_engine.optimize_contract_terms(
        prospect_industry=industry,
        company_size=company_size_enum,
        annual_price=annual_price,
        prospect_preferences=prospect_prefs,
    )

    return {
        "status": "success",
        "contract_terms": {
            "annual_price": terms.annual_price,
            "payment_schedule": terms.payment_schedule,
            "contract_duration_months": terms.contract_duration_months,
            "auto_renewal": terms.auto_renewal,
            "support_level": terms.support_level,
            "sla_uptime_percent": terms.sla_uptime_percent,
            "implementation_included": terms.implementation_included,
            "training_hours_included": terms.training_hours_included,
            "legal_review_needed": terms.legal_review_needed,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/negotiate/strategy")
async def select_negotiation_strategy(
    intent_score: float = Query(..., ge=0.0, le=1.0),
    company_size: str = Query("smb"),
    expansion_potential: float = Query(0.5, ge=0.0, le=1.0),
    previous_objections: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """
    Select optimal negotiation strategy based on deal profile.

    Strategies:
    - AGGRESSIVE: Fast close, max discount authority (high intent, no expansion focus)
    - BALANCED: Fair terms, sustainable relationships
    - STRATEGIC: Long-term expansion play (high expansion potential)
    - CONSERVATIVE: Margin preservation (low intent/fit)

    Returns: Selected strategy + playbook with specific tactics.
    """
    try:
        company_size_enum = CompanySize[company_size.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid company_size")

    strategy = await negotiation_engine.select_negotiation_strategy(
        intent_score=intent_score,
        company_size=company_size_enum,
        expansion_potential=expansion_potential,
        previous_objections_count=previous_objections,
    )

    playbook = await negotiation_engine.get_strategy_playbook(strategy)

    return {
        "status": "success",
        "strategy": strategy.value,
        "playbook": playbook,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/negotiate/discount-authority")
async def get_discount_authority(
    company_size: str = Query("smb"),
) -> Dict[str, Any]:
    """
    Get discount authority matrix for a company size.
    Shows max allowed discounts and escalation thresholds.
    """
    try:
        company_size_enum = CompanySize[company_size.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid company_size")

    authority = negotiation_engine.discount_authority_matrix[company_size_enum]

    return {
        "status": "success",
        "company_size": company_size_enum.value,
        "authority": {
            "base_discount_max_percent": authority.base_discount_max * 100,
            "volume_bonus_threshold": authority.volume_bonus_threshold,
            "volume_bonus_max_percent": authority.volume_bonus_max * 100,
            "expansion_potential_multiplier": authority.expansion_potential_multiplier,
            "legal_review_threshold_percent": authority.legal_review_threshold * 100,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================
# CRM Integration Endpoints
# ============================================================


@router.get("/crm/leads")
async def get_crm_leads(
    min_lead_score: Optional[int] = Query(None, ge=0, le=100),
    stage: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    min_company_size: Optional[int] = Query(None),
) -> Dict[str, Any]:
    """
    Fetch leads from CRM with optional filtering.

    Supports: lead_score, stage, industry, company_size
    """
    try:
        crm = await CRMAdapterFactory.get_default_adapter()

        filters = {}
        if min_lead_score is not None:
            filters["min_lead_score"] = min_lead_score
        if stage:
            filters["stage"] = stage
        if industry:
            filters["industry"] = industry
        if min_company_size is not None:
            filters["min_company_size"] = min_company_size

        leads = await crm.fetch_leads(filters=filters if filters else None)

        return {
            "status": "success",
            "lead_count": len(leads),
            "leads": [lead.dict() for lead in leads],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception("CRM lead fetch failed")
        raise HTTPException(status_code=500, detail=f"CRM error: {str(e)}")


@router.get("/crm/lead/{lead_id}")
async def get_crm_lead(lead_id: str) -> Dict[str, Any]:
    """Fetch single lead from CRM."""
    try:
        crm = await CRMAdapterFactory.get_default_adapter()
        lead = await crm.fetch_lead(lead_id)

        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

        return {
            "status": "success",
            "lead": lead.dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"CRM lead fetch failed: {lead_id}")
        raise HTTPException(status_code=500, detail=f"CRM error: {str(e)}")


@router.post("/crm/lead/{lead_id}/route-with-negotiation")
async def route_lead_with_negotiation(
    lead_id: str,
) -> Dict[str, Any]:
    """
    Comprehensive flow: Fetch lead from CRM → Calculate pricing → Select strategy.
    Single endpoint for end-to-end negotiation setup.
    """
    try:
        # Fetch from CRM
        crm = await CRMAdapterFactory.get_default_adapter()
        lead = await crm.fetch_lead(lead_id)

        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

        # Estimate company size if not in CRM
        if lead.company_size:
            company_size = await negotiation_engine.estimate_company_size(
                employee_count=lead.company_size
            )
        else:
            company_size = CompanySize.SMB

        # Calculate intent from engagement signals
        intent_score = min(
            1.0,
            0.3 * (lead.lead_score or 0) / 100  # 30% from lead score
            + 0.3 * (1.0 if lead.demo_attended else 0)  # 30% for demo
            + 0.2 * (1.0 if lead.call_scheduled else 0)  # 20% for call
            + 0.2 * min(1.0, (lead.email_opens or 0) / 10),  # 20% for engagement
        )

        # Estimate expansion potential from company size and revenue
        if lead.annual_revenue and lead.annual_revenue > 100_000_000:
            expansion_potential = 0.8
        elif lead.annual_revenue and lead.annual_revenue > 10_000_000:
            expansion_potential = 0.6
        else:
            expansion_potential = 0.3

        # 1. Calculate pricing
        pricing = await negotiation_engine.calculate_dynamic_pricing(
            intent_score=intent_score,
            company_size=company_size,
            prospect_budget=float(lead.budget.split("-")[1].replace("k", "000"))
            if lead.budget
            else None,
            expansion_potential=expansion_potential,
        )

        # 2. Generate pricing tiers
        tiers = await negotiation_engine.generate_pricing_tiers(
            final_price=pricing["final_price"],
            company_size=company_size,
        )

        # 3. Optimize contract terms
        terms = await negotiation_engine.optimize_contract_terms(
            prospect_industry=lead.industry or "saas",
            company_size=company_size,
            annual_price=pricing["final_price"],
        )

        # 4. Select strategy
        strategy = await negotiation_engine.select_negotiation_strategy(
            intent_score=intent_score,
            company_size=company_size,
            expansion_potential=expansion_potential,
        )

        playbook = await negotiation_engine.get_strategy_playbook(strategy)

        # Update CRM with negotiation plan
        await crm.update_lead(
            lead_id,
            {
                "stage": "negotiation",
                "estimated_value": pricing["final_price"],
            },
        )

        return {
            "status": "success",
            "lead_id": lead_id,
            "lead_summary": {
                "company": lead.company_name,
                "contact": lead.contact_name,
                "industry": lead.industry,
                "company_size": company_size.value,
                "intent_score": round(intent_score, 2),
                "expansion_potential": round(expansion_potential, 2),
            },
            "negotiation_plan": {
                "strategy": strategy.value,
                "base_price": pricing["base_price"],
                "recommended_price": pricing["final_price"],
                "discount_percent": round(pricing["discount_percent"], 1),
                "needs_legal_review": pricing["needs_legal_review"],
                "pricing_tiers": [
                    {
                        "name": tier.name,
                        "annual_price": tier.annual_price,
                        "features": tier.features,
                    }
                    for tier in tiers
                ],
                "contract_terms": {
                    "duration_months": terms.contract_duration_months,
                    "payment_schedule": terms.payment_schedule,
                    "support_level": terms.support_level,
                },
                "playbook": playbook,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Route with negotiation failed: {lead_id}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
