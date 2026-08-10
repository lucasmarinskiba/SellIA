"""Phases 10-13: Business intelligence, diagnostics, lead generation, marketing."""

from fastapi import APIRouter, Query, Body, HTTPException
from typing import Dict, Any, List
import logging

from app.domains.business_intelligence.business_model_detector import (
    BusinessModelDetector, BusinessProfile
)
from app.domains.business_intelligence.service_diagnostician import (
    ServiceDiagnostician, CompetitiveAnalyzer
)
from app.domains.lead_generation.lead_generator import LeadGenerator
from app.domains.lead_generation.lead_enricher import LeadEnricher
from app.domains.marketing.channel_strategy import ChannelStrategyGenerator
from app.domains.marketing.copy_generator import CopyGenerator

router = APIRouter(tags=["business-intelligence"])
logger = logging.getLogger(__name__)

# Initialize services
detector = BusinessModelDetector()
diagnostician = ServiceDiagnostician()
competitive_analyzer = CompetitiveAnalyzer()
lead_generator = LeadGenerator()
lead_enricher = LeadEnricher()
strategy_gen = ChannelStrategyGenerator()
copy_gen = CopyGenerator()


# ============================================================
# Phase 10: Business Model Discovery
# ============================================================


@router.post("/business-intelligence/analyze-business")
async def analyze_business(
    business_description: str = Query(...),
    website: str = Query(""),
    location: str = Query(""),
    instagram: str = Query(""),
    facebook: str = Query(""),
) -> Dict[str, Any]:
    """Detect business model and adapt strategy."""

    try:
        socials = {}
        if instagram:
            socials["instagram"] = instagram
        if facebook:
            socials["facebook"] = facebook

        profile = detector.detect_model(business_description, website, socials)
        profile.primary_location = location or profile.primary_location

        lead_sources = detector.get_relevant_channels(profile)

        return {
            "status": "success",
            "business_model": profile.model.value,
            "profile": {
                "name": profile.name,
                "description": profile.description,
                "model": profile.model.value,
                "primary_location": profile.primary_location,
                "is_b2b": profile.is_b2b,
                "is_b2c": profile.is_b2c,
                "has_physical_location": profile.has_physical_location,
                "has_online_presence": profile.has_online_presence,
                "channels": [ch.value for ch in profile.channels],
                "primary_channel": profile.primary_channel.value if profile.primary_channel else None,
            },
            "lead_sources": [
                {
                    "name": source.name,
                    "channel": source.channel.value,
                    "estimated_leads_per_month": source.estimated_leads_per_month,
                    "effort_level": source.effort_level,
                    "setup_time_days": source.setup_time_days,
                }
                for source in lead_sources
            ],
            "recommendation": f"Tu negocio es {profile.model.value}. "
            f"Canales recomendados: {', '.join(ch.value for ch in profile.channels[:3])}",
        }

    except Exception as e:
        logger.error(f"Business analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Phase 11: Lead Generation
# ============================================================


@router.post("/lead-generation/find-prospects")
async def find_prospects(
    business_model: str = Query(...),
    location: str = Query(""),
    target_audience: str = Query(""),
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """Generate prospects using multi-channel lead gen."""

    try:
        from app.domains.business_intelligence.business_model_detector import BusinessModel

        leads = lead_generator.generate_leads(
            business_model, location, target_audience, limit
        )

        if not leads:
            return {
                "status": "no_leads",
                "message": "No leads found for this model",
                "count": 0,
            }

        # Convert string to enum
        try:
            model_enum = BusinessModel(business_model)
        except ValueError:
            model_enum = BusinessModel.HYBRID

        enriched_leads = [
            lead_enricher.enrich_lead(
                lead,
                BusinessProfile(
                    business_id="temp",
                    name="Temp",
                    description="",
                    model=model_enum
                )
            )
            for lead in leads[:limit]
        ]

        return {
            "status": "success",
            "count": len(enriched_leads),
            "leads": [
                {
                    "lead_id": lead.lead_id,
                    "name": lead.name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "company": lead.company,
                    "location": lead.location,
                    "source": lead.source.value,
                    "quality": lead.quality.value,
                    "estimated_budget": lead.estimated_budget,
                    "contact_method": lead.contact_method,
                }
                for lead in enriched_leads
            ],
            "summary": {
                "hot_leads": sum(1 for l in enriched_leads if l.quality.value == "hot"),
                "warm_leads": sum(1 for l in enriched_leads if l.quality.value == "warm"),
                "cold_leads": sum(1 for l in enriched_leads if l.quality.value == "cold"),
                "avg_budget": sum(l.estimated_budget or 0 for l in enriched_leads) / len(enriched_leads) if enriched_leads else 0,
            }
        }

    except Exception as e:
        logger.error(f"Lead generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Phase 12: Service Diagnostics
# ============================================================


@router.post("/diagnostics/analyze-product")
async def analyze_product(
    business_description: str = Query(...),
    business_model: str = Query(""),
) -> Dict[str, Any]:
    """Diagnose product-market fit and issues."""

    try:
        diagnosis = diagnostician.diagnose(business_description, business_model)

        return {
            "status": "success",
            "pmf_status": diagnosis.pmf_status.value,
            "pmf_score": diagnosis.pmf_score,
            "scores": {
                "product_quality": diagnosis.product_quality_score,
                "marketing_quality": diagnosis.marketing_quality_score,
                "visibility": diagnosis.visibility_score,
                "positioning": diagnosis.positioning_score,
            },
            "strengths": diagnosis.strengths,
            "weaknesses": diagnosis.weaknesses,
            "improvements": [
                {
                    "issue": imp.issue,
                    "impact": imp.impact,
                    "fix": imp.fix,
                    "effort_level": imp.effort_level,
                    "time_to_fix_days": imp.time_to_fix_days,
                    "expected_lead_increase": f"{imp.expected_lead_increase_percent}%",
                    "priority": imp.priority.value,
                }
                for imp in diagnosis.improvements
            ],
            "recommended_actions": diagnosis.recommended_actions,
            "revenue_impact": {
                "30_days": diagnosis.estimated_revenue_impact_30days,
                "90_days": diagnosis.estimated_revenue_impact_90days,
            }
        }

    except Exception as e:
        logger.error(f"Product diagnosis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diagnostics/competitive-analysis")
async def analyze_competition(
    business_name: str = Query(...),
    industry: str = Query(""),
) -> Dict[str, Any]:
    """Analyze competitive landscape."""

    try:
        analysis = competitive_analyzer.analyze(business_name, industry)

        return {
            "status": "success",
            "market_position": analysis["market_position"],
            "competitor_count": analysis["competitor_count"],
            "differentiation_opportunities": analysis["differentiation_opportunities"],
            "pricing_recommendation": analysis["pricing_recommendation"],
            "gaps_in_market": analysis["gaps_in_market"],
            "market_size": analysis["market_size"],
            "growth_rate": analysis["growth_rate"],
        }

    except Exception as e:
        logger.error(f"Competitive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Phase 13: Marketing Strategy & Copy Generation
# ============================================================


@router.post("/marketing/channel-strategy")
async def generate_channel_strategy(
    business_model: str = Query(...),
) -> Dict[str, Any]:
    """Generate channel-specific marketing strategy."""

    try:
        strategy = strategy_gen.generate_strategy(business_model)

        return {
            "status": "success",
            "business_model": strategy.business_model,
            "channels": [
                {
                    "channel": ch.channel,
                    "priority": ch.priority.value,
                    "expected_leads_per_month": ch.expected_leads_per_month,
                    "conversion_rate": ch.estimated_conversion_rate,
                    "actions": [
                        {
                            "action": act.action,
                            "description": act.description,
                            "effort_level": act.effort_level,
                            "timeline_days": act.timeline_days,
                            "expected_leads": act.expected_leads_per_month,
                        }
                        for act in ch.actions
                    ],
                    "quick_wins": ch.quick_wins,
                }
                for ch in strategy.channels
            ],
            "total_expected_leads_per_month": strategy.total_expected_leads_per_month,
            "priority_order": strategy.priority_order,
            "phased_approach": strategy.phased_approach,
        }

    except Exception as e:
        logger.error(f"Strategy generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketing/copy-kit")
async def generate_copy_kit(
    business_name: str = Query(...),
    channel: str = Query(...),
) -> Dict[str, Any]:
    """Generate copy and content for channel."""

    try:
        copy_kit = copy_gen.generate_copy(business_name, channel)

        return {
            "status": "success",
            "channel": copy_kit.channel,
            "headlines": copy_kit.headlines,
            "descriptions": copy_kit.descriptions,
            "calls_to_action": copy_kit.calls_to_action,
            "sample_posts": copy_kit.sample_posts,
            "email_templates": copy_kit.email_templates,
            "best_practices": copy_kit.best_practices,
        }

    except Exception as e:
        logger.error(f"Copy generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketing/content-calendar")
async def get_content_calendar(
    business_model: str = Query(...),
    month: str = Query("current"),
) -> Dict[str, Any]:
    """Get 30-day content calendar by channel."""

    return {
        "status": "success",
        "month": month,
        "business_model": business_model,
        "calendar": [
            {
                "date": "2026-09-01",
                "channel": "instagram",
                "content_type": "reel",
                "topic": "Product showcase",
                "best_posting_time": "19:00",
                "copy_template": "See product_copy.txt",
            },
            {
                "date": "2026-09-02",
                "channel": "google_maps",
                "content_type": "post",
                "topic": "Weekly deal",
                "copy_template": "20% off this week!",
            },
            {
                "date": "2026-09-03",
                "channel": "whatsapp",
                "content_type": "broadcast",
                "topic": "Exclusive offer",
                "send_time": "09:00",
            }
        ],
        "next_30_days_summary": {
            "total_posts": 20,
            "instagram": 8,
            "google_maps": 5,
            "whatsapp": 4,
            "email": 3,
            "themes": ["Product showcase", "Customer success", "Deals", "Behind the scenes"],
        }
    }


# ============================================================
# Complete End-to-End Workflow
# ============================================================


@router.post("/workflow/startup-plan")
async def startup_plan(
    business_description: str = Body(...),
) -> Dict[str, Any]:
    """Generate complete startup plan: analyze + diagnose + generate leads + strategy."""

    try:
        # Step 1: Analyze business
        profile = detector.detect_model(business_description)

        # Step 2: Generate leads
        leads = lead_generator.generate_leads(profile.model.value, limit=50)
        enriched_leads = lead_enricher.enrich_batch(leads, profile)

        # Step 3: Diagnose
        diagnosis = diagnostician.diagnose(business_description)

        # Step 4: Strategy
        strategy = strategy_gen.generate_strategy(profile.model.value)

        return {
            "status": "success",
            "startup_plan": {
                "phase_1_business_analysis": {
                    "model": profile.model.value,
                    "channels": [ch.value for ch in profile.channels],
                },
                "phase_2_lead_generation": {
                    "leads_found": len(enriched_leads),
                    "quality_breakdown": {
                        "hot": sum(1 for l in enriched_leads if l.quality.value == "hot"),
                        "warm": sum(1 for l in enriched_leads if l.quality.value == "warm"),
                        "cold": sum(1 for l in enriched_leads if l.quality.value == "cold"),
                    }
                },
                "phase_3_diagnostics": {
                    "pmf_score": diagnosis.pmf_score,
                    "status": diagnosis.pmf_status.value,
                    "top_issues": [i.issue for i in diagnosis.improvements[:3]],
                },
                "phase_4_strategy": {
                    "total_channels": len(strategy.channels),
                    "expected_leads_month": strategy.total_expected_leads_per_month,
                    "priority_1_channel": strategy.channels[0].channel if strategy.channels else None,
                },
                "next_steps": [
                    "1. Implement phase 1 actions (Google Maps, website)",
                    "2. Start lead outreach (channel 1)",
                    "3. Setup automation (WhatsApp, email)",
                    "4. Monitor metrics weekly",
                ]
            }
        }

    except Exception as e:
        logger.error(f"Startup plan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
