"""Phase 18: Autonomous Lead Generation Agent Endpoints."""

from fastapi import APIRouter, Query, Body, HTTPException
from typing import Dict, Any
import logging

from app.domains.agents.lead_generation_agent import (
    LeadGenerationAgent, ProductDescriptor, LeadSourceType
)

router = APIRouter(tags=["lead-generation-agent"])
logger = logging.getLogger(__name__)

# Global agent instance
agent = LeadGenerationAgent()


@router.post("/lead-agent/create-campaign")
async def create_lead_campaign(
    user_id: str = Query(...),
    product_name: str = Query(...),
    product_category: str = Query(...),
    description: str = Query(...),
    target_audience: str = Query(...),
    price_range: str = Query(...),
    unique_selling_point: str = Query(...),
    delivery_model: str = Query(..., description="online, offline, hybrid, hybrid_on_demand"),
    geographic_scope: str = Query(...),
    leads_target: int = Query(50, ge=10, le=500),
) -> Dict[str, Any]:
    """Create autonomous lead generation campaign for user's product/service."""

    try:
        product = ProductDescriptor(
            name=product_name,
            category=product_category,
            description=description,
            target_audience=target_audience,
            price_range=price_range,
            unique_selling_point=unique_selling_point,
            delivery_model=delivery_model,
            geographic_scope=geographic_scope
        )

        campaign = agent.create_campaign(user_id, product, leads_target)

        return {
            "status": "success",
            "campaign_id": campaign.campaign_id,
            "user_id": user_id,
            "product": {
                "name": product.name,
                "category": product.category,
                "delivery_model": product.delivery_model
            },
            "sources": [s.value for s in campaign.sources],
            "leads_target": leads_target,
            "message": f"Campaign created. Will generate leads from {len(campaign.sources)} sources."
        }

    except Exception as e:
        logger.error(f"Campaign creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lead-agent/generate-leads/{campaign_id}")
async def generate_leads(
    campaign_id: str,
    limit: int = Query(50, ge=10, le=200),
) -> Dict[str, Any]:
    """Generate leads for campaign."""

    try:
        leads = agent.generate_leads_for_campaign(campaign_id, limit)

        qualified = len([l for l in leads if l.fit_score > 0.7])

        return {
            "status": "success" if leads else "no_leads",
            "campaign_id": campaign_id,
            "total_generated": len(leads),
            "qualified_leads": qualified,
            "qualification_rate": f"{(qualified / len(leads) * 100):.1f}%" if leads else "0%",
            "leads_sample": [
                {
                    "lead_id": l.lead_id,
                    "name": l.prospect_name,
                    "email": l.prospect_email,
                    "company": l.prospect_company,
                    "location": l.prospect_location,
                    "fit_score": f"{l.fit_score:.2f}",
                    "source": l.source.value,
                    "contact_method": l.contact_method
                }
                for l in leads[:10]
            ]
        }

    except Exception as e:
        logger.error(f"Lead generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lead-agent/campaign/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: str) -> Dict[str, Any]:
    """Get campaign statistics."""

    try:
        stats = agent.get_campaign_stats(campaign_id)

        if not stats:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return {
            "status": "success",
            "campaign": stats
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lead-agent/campaign/{campaign_id}/leads")
async def get_qualified_leads(
    campaign_id: str,
    min_fit_score: float = Query(0.7, ge=0.0, le=1.0),
) -> Dict[str, Any]:
    """Get qualified leads from campaign."""

    try:
        leads = agent.get_campaign_leads(campaign_id, min_fit_score)

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "min_fit_score": min_fit_score,
            "total_leads": len(leads),
            "leads": [
                {
                    "lead_id": l.lead_id,
                    "name": l.prospect_name,
                    "email": l.prospect_email,
                    "phone": l.prospect_phone,
                    "company": l.prospect_company,
                    "location": l.prospect_location,
                    "fit_score": f"{l.fit_score:.2f}",
                    "reason_fit": l.reason_fit,
                    "source": l.source.value,
                    "contact_method": l.contact_method,
                    "keywords_matched": l.keywords_matched
                }
                for l in leads
            ]
        }

    except Exception as e:
        logger.error(f"Leads retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lead-agent/schedule-continuous/{campaign_id}")
async def schedule_continuous_generation(
    campaign_id: str,
    frequency_hours: int = Query(24, ge=1, le=720),
) -> Dict[str, Any]:
    """Schedule continuous automatic lead generation."""

    try:
        result = agent.schedule_continuous_generation(campaign_id, frequency_hours)

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "frequency_hours": frequency_hours,
            "message": f"Lead generation scheduled every {frequency_hours} hours",
            "next_run": result.get("next_run")
        }

    except Exception as e:
        logger.error(f"Scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lead-agent/export/{campaign_id}")
async def export_leads(
    campaign_id: str,
    format: str = Query("json", regex="^(csv|json)$"),
) -> Dict[str, Any]:
    """Export leads in specified format for outreach."""

    try:
        result = agent.export_leads_for_outreach(campaign_id, format)

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "format": format,
            "data": result.get("data") or result.get("leads")
        }

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lead-agent/quick-start")
async def quick_start_campaign(
    user_id: str = Query(...),
    product_description: str = Body(..., description="What do you sell/offer?"),
    target_market: str = Body(..., description="Who are your customers?"),
) -> Dict[str, Any]:
    """Quick-start: Create campaign from minimal info."""

    try:
        # Parse user input and create product descriptor
        product = ProductDescriptor(
            name=product_description.split()[0] if product_description else "Product",
            category="General",
            description=product_description,
            target_audience=target_market,
            price_range="Varies",
            unique_selling_point="Quality and reliability",
            delivery_model="hybrid",
            geographic_scope="Local"
        )

        campaign = agent.create_campaign(user_id, product, leads_target=100)
        leads = agent.generate_leads_for_campaign(campaign.campaign_id, 50)

        return {
            "status": "success",
            "campaign_id": campaign.campaign_id,
            "message": f"Campaign started! Generated {len(leads)} leads.",
            "next_steps": [
                "Review qualified leads above",
                "Contact leads using suggested method",
                "Track responses in dashboard",
                "Leads will refresh every 24 hours"
            ],
            "leads_preview": [
                {
                    "name": l.prospect_name,
                    "email": l.prospect_email,
                    "fit_score": f"{l.fit_score:.2f}",
                    "contact_method": l.contact_method
                }
                for l in leads[:5]
            ]
        }

    except Exception as e:
        logger.error(f"Quick start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
