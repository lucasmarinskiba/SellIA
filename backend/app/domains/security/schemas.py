from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class SecurityWebhookCreate(BaseModel):
    name: str
    url: str
    platform: str  # slack, discord, telegram, generic
    secret: Optional[str] = None
    events: Optional[str] = None  # login, malware, brute_force, new_device


class SecurityWebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    platform: str
    is_active: bool
    events: Optional[str]
    created_at: datetime


class SecurityConfigUpdate(BaseModel):
    blocked_countries: Optional[str] = None
    require_turnstile: Optional[bool] = None
    require_2fa_for_admins: Optional[bool] = None
    alert_on_new_device: Optional[bool] = None
    alert_on_failed_login: Optional[bool] = None
    alert_on_malware: Optional[bool] = None
    max_distance_km: Optional[float] = None
    alert_on_geofence: Optional[bool] = None
    hibp_api_key: Optional[str] = None
    alert_on_breach: Optional[bool] = None


class SecurityConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blocked_countries: Optional[str]
    require_turnstile: bool
    require_2fa_for_admins: bool
    alert_on_new_device: bool
    alert_on_failed_login: bool
    alert_on_malware: bool
    max_distance_km: Optional[float]
    alert_on_geofence: bool
    hibp_api_key: Optional[str]
    alert_on_breach: bool
    updated_at: datetime


class LoginLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ip_address: str
    user_agent: Optional[str]
    device_fingerprint: Optional[str]
    country: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    city: Optional[str]
    success: bool
    created_at: datetime


# Push notifications

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


class PushSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    endpoint: str
    user_agent: Optional[str]
    is_active: bool
    created_at: datetime


# User sessions

class UserSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_name: Optional[str]
    device_fingerprint: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    country: Optional[str]
    last_active_at: datetime
    expires_at: datetime
    is_revoked: bool
    created_at: datetime
    is_current: Optional[bool] = None


# Audit logs (admin)

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user_email: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    country: Optional[str]
    city: Optional[str]
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
