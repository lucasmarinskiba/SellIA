"""Vendedor Multiplataforma API: capabilities, economics and selling actions."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import capabilities, pnl, selling, sync
from .models import PlatformSettings

router = APIRouter(prefix="/platform-commerce", tags=["Platform Commerce"])


class SettingsIn(BaseModel):
    commission_percent: Optional[float] = Field(None, ge=0, le=100)
    fixed_fee_per_order: Optional[float] = Field(None, ge=0)
    cogs_percent: Optional[float] = Field(None, ge=0, le=100)
    monthly_fixed_cost: Optional[float] = Field(None, ge=0)
    monthly_ad_spend: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)


async def _business_ids(db: AsyncSession, user: User) -> list[Any]:
    from app.domains.authority.service import business_ids_for

    return await business_ids_for(db, user.id)


@router.get("/overview")
async def overview(
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Everything the multi-platform screen needs: what each connected platform
    can really do, what it sold, and the consolidated position."""
    from app.domains.channels.models import ChannelConnection

    business_ids = await _business_ids(db, user)
    economics = await pnl.platform_pnl(db, business_ids, days=days)

    connections: dict[str, dict[str, Any]] = {}
    if business_ids:
        result = await db.execute(
            select(ChannelConnection).where(ChannelConnection.business_id.in_(business_ids))
        )
        for channel in result.scalars().all():
            platform = channel.platform.value if hasattr(channel.platform, "value") else str(channel.platform)
            connections[platform] = {
                "connected": bool(channel.is_active),
                "status": channel.status.value if hasattr(channel.status, "value") else str(channel.status),
                "status_message": channel.status_message,
                "last_sync_at": channel.last_sync_at.isoformat() if channel.last_sync_at else None,
            }

    settings_rows: dict[str, PlatformSettings] = {}
    if business_ids:
        settings_result = await db.execute(
            select(PlatformSettings).where(PlatformSettings.business_id.in_(business_ids))
        )
        settings_rows = {s.platform: s for s in settings_result.scalars().all()}

    platforms = []
    for row in economics["platforms"]:
        platform = row["platform"]
        config = settings_rows.get(platform)
        platforms.append({
            **row,
            "connection": connections.get(platform),
            "capabilities": capabilities.describe(platform),
            "actions": selling.actions_for(platform),
            "settings": {
                "commission_percent": float(config.commission_percent) if config and config.commission_percent is not None else None,
                "fixed_fee_per_order": float(config.fixed_fee_per_order) if config and config.fixed_fee_per_order is not None else None,
                "cogs_percent": float(config.cogs_percent) if config and config.cogs_percent is not None else None,
                "monthly_fixed_cost": float(config.monthly_fixed_cost) if config and config.monthly_fixed_cost is not None else None,
                "monthly_ad_spend": float(config.monthly_ad_spend) if config and config.monthly_ad_spend is not None else None,
            } if config else None,
        })

    return {
        "period_days": days,
        "platforms": platforms,
        "consolidated": economics["consolidated"],
        "has_business": bool(business_ids),
        "generated_at": economics["generated_at"],
    }


@router.put("/settings/{platform}")
async def update_settings(
    platform: str,
    payload: SettingsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Declare this platform's real economics. Only the seller knows these:
    a commission rate assumed from a public rate card would be wrong for most
    sellers and would silently produce a wrong margin."""
    business_ids = await _business_ids(db, user)
    if not business_ids:
        raise HTTPException(status_code=400, detail="Necesitás un negocio creado.")

    result = await db.execute(
        select(PlatformSettings).where(
            PlatformSettings.business_id == business_ids[0],
            PlatformSettings.platform == platform,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        config = PlatformSettings(business_id=business_ids[0], platform=platform)
        db.add(config)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    await db.commit()
    return {"platform": platform, "saved": True}


@router.post("/sync")
async def sync_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Pull real orders from every connected platform that can report them."""
    business_ids = await _business_ids(db, user)
    results = await sync.sync_all(db, business_ids)
    return {
        "results": results,
        "imported": sum(r.get("imported", 0) for r in results),
        "updated": sum(r.get("updated", 0) for r in results),
    }


@router.get("/{platform}/pending-questions")
async def pending_questions(
    platform: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Buyers on this platform still waiting for an answer, with their real
    question -- shown before the AI is allowed to reply to them."""
    business_ids = await _business_ids(db, user)
    if not business_ids:
        return {"pending": []}
    return {"pending": await selling.pending_questions(db, business_ids[0], platform)}


@router.post("/{platform}/actions/{action_key}")
async def run_action(
    platform: str,
    action_key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run a real selling action on this platform."""
    business_ids = await _business_ids(db, user)
    if not business_ids:
        raise HTTPException(status_code=400, detail="Necesitás un negocio creado.")

    spec = selling.ACTIONS.get(action_key)
    if spec is None:
        raise HTTPException(status_code=404, detail="Acción desconocida")
    if not capabilities.can(platform, spec["capability"]):
        raise HTTPException(
            status_code=400,
            detail=f"El conector de {platform} no puede hacer esto todavía.",
        )

    try:
        if action_key == "answer_buyers":
            return await selling.answer_buyers(db, business_ids[0])
        if action_key == "answer_pending":
            return await selling.answer_pending(db, business_ids[0], platform)
        if action_key == "sync_orders":
            return await selling.sync_orders(db, business_ids[0], platform)
        if action_key == "publish_catalog":
            return await selling.publish_catalog(db, business_ids[0], platform)
    except selling.ActionNotAvailable as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    raise HTTPException(status_code=400, detail="Acción no implementada")
