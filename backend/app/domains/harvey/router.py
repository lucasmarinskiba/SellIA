"""Harvey API — /api/v1/businesses/{business_id}/harvey/*

Reads need business access (owner or active member); anything that writes,
drafts or approves needs manage access (owner or ADMIN member).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.harvey import weekly
from app.domains.harvey.competitors_service import CompetitorError, CompetitorService
from app.domains.harvey.schemas import (
    BriefResponse,
    CompetitorIn,
    CompetitorResponse,
    DiscoverIn,
    DiscoverResponse,
    DiscoveryKeysIn,
    ImportCsvResponse,
    OutboxEdit,
    OutboxItemResponse,
    ProfileResponse,
    ProfileUpdate,
    ProspectResponse,
    ProspectsCreate,
    ProspectsCreateResponse,
    ReplyIn,
    ReplyResponse,
    StatusResponse,
    SummaryResponse,
    VerifyIn,
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
async def draft_email(
    business_id: UUID,
    prospect_id: UUID,
    step: int = Query(1, ge=1, le=3, description="Paso de la secuencia (1 a 3)"),
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
        return await service.draft_step(business, profile, prospect, step)
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


@router.post("/outbox/send-approved", response_model=SummaryResponse)
async def send_approved(
    business_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        return {"counts": await service.send_approved(business, profile, limit)}
    except HarveyError as e:
        raise _http(e) from e


@router.post("/outbox/{item_id}/send", response_model=OutboxItemResponse)
async def send_item(
    business_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        item = await service.get_outbox_item(business_id, item_id)
        account = await service.require_account(business_id)
        return await service.send_item(business, profile, item, account)
    except HarveyError as e:
        raise _http(e) from e


@router.post("/sequences/run", response_model=SummaryResponse)
async def run_sequences(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Draft the next email (step 2 or 3) for prospects whose previous one is due and unanswered."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        if not profile.is_enabled:
            raise HarveyError("Harvey está desactivado para este negocio", 409)
        return {"counts": await service.plan_followups(business, profile)}
    except HarveyError as e:
        raise _http(e) from e


@router.post("/inbox/sync", response_model=SummaryResponse)
async def sync_inbox(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read the business's inbox and record replies to Harvey's emails."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        return {"counts": await service.sync_inbox(business, profile)}
    except HarveyError as e:
        raise _http(e) from e


@router.get("/status", response_model=StatusResponse)
async def get_status(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = await require_business_access(db, business_id, current_user)
    service = HarveyService(db)
    profile = await service.get_or_create_profile(business)
    return await service.status(business, profile)


@router.patch("/outbox/{item_id}", response_model=OutboxItemResponse)
async def edit_item(
    business_id: UUID,
    item_id: UUID,
    body: OutboxEdit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rewrite a draft that has not been approved yet. The gate runs again on the new text."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        return await service.edit_item(business_id, profile, item_id, body.subject, body.body)
    except HarveyError as e:
        raise _http(e) from e


@router.post("/prospects/verify", response_model=SummaryResponse)
async def verify_prospects(
    business_id: UUID,
    body: VerifyIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm (or reject) addresses found by discovery. Mail only goes to verified addresses."""
    await require_business_access(db, business_id, current_user, manage=True)
    changed = await HarveyService(db).verify_prospects(business_id, body.prospect_ids, body.verified)
    return {"counts": {"updated": changed}}


@router.post("/prospects/discover", response_model=DiscoverResponse)
async def discover_prospects(
    business_id: UUID,
    body: DiscoverIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read the given sites (and/or sites a web search returns) and add the contact address each publishes."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        queries = body.queries
        if not body.urls and not queries:
            queries = service.discovery_queries(profile, datetime.now(timezone.utc))[:1]
        if not body.urls and not queries:
            raise HarveyError("Pasá al menos un sitio, o completá palabras clave en el cliente ideal", 422)
        return await service.discover(business, profile, urls=body.urls, queries=queries, limit=body.limit)
    except HarveyError as e:
        raise _http(e) from e


@router.post("/replies/{reply_id}/answer", response_model=OutboxItemResponse, status_code=status.HTTP_201_CREATED)
async def answer_reply(
    business_id: UUID,
    reply_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stage the drafted answer to a prospect's reply in the outbox, to review and approve."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        return await service.answer_reply(business, profile, reply_id)
    except HarveyError as e:
        raise _http(e) from e


@router.put("/discovery-keys", response_model=StatusResponse)
async def set_discovery_keys(
    business_id: UUID,
    body: DiscoveryKeysIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The business's own Brave / Google Places key. Write-only: the response says only whether one is loaded."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    profile = await service.get_or_create_profile(business)
    await service.set_search_keys(
        business_id, profile, brave=body.brave_api_key, google=body.google_places_api_key, provider=body.search_provider
    )
    return await service.status(business, profile)


@router.post("/prospects/import-csv", response_model=ImportCsvResponse, status_code=status.HTTP_201_CREATED)
async def import_prospects_csv(
    business_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import the business's own contact list (CSV with an ``email`` column) as prospects."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    service = HarveyService(db)
    try:
        profile = await service.get_or_create_profile(business)
        return await service.import_csv(business, profile, await file.read(1_000_001))
    except HarveyError as e:
        raise _http(e) from e


# ── competitor map ────────────────────────────────────────────────────────
def _comp_http(e: CompetitorError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/competitors", response_model=list[CompetitorResponse])
async def list_competitors(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user)
    return await CompetitorService(db).list_all(business_id)


@router.post("/competitors", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def add_competitor(
    business_id: UUID,
    body: CompetitorIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    try:
        return await CompetitorService(db).add(business_id, body.url, body.kind, body.name)
    except CompetitorError as e:
        raise _comp_http(e) from e


@router.get("/competitors/brief", response_model=BriefResponse)
async def get_competitive_brief(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user)
    row = await CompetitorService(db).get_brief(business_id)
    return BriefResponse(brief=row.brief if row else {}, generated_at=row.generated_at if row else None)


@router.post("/competitors/analyze", response_model=BriefResponse)
async def analyze_competitors(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-read stale sites and compare them with the business's own offer; the result feeds Harvey's drafts."""
    business = await require_business_access(db, business_id, current_user, manage=True)
    try:
        profile = await HarveyService(db).get_or_create_profile(business)
        return await CompetitorService(db).analyze(business, profile)
    except CompetitorError as e:
        raise _comp_http(e) from e


@router.post("/competitors/{competitor_id}/scan", response_model=CompetitorResponse)
async def scan_competitor(
    business_id: UUID,
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    service = CompetitorService(db)
    try:
        return await service.scan_one(await service.get(business_id, competitor_id))
    except CompetitorError as e:
        raise _comp_http(e) from e


@router.delete("/competitors/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    business_id: UUID,
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_business_access(db, business_id, current_user, manage=True)
    try:
        await CompetitorService(db).remove(business_id, competitor_id)
    except CompetitorError as e:
        raise _comp_http(e) from e


@router.get("/weekly-summary")
async def weekly_summary(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The last 7 days with Harvey (sent, replies, CRM deals) and what to do next."""
    await require_business_access(db, business_id, current_user)
    return await weekly.weekly_summary(db, business_id)
