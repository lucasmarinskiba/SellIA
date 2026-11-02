"""
Analytics & Monitoring API v1 — Phase 5

These endpoints used to answer with fixed numbers (a traffic count, a funnel, an A/B test)
to every caller. Nothing behind them is connected yet, so they answer
501 with an explicit message instead of inventing data. The routes stay mounted so the
frontend gets that answer, not a 404. Each one comes back when a real source exists
(Google Search Console, the page-view tracker, the CRM).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any

router = APIRouter(tags=["analytics"])


def _not_connected(feature: str) -> HTTPException:
    return HTTPException(
        status_code=501,
        detail=f"{feature}: todavía no hay una fuente de datos conectada",
    )


@router.post("/track-event")
async def track_event(
    event_name: str,
    user_id: Optional[str] = None,
    page: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Track user event. Not stored anywhere yet, so it says so instead of reporting success."""
    raise _not_connected("Registro de eventos")


@router.get("/funnel/conversion")
async def get_conversion_funnel(
    funnel_name: str = Query("default", description="Funnel: default|premium|testimonials"),
    days: int = Query(7, ge=1, le=90),
) -> Dict[str, Any]:
    """Conversion funnel. Not connected yet."""
    raise _not_connected("Embudo de conversión")


@router.get("/ab-test/active")
async def get_active_ab_tests() -> Dict[str, Any]:
    """Active A/B tests. Not connected yet."""
    raise _not_connected("Tests A/B")


@router.post("/ab-test/create")
async def create_ab_test(
    test_name: str,
    control_url: str,
    variant_url: str,
    traffic_split: int = 50,
) -> Dict[str, Any]:
    """Create an A/B test. Not connected yet, so nothing is created."""
    raise _not_connected("Tests A/B")


@router.get("/anomalies/seo")
async def get_seo_anomalies() -> Dict[str, Any]:
    """SEO anomalies. Not connected yet."""
    raise _not_connected("Anomalías SEO")


@router.get("/performance/core-web-vitals")
async def get_core_web_vitals() -> Dict[str, Any]:
    """Core Web Vitals. Needs real-user measurements; not connected yet."""
    raise _not_connected("Core Web Vitals")


@router.get("/personalization/user-segment")
async def get_user_segment(user_id: str) -> Dict[str, Any]:
    """Personalization score. Not connected yet."""
    raise _not_connected("Personalización")


@router.get("/dashboard/seo-metrics")
async def get_seo_dashboard() -> Dict[str, Any]:
    """SEO metrics. Needs Google Search Console; not connected yet."""
    raise _not_connected("Métricas SEO (Google Search Console)")


@router.get("/dashboard/marketing-metrics")
async def get_marketing_dashboard() -> Dict[str, Any]:
    """Marketing metrics. Not connected yet."""
    raise _not_connected("Métricas de marketing")
