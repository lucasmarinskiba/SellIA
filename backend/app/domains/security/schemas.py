from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SecurityWebhookCreate(BaseModel):
    name: str
    url: str
    platform: str  # slack, discord, telegram, generic
    secret: str | None = None
    events: str | None = None  # login, malware, brute_force, new_device


class SecurityWebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    platform: str
    is_active: bool
    events: str | None
    created_at: datetime


class SecurityConfigUpdate(BaseModel):
    blocked_countries: str | None = None
    require_turnstile: bool | None = None
    require_2fa_for_admins: bool | None = None
    alert_on_new_device: bool | None = None
    alert_on_failed_login: bool | None = None
    alert_on_malware: bool | None = None
    max_distance_km: float | None = None
    alert_on_geofence: bool | None = None
    hibp_api_key: str | None = None
    alert_on_breach: bool | None = None


class SecurityConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blocked_countries: str | None
    require_turnstile: bool
    require_2fa_for_admins: bool
    alert_on_new_device: bool
    alert_on_failed_login: bool
    alert_on_malware: bool
    max_distance_km: float | None
    alert_on_geofence: bool
    hibp_api_key: str | None
    alert_on_breach: bool
    updated_at: datetime


class LoginLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ip_address: str
    user_agent: str | None
    device_fingerprint: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    city: str | None
    success: bool
    created_at: datetime


# Push notifications

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None = None


class PushSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    endpoint: str
    user_agent: str | None
    is_active: bool
    created_at: datetime


# User sessions

class UserSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_name: str | None
    device_fingerprint: str | None
    ip_address: str
    user_agent: str | None
    country: str | None
    last_active_at: datetime
    expires_at: datetime
    is_revoked: bool
    created_at: datetime
    is_current: bool | None = None


# Audit logs (admin)

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user_email: str | None
    ip_address: str
    user_agent: str | None
    country: str | None
    city: str | None
    success: bool
    created_at: datetime


class SecurityStatsResponse(BaseModel):
    total_logins_today: int
    failed_logins_today: int
    new_devices_today: int
    active_sessions: int
    blocked_attempts_today: int
    geofence_violations_today: int


# Backup codes

class BackupCodeResponse(BaseModel):
    codes: list[str]
    message: str


# Breach check

class BreachCheckResponse(BaseModel):
    email: str
    found: bool
    count: int
    names: list[str]
    checked_at: datetime


# Metrics

class SecurityMetricsResponse(BaseModel):
    total_logins_24h: int
    failed_logins_24h: int
    unique_users_24h: int
    active_sessions: int
    avg_risk_score: float
    top_countries: list[dict]
    login_timeline: list[dict]
    device_breakdown: list[dict]


class SecurityMetricsTimelineResponse(BaseModel):
    hour: str
    logins: int
    failed: int
    new_devices: int
