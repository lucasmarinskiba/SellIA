from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import json
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.websites.models import Website, Domain

router = APIRouter()


async def _get_website_for_user(
    business_id: UUID, user: User, db: AsyncSession
) -> tuple[Business, Website]:
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == user.id,
            Business.is_active == True,
        )
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    website_result = await db.execute(
        select(Website).where(Website.business_id == business_id)
    )
    website = website_result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")

    return business, website


@router.get("/businesses/{business_id}/seo/meta")
async def get_seo_metadata(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get SEO metadata (meta tags) for website."""
    business, website = await _get_website_for_user(business_id, current_user, db)

    return {
        "meta_title": website.meta_title or website.title or business.name,
        "meta_description": website.meta_description or business.description or "",
        "meta_keywords": website.meta_keywords or "",
        "og_image_url": website.og_image_url or website.hero_image_url or "",
    }


@router.put("/businesses/{business_id}/seo/meta")
async def update_seo_metadata(
    business_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update SEO metadata."""
    business, website = await _get_website_for_user(business_id, current_user, db)

    website.meta_title = data.get("meta_title", website.meta_title)
    website.meta_description = data.get("meta_description", website.meta_description)
    website.meta_keywords = data.get("meta_keywords", website.meta_keywords)
    website.og_image_url = data.get("og_image_url", website.og_image_url)

    await db.commit()

    return {
        "meta_title": website.meta_title,
        "meta_description": website.meta_description,
        "meta_keywords": website.meta_keywords,
        "og_image_url": website.og_image_url,
    }


@router.get("/businesses/{business_id}/seo/schema")
async def get_schema_markup(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Schema.org markup for website."""
    business, website = await _get_website_for_user(business_id, current_user, db)

    # Fetch domain
    domain_result = await db.execute(
        select(Domain).where(Domain.website_id == website.id)
    )
    domain = domain_result.scalar_one_or_none()
    domain_url = f"https://{domain.subdomain}.sellia.app" if domain else "https://example.com"

    # LocalBusiness schema
    local_business = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": business.name,
        "description": business.description or "",
        "url": domain_url,
        "image": website.hero_image_url or "",
        "telephone": "",  # TODO: add phone to business model
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "",  # TODO
            "addressLocality": "",  # TODO
            "postalCode": "",  # TODO
            "addressCountry": "AR",  # TODO: parameterize
        },
    }

    # Organization schema
    organization = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": business.name,
        "url": domain_url,
        "logo": website.hero_image_url or "",
        "description": business.description or "",
        "sameAs": [],  # Social profiles
    }

    # BreadcrumbList schema
    breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Inicio",
                "item": domain_url,
            },
        ],
    }

    return {
        "local_business": local_business,
        "organization": organization,
        "breadcrumb_list": breadcrumbs,
    }


@router.get("/businesses/{business_id}/seo/sitemap.xml", response_class=PlainTextResponse)
async def get_sitemap(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate dynamic XML sitemap."""
    business, website = await _get_website_for_user(business_id, current_user, db)

    # Fetch domain
    domain_result = await db.execute(
        select(Domain).where(Domain.website_id == website.id)
    )
    domain = domain_result.scalar_one_or_none()
    domain_url = f"https://{domain.subdomain}.sellia.app" if domain else "https://example.com"

    # Get pages from website config
    pages = website.pages or {}
    page_urls = list(pages.keys()) if pages else []

    # Build sitemap XML
    sitemap_entries = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    # Home page
    sitemap_entries.append(
        f"<url><loc>{domain_url}</loc><lastmod>{website.updated_at.isoformat()}</lastmod><priority>1.0</priority></url>"
    )

    # Other pages
    for page_slug in page_urls:
        if page_slug != "/":
            sitemap_entries.append(
                f"<url><loc>{domain_url}/{page_slug}</loc><lastmod>{website.updated_at.isoformat()}</lastmod><priority>0.8</priority></url>"
            )

    sitemap_entries.append("</urlset>")

    return "\n".join(sitemap_entries)


@router.get("/businesses/{business_id}/seo/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate dynamic robots.txt."""
    business, website = await _get_website_for_user(business_id, current_user, db)

    # Fetch domain for sitemap URL
    domain_result = await db.execute(
        select(Domain).where(Domain.website_id == website.id)
    )
    domain = domain_result.scalar_one_or_none()
    domain_url = f"https://{domain.subdomain}.sellia.app" if domain else "https://example.com"

    robots_content = f"""# SellIA robots.txt
User-agent: *
Allow: /

# Sitemap
Sitemap: {domain_url}/seo/sitemap.xml

# Disallow admin paths
Disallow: /admin/
Disallow: /api/
"""

    return robots_content


@router.get("/businesses/{business_id}/seo/audit")
async def get_seo_audit(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get SEO audit checklist."""
    business, website = await _get_website_for_user(business_id, current_user, db)

    domain_result = await db.execute(
        select(Domain).where(Domain.website_id == website.id)
    )
    domain = domain_result.scalar_one_or_none()

    checks = {
        "meta_title": {
            "label": "Meta Title",
            "passed": bool(website.meta_title),
            "recommendation": "Set a descriptive title (50-60 chars) with keywords",
        },
        "meta_description": {
            "label": "Meta Description",
            "passed": bool(website.meta_description) and len(website.meta_description) >= 120,
            "recommendation": "Add a description (120-160 chars) that summarizes your page",
        },
        "og_image": {
            "label": "Open Graph Image",
            "passed": bool(website.og_image_url or website.hero_image_url),
            "recommendation": "Add an image for social sharing (1200x630px recommended)",
        },
        "domain_verified": {
            "label": "Domain Verified",
            "passed": domain.is_verified if domain else False,
            "recommendation": "Verify your domain with Google Search Console",
        },
        "sitemap": {
            "label": "Sitemap",
            "passed": True,  # Always available
            "recommendation": "Sitemap is auto-generated and available at /seo/sitemap.xml",
        },
        "robots_txt": {
            "label": "robots.txt",
            "passed": True,  # Always available
            "recommendation": "robots.txt is auto-generated and available at /robots.txt",
        },
        "website_published": {
            "label": "Website Published",
            "passed": website.status == "PUBLISHED",
            "recommendation": "Publish your website to make it live and indexable",
        },
        "has_content": {
            "label": "Content Available",
            "passed": bool(website.description or (website.pages and len(website.pages) > 0)),
            "recommendation": "Add quality content describing your business and offerings",
        },
    }

    passed = sum(1 for check in checks.values() if check["passed"])
    total = len(checks)
    score = (passed / total * 100) if total > 0 else 0

    return {
        "score": int(score),
        "passed": passed,
        "total": total,
        "checks": checks,
    }
