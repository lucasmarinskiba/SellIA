"""Landing Page Builder Router"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.landing_builder import service as landing_service
from app.domains.agents.landing_builder.schemas import (
    LandingPageJobCreate,
    LandingPageJobOut,
    LandingPageCodeOut,
)

router = APIRouter(prefix="/landing-builder", tags=["landing-builder"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/generate", response_model=LandingPageJobOut, status_code=status.HTTP_201_CREATED)
async def start_generation(
    data: LandingPageJobCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Genera una landing page con variantes A/B para un producto."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    job = await landing_service.generate_landing_page(
        db=db,
        business_id=business.id,
        product_id=data.product_id,
        style=data.style,
    )
    return job


@router.get("/jobs", response_model=list[LandingPageJobOut])
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Lista los jobs de landing page del negocio."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    return await landing_service.list_jobs(db, business.id)


@router.get("/jobs/{job_id}", response_model=LandingPageCodeOut)
async def get_job_with_code(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Obtiene un job con su código generado."""
    code_data = await landing_service.get_landing_code(db, job_id)
    if not code_data:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return code_data


@router.get("/jobs/{job_id}/code")
async def download_zip(
    job_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Descarga el código generado como ZIP."""
    zip_bytes = await landing_service.get_landing_zip(job_id)
    if zip_bytes is None:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=landing_{job_id}.zip"},
    )
