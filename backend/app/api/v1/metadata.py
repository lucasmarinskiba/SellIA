"""
Metadata API v1 — SEO-optimized structured data endpoints
Generates dynamic JSON-LD schemas for each entity type.
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import json
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.database import get_async_session
from app.domains.businesses.models import Business
from app.domains.agents.models import Agent
from app.domains.automations.models import Workflow as AutomationWorkflow
from app.domains.users.models import User

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])

SITE_URL = "https://sellia-brain.vercel.app"


@router.get("/organization")
async def get_organization_metadata() -> Dict[str, Any]:
    """Get Organization structured data for SellIA"""
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "SellIA",
        "url": SITE_URL,
        "logo": f"{SITE_URL}/logo.png",
        "description": "AI-powered autonomous sales agents for B2B businesses",
        "sameAs": [
            "https://www.linkedin.com/company/sellia",
            "https://twitter.com/sellia",
        ],
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": "+1-800-SELLIA",
            "contactType": "Customer Service",
            "email": "support@sellia.ai",
        },
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "US",
        },
    }


@router.get("/software-application")
async def get_software_application_metadata() -> Dict[str, Any]:
    """Get SoftwareApplication schema for SellIA Brain"""
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "SellIA Brain",
        "description": "AI sales agent command center for autonomous B2B selling",
        "url": f"{SITE_URL}/sellia-brain",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.8",
            "ratingCount": "120",
        },
        "featureList": [
            "Real-time Sales Agent Monitoring",
            "AI-powered Lead Scoring",
            "Autonomous Outreach",
            "Sales Pipeline Management",
            "Computer Use Automation",
            "Revenue Operations Dashboard",
            "Multi-channel Integration",
            "Webhook System",
        ],
        "author": {
            "@type": "Organization",
            "name": "SellIA",
        },
    }


@router.get("/business/{business_id}")
async def get_business_metadata(
    business_id: str,
    session: AsyncSession = next(get_async_session()),
) -> Dict[str, Any]:
    """Get Business entity metadata as LocalBusiness schema"""
    try:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()

        if not business:
            raise HTTPException(404, "Business not found")

        return {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": business.name,
            "description": f"B2B business using SellIA for sales automation",
            "url": f"{SITE_URL}/businesses/{business_id}",
            "image": business.logo_url or f"{SITE_URL}/default-logo.png",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": business.country or "US",
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Sales",
                "email": business.contact_email or "sales@example.com",
            },
            "foundingDate": business.created_at.isoformat() if business.created_at else None,
            "sameAs": [
                url for url in [
                    business.website_url,
                    business.linkedin_url,
                    business.twitter_url,
                ]
                if url
            ],
        }

    except Exception as e:
        raise HTTPException(500, f"Error fetching business metadata: {str(e)}")


@router.get("/faq")
async def get_faq_metadata() -> Dict[str, Any]:
    """Get FAQ schema for SellIA common questions"""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "What is SellIA?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "SellIA is an AI-powered sales agent platform that automates the entire B2B sales process from lead generation to deal closure.",
                },
            },
            {
                "@type": "Question",
                "name": "How does SellIA's AI work?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "SellIA uses large language models, real-time data integration, and autonomous reasoning to understand buyer intent and execute multi-channel sales strategies.",
                },
            },
            {
                "@type": "Question",
                "name": "Can SellIA integrate with my CRM?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes, SellIA integrates with all major CRM platforms via API or webhook system for seamless data synchronization.",
                },
            },
            {
                "@type": "Question",
                "name": "What's the ROI from using SellIA?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Customers typically see 3-5x reduction in CAC, 40-60% increase in pipeline velocity, and 20-30% improvement in win rates.",
                },
            },
        ],
    }


@router.get("/breadcrumb")
async def get_breadcrumb_metadata(
    path: str = Query(..., description="Current page path"),
) -> Dict[str, Any]:
    """Get BreadcrumbList schema for current page"""
    # Parse path into breadcrumbs
    parts = [p for p in path.split("/") if p]
    breadcrumbs = []

    for i, part in enumerate(parts):
        url_path = "/" + "/".join(parts[:i+1])
        label = part.replace("-", " ").title()

        breadcrumbs.append({
            "@type": "ListItem",
            "position": i + 1,
            "name": label,
            "item": f"{SITE_URL}{url_path}",
        })

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs,
    }


@router.get("/product/{product_id}")
async def get_product_metadata(
    product_id: str,
) -> Dict[str, Any]:
    """Get Product schema (for future e-commerce integrations)"""
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"SellIA AI Agent - {product_id}",
        "description": "Autonomous B2B sales agent",
        "url": f"{SITE_URL}/products/{product_id}",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.8",
            "ratingCount": "150",
        },
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
        },
    }


@router.get("/event/{event_id}")
async def get_event_metadata(event_id: str) -> Dict[str, Any]:
    """Get Event schema (for webinars, demos, workshops)"""
    return {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": f"SellIA Event - {event_id}",
        "description": "AI sales automation webinar and demo",
        "startDate": datetime.now().isoformat(),
        "endDate": (datetime.now().replace(hour=datetime.now().hour + 2)).isoformat(),
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
        "location": {
            "@type": "VirtualLocation",
            "url": SITE_URL,
        },
        "organizer": {
            "@type": "Organization",
            "name": "SellIA",
            "url": SITE_URL,
        },
    }
