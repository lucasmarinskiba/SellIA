"""Market Analyst Router"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.market_analyst import service as market_service
from app.domains.agents.market_analyst.schemas import (
    MarketAnalysisJobCreate,
    MarketAnalysisJobOut,
    MarketAnalysisJobDetailOut,
    MarketReportOut,
)

router = APIRouter(prefix="/market-analyst", tags=["market-analyst"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/analyze", response_model=MarketAnalysisJobOut, status_code=status.HTTP_201_CREATED)
async def start_analysis(
    data: MarketAnalysisJobCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Inicia un análisis de mercado para el negocio del usuario."""
    # Se asume que el primer negocio del usuario es el activo; ajustar si se requiere otro criterio
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    job = await market_service.run_market_analysis(
        db=db,
        business_id=business.id,
        target_market=data.target_market,
        competitors_list=data.competitors_list,
    )
    return job


@router.get("/jobs", response_model=list[MarketAnalysisJobOut])
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Lista los jobs de análisis de mercado del negocio."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    return await market_service.list_jobs(db, business.id)


@router.get("/jobs/{job_id}", response_model=MarketReportOut)
async def get_report(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Retorna el reporte completo de un análisis de mercado."""
    report = await market_service.get_market_report(db, job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return report
