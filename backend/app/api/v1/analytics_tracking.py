from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.websites.models import Website
from app.domains.analytics.models import AnalyticsEvent, EventType, Conversion

router = APIRouter()

async def _get_website_for_user(business_id: UUID, user: User, db: AsyncSession) -> Website:
    result = await db.execute(
        select(Website).join(Business).where(
            Business.id == business_id,
            Business.user_id == user.id,
            Business.is_active == True,
        )
    )
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website no encontrado")
    return website

@router.post("/track/event")
async def track_event(data: dict, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        website_id = data.get("website_id")
        event_type = data.get("event_type", "page_view")
        page_url = data.get("page_url")
        session_id = data.get("session_id")
        if not all([website_id, page_url, session_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        event = AnalyticsEvent(
            website_id=website_id,
            event_type=EventType(event_type),
            event_name=data.get("event_name"),
            page_url=page_url,
            page_title=data.get("page_title"),
            session_id=session_id,
            user_id=data.get("user_id"),
            user_agent=request.headers.get("user-agent"),
            device_type=data.get("device_type"),
            browser=data.get("browser"),
            duration_ms=data.get("duration_ms"),
            scroll_depth=data.get("scroll_depth"),
            metadata=data.get("metadata", {}),
        )
        db.add(event)
        await db.commit()
        return {"status": "tracked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track/conversion")
async def track_conversion(data: dict, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        website_id = data.get("website_id")
        conversion_type = data.get("conversion_type")
        session_id = data.get("session_id")
        if not all([website_id, conversion_type, session_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        conversion = Conversion(
            website_id=website_id,
            conversion_type=conversion_type,
            conversion_value=data.get("conversion_value"),
            session_id=session_id,
            user_id=data.get("user_id"),
            source_page=data.get("source_page"),
            metadata=data.get("metadata", {}),
        )
        db.add(conversion)
        await db.commit()
        return {"status": "tracked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/businesses/{business_id}/analytics/summary")
async def get_analytics_summary(business_id: UUID, days: int = 30, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    website = await _get_website_for_user(business_id, current_user, db)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    views_result = await db.execute(select(func.count(AnalyticsEvent.id)).where(AnalyticsEvent.website_id == website.id, AnalyticsEvent.event_type == EventType.PAGE_VIEW, AnalyticsEvent.created_at >= since))
    total_views = views_result.scalar() or 0
    sessions_result = await db.execute(select(func.count(func.distinct(AnalyticsEvent.session_id))).where(AnalyticsEvent.website_id == website.id, AnalyticsEvent.created_at >= since))
    unique_sessions = sessions_result.scalar() or 0
    conversions_result = await db.execute(select(func.count(Conversion.id)).where(Conversion.website_id == website.id, Conversion.created_at >= since))
    total_conversions = conversions_result.scalar() or 0
    value_result = await db.execute(select(func.sum(Conversion.conversion_value)).where(Conversion.website_id == website.id, Conversion.created_at >= since))
    total_value = value_result.scalar() or 0
    conversion_rate = (total_conversions / total_views * 100) if total_views > 0 else 0
    return {"period_days": days, "total_views": total_views, "unique_sessions": unique_sessions, "total_conversions": total_conversions, "conversion_rate": round(conversion_rate, 2), "total_conversion_value": round(total_value, 2), "avg_views_per_session": round(total_views / unique_sessions, 2) if unique_sessions > 0 else 0}

@router.get("/businesses/{business_id}/analytics/pages")
async def get_top_pages(business_id: UUID, days: int = 30, limit: int = 10, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    website = await _get_website_for_user(business_id, current_user, db)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(select(AnalyticsEvent.page_url, AnalyticsEvent.page_title, func.count(AnalyticsEvent.id).label("views"), func.count(func.distinct(AnalyticsEvent.session_id)).label("sessions")).where(AnalyticsEvent.website_id == website.id, AnalyticsEvent.event_type == EventType.PAGE_VIEW, AnalyticsEvent.created_at >= since).group_by(AnalyticsEvent.page_url, AnalyticsEvent.page_title).order_by(func.count(AnalyticsEvent.id).desc()).limit(limit))
    pages = [{"page_url": r[0], "page_title": r[1], "views": r[2], "sessions": r[3]} for r in result.fetchall()]
    return {"pages": pages}

@router.get("/businesses/{business_id}/analytics/conversions")
async def get_conversions(business_id: UUID, days: int = 30, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    website = await _get_website_for_user(business_id, current_user, db)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(select(Conversion.conversion_type, func.count(Conversion.id).label("count"), func.sum(Conversion.conversion_value).label("total_value")).where(Conversion.website_id == website.id, Conversion.created_at >= since).group_by(Conversion.conversion_type).order_by(func.count(Conversion.id).desc()))
    conversions = [{"type": r[0], "count": r[1], "total_value": round(r[2] or 0, 2), "avg_value": round((r[2] or 0) / r[1], 2) if r[1] > 0 else 0} for r in result.fetchall()]
    return {"conversions": conversions}
