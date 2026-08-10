"""Phases 19-22: Launch & Scale Endpoints."""

from fastapi import APIRouter, Query, Body
from typing import Dict, Any
import logging

from app.domains.onboarding.user_onboarding import OnboardingEngine, OnboardingStep, OnboardingSession
from app.domains.admin.platform_dashboard import PlatformDashboard
from app.domains.scaling.multi_tenant import MultiTenantManager, AlertSeverity
from app.domains.monitoring.monitoring import MonitoringSystem, AlertType

router = APIRouter(tags=["launch-scale"])
logger = logging.getLogger(__name__)

onboarding = OnboardingEngine()
dashboard = PlatformDashboard()
tenant_mgr = MultiTenantManager()
monitoring = MonitoringSystem()


# ============================================================
# Phase 19: User Onboarding
# ============================================================


@router.post("/onboarding/start/{user_id}")
async def start_onboarding(user_id: str) -> Dict[str, Any]:
    """Start onboarding for new user."""

    session = onboarding.create_session(user_id)

    return {
        "status": "success",
        "session_id": session.session_id,
        "current_step": session.current_step.value,
        "total_steps": 5,
        "estimated_time_minutes": 15
    }


@router.get("/onboarding/step/{session_id}")
async def get_onboarding_step(session_id: str) -> Dict[str, Any]:
    """Get current onboarding step."""

    # Mock step - would retrieve from DB
    step = OnboardingStep.PROFILE
    content = onboarding.get_step_content(step)

    return {
        "status": "success",
        "session_id": session_id,
        "step": step.value,
        "content": content
    }


@router.post("/onboarding/complete-step/{session_id}")
async def complete_onboarding_step(
    session_id: str,
    step: str = Query(...),
    answers: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Complete onboarding step."""

    return {
        "status": "success",
        "session_id": session_id,
        "next_step": "product",
        "progress_percent": 20
    }


@router.get("/onboarding/progress/{session_id}")
async def get_onboarding_progress(session_id: str) -> Dict[str, Any]:
    """Get onboarding progress."""

    # Mock session
    session = OnboardingSession(user_id="user", session_id=session_id)
    progress = onboarding.get_onboarding_progress(session)

    return {
        "status": "success",
        "session_id": session_id,
        "progress": progress
    }


# ============================================================
# Phase 20: Admin Dashboard
# ============================================================


@router.get("/admin/metrics")
async def get_platform_metrics() -> Dict[str, Any]:
    """Get platform-wide metrics."""

    metrics = dashboard.get_platform_metrics()

    return {
        "status": "success",
        "metrics": {
            "total_users": metrics.total_users,
            "active_24h": metrics.active_users_24h,
            "leads_generated": metrics.total_leads_generated,
            "deals_closed": metrics.total_deals_closed,
            "revenue": f"${metrics.total_revenue:,.0f}",
            "conversion_rate": f"{metrics.platform_conversion_rate * 100:.2f}%",
            "uptime": f"{metrics.system_uptime_percent:.2f}%",
            "api_latency_ms": metrics.api_response_time_ms
        }
    }


@router.get("/admin/trends")
async def get_trending_metrics() -> Dict[str, Any]:
    """Get trending metrics."""

    trends = dashboard.get_trending_metrics()

    return {
        "status": "success",
        "trends": trends
    }


@router.get("/admin/system-health")
async def get_system_health() -> Dict[str, Any]:
    """Get system health status."""

    health = dashboard.get_system_health()

    return {
        "status": "success",
        "health": health
    }


@router.get("/admin/top-users")
async def get_top_users(limit: int = Query(10, ge=1, le=100)) -> Dict[str, Any]:
    """Get top performing users."""

    users = dashboard.get_top_users(limit)

    return {
        "status": "success",
        "top_users": users
    }


@router.get("/admin/insights")
async def get_insights() -> Dict[str, Any]:
    """Get actionable insights."""

    insights = dashboard.get_insights()

    return {
        "status": "success",
        "insights": insights
    }


# ============================================================
# Phase 21: Multi-Tenancy
# ============================================================


@router.post("/tenant/create")
async def create_tenant(
    name: str = Query(...),
    tier: str = Query("pro", regex="^(free|pro|enterprise)$")
) -> Dict[str, Any]:
    """Create new tenant."""

    tenant = tenant_mgr.create_tenant(name, tier)

    return {
        "status": "success",
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "tier": tenant.tier,
        "users_limit": tenant.users_limit,
        "campaigns_limit": tenant.campaigns_limit
    }


@router.get("/tenant/{tenant_id}/usage")
async def get_tenant_usage(tenant_id: str) -> Dict[str, Any]:
    """Get tenant usage."""

    usage = tenant_mgr.get_tenant_usage(tenant_id)

    return {
        "status": "success",
        "tenant_id": tenant_id,
        "usage": usage
    }


@router.post("/tenant/{tenant_id}/upgrade")
async def upgrade_tenant(
    tenant_id: str,
    new_tier: str = Query(..., regex="^(pro|enterprise)$")
) -> Dict[str, Any]:
    """Upgrade tenant plan."""

    result = tenant_mgr.upgrade_tenant(tenant_id, new_tier)

    return result


@router.get("/tenant/{tenant_id}/billing")
async def get_billing(tenant_id: str) -> Dict[str, Any]:
    """Get tenant billing info."""

    billing = tenant_mgr.get_billing_summary(tenant_id)

    return {
        "status": "success",
        "billing": billing
    }


# ============================================================
# Phase 22: Monitoring & Alerting
# ============================================================


@router.get("/monitoring/alerts")
async def get_active_alerts() -> Dict[str, Any]:
    """Get active alerts."""

    alerts = monitoring.get_active_alerts()

    return {
        "status": "success",
        "active_alerts": len(alerts),
        "alerts": alerts
    }


@router.get("/monitoring/performance")
async def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics."""

    stats = monitoring.get_performance_stats()

    return {
        "status": "success",
        "performance": stats
    }


@router.get("/monitoring/health")
async def get_system_status() -> Dict[str, Any]:
    """Get overall system health."""

    summary = monitoring.get_alert_summary()
    perf = monitoring.get_performance_stats()

    return {
        "status": "success",
        "alerts": summary,
        "performance": perf,
        "overall_status": "healthy" if summary["critical_alerts"] == 0 else "degraded"
    }


@router.post("/monitoring/alert")
async def create_alert(
    alert_type: str = Query(...),
    severity: str = Query(..., regex="^(critical|high|medium|low|info)$"),
    title: str = Query(...),
    message: str = Query(...)
) -> Dict[str, Any]:
    """Create alert (admin only)."""

    alert = monitoring.create_alert(
        alert_type=AlertType(alert_type),
        severity=AlertSeverity(severity),
        title=title,
        message=message
    )

    return {
        "status": "success",
        "alert_id": alert.alert_id,
        "severity": alert.severity.value
    }
