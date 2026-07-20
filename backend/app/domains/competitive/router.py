"""
Competitive Router
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.competitive import service as competitive_service
from app.domains.competitive.intelligence_engine import CompetitiveIntelligenceEngine
from app.domains.competitive.schemas import (
    BattlecardCreate,
    BattlecardUpdate,
    BattlecardOut,
    BattlecardCompareOut,
    MonitorCreate,
    MonitorUpdate,
    MonitorOut,
    ScrapeResult,
    IntelligenceDashboard,
)

router = APIRouter(prefix="/battlecards", tags=["competitive"])
intelligence_router = APIRouter(prefix="/competitive", tags=["competitive"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ═══════════════════════════════════════════════════════
#   Battlecards (existentes)
# ═══════════════════════════════════════════════════════

@router.get("", response_model=list[BattlecardOut])
async def list_battlecards(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List user's battlecards."""
    return await competitive_service.list_battlecards(db, current_user.id)


@router.post("", response_model=BattlecardOut, status_code=status.HTTP_201_CREATED)
async def create_battlecard(
    data: BattlecardCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new battlecard."""
    return await competitive_service.create_battlecard(
        db, current_user.id, data.model_dump()
    )


@router.get("/{battlecard_id}", response_model=BattlecardOut)
async def get_battlecard(
    battlecard_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a single battlecard."""
    battlecard = await competitive_service.get_battlecard(db, battlecard_id, current_user.id)
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard no encontrado")
    return battlecard


@router.patch("/{battlecard_id}", response_model=BattlecardOut)
async def update_battlecard(
    battlecard_id: UUID,
    data: BattlecardUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a battlecard."""
    battlecard = await competitive_service.get_battlecard(db, battlecard_id, current_user.id)
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard no encontrado")
    return await competitive_service.update_battlecard(
        db, battlecard, data.model_dump(exclude_unset=True)
    )


@router.delete("/{battlecard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_battlecard(
    battlecard_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a battlecard."""
    battlecard = await competitive_service.get_battlecard(db, battlecard_id, current_user.id)
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard no encontrado")
    await competitive_service.delete_battlecard(db, battlecard)
    return None


@router.get("/{battlecard_id}/compare")
async def compare_battlecard(
    battlecard_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return structured comparison data for a battlecard."""
    battlecard = await competitive_service.get_battlecard(db, battlecard_id, current_user.id)
    if not battlecard:
        raise HTTPException(status_code=404, detail="Battlecard no encontrado")
    return await competitive_service.get_comparison_data(battlecard)


# ═══════════════════════════════════════════════════════
#   Competitive Intelligence (nuevo)
# ═══════════════════════════════════════════════════════

@intelligence_router.post("/monitors", response_model=MonitorOut, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    data: MonitorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Agrega un competidor para monitoreo 24/7."""
    engine = CompetitiveIntelligenceEngine(db)
    monitor = await engine.monitor_competitor(
        business_id=data.business_id,
        competitor_url=data.competitor_url,
        competitor_name=data.competitor_name,
        products_to_track=data.products_to_track,
    )
    return monitor


@intelligence_router.get("/monitors", response_model=list[MonitorOut])
async def list_monitors(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Lista los competidores monitoreados."""
    from sqlalchemy import select, desc
    from app.domains.competitive.models import CompetitiveMonitor

    result = await db.execute(
        select(CompetitiveMonitor)
        .where(CompetitiveMonitor.business_id == business_id)
        .order_by(desc(CompetitiveMonitor.created_at))
    )
    return result.scalars().all()


@intelligence_router.get("/intelligence")
async def get_intelligence(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Retorna el dashboard de inteligencia competitiva."""
    engine = CompetitiveIntelligenceEngine(db)
    return await engine.get_intelligence_dashboard(business_id)


@intelligence_router.get("/alerts")
async def get_competitive_alerts(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Alertas recientes generadas por cambios de competidores."""
    from sqlalchemy import select, desc
    from app.domains.alerts.models import Alert

    result = await db.execute(
        select(Alert)
        .where(
            Alert.business_id == business_id,
            Alert.title.ilike("%competidor%"),
        )
        .order_by(desc(Alert.created_at))
        .limit(50)
    )
    return result.scalars().all()


@intelligence_router.post("/{monitor_id}/scrape")
async def scrape_monitor(
    monitor_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Dispara un scrape manual de un competidor."""
    engine = CompetitiveIntelligenceEngine(db)
    result = await engine.scrape_competitor(monitor_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@intelligence_router.delete("/monitors/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Elimina un monitor de competidor."""
    from sqlalchemy import select
    from app.domains.competitive.models import CompetitiveMonitor

    result = await db.execute(
        select(CompetitiveMonitor).where(CompetitiveMonitor.id == monitor_id)
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor no encontrado")
    await db.delete(monitor)
    await db.commit()
    return None
