"""Credential Service — Encrypt/decrypt and manage platform credentials."""

import uuid
import os
from typing import Optional, List
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SiteCredential, AuthType


class CredentialService:
    """Service for securely storing and retrieving platform credentials."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._fernet = self._get_fernet()

    @staticmethod
    def _get_fernet() -> Fernet:
        key = os.getenv("CREDENTIAL_MASTER_KEY")
        if not key:
            # Fallback: derive from secret key (not ideal for production but works for dev)
            from app.core.config import get_settings
            settings = get_settings()
            base = settings.SECRET_KEY[:32] if hasattr(settings, "SECRET_KEY") else "default-secret-key-32-chars-long!!"
            import base64
            key = base64.urlsafe_b64encode(base.encode()[:32].ljust(32, b"0"))
        return Fernet(key)

    def _encrypt(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return self._fernet.encrypt(value.encode()).decode()

    def _decrypt(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except Exception:
            return None

    async def store(
        self,
        user_id: uuid.UUID,
        domain: str,
        platform_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        auth_type: AuthType = AuthType.PASSWORD,
        business_id: Optional[uuid.UUID] = None,
    ) -> SiteCredential:
        result = await self.db.execute(
            select(SiteCredential).where(
                SiteCredential.user_id == user_id,
                SiteCredential.domain == domain,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            if username:
                existing.encrypted_username = self._encrypt(username)
            if password:
                existing.encrypted_password = self._encrypt(password)
            if api_key:
                existing.encrypted_api_key = self._encrypt(api_key)
            if api_secret:
                existing.encrypted_api_secret = self._encrypt(api_secret)
            existing.platform_name = platform_name
            existing.auth_type = auth_type
            existing.is_active = True
            existing.failed_attempts = 0
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        cred = SiteCredential(
            user_id=user_id,
            business_id=business_id,
            domain=domain,
            platform_name=platform_name,
            auth_type=auth_type,
            encrypted_username=self._encrypt(username),
            encrypted_password=self._encrypt(password),
            encrypted_api_key=self._encrypt(api_key),
            encrypted_api_secret=self._encrypt(api_secret),
        )
        self.db.add(cred)
        await self.db.commit()
        await self.db.refresh(cred)
        return cred

    async def get(self, user_id: uuid.UUID, domain: str) -> Optional[dict]:
        result = await self.db.execute(
            select(SiteCredential).where(
                SiteCredential.user_id == user_id,
                SiteCredential.domain == domain,
                SiteCredential.is_active == True,
            )
        )
        cred = result.scalar_one_or_none()
        if not cred:
            return None
        return {
            "id": str(cred.id),
            "domain": cred.domain,
            "platform_name": cred.platform_name,
            "username": self._decrypt(cred.encrypted_username),
            "password": self._decrypt(cred.encrypted_password),
            "api_key": self._decrypt(cred.encrypted_api_key),
            "api_secret": self._decrypt(cred.encrypted_api_secret),
            "auth_type": cred.auth_type.value,
        }

    async def has_credential(self, user_id: uuid.UUID, domain: str) -> bool:
        result = await self.db.execute(
            select(SiteCredential).where(
                SiteCredential.user_id == user_id,
                SiteCredential.domain == domain,
                SiteCredential.is_active == True,
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_for_user(self, user_id: uuid.UUID) -> List[SiteCredential]:
        result = await self.db.execute(
            select(SiteCredential).where(
                SiteCredential.user_id == user_id,
                SiteCredential.is_active == True,
            ).order_by(SiteCredential.platform_name)
        )
        return list(result.scalars().all())

    async def delete(self, user_id: uuid.UUID, credential_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(SiteCredential).where(
                SiteCredential.id == credential_id,
                SiteCredential.user_id == user_id,
            )
        )
        cred = result.scalar_one_or_none()
        if not cred:
            return False
        cred.is_active = False
        await self.db.commit()
        return True

    async def mark_used(self, credential_id: uuid.UUID, success: bool = True) -> None:
        result = await self.db.execute(
            select(SiteCredential).where(SiteCredential.id == credential_id)
        )
        cred = result.scalar_one_or_none()
        if not cred:
            return
        cred.last_used_at = datetime.now(timezone.utc)
        if success:
            cred.last_successful_login = datetime.now(timezone.utc)
            cred.failed_attempts = 0
        else:
            cred.failed_attempts += 1
        await self.db.commit()
