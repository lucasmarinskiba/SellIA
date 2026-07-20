"""Channel management."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.security import CurrentUser, get_current_user, require_role
from app.db.models import Channel, ChannelKind
from app.db.session import get_session


router = APIRouter()


class ChannelOut(BaseModel):
    id: uuid.UUID
    kind: ChannelKind
    external_id: str
    is_active: bool


class ChannelCreate(BaseModel):
    kind: ChannelKind
    external_id: str
    config: dict


@router.get("", response_model=list[ChannelOut])
async def list_channels(user: CurrentUser = Depends(get_current_user)) -> list[ChannelOut]:
    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Channel).where(Channel.tenant_id == user.tenant_id))
        return [
            ChannelOut(id=c.id, kind=c.kind, external_id=c.external_id, is_active=c.is_active)
            for c in result.scalars().all()
        ]


@router.post("", response_model=ChannelOut, status_code=201)
async def create_channel(
    payload: ChannelCreate,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> ChannelOut:
    async with get_session(tenant_id=user.tenant_id) as db:
        ch = Channel(
            tenant_id=uuid.UUID(user.tenant_id),
            kind=payload.kind,
            external_id=payload.external_id,
            config=payload.config,
        )
        db.add(ch)
        await db.flush()
        return ChannelOut(id=ch.id, kind=ch.kind, external_id=ch.external_id, is_active=ch.is_active)


@router.delete("/{channel_id}", status_code=204)
async def disconnect_channel(
    channel_id: uuid.UUID,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> None:
    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        ch = result.scalar_one_or_none()
        if not ch:
            raise HTTPException(status_code=404)
        ch.is_active = False
        await db.flush()
