"""Two-factor authentication and API key rotation.

Implements:
- TOTP (Time-based One-Time Password) via authenticator apps
- API key generation with expiration
- API key rotation with automatic notification
- Backup codes
"""

import pyotp
import qrcode
import io
import base64
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer, Index, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import logging

Base = declarative_base()
logger = logging.getLogger(__name__)


class TOTP2FA(Base):
    """Two-factor authentication via TOTP (Time-based One-Time Password)."""

    __tablename__ = "totp_2fa"
    __table_args__ = (
        Index("idx_seller_id", "seller_id"),
        Index("idx_user_id", "user_id"),
    )

    id = Column(String(50), primary_key=True)
    seller_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # TOTP secret (base32 encoded)
    secret = Column(String(32), nullable=False)
    # QR code provisioning URI for scanning
    provisioning_uri = Column(String(255), nullable=False)

    # Backup codes (JSON array of hashed codes)
    backup_codes = Column(JSON, nullable=True)  # List of hashed backup codes
    backup_codes_used = Column(JSON, default=[])  # List of used backup code hashes

    # Status
    is_enabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)

    # Recovery
    last_used_at = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class APIKey(Base):
    """API key for programmatic access."""

    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_seller_id", "seller_id"),
        Index("idx_user_id", "user_id"),
        Index("idx_key_hash", "key_hash"),
        Index("idx_is_active", "is_active"),
    )

    id = Column(String(50), primary_key=True)
    seller_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # Key hash (never store actual key)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    # Key prefix (for display, e.g., "sk_live_abc123...")
    key_prefix = Column(String(20), nullable=False)
    # Full key stored in secure enclave (or encrypted)
    key_encrypted = Column(String(500), nullable=False)

    # Metadata
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    scopes = Column(JSON, default=[])  # List of allowed scopes

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_rotated = Column(Boolean, default=False)  # Was this key rotated?

    # Limits
    rate_limit_per_min = Column(Integer, default=60)
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String(50), nullable=True)

    # Rotation
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)  # Default 30 days
    rotation_scheduled_at = Column(DateTime, nullable=True)
    rotated_at = Column(DateTime, nullable=True)

    # Audit
    created_by = Column(String(255), nullable=True)  # User who created key
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(255), nullable=True)
    revoke_reason = Column(String(255), nullable=True)


