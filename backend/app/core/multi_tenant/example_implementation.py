"""
Real-world implementation example: Complete tenant endpoints.
Shows how to integrate multi-tenant into your FastAPI app.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from .tenant_manager import TenantService, TenantTier
from .tenant_isolation import TenantIsolation
from .tenant_context import (
    require_tenant_context,
    require_admin_access,
    require_owner_access,
    TenantContext,
)
from .api_key_management import APIKeyService
from .billing_integration import BillingService
from .audit_logging import AuditService, AuditAction, AuditStatus
from .models import Tenant, TenantMember, TenantAPIKey

router = APIRouter(prefix="/api/v1/tenants", tags=["multi-tenant"])


# ============================================================================
# Tenant Management
# ============================================================================

@router.post("")
async def create_tenant(
    name: str,
    description: str = None,
    tier: str = TenantTier.STARTER,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new tenant (organization).
    Current user becomes owner.
    """
    service = TenantService(db)

    try:
        tenant = await service.create_tenant(
            name=name,
            owner_id=str(current_user.id),
            description=description,
            tier=tier,
        )

        # Log creation
        audit = AuditService(db)
        await audit.log_action(
            tenant_id=str(tenant.id),
            action=AuditAction.TENANT_CREATED,
            resource_type="tenant",
            change_type="create",
            user_id=str(current_user.id),
            user_email=current_user.email,
            ip_address=None,  # Get from request headers
            status=AuditStatus.SUCCESS,
            new_values={
                "name": name,
                "tier": tier,
            },
        )

        return {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "tier": tenant.tier,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/my-tenants")
async def list_my_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tenants user belongs to."""
    service = TenantService(db)
    tenants = await service.list_user_tenants(str(current_user.id))

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "tier": t.tier,
            "members_count": len(t.members) if t.members else 0,
        }
        for t in tenants
    ]


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    tenant_context: TenantContext = Depends(require_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant details (members only)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Not your tenant")

    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "tier": tenant.tier,
        "max_users": tenant.max_users,
        "max_api_keys": tenant.max_api_keys,
        "members_count": len(tenant.members) if tenant.members else 0,
        "is_active": tenant.is_active,
        "is_paused": tenant.is_paused,
        "created_at": tenant.created_at.isoformat(),
    }


@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    name: str = None,
    description: str = None,
    tenant_context: TenantContext = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant settings (admin only)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    service = TenantService(db)
    update_data = {}

    if name:
        update_data["name"] = name
    if description:
        update_data["description"] = description

    tenant = await service.update_tenant(tenant_id, **update_data)

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
    }


@router.post("/{tenant_id}/upgrade")
async def upgrade_tier(
    tenant_id: str,
    new_tier: str,
    tenant_context: TenantContext = Depends(require_owner_access),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade tenant tier (owner only)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    service = TenantService(db)

    try:
        tenant = await service.upgrade_tier(tenant_id, new_tier)

        return {
            "tier": tenant.tier,
            "max_users": tenant.max_users,
            "max_api_keys": tenant.max_api_keys,
            "max_monthly_api_calls": tenant.max_monthly_api_calls,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Tenant Members (RBAC)
# ============================================================================

@router.get("/{tenant_id}/members")
async def list_members(
    tenant_id: str,
    tenant_context: TenantContext = Depends(require_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """List tenant members."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    # Query members
    from sqlalchemy import select
    result = await db.execute(
        select(TenantMember)
        .where(TenantMember.tenant_id == tenant_id)
        .where(TenantMember.is_active == True)
    )
    members = result.scalars().all()

    return [
        {
            "user_id": str(m.user_id),
            "email": m.user.email if m.user else "unknown",
            "role": m.role,
            "invited_at": m.invited_at.isoformat() if m.invited_at else None,
            "accepted_at": m.accepted_at.isoformat() if m.accepted_at else None,
        }
        for m in members
    ]


@router.post("/{tenant_id}/members")
async def invite_member(
    tenant_id: str,
    email: str,
    role: str = "member",
    tenant_context: TenantContext = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Invite user to tenant (admin only)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    from sqlalchemy import select

    # Find user by email
    user_result = await db.execute(
        select(User).where(User.email == email)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User {email} not found",
        )

    # Create membership
    member = TenantMember(
        tenant_id=tenant_id,
        user_id=user.id,
        role=role,
        invited_by=tenant_context.user_id,
    )

    db.add(member)
    await db.commit()

    # Log invitation
    audit = AuditService(db)
    await audit.log_action(
        tenant_id=tenant_id,
        action=AuditAction.USER_INVITED,
        resource_type="user",
        change_type="create",
        user_id=tenant_context.user_id,
        resource_id=str(user.id),
        status=AuditStatus.SUCCESS,
        details={"email": email, "role": role},
    )

    return {
        "user_id": str(user.id),
        "email": user.email,
        "role": role,
        "invited_at": member.invited_at.isoformat(),
    }


# ============================================================================
# API Keys
# ============================================================================

@router.post("/{tenant_id}/api-keys")
async def create_api_key(
    tenant_id: str,
    name: str,
    scopes: list = None,
    rate_limit_per_minute: int = 100,
    tenant_context: TenantContext = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Create API key (admin only)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    service = APIKeyService(db)

    try:
        api_key, plaintext = await service.create_api_key(
            tenant_id=tenant_id,
            name=name,
            created_by=tenant_context.user_id,
            scopes=scopes or ["read"],
            rate_limit_per_minute=rate_limit_per_minute,
        )

        # Log creation
        audit = AuditService(db)
        await audit.log_action(
            tenant_id=tenant_id,
            action=AuditAction.API_KEY_CREATED,
            resource_type="api_key",
            change_type="create",
            user_id=tenant_context.user_id,
            resource_id=str(api_key.id),
            status=AuditStatus.SUCCESS,
            details={"name": name, "scopes": scopes},
        )

        return {
            "id": str(api_key.id),
            "key": plaintext,  # Only returned once!
            "key_prefix": api_key.key_prefix,
            "name": name,
            "scopes": scopes,
            "created_at": api_key.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{tenant_id}/api-keys")
async def list_api_keys(
    tenant_id: str,
    tenant_context: TenantContext = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """List API keys (admin only)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    service = APIKeyService(db)
    keys = await service.list_api_keys(tenant_id)

    return [
        {
            "id": str(k.id),
            "key_prefix": k.key_prefix,
            "name": k.name,
            "scopes": k.scopes,
            "is_active": k.is_active,
            "is_revoked": k.is_revoked,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@router.post("/{tenant_id}/api-keys/{key_id}/rotate")
async def rotate_api_key(
    tenant_id: str,
    key_id: str,
    tenant_context: TenantContext = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Rotate API key (revoke old, create new)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    service = APIKeyService(db)

    try:
        new_key, plaintext = await service.rotate_api_key(key_id)

        # Log rotation
        audit = AuditService(db)
        await audit.log_action(
            tenant_id=tenant_id,
            action=AuditAction.API_KEY_ROTATED,
            resource_type="api_key",
            change_type="update",
            user_id=tenant_context.user_id,
            resource_id=key_id,
            status=AuditStatus.SUCCESS,
        )

        return {
            "new_key_id": str(new_key.id),
            "key": plaintext,
            "key_prefix": new_key.key_prefix,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# Billing
# ============================================================================

@router.get("/{tenant_id}/billing/usage")
async def get_billing_usage(
    tenant_id: str,
    tenant_context: TenantContext = Depends(require_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get current billing period usage."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    service = BillingService(db)
    stats = await service.get_usage_stats(tenant_id)

    return stats


# ============================================================================
# Audit Logs
# ============================================================================

@router.get("/{tenant_id}/audit-logs")
async def get_audit_logs(
    tenant_id: str,
    action: str = None,
    days_back: int = 30,
    limit: int = 100,
    tenant_context: TenantContext = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs (admin only)."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)

    service = AuditService(db)
    logs, count = await service.list_tenant_audit_logs(
        tenant_id=tenant_id,
        action_filter=action,
        days_back=days_back,
        limit=limit,
    )

    return {
        "total": count,
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "action": log.action,
                "user_email": log.user_email,
                "ip_address": log.ip_address,
                "status": log.status,
                "reason": log.reason,
            }
            for log in logs
        ],
    }


# Dependency for use in other routers
def inject_tenant_id_from_context(
    tenant_context: TenantContext = Depends(require_tenant_context),
) -> str:
    """Extract tenant_id from context for use in other endpoints."""
    return tenant_context.tenant_id
