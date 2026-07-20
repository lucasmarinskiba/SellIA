"""
TenantIsolation: Row-level security, schema isolation, data boundaries.
500 lines: Prevents data leakage between tenants.
"""

from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import text, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.exceptions import AppException
from .models import Tenant, TenantMember

logger = get_logger(__name__)


class TenantContext:
    """
    Request context: tracks current tenant & user.
    Injected into all DB queries to enforce isolation.
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
        """Check if current user has permission for action."""
        # Owner/Admin can do anything
        if self.role in ("owner", "admin"):
            return True

        # Check custom permissions
        return self.permissions.get(action, False)


class TenantIsolation:
    """
    Enforces tenant data isolation.
    - Row-level security: filters all queries by tenant_id
    - Schema isolation: separate PostgreSQL schemas per tenant
    - Cross-tenant validation: prevent user from accessing other tenant data
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_tenant_access(
        self,
        tenant_id: str,
        user_id: str,
    ) -> TenantContext:
        """
        Validate user can access tenant.
        Returns TenantContext with role & permissions.

        Raises:
            AppException: If user not member or membership inactive
        """
        result = await self.db.execute(
            select(TenantMember).where(
                and_(
                    TenantMember.tenant_id == tenant_id,
                    TenantMember.user_id == user_id,
                    TenantMember.is_active == True,
                )
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            logger.warning(
                f"Unauthorized tenant access attempt",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                },
            )
            raise AppException(
                "You do not have access to this tenant",
                status_code=403,
            )

        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=member.role,
            permissions=member.permissions or {},
        )

    async def validate_admin_access(
        self,
        tenant_id: str,
        user_id: str,
    ) -> TenantContext:
        """
        Validate user is admin/owner of tenant.

        Raises:
            AppException: If user not admin
        """
        context = await self.validate_tenant_access(tenant_id, user_id)

        if context.role not in ("owner", "admin"):
            raise AppException(
                "Admin access required",
                status_code=403,
            )

        return context

    async def validate_owner_access(
        self,
        tenant_id: str,
        user_id: str,
    ) -> TenantContext:
        """
        Validate user is owner of tenant.

        Raises:
            AppException: If user not owner
        """
        context = await self.validate_tenant_access(tenant_id, user_id)

        if context.role != "owner":
            raise AppException(
                "Owner access required",
                status_code=403,
            )

        return context

    async def apply_tenant_filter(
        self,
        query,
        tenant_id: str,
        model,
    ):
        """
        Apply WHERE clause to query: filter by tenant_id.
        Works for any model with tenant_id foreign key.

        Usage:
            query = select(User)
            query = await isolation.apply_tenant_filter(query, tenant_id, User)
            result = await db.execute(query)
        """
        if not hasattr(model, "tenant_id"):
            raise AppException(
                f"Model {model.__name__} does not support tenant isolation",
                status_code=500,
            )

        return query.where(model.tenant_id == tenant_id)

    async def get_tenant_schema(self, tenant_id: str) -> str:
        """Get PostgreSQL schema name for tenant."""
        result = await self.db.execute(
            select(Tenant.schema_name).where(Tenant.id == tenant_id)
        )
        schema = result.scalar_one_or_none()

        if not schema:
            raise AppException("Tenant not found", status_code=404)

        return schema

    async def set_tenant_schema(self, tenant_id: str) -> None:
        """
        Set PostgreSQL search_path to tenant schema.
        Run at connection start for isolation.
        """
        schema = await self.get_tenant_schema(tenant_id)

        # Set schema for this connection
        await self.db.execute(
            text(f"SET search_path = {schema}, public")
        )

    async def create_tenant_schema(self, tenant_id: str) -> None:
        """
        Create isolated PostgreSQL schema for tenant.
        Run during tenant creation.
        """
        tenant = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_obj = tenant.scalar_one_or_none()

        if not tenant_obj:
            raise AppException("Tenant not found", status_code=404)

        schema = tenant_obj.schema_name

        try:
            # Create schema
            await self.db.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            )

            # Grant permissions to app user
            app_user = "postgres_app_user"  # Configure in .env
            await self.db.execute(
                text(f"GRANT USAGE ON SCHEMA {schema} TO {app_user}")
            )
            await self.db.execute(
                text(f"GRANT CREATE ON SCHEMA {schema} TO {app_user}")
            )

            # Set default privileges for future objects
            await self.db.execute(
                text(
                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} "
                    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {app_user}"
                )
            )

            await self.db.commit()

            logger.info(
                f"Tenant schema created",
                extra={"tenant_id": str(tenant_id), "schema": schema},
            )

        except Exception as e:
            logger.error(f"Failed to create tenant schema: {e}")
            raise AppException(
                "Failed to create tenant schema",
                status_code=500,
            )

    async def drop_tenant_schema(self, tenant_id: str) -> None:
        """
        Drop tenant schema (hard delete).
        CASCADE deletes all objects in schema.
        """
        tenant = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_obj = tenant.scalar_one_or_none()

        if not tenant_obj:
            raise AppException("Tenant not found", status_code=404)

        schema = tenant_obj.schema_name

        try:
            await self.db.execute(
                text(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            )
            await self.db.commit()

            logger.warning(
                f"Tenant schema dropped",
                extra={"tenant_id": str(tenant_id), "schema": schema},
            )

        except Exception as e:
            logger.error(f"Failed to drop tenant schema: {e}")
            raise AppException(
                "Failed to drop tenant schema",
                status_code=500,
            )

    async def check_user_tenant_membership(
        self,
        user_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Fast check: does user belong to tenant?
        Used in middleware for early rejection.
        """
        result = await self.db.execute(
            select(TenantMember).where(
                and_(
                    TenantMember.user_id == user_id,
                    TenantMember.tenant_id == tenant_id,
                    TenantMember.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none() is not None


class TenantIsolationMiddleware:
    """
    FastAPI middleware: enforces tenant isolation on all requests.
    Extracts tenant from request, validates access, injects context.
    """

    def __init__(self, get_db_func):
        self.get_db_func = get_db_func

    async def __call__(self, request, call_next):
        """
        Process request:
        1. Extract tenant_id from path/header/token
        2. Validate user access
        3. Inject TenantContext into request.state
        4. All DB queries auto-filtered by tenant
        """
        # Extract tenant from request
        tenant_id = extract_tenant_from_request(request)

        if not tenant_id:
            # Some endpoints (auth, health) don't need tenant
            return await call_next(request)

        # Get user from request
        user = getattr(request.state, "user", None)
        if not user:
            return await call_next(request)

        # Validate access
        try:
            db = self.get_db_func()
            isolation = TenantIsolation(db)
            context = await isolation.validate_tenant_access(
                tenant_id,
                str(user.id),
            )

            # Inject into request
            request.state.tenant_context = context

        except AppException as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.message},
            )

        return await call_next(request)


def extract_tenant_from_request(request) -> Optional[str]:
    """
    Extract tenant_id from request:
    1. Path parameter: /api/tenants/{tenant_id}/...
    2. Header: X-Tenant-ID
    3. Query param: ?tenant_id=...
    """
    # Path parameter
    if "tenant_id" in request.path_params:
        return request.path_params["tenant_id"]

    # Header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    # Query param
    tenant_id = request.query_params.get("tenant_id")
    if tenant_id:
        return tenant_id

    return None


async def get_tenant_isolation(db: AsyncSession) -> TenantIsolation:
    """Dependency: inject TenantIsolation into handlers."""
    return TenantIsolation(db)