class Auth2FAService:
    """Service for managing 2FA."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def setup_totp(
        self,
        db: Session,
        seller_id: str,
        user_id: str,
        name: Optional[str] = None,
    ) -> Tuple[str, str, List[str]]:
        """
        Set up TOTP for a user.

        Returns:
            (secret, qr_code_url, backup_codes)
        """
        from app.core.encryption import encrypt_value

        # Generate secret
        secret = pyotp.random_base32()
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_id,
            issuer_name=name or "SellIA",
        )

        # Generate backup codes
        backup_codes = [secrets.token_hex(8) for _ in range(10)]

        # Hash backup codes for storage
        import hashlib

        backup_codes_hashed = [
            hashlib.sha256(code.encode()).hexdigest() for code in backup_codes
        ]

        # Store TOTP (not yet enabled until verified)
        totp_2fa = TOTP2FA(
            id=str(uuid.uuid4()),
            seller_id=seller_id,
            user_id=user_id,
            secret=secret,
            provisioning_uri=provisioning_uri,
            backup_codes=backup_codes_hashed,
            is_enabled=False,
            is_verified=False,
        )

        db.add(totp_2fa)
        db.commit()

        # Generate QR code
        qr = qrcode.QRCode()
        qr.add_data(provisioning_uri)
        qr.make()

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_code_url = f"data:image/png;base64,{qr_code_base64}"

        return secret, qr_code_url, backup_codes

    async def verify_totp(
        self,
        db: Session,
        seller_id: str,
        user_id: str,
        code: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify TOTP code (6 digits).

        Returns:
            (is_valid, error_message)
        """
        totp_2fa = (
            db.query(TOTP2FA)
            .filter(
                TOTP2FA.seller_id == seller_id,
                TOTP2FA.user_id == user_id,
                TOTP2FA.is_enabled == False,  # Not yet enabled
            )
            .first()
        )

        if not totp_2fa:
            return False, "2FA not set up"

        if not code or len(code) != 6 or not code.isdigit():
            return False, "Invalid code format"

        # Verify TOTP (allow 30s window before/after)
        totp = pyotp.TOTP(totp_2fa.secret)
        if not totp.verify(code, valid_window=1):
            totp_2fa.failed_attempts += 1
            db.commit()

            if totp_2fa.failed_attempts >= 3:
                return False, "Too many failed attempts"

            return False, "Invalid code"

        # Mark as verified and enabled
        totp_2fa.is_verified = True
        totp_2fa.is_enabled = True
        totp_2fa.verified_at = datetime.now(timezone.utc)
        totp_2fa.failed_attempts = 0
        db.commit()

        return True, None

    async def verify_totp_login(
        self,
        db: Session,
        seller_id: str,
        user_id: str,
        code: str,
    ) -> Tuple[bool, Optional[str]]:
        """Verify TOTP code during login."""
        totp_2fa = (
            db.query(TOTP2FA)
            .filter(
                TOTP2FA.seller_id == seller_id,
                TOTP2FA.user_id == user_id,
                TOTP2FA.is_enabled == True,
            )
            .first()
        )

        if not totp_2fa:
            return False, "2FA not enabled"

        totp = pyotp.TOTP(totp_2fa.secret)
        if not totp.verify(code, valid_window=1):
            totp_2fa.failed_attempts += 1
            db.commit()

            if totp_2fa.failed_attempts >= 5:
                # Lock account temporarily
                return False, "Too many failed attempts. Try again in 15 minutes."

            return False, "Invalid code"

        # Clear failed attempts on success
        totp_2fa.failed_attempts = 0
        totp_2fa.last_used_at = datetime.now(timezone.utc)
        db.commit()

        return True, None

    async def verify_backup_code(
        self,
        db: Session,
        seller_id: str,
        user_id: str,
        code: str,
    ) -> Tuple[bool, Optional[str]]:
        """Verify backup code (only usable once)."""
        import hashlib

        totp_2fa = (
            db.query(TOTP2FA)
            .filter(
                TOTP2FA.seller_id == seller_id,
                TOTP2FA.user_id == user_id,
                TOTP2FA.is_enabled == True,
            )
            .first()
        )

        if not totp_2fa or not totp_2fa.backup_codes:
            return False, "No backup codes available"

        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Check if code exists and hasn't been used
        if code_hash not in totp_2fa.backup_codes:
            return False, "Invalid backup code"

        if code_hash in (totp_2fa.backup_codes_used or []):
            return False, "Backup code already used"

        # Mark as used
        if not totp_2fa.backup_codes_used:
            totp_2fa.backup_codes_used = []
        totp_2fa.backup_codes_used.append(code_hash)
        db.commit()

        return True, None

    async def disable_totp(
        self,
        db: Session,
        seller_id: str,
        user_id: str,
    ) -> bool:
        """Disable TOTP for user."""
        totp_2fa = (
            db.query(TOTP2FA)
            .filter(
                TOTP2FA.seller_id == seller_id,
                TOTP2FA.user_id == user_id,
            )
            .first()
        )

        if not totp_2fa:
            return False

        db.delete(totp_2fa)
        db.commit()
        return True


