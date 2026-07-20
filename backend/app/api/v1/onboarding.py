"""Onboarding Mágico — API Router

Endpoints para el flujo de onboarding automático con IA.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.onboarding.schemas import (
    OnboardingAnalyzeRequest,
    OnboardingAnalyzeResponse,
    OnboardingCreateRequest,
    OnboardingCreateResponse,
)
from app.domains.onboarding.scraper import OnboardingScraper
from app.domains.onboarding.analyzer import OnboardingAnalyzer
from app.domains.onboarding.generator import OnboardingGenerator

router = APIRouter(tags=["Onboarding Mágico"])


@router.post("/analyze", response_model=OnboardingAnalyzeResponse)
async def analyze_source(
    req: OnboardingAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Analiza un Instagram handle o URL y devuelve datos estructurados del negocio."""
    try:
        scraper = OnboardingScraper()
        raw_text = await scraper.scrape(req.source)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo acceder a la fuente. Verificá que sea pública. Error: {str(e)}",
        )

    analyzer = OnboardingAnalyzer()
    discovery = await analyzer.analyze(raw_text)

    return OnboardingAnalyzeResponse(raw_text=raw_text, discovery=discovery)


@router.post("/create", response_model=OnboardingCreateResponse)
async def create_from_discovery(
    req: OnboardingCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crea negocio, catálogo, agentes y workflows a partir de un descubrimiento IA."""
    generator = OnboardingGenerator(db)
    result = await generator.generate(current_user.id, req.discovery)

    return OnboardingCreateResponse(
        business_id=result["business_id"],
        catalog_items_count=result["catalog_items_count"],
        agents_count=result["agents_count"],
        workflows_count=result["workflows_count"],
        message=result["message"],
    )
