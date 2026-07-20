import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Float, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UserLoginLog(Base):
    """Registro de logins para detectar dispositivos nuevos."""
    __tablename__ = "user_login_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(64), nullable=True)
    country = Column(String(10), nullable=True)
    # Geolocalización para geofencing
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    city = Column(String(100), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SecurityWebhook(Base):
    """Webhooks para alertas de seguridad (Slack, Discord, Telegram)."""
    __tablename__ = "security_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    platform = Column(String(20), nullable=False)  # slack, discord, telegram, generic
    secret = Column(String(255), nullable=True)  # para firmar payloads
    is_active = Column(Boolean, default=True, nullable=False)
    events = Column(Text, nullable=True)  # lista separada por comas: login, malware, brute_force
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SecurityConfig(Base):
    """Configuración global de seguridad."""
    __tablename__ = "security_config"

    id = Column(Integer, primary_key=True)
    blocked_countries = Column(Text, nullable=True)  # ISO codes separados por coma: CN,RU,IR
    require_turnstile = Column(Boolean, default=False, nullable=False)
    require_2fa_for_admins = Column(Boolean, default=False, nullable=False)
    alert_on_new_device = Column(Boolean, default=True, nullable=False)
    alert_on_failed_login = Column(Boolean, default=True, nullable=False)
    alert_on_malware = Column(Boolean, default=True, nullable=False)
    # Geofencing
    max_distance_km = Column(Float, default=500.0, nullable=True)  # null = desactivado
    alert_on_geofence = Column(Boolean, default=True, nullable=False)
    # Have I Been Pwned
    hibp_api_key = Column(String(255), nullable=True)
    alert_on_breach = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PushSubscription(Base):
    """Suscripciones Web Push de los usuarios."""
    __tablename__ = "push_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserSession(Base):
    """Sesiones activas del usuario para poder ver y revocar."""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)  # hash del JWT
    device_name = Column(String(255), nullable=True)  # nombre del dispositivo
    device_fingerprint = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    country = Column(String(10), nullable=True)
    last_active_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TwoFABackupCode(Base):
    """Códigos de backup para 2FA (un solo uso)."""
    __tablename__ = "two_fa_backup_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class BreachCheckLog(Base):
    """Registro de verificaciones Have I Been Pwned."""
    __tablename__ = "breach_check_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    breaches_found = Column(Integer, default=0, nullable=False)
    breach_names = Column(Text, nullable=True)  # nombres de breaches separados por coma
    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ============================================================
#  Subscription Integrity & Anti-Chargeback
# ============================================================

class SubscriptionAccessLog(Base):
    """Log de acceso a features para probar entrega de servicio."""
    __tablename__ = "subscription_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_name = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(255), nullable=True)
    response_status = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ChargebackAlert(Base):
    """Alertas de chargeback con evidencia de uso."""
    __tablename__ = "chargeback_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_provider = Column(String(50), nullable=False)  # stripe, mercadopago
    transaction_id = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    reason = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)  # JSON con evidencia de uso
    status = Column(String(20), default="open", nullable=False)  # open, contested, won, lost
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ============================================================
#  Multi-Factor Authentication (Email OTP, WebAuthn, Hardware Keys)
# ============================================================

class EmailOTP(Base):
    """Códigos OTP enviados por email."""
    __tablename__ = "email_otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False)  # login, password_reset, email_verify, device_verify
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WebAuthnCredential(Base):
    """Credenciales WebAuthn / Passkeys."""
    __tablename__ = "webauthn_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_id = Column(Text, nullable=False, unique=True)  # base64url
    public_key = Column(Text, nullable=False)  # base64url
    sign_count = Column(Integer, default=0, nullable=False)
    device_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SecurityKey(Base):
    """Hardware Security Keys (YubiKey, etc.)."""
    __tablename__ = "security_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_id = Column(Text, nullable=False, unique=True)
    attestation = Column(Text, nullable=True)
    nickname = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ============================================================
#  Trusted Devices & Session Integrity
# ============================================================

class TrustedDevice(Base):
    """Dispositivos de confianza del usuario."""
    __tablename__ = "trusted_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_fingerprint = Column(String(64), nullable=False)
    device_name = Column(String(255), nullable=True)
    os = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    country = Column(String(10), nullable=True)
    first_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_trusted = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    remember_days = Column(Integer, default=30, nullable=True)


class SessionNonce(Base):
    """Nonce rotativo para anti-tamper de sesión."""
    __tablename__ = "session_nonces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_hash = Column(String(255), nullable=False, unique=True, index=True)
    nonce = Column(String(64), nullable=False)
    rotated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ============================================================
#  Access Control (Time, IP)
# ============================================================