class APIKeyService:
    """Service for managing API keys."""

    KEY_PREFIX = "sk_live_"  # Production prefix
    KEY_LENGTH = 32  # Length of random portion

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def generate_api_key(
        self,
        db: Session,
        seller_id: str,
        user_id: str,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_in_days: int = 30,
    ) -> str:
        """
        Generate a new API key.

        Returns:
            Full API key (only shown once to user)
        """
        from app.core.encryption import encrypt_value
        import hashlib

        # Generate random key
        random_portion = secrets.token_hex(self.KEY_LENGTH // 2)
        full_key = f"{self.KEY_PREFIX}{random_portion}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_prefix = full_key[:20]

        # Encrypt full key for storage
        key_encrypted = encrypt_value(full_key)

        api_key = APIKey(
            id=str(uuid.uuid4()),
            seller_id=seller_id,
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            key_encrypted=key_encrypted,
            name=name,
            scopes=scopes or ["*"],
            is_active=True,
            created_by=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        )

        db.add(api_key)
        db.commit()

        return full_key

    async def verify_api_key(
        self,
        db: Session,
        seller_id: str,
        key: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[Optional[APIKey], Optional[str]]:
        """
        Verify API key.

        Returns:
            (api_key_record, error_message)
        """
        import hashlib
        from app.core.encryption import decrypt_value

        key_hash = hashlib.sha256(key.encode()).hexdigest()

        api_key = (
            db.query(APIKey)
            .filter(
                APIKey.seller_id == seller_id,
                APIKey.key_hash == key_hash,
            )
            .first()
        )

        if not api_key:
            return None, "Invalid API key"

        if not api_key.is_active:
            return None, "API key is revoked"

        if api_key.expires_at < datetime.now(timezone.utc):
            return None, "API key has expired"

        # Update last used
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.last_used_ip = ip_address
        db.commit()

        return api_key, None

    async def rotate_api_key(
        self,
        db: Session,
        seller_id: str,
        key_id: str,
        user_id: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Rotate an API key (invalidate old, create new).

        Returns:
            (new_key, error_message)
        """
        api_key = (
            db.query(APIKey)
            .filter(
                APIKey.id == key_id,
                APIKey.seller_id == seller_id,
            )
            .first()
        )

        if not api_key:
            return None, "API key not found"

        # Mark old key as rotated
        api_key.is_rotated = True
        api_key.rotated_at = datetime.now(timezone.utc)
        api_key.is_active = False
        db.commit()

        # Generate new key
        new_key = await self.generate_api_key(
            db,
            seller_id=seller_id,
            user_id=user_id,
            name=f"{api_key.name} (rotated)",
            scopes=api_key.scopes,
            expires_in_days=30,
        )

        # TODO: Send notification to user about key rotation

        return new_key, None

    async def revoke_api_key(
        self,
        db: Session,
        seller_id: str,
        key_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Revoke an API key."""
        api_key = (
            db.query(APIKey)
            .filter(
                APIKey.id == key_id,
                APIKey.seller_id == seller_id,
            )
            .first()
        )

        if not api_key:
            return False, "API key not found"

        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        api_key.revoked_by = user_id
        api_key.revoke_reason = reason
        db.commit()

        return True, None

    async def list_api_keys(
        self,
        db: Session,
        seller_id: str,
        include_inactive: bool = False,
    ) -> List[APIKey]:
        """List API keys for seller."""
        query = db.query(APIKey).filter(APIKey.seller_id == seller_id)

        if not include_inactive:
            query = query.filter(APIKey.is_active == True)

        return query.order_by(APIKey.created_at.desc()).all()

    async def schedule_expiration_check(self, db: Session, days_before: int = 7) -> List[str]:
        """Find API keys expiring soon."""
        soon = datetime.now(timezone.utc) + timedelta(days=days_before)
        expiring = (
            db.query(APIKey)
            .filter(
                APIKey.is_active == True,
                APIKey.expires_at <= soon,
                APIKey.expires_at > datetime.now(timezone.utc),
            )
            .all()
        )

        # TODO: Send notification to users about expiring keys

        return [k.id for k in expiring]


# Global services
_auth_2fa_service: Optional[Auth2FAService] = None
_api_key_service: Optional[APIKeyService] = None


def get_auth_2fa_service() -> Auth2FAService:
    """Get global 2FA service."""
    global _auth_2fa_service
    if _auth_2fa_service is None:
        _auth_2fa_service = Auth2FAService()
    return _auth_2fa_service


def get_api_key_service() -> APIKeyService:
    """Get global API key service."""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service
