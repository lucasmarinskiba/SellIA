"""Harvey API — /api/v1/businesses/{business_id}/harvey/*

Reads need business access (owner or active member); anything that writes,
drafts or approves needs manage access (owner or ADMIN member).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.harvey.schemas import (
    OutboxItemResponse,
    ProfileResponse,
    ProfileUpdate,
    ProspectResponse,
    ProspectsCreate,
    ProspectsCreateResponse,
    ReplyIn,
    ReplyResponse,
)
from app.domains.harvey.service import HarveyError, HarveyService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/harvey", tags=["Harvey"])


def _http(e: HarveyError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user)
    return await HarveyService(db).get_or_create_profile(business)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    business_id: UUID,
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user, manage=True)
    try:
        return await HarveyService(db).update_profile(business, body.model_dump(exclude_unset=True))
    except HarveyError as e:
        raise _http(e) from e


@router.get("/prospects", response_model=list[ProspectResponse])
async def list_prospects(
    business_id: UUID,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user)
    return await HarveyService(db).list_prospects(business_id, status_filter, limit, offset)


@router.post("/prospects", response_model=ProspectsCreateResponse, status_code=status.HTTP_201_CREATED)
async def add_prospects(
    business_id: UUID,
    body: ProspectsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    profile = await service.get_or_create_profile(business)
    created, skipped = await service.add_prospects(
        business_id, profile, [p.model_dump() for p in body.prospects]
    )
    return {"created": created, "skipped": skipped}


@router.post(
    "/prospects/{prospect_id}/draft", response_model=OutboxItemResponse, status_code=status.HTTP_201_CREATED
)
async def draft_first_email(
    business_id: UUID,
    prospect_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        if not profile.is_enabled:
            raise HarveyError("Harvey está desactivado para este negocio", 409)
        prospect = await service.get_prospect(business_id, prospect_id)
        return await service.draft_first_email(business, profile, prospect)
    except HarveyError as e:
        raise _http(e) from e


@router.post(
    "/prospects/{prospect_id}/replies", response_model=ReplyResponse, status_code=status.HTTP_201_CREATED
)
async def record_reply(
    business_id: UUID,
    prospect_id: UUID,
    body: ReplyIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        prospect = await service.get_prospect(business_id, prospect_id)
        return await service.record_reply(business, profile, prospect, body.body)
    except HarveyError as e:
        raise _http(e) from e


@router.get("/replies", response_model=list[ReplyResponse])
async def list_replies(
    business_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user)
    return await HarveyService(db).list_replies(business_id, limit, offset)


@router.get("/outbox", response_model=list[OutboxItemResponse])
async def list_outbox(
    business_id: UUID,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user)
    return await HarveyService(db).list_outbox(business_id, status_filter, limit, offset)


async def _decide(business_id: UUID, item_id: UUID, approve: bool, db: AsyncSession, user: User):
    business = await require_business_access(db, business_id, user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        return await service.decide(business_id, profile, item_id, user.id, approve)
    except HarveyError as e:
        raise _http(e) from e


@router.post("/outbox/{item_id}/approve", response_model=OutboxItemResponse)
async def approve_item(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _decide(business_id, item_id, True, db, current_user)


@router.post("/outbox/{item_id}/reject", response_model=OutboxItemResponse)
async def reject_item(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _decide(business_id, item_id, False, db, current_user)
