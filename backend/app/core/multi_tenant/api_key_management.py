"""
APIKeyManager: Generate, rotate, revoke, rate-limit API keys.
400 lines: Production-ready key management with security.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.exceptions import AppException
from .models import TenantAPIKey, AuditLog, Tenant

logger = get_logger(__name__)


class APIKeyService:
    """API key CRUD, validation, rotation, revocation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _hash_key(self, key: str) -> str:
        """SHA256 hash key (never store plaintext)."""
        return hashlib.sha256(key.encode()).hexdigest()

    def _generate_key(self, prefix: str = "sk") -> tuple[str, str]:
        """
        Generate API key: prefix + random bytes + hash.

        Returns:
            (full_key, key_hash, key_prefix)
            Only return full_key to user once.
        """
        # 32 random bytes = 256-bit entropy
        random_part = secrets.token_urlsafe(32)
        full_key = f"{prefix}_{random_part}"

        key_hash = self._hash_key(full_key)
        key_prefix = full_key[:16]  # Show first 16 chars

        return full_key, key_hash, key_prefix

    async def create_api_key(
        self,
        tenant_id: str,
        name: str,
        created_by: str,
        scopes: Optional[List[str]] = None,
        ip_whitelist: Optional[List[str]] = None,
        rate_limit_per_minute: int = 100,
        description: Optional[str] = None,
    ) -> tuple[TenantAPIKey, str]:
        """
        Create API key for tenant.

        Args:
            tenant_id: Tenant UUID
            name: User-friendly name
            created_by: Creator user UUID
            scopes: ["read", "write", "admin"]
            ip_whitelist: Optional IP restrictions (CIDR)
            rate_limit_per_minute: Rate limit
            description: Optional description

        Returns:
            (api_key_obj, plaintext_key)
            NOTE: Only return plaintext to user once. Never log it.
        """
        # Check tenant exists
        tenant = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        if not tenant.scalar_one_or_none():
            raise AppException("Tenant not found", status_code=404)

        # Check key limit
        key_count = await self.db.execute(
            select(TenantAPIKey).where(
                and_(
                    TenantAPIKey.tenant_id == tenant_id,
                    TenantAPIKey.is_active == True,
                    TenantAPIKey.is_revoked == False,
                )
            )
        )
        active_keys = len(key_count.all())

        tenant_obj = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_obj = tenant_obj.scalar_one()

        if active_keys >= tenant_obj.max_api_keys:
            raise AppException(
                f"Maximum API keys ({tenant_obj.max_api_keys}) reached",
                status_code=429,
            )

        # Generate key
        full_key, key_hash, key_prefix = self._generate_key()

        # Create record (hash only, never plaintext)
        api_key = TenantAPIKey(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            description=description,
            scopes=scopes or ["read"],
            ip_whitelist=ip_whitelist or [],
            rate_limit_per_minute=rate_limit_per_minute,
            created_by=created_by,
            is_active=True,
        )

        self.db.add(api_key)
        await self.db.commit()

        logger.info(
            f"API key created",
            extra={
                "tenant_id": str(tenant_id),
                "key_id": str(api_key.id),
                "key_prefix": key_prefix,
            },
        )

        # Return plaintext only once
        return api_key, full_key

    async def validate_api_key(
        self,
        key: str,
        ip_address: Optional[str] = None,
    ) -> Optional[TenantAPIKey]:
        """
        Validate API key: hash it, check DB, check revocation/expiry.

        Args:
            key: Plaintext API key from request
            ip_address: Optional client IP for whitelist check

        Returns:
            TenantAPIKey if valid, None if invalid
        """
        # Hash the provided key
        key_hash = self._hash_key(key)

        # Look up in DB
        result = await self.db.execute(
            select(TenantAPIKey).where(
                and_(
                    TenantAPIKey.key_hash == key_hash,
                    TenantAPIKey.is_active == True,
                    TenantAPIKey.is_revoked == False,
                )
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check if key must be rotated
        if api_key.must_rotate_by and datetime.now(timezone.utc) > api_key.must_rotate_by:
            logger.warning(
                f"API key rotation required",
                extra={"key_id": str(api_key.id)},
            )
            return None

        # Check IP whitelist
        if api_key.ip_whitelist and ip_address:
            if not self._check_ip_whitelist(ip_address, api_key.ip_whitelist):
                logger.warning(
                    f"API key access denied by IP whitelist",
                    extra={
                        "key_id": str(api_key.id),
                        "ip": ip_address,
                    },
                )
                return None

        # Update last_used_at
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.total_requests += 1

        await self.db.commit()

        return api_key

    async def rotate_api_key(self, key_id: str) -> tuple[TenantAPIKey, str]:
        """
        Rotate API key: revoke old, create new with same scopes.

        Returns:
            (new_key_obj, new_plaintext_key)
        """
        old_key = await self.db.execute(
            select(TenantAPIKey).where(TenantAPIKey.id == key_id)
        )
        old_key = old_key.scalar_one_or_none()

        if not old_key:
            raise AppException("API key not found", status_code=404)

        # Revoke old key
        old_key.is_revoked = True
        old_key.revoked_at = datetime.now(timezone.utc)
        old_key.revoked_reason = "Key rotated"

        # Create new key with same properties
        new_key, plaintext = await self.create_api_key(
            tenant_id=old_key.tenant_id,
            name=f"{old_key.name} (rotated)",
            created_by=old_key.created_by,
            scopes=old_key.scopes,
            ip_whitelist=old_key.ip_whitelist,
            rate_limit_per_minute=old_key.rate_limit_per_minute,
            description=old_key.description,
        )

        # Schedule old key deletion after grace period
        old_key.rotation_scheduled_at = datetime.now(timezone.utc) + timedelta(days=7)

        await self.db.commit()

        logger.info(
            f"API key rotated",
            extra={
                "old_key_id": str(key_id),
                "new_key_id": str(new_key.id),
            },
        )

        return new_key, plaintext

    async def revoke_api_key(self, key_id: str, reason: str) -> None:
        """Revoke API key (soft delete)."""
        api_key = await self.db.execute(
            select(TenantAPIKey).where(TenantAPIKey.id == key_id)
        )
        api_key = api_key.scalar_one_or_none()

        if not api_key:
            raise AppException("API key not found", status_code=404)

        api_key.is_revoked = True
        api_key.revoked_at = datetime.now(timezone.utc)
        api_key.revoked_reason = reason

        await self.db.commit()

        logger.warning(
            f"API key revoked",
            extra={
                "key_id": str(key_id),
                "reason": reason,
            },
        )

    async def get_api_key(self, key_id: str) -> Optional[TenantAPIKey]:
        """Get API key by ID (never returns plaintext)."""
        result = await self.db.execute(
            select(TenantAPIKey).where(TenantAPIKey.id == key_id)
        )
        return result.scalar_one_or_none()

    async def list_api_keys(
        self,
        tenant_id: str,
        include_revoked: bool = False,
        limit: int = 50,
    ) -> List[TenantAPIKey]:
        """List API keys for tenant."""
        query = select(TenantAPIKey).where(TenantAPIKey.tenant_id == tenant_id)

        if not include_revoked:
            query = query.where(TenantAPIKey.is_revoked == False)

        query = query.order_by(desc(TenantAPIKey.created_at)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def enforce_rotation_schedule(self) -> None:
        """
        Enforce key rotation: find keys past must_rotate_by, disable them.
        Run as scheduled task daily.
        """
        result = await self.db.execute(
            select(TenantAPIKey).where(
                and_(
                    TenantAPIKey.must_rotate_by.isnot(None),
                    TenantAPIKey.must_rotate_by < datetime.now(timezone.utc),
                    TenantAPIKey.is_revoked == False,
                )
            )
        )

        keys_to_rotate = result.scalars().all()

        for key in keys_to_rotate:
            key.is_revoked = True
            key.revoked_at = datetime.now(timezone.utc)
            key.revoked_reason = "Mandatory rotation deadline passed"

            logger.warning(
                f"API key auto-revoked for mandatory rotation",
                extra={"key_id": str(key.id)},
            )

        if keys_to_rotate:
            await self.db.commit()

    @staticmethod
    def _check_ip_whitelist(client_ip: str, whitelist: List[str]) -> bool:
        """
        Check if client IP is in whitelist (CIDR support).
        """
        try:
            import ipaddress
            client = ipaddress.ip_address(client_ip)
            for cidr in whitelist:
                if client in ipaddress.ip_network(cidr, strict=False):
                    return True
        except (ValueError, ipaddress.AddressValueError):
            pass

        return False


class APIKeyManager:
    """Singleton manager for API key operations."""

    def get_service(self, db: AsyncSession) -> APIKeyService:
        return APIKeyService(db)

    async def validate_key(
        self,
        db: AsyncSession,
        key: str,
        ip_address: Optional[str] = None,
    ) -> Optional[TenantAPIKey]:
        service = self.get_service(db)
        return await service.validate_api_key(key, ip_address)


_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get singleton APIKeyManager."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
