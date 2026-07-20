"""
TenantContext: Request context middleware, dependency injection.
250 lines: Injects tenant info into every request for isolation.
"""

from typing import Optional
from contextvars import ContextVar

from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import get_logger
from app.core.exceptions import AppException
from .tenant_isolation import TenantIsolation

logger = get_logger(__name__)


# Context variable: stores tenant context for current request
_tenant_context: ContextVar[Optional["TenantContext"]] = ContextVar(
    "tenant_context", default=None
)


class TenantContext:
    """
    Current request context:
    - tenant_id: which tenant owns this request
    - user_id: which user made the request
    - role: owner/admin/member/viewer
    - permissions: custom permissions dict
    """

    def __init__(
        self,
        tenant_id: str,
        user_id: str,
        role: str = "member",
        permissions: Optional[dict] = None,
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
        self.permissions = permissions or {}

    def has_permission(self, action: str) -> bool:
        """Check if user has permission for action."""
        if self.role in ("owner", "admin"):
            return True
        return self.permissions.get(action, False)

    def is_owner(self) -> bool:
        """Is user the tenant owner?"""
        return self.role == "owner"

    def is_admin(self) -> bool:
        """Is user admin or owner?"""
        return self.role in ("owner", "admin")

    def __repr__(self) -> str:
        return f"TenantContext(tenant={self.tenant_id[:8]}..., user={self.user_id[:8]}..., role={self.role})"


async def get_tenant_context() -> Optional[TenantContext]:
    """
    Dependency: get current tenant context.
    Injected by middleware, available in all handlers.

    Usage:
        async def get_data(
            tenant_context: TenantContext = Depends(get_tenant_context)
        ):
            print(tenant_context.tenant_id)  # Current tenant
    """
    return _tenant_context.get()


async def require_tenant_context() -> TenantContext:
    """
    Dependency: require tenant context (fail if missing).

    Usage:
        async def protected_endpoint(
            tenant_context: TenantContext = Depends(require_tenant_context)
        ):
            # tenant_context guaranteed non-None here
    """
    context = _tenant_context.get()
    if not context:
        raise AppException(
            "Tenant context not found",
            status_code=500,
        )
    return context


async def require_admin_access() -> TenantContext:
    """
    Dependency: require admin/owner role.
    """
    context = await require_tenant_context()
    if not context.is_admin():
        raise AppException(
            "Admin access required",
            status_code=403,
        )
    return context


async def require_owner_access() -> TenantContext:
    """
    Dependency: require owner role.
    """
    context = await require_tenant_context()
    if not context.is_owner():
        raise AppException(
            "Owner access required",
            status_code=403,
        )
    return context


def extract_tenant_from_request(request: Request) -> Optional[str]:
    """
    Extract tenant_id from request:
    1. Path param: /api/tenants/{tenant_id}/...
    2. Header: X-Tenant-ID
    3. Query param: tenant_id=...

    Returns:
        tenant_id string or None
    """
    # 1. Path parameter
    if "tenant_id" in request.path_params:
        return request.path_params["tenant_id"]

    # 2. Custom header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    # 3. Query parameter
    tenant_id = request.query_params.get("tenant_id")
    if tenant_id:
        return tenant_id

    return None


class TenantContextMiddleware:
    """
    FastAPI middleware: populate tenant context on every request.

    Installation:
        from app.core.multi_tenant import TenantContextMiddleware
        app.add_middleware(TenantContextMiddleware, get_db_func=get_db)
    """

    def __init__(self, app, get_db_func):
        self.app = app
        self.get_db_func = get_db_func

    async def __call__(self, request: Request, call_next):
        """
        1. Extract tenant_id from request
        2. Load tenant membership from DB
        3. Validate access (security check)
        4. Inject context into request.state
        5. Continue request
        """
        # Extract tenant_id
        tenant_id = extract_tenant_from_request(request)

        if not tenant_id:
            # No tenant in request: continue (some endpoints don't need it)
            request.state.tenant_context = None
            response = await call_next(request)
            return response

        # Get user from request
        user = getattr(request.state, "user", None)
        if not user:
            # No authenticated user: deny access
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        # Validate tenant access
        try:
            db = self.get_db_func()
            isolation = TenantIsolation(db)

            # This validates membership and returns role/permissions
            context = await isolation.validate_tenant_access(
                str(tenant_id),
                str(user.id),
            )

            # Store in request state
            request.state.tenant_context = context

            # Also set in context var (for nested async calls)
            _tenant_context.set(context)

        except AppException as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.message},
            )
        except Exception as e:
            logger.error(f"Tenant context middleware error: {e}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        # Continue request
        response = await call_next(request)
        return response


async def inject_tenant_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[TenantContext]:
    """
    Dependency: load tenant context if needed.
    Used in endpoint handlers that explicitly need it.
    """
    tenant_id = extract_tenant_from_request(request)
    if not tenant_id:
        return None

    user = getattr(request.state, "user", None)
    if not user:
        raise AppException("Not authenticated", status_code=401)

    isolation = TenantIsolation(db)
    context = await isolation.validate_tenant_access(str(tenant_id), str(user.id))

    _tenant_context.set(context)
    return context
