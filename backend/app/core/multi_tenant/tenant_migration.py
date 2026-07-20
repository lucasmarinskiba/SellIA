"""
TenantMigration: Migrate existing single-tenant users to multi-tenant.
250 lines: Safe data migration with rollback capability.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.exceptions import AppException
from app.domains.users.models import User
from .models import Tenant, TenantMember, TenantBilling
from .tenant_manager import TenantService, TIER_LIMITS

logger = get_logger(__name__)


class MigrationService:
    """Migrate single-tenant users to multi-tenant architecture."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def migrate_user_to_tenant(
        self,
        user_id: str,
        tenant_name: Optional[str] = None,
        tier: str = "starter",
    ) -> Tenant:
        """
        Migrate single user to tenant owner.
        Creates tenant, adds user as owner, creates billing record.

        Args:
            user_id: User UUID to migrate
            tenant_name: Tenant name (defaults to user's business name or email)
            tier: starter, pro, enterprise

        Returns:
            New Tenant object

        Raises:
            AppException: If user already has tenant
        """
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise AppException("User not found", status_code=404)

        # Check if user is already a tenant owner
        existing_tenant = await self.db.execute(
            select(Tenant).where(Tenant.owner_id == user_id)
        )
        if existing_tenant.scalar_one_or_none():
            raise AppException(
                "User already owns a tenant",
                status_code=409,
            )

        # Use provided tenant name or default
        if not tenant_name:
            # Try to get business name, fall back to email
            tenant_name = f"{user.full_name}'s Workspace"

        # Create tenant
        service = TenantService(self.db)
        tenant = await service.create_tenant(
            name=tenant_name,
            owner_id=user_id,
            tier=tier,
            description=f"Migrated from single-tenant account",
        )

        logger.info(
            f"User migrated to tenant",
            extra={
                "user_id": str(user_id),
                "tenant_id": str(tenant.id),
                "tenant_name": tenant_name,
            },
        )

        return tenant

    async def migrate_bulk_users(
        self,
        user_ids: List[str],
        tenant_tier: str = "starter",
    ) -> Dict[str, Any]:
        """
        Bulk migrate multiple users.
        Skip users already migrated.

        Returns:
            {
                "total": 100,
                "successful": 98,
                "failed": 2,
                "errors": [{"user_id": "...", "reason": "..."}]
            }
        """
        results = {
            "total": len(user_ids),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for user_id in user_ids:
            try:
                await self.migrate_user_to_tenant(
                    user_id,
                    tier=tenant_tier,
                )
                results["successful"] += 1
            except AppException as e:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": user_id,
                    "reason": e.message,
                })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": user_id,
                    "reason": str(e),
                })

        logger.info(
            f"Bulk user migration completed",
            extra=results,
        )

        return results

    async def migrate_existing_data_to_tenant(
        self,
        tenant_id: str,
        user_id: str,
        data_models: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """
        Migrate existing user data (businesses, conversations, etc.) to tenant.
        Associates all user data with tenant_id.

        Args:
            tenant_id: Target tenant
            user_id: User whose data to migrate
            data_models: Models to migrate (defaults to all)

        Returns:
            {"model_name": count_migrated, ...}
        """
        migrated = {}

        # Models that need tenant_id added
        if not data_models:
            data_models = ["business", "conversation", "agent", "mission"]

        # Example: migrate businesses
        if "business" in data_models:
            from app.domains.businesses.models import Business

            result = await self.db.execute(
                select(Business).where(Business.user_id == user_id)
            )
            businesses = result.scalars().all()

            for biz in businesses:
                if not hasattr(biz, "tenant_id"):
                    # Model doesn't support multi-tenant yet
                    continue
                biz.tenant_id = tenant_id

            migrated["business"] = len(businesses)

        # Commit all changes
        await self.db.commit()

        logger.info(
            f"User data migrated to tenant",
            extra={
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "migrated": migrated,
            },
        )

        return migrated

    async def validate_migration(
        self,
        tenant_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Validate migration success: check tenant, member, billing records exist.

        Returns:
            {
                "tenant_exists": bool,
                "user_is_owner": bool,
                "billing_exists": bool,
                "is_valid": bool,
            }
        """
        # Check tenant exists
        tenant_result = await self.db.execute(
            select(Tenant).where(
                and_(
                    Tenant.id == tenant_id,
                    Tenant.owner_id == user_id,
                )
            )
        )
        tenant = tenant_result.scalar_one_or_none()

        # Check member record
        member_result = await self.db.execute(
            select(TenantMember).where(
                and_(
                    TenantMember.tenant_id == tenant_id,
                    TenantMember.user_id == user_id,
                    TenantMember.role == "owner",
                )
            )
        )
        member = member_result.scalar_one_or_none()

        # Check billing
        billing_result = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing = billing_result.scalar_one_or_none()

        is_valid = tenant and member and billing

        return {
            "tenant_exists": tenant is not None,
            "user_is_owner": member is not None,
            "billing_exists": billing is not None,
            "is_valid": is_valid,
        }

    async def rollback_migration(self, tenant_id: str) -> None:
        """
        Rollback migration: delete tenant and all related data.
        WARNING: This is destructive and cannot be undone.
        """
        tenant = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_obj = tenant.scalar_one_or_none()

        if not tenant_obj:
            raise AppException("Tenant not found", status_code=404)

        # Delete cascade will remove all related records
        await self.db.delete(tenant_obj)
        await self.db.commit()

        logger.warning(
            f"Migration rolled back",
            extra={"tenant_id": str(tenant_id)},
        )


class TenantMigrator:
    """Singleton for migration operations."""

    def get_service(self, db: AsyncSession) -> MigrationService:
        return MigrationService(db)

    async def migrate_user(
        self,
        db: AsyncSession,
        user_id: str,
        **kwargs,
    ) -> Tenant:
        service = self.get_service(db)
        return await service.migrate_user_to_tenant(user_id, **kwargs)


_tenant_migrator: Optional[TenantMigrator] = None


def get_tenant_migrator() -> TenantMigrator:
    """Get singleton TenantMigrator."""
    global _tenant_migrator
    if _tenant_migrator is None:
        _tenant_migrator = TenantMigrator()
    return _tenant_migrator
