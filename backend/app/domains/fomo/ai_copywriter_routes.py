"""Fase A: AI FOMO Copywriter Agent — API routes"""

import uuid
from typing import Optional, Dict, List, Any

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.fomo.ai_copywriter_agent import (
    AICopywriterAgent,
    CopyTone,
    SupportedLanguage,
)

router = APIRouter(prefix="/fomo/ai/copywriter", tags=["fomo-ai-copywriter"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/generate")
async def generate_campaign_copy(
    business_id: uuid.UUID = Query(...),
    campaign_type: str = Query(..., description="e.g. flash_sale, cart_abandonment, countdown"),
    product_name: str = Query(...),
    product_description: str = Query(...),
    audience: str = Query("general"),
    tone: CopyTone = Query(CopyTone.URGENT),
    language: SupportedLanguage = Query(SupportedLanguage.ES),
    variant_count: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate FOMO copy variants (subject lines, urgency messages, CTAs, SMS) via AI"""
    result = await AICopywriterAgent.generate_campaign_copy(
        db=db,
        business_id=business_id,
        campaign_type=campaign_type,
        product_name=product_name,
        product_description=product_description,
        audience=audience,
        tone=tone,
        language=language,
        variant_count=variant_count,
    )
    return result


@router.post("/generate-and-rank")
async def generate_and_rank_copy(
    business_id: uuid.UUID = Query(...),
    campaign_type: str = Query(...),
    product_name: str = Query(...),
    product_description: str = Query(...),
    audience: str = Query("general"),
    tone: CopyTone = Query(CopyTone.URGENT),
    language: SupportedLanguage = Query(SupportedLanguage.ES),
    variant_count: int = Query(5, ge=1, le=10),
    historical_data: Optional[Dict[str, List[Dict[str, Any]]]] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate copy AND auto-rank variants by predicted performance
    (uses historical open/click rate data when provided, heuristics otherwise)"""
    result = await AICopywriterAgent.generate_and_rank(
        db=db,
        business_id=business_id,
        campaign_type=campaign_type,
        product_name=product_name,
        product_description=product_description,
        audience=audience,
        tone=tone,
        language=language,
        variant_count=variant_count,
        historical_data=historical_data,
    )
    return result


@router.post("/translate")
async def translate_campaign_copy(
    business_id: uuid.UUID = Query(...),
    target_language: SupportedLanguage = Query(...),
    content: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Translate existing FOMO copy to another language, preserving persuasive intent"""
    result = await AICopywriterAgent.translate_copy(
        db=db,
        business_id=business_id,
        content=content,
        target_language=target_language,
    )
    return result


@router.get("/supported-languages")
async def get_supported_languages():
    """List supported languages for AI copywriter"""
    return {
        "languages": [
            {"code": "es", "name": "Español"},
            {"code": "en", "name": "English"},
            {"code": "pt", "name": "Português"},
        ]
    }


@router.get("/supported-tones")
async def get_supported_tones():
    """List supported copy tones"""
    return {
        "tones": [
            {"id": "urgent", "name": "Urgente", "description": "Urgencia alta, acción inmediata"},
            {"id": "friendly", "name": "Cercano", "description": "Cálido, como recomendación de amigo"},
            {"id": "luxury", "name": "Exclusivo", "description": "Aspiracional, elegante"},
            {"id": "playful", "name": "Divertido", "description": "Energético, emojis moderados"},
            {"id": "professional", "name": "Profesional", "description": "Directo, confiable"},
        ]
    }
