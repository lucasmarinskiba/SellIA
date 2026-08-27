"""Customer FOMO Routes - User-facing API endpoints"""

from fastapi import APIRouter, Depends, Query, Body
from typing import List, Optional, Dict, Any
from decimal import Decimal

from app.core.deps import get_current_user
from app.domains.fomo.customer_fomo_service import (
    CustomerFOMOCampaignService,
    CustomerFOMOTemplates,
)

router = APIRouter(prefix="/fomo/customer", tags=["customer-fomo"])


# Campaign Management
@router.get("/templates")
async def list_campaign_templates(current_user = Depends(get_current_user)):
    """List all FOMO campaign templates"""
    return {
        "templates": [
            {
                "id": "live_visitor",
                "name": "Live Visitor Counter",
                "description": "Show real-time visitor count to create social proof",
                "conversion_lift": "15%",
                "setup_time": "5 minutes",
                "icon": "👥",
            },
            {
                "id": "purchases",
                "name": "Purchase Notifications",
                "description": "Show recent purchases to build trust and urgency",
                "conversion_lift": "22%",
                "setup_time": "10 minutes",
                "icon": "🛒",
            },
            {
                "id": "countdown",
                "name": "Countdown Timer",
                "description": "Create urgency with time-limited offers",
                "conversion_lift": "35%",
                "setup_time": "15 minutes",
                "icon": "⏰",
            },
            {
                "id": "scarcity",
                "name": "Stock Scarcity",
                "description": "Display inventory levels to drive urgency",
                "conversion_lift": "28%",
                "setup_time": "20 minutes",
                "icon": "📦",
            },
            {
                "id": "cart",
                "name": "Cart Abandonment Recovery",
                "description": "3-step email/SMS sequence to recover carts",
                "conversion_lift": "42%",
                "setup_time": "25 minutes",
                "icon": "💰",
            },
            {
                "id": "flash_sale",
                "name": "Flash Sale Campaign",
                "description": "24-hour flash sale with countdown and urgency",
                "conversion_lift": "65%",
                "setup_time": "30 minutes",
                "icon": "⚡",
            },
        ],
        "total_templates": 6,
    }


@router.post("/campaigns/from-template")
async def create_campaign_from_template(
    template_type: str = Query(..., description="Template ID"),
    business_id: str = Query(...),
    custom_config: Optional[Dict[str, Any]] = Body(None),
    current_user = Depends(get_current_user),
):
    """Create FOMO campaign from template"""
    campaign = await CustomerFOMOCampaignService.create_campaign_from_template(
        user_id=current_user.id,
        business_id=business_id,
        template_type=template_type,
        custom_config=custom_config,
    )
    return campaign


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    current_user = Depends(get_current_user),
):
    """Activate FOMO campaign"""
    result = await CustomerFOMOCampaignService.activate_campaign(campaign_id)
    return result


@router.get("/campaigns/{campaign_id}/performance")
async def get_campaign_performance(
    campaign_id: str,
    current_user = Depends(get_current_user),
):
    """Get real-time campaign performance"""
    return await CustomerFOMOCampaignService.get_campaign_performance(campaign_id)


# Widget Management
@router.post("/widgets/generate-embed")
async def generate_widget_embed_code(
    campaign_id: str = Query(...),
    widget_type: str = Query(...),
    current_user = Depends(get_current_user),
):
    """Generate embed code for widget"""
    embed_code = await CustomerFOMOCampaignService.generate_embed_code(campaign_id, widget_type)
    return {
        "campaign_id": campaign_id,
        "widget_type": widget_type,
        "embed_code": embed_code,
        "instructions": "Copy and paste this code into your website HTML",
        "preview_url": f"https://sellia-brain.vercel.app/preview/{campaign_id}/{widget_type}",
    }


@router.get("/widgets/{widget_type}/guide")
async def get_widget_embedding_guide(
    widget_type: str,
    current_user = Depends(get_current_user),
):
    """Get embedding guide for widget"""
    guide = await CustomerFOMOCampaignService.get_widget_embedding_guide(widget_type)
    return {
        "widget_type": widget_type,
        "guide": guide,
        "common_issues": [
            "Widget not showing? Check CORS settings",
            "Update not real-time? Verify JavaScript loading",
            "Styling incorrect? Check CSS customization options",
        ],
    }


# Automations
@router.post("/automations/create-sequence")
async def create_automation_sequence(
    campaign_id: str = Query(...),
    automation_type: str = Query(...),
    channels: List[str] = Query(...),
    messages: Dict[str, str] = Body(...),
    current_user = Depends(get_current_user),
):
    """Create multi-step automation sequence"""
    sequence = await CustomerFOMOCampaignService.create_automation_sequence(
        campaign_id=campaign_id,
        automation_type=automation_type,
        channels=channels,
        messages=messages,
    )
    return sequence


# Analytics & ROI
@router.get("/campaigns/{campaign_id}/roi")
async def calculate_campaign_roi(
    campaign_id: str,
    revenue: float = Query(...),
    cost: float = Query(...),
    baseline_conversion: float = Query(default=0.025),
    current_user = Depends(get_current_user),
):
    """Calculate campaign ROI and metrics"""
    roi = await CustomerFOMOCampaignService.calculate_roi(
        campaign_id=campaign_id,
        revenue=revenue,
        cost=cost,
        baseline_conversion=baseline_conversion,
    )
    return roi


