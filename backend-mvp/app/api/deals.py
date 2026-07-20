"""Deals CRUD · tenant-scoped via RLS."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.security import CurrentUser, get_current_user
from app.db.models import Deal, DealStage
from app.db.session import get_session


router = APIRouter()


class DealCreate(BaseModel):
    contact_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    value_cents: int = Field(ge=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    stage: DealStage = DealStage.PROSPECT


class DealUpdate(BaseModel):
    title: str | None = None
    value_cents: int | None = Field(default=None, ge=0)
    stage: DealStage | None = None
    probability: int | None = Field(default=None, ge=0, le=100)


class DealOut(BaseModel):
    id: uuid.UUID
    title: str
    value_cents: int
    currency: str
    stage: DealStage
    probability: int

    class Config:
        from_attributes = True


@router.get("", response_model=list[DealOut])
async def list_deals(user: CurrentUser = Depends(get_current_user)) -> list[DealOut]:
    async with get_session(tenant_id=user.tenant_id) as db:
        # RLS auto-filters by tenant
        result = await db.execute(select(Deal).order_by(Deal.updated_at.desc()).limit(200))
        return [DealOut.model_validate(d) for d in result.scalars().all()]


@router.post("", response_model=DealOut, status_code=201)
async def create_deal(payload: DealCreate, user: CurrentUser = Depends(get_current_user)) -> DealOut:
    async with get_session(tenant_id=user.tenant_id) as db:
        deal = Deal(
            tenant_id=uuid.UUID(user.tenant_id),
            contact_id=payload.contact_id,
            title=payload.title,
            value_cents=payload.value_cents,
            currency=payload.currency,
            stage=payload.stage,
        )
        db.add(deal)
        await db.flush()
        return DealOut.model_validate(deal)


@router.patch("/{deal_id}", response_model=DealOut)
async def update_deal(
    deal_id: uuid.UUID,
    payload: DealUpdate,
    user: CurrentUser = Depends(get_current_user),
) -> DealOut:
    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Deal).where(Deal.id == deal_id))
        deal = result.scalar_one_or_none()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(deal, field, value)

        await db.flush()
        return DealOut.model_validate(deal)


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(deal_id: uuid.UUID, user: CurrentUser = Depends(get_current_user)) -> None:
    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Deal).where(Deal.id == deal_id))
        deal = result.scalar_one_or_none()
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        await db.delete(deal)
