import os
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.investor_pitch.service import InvestorPitchService

router = APIRouter(prefix="/investor-pitch", tags=["investor-pitch"])


@router.post("/decks", status_code=status.HTTP_201_CREATED)
async def generate_deck(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InvestorPitchService(db)
    try:
        deck = await service.generate_pitch_deck(current_user.business_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": deck.id,
        "business_id": deck.business_id,
        "title": deck.title,
        "status": deck.status,
        "html_url": deck.html_url,
        "pdf_url": deck.pdf_url,
        "created_at": deck.created_at,
    }


@router.get("/decks")
async def list_decks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InvestorPitchService(db)
    result = await service.list_decks(
        business_id=current_user.business_id,
        limit=limit,
        offset=offset,
    )
    return {
        "total": result["total"],
        "decks": [
            {
                "id": d.id,
                "title": d.title,
                "status": d.status,
                "html_url": d.html_url,
                "pdf_url": d.pdf_url,
                "created_at": d.created_at,
            }
            for d in result["decks"]
        ],
    }


@router.get("/decks/{deck_id}")
async def get_deck(
    deck_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InvestorPitchService(db)
    data = await service.get_deck_with_slides(deck_id, current_user.business_id)
    if not data:
        raise HTTPException(status_code=404, detail="Deck not found")

    deck = data["deck"]
    slides = data["slides"]
    return {
        "id": deck.id,
        "business_id": deck.business_id,
        "title": deck.title,
        "status": deck.status,
        "metrics": deck.metrics,
        "slides": [
            {
                "slide_number": s.slide_number,
                "title": s.title,
                "content": s.content,
                "chart_data": s.chart_data,
                "notes": s.notes,
            }
            for s in slides
        ],
        "html_url": deck.html_url,
        "pdf_url": deck.pdf_url,
        "created_at": deck.created_at,
    }


@router.get("/decks/{deck_id}/html")
async def get_html(
    deck_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InvestorPitchService(db)
    deck = await service.get_deck(deck_id, current_user.business_id)
    if not deck or not deck.html_url:
        raise HTTPException(status_code=404, detail="HTML not found")

    if not os.path.exists(deck.html_url):
        raise HTTPException(status_code=404, detail="HTML file missing")

    return FileResponse(deck.html_url, media_type="text/html", filename=f"deck_{deck_id}.html")


@router.get("/decks/{deck_id}/pdf")
async def get_pdf(
    deck_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InvestorPitchService(db)
    deck = await service.get_deck(deck_id, current_user.business_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    if not deck.pdf_url or not os.path.exists(deck.pdf_url):
        try:
            pdf_path = await service.export_pdf(deck_id, current_user.business_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        pdf_path = deck.pdf_url

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"deck_{deck_id}.pdf")
