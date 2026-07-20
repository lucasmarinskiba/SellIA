"""RBAC (Role-Based Access Control) for SellIA.

Simple permission system: roles have permissions, users have roles per business.
"""

import uuid
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.security.models import BusinessUserRole, RolePermission


# Default permissions matrix
DEFAULT_PERMISSIONS = [
    # (role, resource, action)
    ("owner", "*", "admin"),
    ("admin", "*", "write"),
    ("admin", "*", "read"),
    ("marketing", "conversations", "read"),
    ("marketing", "conversations", "write"),
    ("marketing", "objectives", "read"),
    ("marketing", "objectives", "write"),
    ("marketing", "retention", "read"),
    ("marketing", "retention", "write"),
    ("marketing", "analytics", "read"),
    ("marketing", "bi", "read"),
    ("sales", "conversations", "read"),
    ("sales", "conversations", "write"),
    ("sales", "orders", "read"),
    ("sales", "orders", "write"),
    ("sales", "crm", "read"),
    ("sales", "crm", "write"),
    ("sales", "objectives", "read"),
    ("support", "conversations", "read"),
    ("support", "conversations", "write"),
    ("support", "support", "read"),
    ("support", "support", "write"),
    ("viewer", "*", "read"),
]


async def seed_default_permissions(db: AsyncSession):
    """Seed default role permissions if table is empty."""
    result = await db.execute(select(RolePermission))
    if result.scalars().first():
        return
    for role, resource, action in DEFAULT_PERMISSIONS:
        db.add(RolePermission(role=role, resource=resource, action=action))
    await db.commit()


async def check_permission(
    db: AsyncSession,
    user_id: uuid.UUID,
    business_id: uuid.UUID,
    resource: str,
    action: str,
) -> bool:
    """Check if user has permission on resource for business."""
    # Superusers bypass
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user and user.is_superuser:
        return True

    # Get user's role in this business
    result = await db.execute(
        select(BusinessUserRole).where(
            BusinessUserRole.user_id == user_id,
            BusinessUserRole.business_id == business_id,
            BusinessUserRole.is_active == True,
        )
    )
    bur = result.scalar_one_or_none()
    if not bur:
        # If no role assigned, check if user owns the business
        from app.domains.businesses.models import Business
        result = await db.execute(
            select(Business).where(Business.id == business_id, Business.user_id == user_id)
        )
        if result.scalar_one_or_none():
            return True
        return False

    role = bur.role

    # Check wildcard permissions
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role == role,
            RolePermission.resource.in_([resource, "*"]),
            RolePermission.action.in_([action, "admin"]),
        )
    )
    if result.scalars().first():
        return True

    return False


def require_permission(resource: str, action: str = "read"):
    """Decorator to require a permission on an endpoint."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            business_id: uuid.UUID,
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
            *args,
            **kwargs,
        ):
            has = await check_permission(db, current_user.id, business_id, resource, action)
            if not has:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No tienes permiso para {action} en {resource}.",
                )
            return await func(business_id=business_id, db=db, current_user=current_user, *args, **kwargs)
        return wrapper
    return decorator
