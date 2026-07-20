"""Brand Visual Agent API Router"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.brand_visual.schemas import (
    BrandKitGenerateRequest,
    BrandKitJobResponse,
    BrandAssetResponse,
)
from app.domains.agents.brand_visual.service import BrandVisualService

router = APIRouter(prefix="/agents/brand-visual", tags=["brand-visual"])


@router.post("/generate", response_model=BrandKitJobResponse, status_code=status.HTTP_201_CREATED)
async def generate_brand_kit(
    req: BrandKitGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BrandVisualService(db)
    job = await service.generate_brand_kit(
        business_id=req.business_id,
        brand_name=req.brand_name,
        industry=req.industry,
        style_preferences=req.style_preferences,
    )
    return job


@router.get("/kits", response_model=list[BrandKitJobResponse])
async def list_kits(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BrandVisualService(db)
    return await service.list_kits(business_id)


@router.get("/kits/{job_id}", response_model=BrandKitJobResponse)
async def get_kit(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BrandVisualService(db)
    job = await service.get_brand_kit(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Brand kit no encontrado")
    return job


@router.get("/kits/{job_id}/download")
async def download_kit(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BrandVisualService(db)
    job = await service.get_brand_kit(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Brand kit no encontrado")

    zip_bytes = await service.build_zip(job_id)
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=brand_kit_{job_id}.zip"},
    )
