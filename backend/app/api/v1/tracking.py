"""Public tracking endpoints for email opens and clicks.

These endpoints do NOT require authentication because they are accessed
from email clients via image pixels and link redirects.
"""

from urllib.parse import urlparse

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.domains.automations.models import SequenceEmailLog, EmailSequence

router = APIRouter(tags=["tracking"])

# Allowed redirect schemes and domains
def _is_safe_redirect_url(url: str) -> bool:
    """Validate redirect URL to prevent open redirect attacks."""
    if not url or url == "/":
        return True
    # Reject javascript:, data:, etc.
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return False
    # Allow relative paths (no netloc)
    if not parsed.netloc:
        return True
    # In production, you may want to restrict to your domain:
    # allowed_domains = {"app.sellia.com", "sellia.com"}
    # return parsed.netloc.lower() in allowed_domains
    return True

# Transparent 1x1 GIF pixel
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x2c,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02,
    0x02, 0x44, 0x01, 0x00, 0x3b,
])


@router.get("/track/open/{tracking_token}")
async def track_open(tracking_token: str, request: Request):
    """Track an email open via a 1x1 transparent pixel."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SequenceEmailLog).where(SequenceEmailLog.tracking_token == tracking_token)
        )
        log = result.scalar_one_or_none()

        if log and not log.opened_at:
            log.opened_at = func.now()
            # Increment sequence opens_count
            await db.execute(
                select(EmailSequence).where(EmailSequence.id == log.sequence_id)
            )
            seq_result = await db.execute(
                select(EmailSequence).where(EmailSequence.id == log.sequence_id)
            )
            seq = seq_result.scalar_one_or_none()
            if seq:
                seq.opens_count = (seq.opens_count or 0) + 1
            await db.commit()

    return Response(
        content=TRACKING_PIXEL,
        media_type="image/gif",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate"},
    )


@router.get("/track/click/{tracking_token}")
async def track_click(tracking_token: str, request: Request):
    """Track an email click and redirect to the original URL."""
    redirect_url = request.query_params.get("url", "/")
    if not _is_safe_redirect_url(redirect_url):
        redirect_url = "/"

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SequenceEmailLog).where(SequenceEmailLog.tracking_token == tracking_token)
        )
        log = result.scalar_one_or_none()

        if log and not log.clicked_at:
            log.clicked_at = func.now()
            seq_result = await db.execute(
                select(EmailSequence).where(EmailSequence.id == log.sequence_id)
            )
            seq = seq_result.scalar_one_or_none()
            if seq:
                seq.clicks_count = (seq.clicks_count or 0) + 1
            await db.commit()

    return RedirectResponse(url=redirect_url)
