"""Chatbots API: one sales bot per platform, configured and testable."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import service
from .models import BotFocus

router = APIRouter(prefix="/chatbots", tags=["Chatbots"])


class ActiveHours(BaseModel):
    """The window, in the seller's own local time with an explicit offset.

    "9 to 21" means nothing without knowing whose 9, which is why the offset is
    part of the value and not assumed from the server.
    """

    from_hour: int = Field(..., ge=0, le=23, alias="from")
    to_hour: int = Field(..., ge=0, le=23, alias="to")
    utc_offset: int = Field(0, ge=-12, le=14)

    model_config = {"populate_by_name": True}


class BotIn(BaseModel):
    enabled: bool | None = None
    personality_slug: str | None = Field(None, max_length=50)
    focus: BotFocus | None = None
    custom_instructions: str | None = Field(None, max_length=4000)
    handoff_keywords: list[str] | None = None
    max_ai_replies: int | None = Field(None, ge=1, le=50)
    active_hours: ActiveHours | None = None
    after_hours_message: str | None = Field(None, max_length=600)
    escalate_on_frustration: bool | None = None
    hold_on_policy_violation: bool | None = None


class TestIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)


async def _business_ids(db: AsyncSession, user: User) -> list[Any]:
    from app.domains.authority.service import business_ids_for

    return await business_ids_for(db, user.id)


@router.get("")
async def list_bots(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """One bot per connected platform, with what it really did there."""
    business_ids = await _business_ids(db, user)
    return await service.overview(db, business_ids)


@router.get("/personalities")
async def list_personalities(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    return {"personalities": await service.personalities(db)}


@router.put("/{platform}")
async def update_bot(
    platform: str,
    payload: BotIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    business_ids = await _business_ids(db, user)
    if not business_ids:
        raise HTTPException(status_code=400, detail="Necesitás un negocio creado.")

    changes = payload.model_dump(exclude_unset=True)
    if "focus" in changes and changes["focus"] is not None:
        changes["focus"] = changes["focus"].value
    if "active_hours" in changes:
        hours = changes["active_hours"]
        changes["active_hours"] = (
            {"from": hours["from_hour"], "to": hours["to_hour"], "utc_offset": hours["utc_offset"]}
            if hours else None
        )
    bot = await service.upsert_bot(db, business_ids[0], platform, changes)
    return service.serialize(bot)


@router.get("/playbooks")
async def list_playbooks(
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """The rules each platform imposes on a reply, and why they exist.

    Served from the backend so the screen cannot show a rule the reply path is
    not actually applying.
    """
    from . import playbooks

    return {
        "playbooks": [playbooks.describe(platform) for platform in sorted(playbooks.PLAYBOOKS)],
        "default": playbooks.describe("default"),
    }


class CheckIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


@router.post("/{platform}/check")
async def check_against_playbook(
    platform: str,
    payload: CheckIn,
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Does this message break the platform's rules?

    The same check the auto-reply runs, offered for text a person typed: the
    rules that sanction a MercadoLibre listing do not care whether the phone
    number was written by a bot or by the seller in a hurry. Returns what is
    wrong and the version trimmed to the platform's budget; it never edits the
    message itself.
    """
    from . import playbooks

    trimmed, problems = playbooks.enforce(platform, payload.text)
    return {
        "platform": platform,
        "ok": not problems,
        "problems": problems,
        "blocking": playbooks.blocking_problems(platform, payload.text),
        "length": len(payload.text),
        "max_chars": playbooks.for_platform(platform).max_chars,
        "trimmed_preview": trimmed if trimmed != payload.text else None,
        "playbook": playbooks.describe(platform),
    }


@router.post("/{platform}/test")
async def test_bot(
    platform: str,
    payload: TestIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Preview this platform's bot on a question, sending nothing to anyone."""
    business_ids = await _business_ids(db, user)
    if not business_ids:
        raise HTTPException(status_code=400, detail="Necesitás un negocio creado.")
    return await service.test_reply(db, business_ids[0], platform, payload.question)
