"""
Example: How to integrate multi-tenant system into FastAPI app.
Copy these patterns into your app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.multi_tenant import (
    TenantContextMiddleware,
    TenantIsolation,
    get_tenant_context,
)
from app.core.multi_tenant.example_implementation import router as tenant_router


# ============================================================================
# Application Setup
# ============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application with multi-tenant support."""

    app = FastAPI(
        title="Multi-Tenant API",
        description="Complete tenant isolation, billing, and compliance",
        version="1.0.0",
    )

    # ========================================================================
    # 1. CORS Middleware
    # ========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "X-Tenant-ID"],  # Allow tenant header
    )

    # ========================================================================
    # 2. MULTI-TENANT MIDDLEWARE (Critical!)
    # ========================================================================
    # Must be added AFTER CORS but BEFORE other middlewares
    app.add_middleware(
        TenantContextMiddleware,
        get_db_func=get_db,
    )

    # What this does:
    # - Extracts tenant_id from request (path param, header, or query)
    # - Validates user is member of tenant
    # - Injects TenantContext into request.state
    # - All subsequent DB queries auto-filtered by tenant_id

    # ========================================================================
    # 3. Request/Response Hooks
    # ========================================================================

    @app.middleware("http")
    async def add_tenant_headers(request, call_next):
        """Add tenant tracking headers to response."""
        response = await call_next(request)

        # Add tenant_id to response headers for debugging
        tenant_context = getattr(request.state, "tenant_context", None)
        if tenant_context:
            response.headers["X-Tenant-ID"] = tenant_context.tenant_id

        return response

    # ========================================================================
    # 4. Startup/Shutdown Events
    # ========================================================================

    @app.on_event("startup")
    async def startup_event():
        """Initialize multi-tenant system on startup."""
        print("✓ Multi-tenant system initialized")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        print("✓ Multi-tenant system shutdown")

    # ========================================================================
    # 5. Health Check Endpoint
    # ========================================================================

    @app.get("/health")
    async def health_check():
        """Health check (no tenant required)."""
        return {"status": "ok", "version": "1.0.0"}

    # ========================================================================
    # 6. Public Auth Endpoints (No Tenant Required)
    # ========================================================================

    # Include your existing auth router here
    # from app.api.v1 import auth
    # app.include_router(auth.router, prefix="/api/v1")

    # ========================================================================
    # 7. MULTI-TENANT ENDPOINTS (Tenant Required)
    # ========================================================================

    # Include tenant management endpoints
    app.include_router(
        tenant_router,
        prefix="/api/v1/tenants",
        tags=["multi-tenant"],
    )

    # Example of including other routers with tenant isolation:
    # from app.api.v1 import businesses, conversations
    # app.include_router(businesses.router)  # Already tenant-aware
    # app.include_router(conversations.router)  # Already tenant-aware

    # ========================================================================
    # 8. Error Handlers
    # ========================================================================

    from fastapi.responses import JSONResponse
    from app.core.exceptions import AppException

    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        """Handle application exceptions with proper status codes."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error_code": getattr(exc, "error_code", "APP_ERROR"),
            },
        )

    # ========================================================================
    # 9. Documentation & OpenAPI
    # ========================================================================

    # The OpenAPI schema automatically includes X-Tenant-ID header
    # Swagger UI will show it as a parameter

    return app


# ============================================================================
# Dependency Injection Patterns
# ============================================================================

async def get_current_tenant_id(
    tenant_context: "TenantContext" = Depends(get_tenant_context),
) -> str:
    """
    Dependency: Get current tenant_id from context.
    Use in any endpoint that needs the tenant.

    Usage:
        @app.get("/data")
        async def get_data(tenant_id: str = Depends(get_current_tenant_id)):
            # tenant_id is automatically injected
            pass
    """
    if not tenant_context:
        raise ValueError("Tenant context not found")
    return tenant_context.tenant_id


async def get_current_tenant_isolation(
    db: AsyncSession = Depends(get_db),
) -> TenantIsolation:
    """
    Dependency: Get tenant isolation service.
    Use for advanced isolation operations.
    """
    return TenantIsolation(db)


# ============================================================================
# Example Endpoint Integration
# ============================================================================

def add_multi_tenant_endpoints(app: FastAPI):
    """
    Example: Add multi-tenant-aware endpoints to existing routers.
    Shows how to modify your routers to support multi-tenancy.
    """

    from fastapi import APIRouter, Depends, HTTPException
    from app.core.multi_tenant import require_tenant_context, TenantContext
    from app.core.database import get_db

    router = APIRouter(prefix="/api/v1", tags=["example"])

    # ====================================================================
    # Pattern 1: Endpoint Requiring Tenant Context
    # ====================================================================

    @router.get("/tenants/{tenant_id}/data")
    async def get_tenant_data(
        tenant_id: str,
        tenant_context: TenantContext = Depends(require_tenant_context),
        db: AsyncSession = Depends(get_db),
    ):
        """
        Get data for current tenant.

        Security:
        - Middleware validates user is member of tenant_id
        - All DB queries auto-filtered by tenant_id
        - Returns only user's tenant data
        """
        if tenant_context.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Not your tenant")

        # Your data retrieval logic here
        # DB queries are auto-isolated by middleware
        return {"tenant_id": tenant_id, "data": []}

    # ====================================================================
    # Pattern 2: Admin-Only Endpoint
    # ====================================================================

    from app.core.multi_tenant import require_admin_access

    @router.post("/tenants/{tenant_id}/settings")
    async def update_tenant_settings(
        tenant_id: str,
        settings: dict,
        tenant_context: TenantContext = Depends(require_admin_access),
    ):
        """
        Update tenant settings (admin only).
        Middleware automatically checks role == "admin" or "owner".
        """
        if tenant_context.tenant_id != tenant_id:
            raise HTTPException(status_code=403)

        # Only admin can execute this
        return {"status": "updated"}

    # ====================================================================
    # Pattern 3: API Key Authenticated Endpoint
    # ====================================================================

    @router.post("/api/query")
    async def query_endpoint(
        query: dict,
        request: "Request",
        db: AsyncSession = Depends(get_db),
    ):
        """
        API endpoint: Accept either Bearer token or API key.
        Shows how to support service-to-service calls.
        """
        from app.core.multi_tenant import APIKeyManager

        # Extract key from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            # Regular token (user)
            key = auth_header[7:]
        else:
            # API key
            key = request.headers.get("X-API-Key")

        if not key:
            raise HTTPException(401, detail="Missing credentials")

        # Validate API key
        manager = APIKeyManager()
        api_key = await manager.validate_key(
            db=db,
            key=key,
            ip_address=request.client.host,
        )

        if not api_key:
            raise HTTPException(401, detail="Invalid API key")

        # Request is now validated and tenant is known
        # tenant_id = api_key.tenant_id
        return {"status": "ok"}

    app.include_router(router)


# ============================================================================
# Scheduled Tasks Setup (Celery)
# ============================================================================

def setup_celery_tasks():
    """
    Configure Celery beat tasks for multi-tenant maintenance.
    Add to your celery app configuration.
    """

    from celery.schedules import crontab

    # In your celery config or celery.py:
    CELERY_BEAT_SCHEDULE = {
        # Key rotation: enforce 90-day rotation deadline
        "enforce-api-key-rotation": {
            "task": "app.core.multi_tenant.tasks.enforce_key_rotation",
            "schedule": crontab(hour=0, minute=0),  # Daily at midnight
            "options": {"expires": 3600},  # 1 hour timeout
        },

        # Billing: finalize monthly billing cycle
        "finalize-billing-cycles": {
            "task": "app.core.multi_tenant.tasks.finalize_billing_cycles",
            "schedule": crontab(day_of_month=1, hour=0, minute=0),  # 1st of month
            "options": {"expires": 86400},  # 24 hour timeout
        },

        # Audit cleanup: delete logs older than 365 days
        "cleanup-old-audit-logs": {
            "task": "app.core.multi_tenant.tasks.cleanup_audit_logs",
            "schedule": crontab(day_of_week=0, hour=2, minute=0),  # Weekly, Sunday 2 AM
            "options": {"expires": 86400},
        },

        # Usage sync: sync usage from cache to DB hourly
        "sync-usage-metrics": {
            "task": "app.core.multi_tenant.tasks.sync_usage_metrics",
            "schedule": crontab(minute=0),  # Every hour
            "options": {"expires": 3600},
        },
    }

    return CELERY_BEAT_SCHEDULE


# ============================================================================
# Testing Setup
# ============================================================================

async def get_test_app() -> FastAPI:
    """
    Get test FastAPI instance with multi-tenant support.
    Use in pytest fixtures.
    """
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    # In-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Import all models to ensure they're registered
    from app.core.database import Base
    from app.core.multi_tenant.models import (
        Tenant, TenantMember, TenantAPIKey, TenantBilling, AuditLog
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

    # Override get_db
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    return app


# ============================================================================
# Quick Start
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    app = create_app()

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Multi-Tenant System — RUNNING                        ║
    ║                                                              ║
    ║  API Docs:     http://localhost:8000/docs                  ║
    ║  ReDoc:        http://localhost:8000/redoc                 ║
    ║  Health:       http://localhost:8000/health                ║
    ║                                                              ║
    ║  Tenant Header: X-Tenant-ID: {tenant-uuid}                ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