class IPAllowlist(Base):
    """IPs permitidas para login (Enterprise/Pro)."""
    __tablename__ = "ip_allowlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    label = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LoginAnomaly(Base):
    """Anomalías de login detectadas por ML."""
    __tablename__ = "login_anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=False)  # impossible_speed, unusual_hour, multiple_devices
    description = Column(Text, nullable=True)
    score = Column(Float, nullable=False)  # 0.0 - 1.0
    ip_address = Column(String(45), nullable=True)
    device_fingerprint = Column(String(64), nullable=True)
    country = Column(String(10), nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ============================================================
#  Data Access Audit Log
# ============================================================

class DataAccessLog(Base):
    """Audit log for access to sensitive data."""
    __tablename__ = "data_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)

    action = Column(String(20), nullable=False)  # read, create, update, delete
    table_name = Column(String(100), nullable=False)
    record_id = Column(String(36), nullable=True)  # UUID as string
    field_name = Column(String(100), nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_path = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_data_access_logs_user_business", "user_id", "business_id"),
        Index("ix_data_access_logs_table_action", "table_name", "action"),
    )


# ============================================================
#  RBAC (Role-Based Access Control)
# ============================================================

class UserRole(str):
    OWNER = "owner"
    ADMIN = "admin"
    MARKETING = "marketing"
    SALES = "sales"
    SUPPORT = "support"
    VIEWER = "viewer"


class RolePermission(Base):
    """Permissions assigned to a role."""
    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String(50), nullable=False, index=True)  # owner, admin, marketing, sales, support, viewer
    resource = Column(String(100), nullable=False)  # conversations, orders, finance, objectives, etc.
    action = Column(String(20), nullable=False)  # read, write, delete, admin

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_role_permissions_role_resource", "role", "resource"),
    )


class BusinessUserRole(Base):
    """Role assignment of a user within a business."""
    __tablename__ = "business_user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default=UserRole.VIEWER)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_business_user_roles_user_business", "user_id", "business_id", unique=True),
    )


# ============================================================
#  Data Retention Policies
# ============================================================

class DataRetentionPolicy(Base):
    """Políticas configurables de retención de datos por negocio y tabla."""
    __tablename__ = "data_retention_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    table_name = Column(String(100), nullable=False)
    retention_days = Column(Integer, nullable=False, default=365)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_data_retention_policies_business_table", "business_id", "table_name"),
    )


class DataRetentionLog(Base):
    """Log de ejecución de políticas de retención."""
    __tablename__ = "data_retention_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("data_retention_policies.id", ondelete="SET NULL"), nullable=True)
    table_name = Column(String(100), nullable=False)
    records_deleted = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="success", nullable=False)  # success, error, skipped
    error_message = Column(Text, nullable=True)


# ============================================================
#  Secret Rotation Log
# ============================================================

class SecretRotationLog(Base):
    """Log de rotación de secretos (webhooks, API keys, etc.)."""
    __tablename__ = "secret_rotation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)
    secret_type = Column(String(50), nullable=False)  # webhook_token, api_key, session, etc.
    target_id = Column(String(36), nullable=True)  # UUID of affected record
    old_value_hash = Column(String(255), nullable=True)
    new_value_hash = Column(String(255), nullable=True)
    rotated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="success", nullable=False)  # success, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ============================================================
#  Auto IP Blocklist (fortaleza + audacia)
# ============================================================

class BlockedIP(Base):
    """IPs bloqueadas automáticamente por comportamiento sospechoso."""
    __tablename__ = "blocked_ips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False, unique=True, index=True)
    reason = Column(String(100), nullable=False)  # brute_force, threat_intel, admin
    blocked_until = Column(DateTime(timezone=True), nullable=True)  # null = permanente
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ============================================================
#  Idempotency Keys (eficacia)
# ============================================================

class IdempotencyKey(Base):
    """Claves de idempotencia para prevenir duplicados en operaciones críticas."""
    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), nullable=False, unique=True, index=True)
    resource = Column(String(50), nullable=False)  # order, payment, invoice
    response_body = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_idempotency_keys_resource_created", "resource", "created_at"),
    )


# ============================================================
#  Webhook Event Deduplication (fortaleza)
# ============================================================

class WebhookEventLog(Base):
    """Log de eventos de webhook procesados para deduplicación."""
    __tablename__ = "webhook_event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(20), nullable=False)  # stripe, mercadopago, shopify, whatsapp
    event_id = Column(String(100), nullable=False, index=True)  # ID único del evento del provider
    event_type = Column(String(50), nullable=False)
    processed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_webhook_event_logs_provider_event", "provider", "event_id", unique=True),
    )