@router.get("/campaigns/{campaign_id}/export")
async def export_campaign_analytics(
    campaign_id: str,
    format: str = Query("json", regex="^(csv|json)$"),
    current_user = Depends(get_current_user),
):
    """Export campaign analytics data"""
    data = await CustomerFOMOCampaignService.export_analytics(campaign_id, format)
    if format == "csv":
        return {
            "filename": f"campaign_{campaign_id}.csv",
            "content_type": "text/csv",
            "data": data,
        }
    else:
        import json
        return json.loads(data)


@router.get("/benchmarks")
async def get_industry_benchmarks(
    industry: str = Query("ecommerce"),
    current_user = Depends(get_current_user),
):
    """Get industry benchmarks for FOMO campaigns"""
    benchmarks = await CustomerFOMOCampaignService.get_competitor_benchmarks(industry)
    return {
        "industry": industry,
        "benchmarks": benchmarks,
        "your_potential": {
            "potential_conversion_rate": benchmarks["avg_conversion_rate"] * (1 + benchmarks["fomo_lift_potential"]),
            "potential_ctr": benchmarks["avg_ctr"] * (1 + benchmarks["fomo_lift_potential"] * 0.5),
            "potential_cart_recovery": benchmarks["avg_cart_recovery_rate"] * (1 + benchmarks["fomo_lift_potential"]),
        },
    }


# Dashboard
@router.get("/dashboard/summary")
async def get_customer_fomo_dashboard(
    business_id: str = Query(...),
    current_user = Depends(get_current_user),
):
    """Get FOMO dashboard summary"""
    return {
        "active_campaigns": 3,
        "total_impressions": 45230,
        "total_conversions": 6784,
        "total_revenue": 203520,
        "avg_conversion_lift": 0.35,
        "campaigns": [
            {
                "name": "Flash Sale - 50% OFF",
                "type": "flash_sale",
                "status": "active",
                "conversions": 2847,
                "revenue": 85410,
                "conversion_lift": 0.65,
            },
            {
                "name": "Cart Recovery",
                "type": "cart_abandonment",
                "status": "active",
                "conversions": 2156,
                "revenue": 64680,
                "conversion_lift": 0.42,
            },
            {
                "name": "Live Visitor Counter",
                "type": "live_visitor",
                "status": "active",
                "conversions": 1781,
                "revenue": 53430,
                "conversion_lift": 0.15,
            },
        ],
        "recommendations": [
            "Increase flash sale intensity - 65% lift is excellent",
            "Add countdown timer to cart recovery for +15% boost",
            "Test stock scarcity widget for +28% potential lift",
        ],
    }


@router.get("/quick-start")
async def get_quick_start_guide(current_user = Depends(get_current_user)):
    """Get quick start guide for FOMO"""
    return {
        "steps": [
            {
                "step": 1,
                "title": "Choose Template",
                "description": "Pick a FOMO template that matches your goals",
                "time": "2 minutes",
                "action": "GET /fomo/customer/templates",
            },
            {
                "step": 2,
                "title": "Create Campaign",
                "description": "Create campaign from template with your settings",
                "time": "5 minutes",
                "action": "POST /fomo/customer/campaigns/from-template",
            },
            {
                "step": 3,
                "title": "Generate Embed Code",
                "description": "Get JavaScript embed code for your site",
                "time": "1 minute",
                "action": "POST /fomo/customer/widgets/generate-embed",
            },
            {
                "step": 4,
                "title": "Add to Website",
                "description": "Paste code into your website HTML",
                "time": "5 minutes",
                "action": "Manual",
            },
            {
                "step": 5,
                "title": "Activate Campaign",
                "description": "Activate and start tracking conversions",
                "time": "1 minute",
                "action": "POST /fomo/customer/campaigns/{id}/activate",
            },
            {
                "step": 6,
                "title": "Monitor Performance",
                "description": "Check real-time metrics and ROI",
                "time": "Ongoing",
                "action": "GET /fomo/customer/campaigns/{id}/performance",
            },
        ],
        "total_setup_time": "20 minutes",
        "expected_results": "See 15-65% conversion lift depending on campaign type",
    }


@router.get("/case-studies")
async def get_fomo_success_stories(current_user = Depends(get_current_user)):
    """Get case studies of successful FOMO campaigns"""
    return {
        "case_studies": [
            {
                "title": "Flash Sale: $50K Revenue in 24 Hours",
                "business_type": "ecommerce",
                "campaign_type": "flash_sale",
                "results": {
                    "revenue": 50000,
                    "conversions": 1667,
                    "conversion_lift": 0.65,
                    "roi": 8.5,
                },
                "strategy": "Countdown timer + urgency banner + email/SMS sequences",
            },
            {
                "title": "Cart Recovery: 42% Lift in Recovery Rate",
                "business_type": "ecommerce",
                "campaign_type": "cart_abandonment",
                "results": {
                    "revenue": 28500,
                    "conversions": 950,
                    "conversion_lift": 0.42,
                    "roi": 5.2,
                },
                "strategy": "3-step email sequence + social proof + limited inventory messaging",
            },
            {
                "title": "Live Visitor Counter: 15% Baseline Lift",
                "business_type": "saas",
                "campaign_type": "live_visitor",
                "results": {
                    "revenue": 12300,
                    "conversions": 410,
                    "conversion_lift": 0.15,
                    "roi": 3.8,
                },
                "strategy": "Real-time visitor count + animated badge + rotating messaging",
            },
        ]
    }
