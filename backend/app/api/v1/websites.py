from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import re

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.websites.models import Website, Domain, WebsiteStatus
from app.domains.websites.schemas import (
    WebsiteCreate, WebsiteUpdate, WebsiteResponse,
    DomainCreate, DomainUpdate, DomainResponse,
    OnboardingCompleteRequest
)

router = APIRouter()


async def _get_business_for_user(
    business_id: UUID, user: User, db: AsyncSession
) -> Business:
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
    return business


def _validate_subdomain(subdomain: str) -> bool:
    """Validate subdomain format (alphanumeric + hyphens, 3-63 chars)."""
    pattern = r'^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$'
    return bool(re.match(pattern, subdomain.lower()))


@router.post("/onboarding/complete", response_model=WebsiteResponse)
async def complete_onboarding(
    req: OnboardingCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete onboarding: create business + website + domain in one call."""

    # Validate subdomain
    if not _validate_subdomain(req.subdomain):
        raise HTTPException(status_code=400, detail="Subdominio inválido. Solo letras, números y guiones.")

    # Check if subdomain already taken
    domain_check = await db.execute(
        select(Domain).where(Domain.subdomain == req.subdomain.lower())
    )
    if domain_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subdominio no disponible")

    # Get or create business
    business_query = await db.execute(
        select(Business).where(
            Business.user_id == current_user.id,
            Business.is_active == True,
        )
    )
    business = business_query.scalars().first()

    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado. Crea uno primero.")

    # Update business info if provided
    if req.business_name:
        business.name = req.business_name
    if req.business_description:
        business.description = req.business_description

    # Create website
    website = Website(
        business_id=business.id,
        template=req.website_template,
        title=req.business_name,
        description=req.business_description,
        status=WebsiteStatus.DRAFT,
    )
    db.add(website)
    await db.flush()

    # Create domain
    domain = Domain(
        website_id=website.id,
        subdomain=req.subdomain.lower(),
        is_primary=True,
        is_verified=True,  # Sellia-hosted subdomain always verified
    )
    db.add(domain)

    await db.commit()
    await db.refresh(website)
    await db.refresh(domain)

    website.domain = domain
    return website


@router.post("/businesses/{business_id}/website", response_model=WebsiteResponse, status_code=status.HTTP_201_CREATED)
async def create_website(
    business_id: UUID,
    req: WebsiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create website for a business."""
    await _get_business_for_user(business_id, current_user, db)

    # Validate subdomain
    if not _validate_subdomain(req.subdomain):
        raise HTTPException(status_code=400, detail="Subdominio inválido")

    # Check if subdomain taken
    domain_check = await db.execute(
        select(Domain).where(Domain.subdomain == req.subdomain.lower())
    )
    if domain_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subdominio no disponible")

    # Check if business already has website
    website_check = await db.execute(
        select(Website).where(Website.business_id == business_id)
    )
    if website_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Negocio ya tiene website")

    website = Website(
        business_id=business_id,
        template=req.template,
        title=req.title,
        description=req.description,
        hero_image_url=req.hero_image_url,
        meta_title=req.meta_title,
        meta_description=req.meta_description,
        meta_keywords=req.meta_keywords,
    )
    db.add(website)
    await db.flush()

    domain = Domain(
        website_id=website.id,
        subdomain=req.subdomain.lower(),
        is_primary=True,
        is_verified=True,
    )
    db.add(domain)

    await db.commit()
    await db.refresh(website)
    await db.refresh(domain)

    website.domain = domain
    return website


@router.get("/businesses/{business_id}/website", response_model=WebsiteResponse)
async def get_website(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get website for a business."""
    await _get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Website).where(Website.business_id == business_id)
    )
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")

    return website


@router.put("/businesses/{business_id}/website", response_model=WebsiteResponse)
async def update_website(
    business_id: UUID,
    req: WebsiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update website."""
    await _get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Website).where(Website.business_id == business_id)
    )
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")

    update_data = req.model_dump(exclude_unset=True)
    if "config" in update_data and website.config:
        update_data["config"] = {**website.config, **update_data["config"]}
    if "pages" in update_data and website.pages:
        update_data["pages"] = {**website.pages, **update_data["pages"]}

    for field, value in update_data.items():
        setattr(website, field, value)

    if req.status == WebsiteStatus.PUBLISHED:
        from datetime import datetime, timezone
        website.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(website)
    return website


@router.post("/businesses/{business_id}/website/publish", response_model=WebsiteResponse)
async def publish_website(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Publish website (make it live)."""
    await _get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Website).where(Website.business_id == business_id)
    )
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")

    from datetime import datetime, timezone
    website.status = WebsiteStatus.PUBLISHED
    website.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(website)
    return website


@router.get("/businesses/{business_id}/domain", response_model=DomainResponse)
async def get_domain(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get domain info for business website."""
    await _get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Website).where(Website.business_id == business_id)
    )
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")

    domain_result = await db.execute(
        select(Domain).where(Domain.website_id == website.id)
    )
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")

    return domain


@router.put("/businesses/{business_id}/domain", response_model=DomainResponse)
async def update_domain(
    business_id: UUID,
    req: DomainUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update domain (e.g., add custom domain)."""
    await _get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Website).where(Website.business_id == business_id)
    )
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")

    domain_result = await db.execute(
        select(Domain).where(Domain.website_id == website.id)
    )
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")

    if req.custom_domain:
        # Check if custom domain already taken
        custom_check = await db.execute(
            select(Domain).where(
                Domain.custom_domain == req.custom_domain,
                Domain.id != domain.id
            )
        )
        if custom_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Dominio personalizado ya en uso")

        domain.custom_domain = req.custom_domain
        domain.is_verified = False  # Needs DNS verification

    if req.is_verified is not None:
        domain.is_verified = req.is_verified

    await db.commit()
    await db.refresh(domain)
    return domain
