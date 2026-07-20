# SellIA Security API Documentation

## Overview

This document describes the advanced security endpoints added to SellIA:

1. **Admin Security Audit Panel** — View and filter login logs across all users
2. **Geofencing** — Automatic detection of logins from unexpected locations
3. **2FA Backup Codes** — Single-use recovery codes for account access if phone is lost
4. **Have I Been Pwned (HIBP) Integration** — Alerts if user email appears in known data breaches

---

## Authentication

All endpoints require Bearer token authentication (JWT) or httpOnly cookie. Admin endpoints additionally require `is_superuser = true`.

```
Authorization: Bearer <access_token>
```

---

## 1. Admin Security Audit Panel

### `GET /api/v1/security/audit-logs`

Retrieve login logs for **all users** (admin only).

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | UUID | No | Filter by specific user |
| `event_type` | string | No | `success` or `failed` |
| `ip` | string | No | Partial IP match |
| `country` | string | No | Country code match |
| `date_from` | datetime | No | ISO 8601 datetime |
| `date_to` | datetime | No | ISO 8601 datetime |
| `limit` | integer | No | Default `100`, max `1000` |
| `offset` | integer | No | Default `0` |

#### Response `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "user_email": "user@example.com",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "country": "AR",
    "city": "Buenos Aires",
    "success": true,
    "created_at": "2026-05-12T14:30:00Z"
  }
]
```

#### Errors

- `403 Forbidden` — User is not a superuser

---

### `GET /api/v1/security/audit-stats`

Get security statistics for the current day (admin only).

#### Response `200 OK`

```json
{
  "total_logins_today": 42,
  "failed_logins_today": 3,
  "new_devices_today": 5,
  "active_sessions": 18,
  "blocked_attempts_today": 0,
  "geofence_violations_today": 1
}
```

---

## 2. Geofencing

Geofencing is evaluated automatically on every login. No manual endpoint is required for the user.

### Configuration

Admins can configure geofencing via the security config endpoint:

### `PUT /api/v1/security/config`

#### Request Body

```json
{
  "max_distance_km": 500,
  "alert_on_geofence": true
}
```

- `max_distance_km`: Maximum allowed distance from last known login location. `null` or `0` disables geofencing.
- `alert_on_geofence`: Whether to send email/push/webhook alerts on violation.

#### How it works

1. On every successful login, the system geolocates the IP address
2. If a previous successful login with coordinates exists, Haversine distance is calculated
3. If distance > `max_distance_km`, a security alert is triggered:
   - Email to user with location details
   - Push notification (if subscribed)
   - Webhook alert (if configured)

---

## 3. 2FA / TOTP & Backup Codes

### `POST /api/v1/auth/2fa/setup`

Start 2FA setup. Returns a TOTP secret and QR code.

#### Response `200 OK`

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgo...",
  "provisioning_uri": "otpauth://totp/SellIA:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=SellIA",
  "message": "Escaneá el QR con Google Authenticator, Authy o similar"
}
```

---

### `POST /api/v1/auth/2fa/verify`

Verify a TOTP code to activate 2FA. Also generates 8 backup codes.

#### Query Parameters

| Parameter | Type | Required |
|-----------|------|----------|
| `code` | string | Yes | 6-digit TOTP code |

#### Response `200 OK`

```json
{
  "message": "2FA activado correctamente",
  "backup_codes": ["A1B2C3D4", "E5F6G7H8", "I9J0K1L2", "M3N4O5P6", "Q7R8S9T0", "U1V2W3X4", "Y5Z6A7B8", "C9D0E1F2"],
  "warning": "Guardá estos códigos en un lugar seguro. Solo se muestran una vez."
}
```

---

### `POST /api/v1/auth/2fa/disable`

Disable 2FA. Requires a valid TOTP code.

#### Query Parameters

| Parameter | Type | Required |
|-----------|------|----------|
| `code` | string | Yes |

#### Response `200 OK`

```json
{
  "message": "2FA desactivado correctamente"
}
```

---

### `GET /api/v1/auth/2fa/backup-codes`

Get the number of remaining unused backup codes.

#### Response `200 OK`

```json
{
  "remaining": 6
}
```

---

### Using Backup Codes at Login

When 2FA is enabled and you cannot access your authenticator app, use a **backup code** instead of a TOTP code:

#### `POST /api/v1/auth/login`

Send the backup code in the same header used for TOTP:

```
X-2FA-Code: A1B2C3D4
```

Backup codes:
- Are 8-character hexadecimal strings
- Are case-insensitive
- Can only be used **once**
- Are verified after TOTP fails (fallback mechanism)

---

## 4. Have I Been Pwned (HIBP) Integration

### Configuration

Admins must set the HIBP API key in security config:

### `PUT /api/v1/security/config`

```json
{
  "hibp_api_key": "your-hibp-api-key",
  "alert_on_breach": true
}
```

Get your API key at: https://haveibeenpwned.com/API/Key

---

### Automatic Checks

When `alert_on_breach = true`:
- **On registration**: New user emails are checked against HIBP
- **On login**: Existing user emails are checked against HIBP

If breaches are found, the user receives:
- Security email with breach names and recommendations
- Webhook alert (if configured)

---

### `POST /api/v1/security/check-breach/{user_id}`

Manually check a user's email against HIBP (admin only).

#### Response `200 OK`

```json
{
  "email": "user@example.com",
  "found": true,
  "count": 3,
  "names": ["Adobe", "LinkedIn", "Dropbox"],
  "checked_at": "2026-05-12T14:30:00Z"
}
```

#### Response (no breaches)

```json
{
  "email": "user@example.com",
  "found": false,
  "count": 0,
  "names": [],
  "checked_at": "2026-05-12T14:30:00Z"
}
```

---

## 5. Security Config (Admin)

### `GET /api/v1/security/config`

### `PUT /api/v1/security/config`

#### Full Config Fields

```json
{
  "blocked_countries": "CN,RU,KP,IR",
  "require_turnstile": false,
  "require_2fa_for_admins": false,
  "alert_on_new_device": true,
  "alert_on_failed_login": true,
  "alert_on_malware": true,
  "max_distance_km": 500,
  "alert_on_geofence": true,
  "hibp_api_key": "your-api-key",
  "alert_on_breach": true
}
```

---

## 6. Webhooks

Security events can be sent to Slack, Discord, Telegram, or generic webhooks.

### `POST /api/v1/security/webhooks`

```json
{
  "name": "Slack Alerts",
  "url": "https://hooks.slack.com/services/...",
  "platform": "slack",
  "secret": "optional-signing-secret",
  "events": "login,failed_login,new_device,malware,brute_force,geofence,breach"
}
```

Platforms: `slack`, `discord`, `telegram`, `generic`

Events: `login`, `failed_login`, `new_device`, `malware`, `brute_force`, `geofence`, `breach`

---

## Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | `2FA_REQUIRED` | Login requires 2FA code |
| 401 | `Credenciales inválidas` | Wrong email/password or expired session |
| 403 | `Cuenta bloqueada temporalmente` | Account locked after 5 failed attempts |
| 403 | `Requiere permisos de administrador` | Admin-only endpoint |
| 429 | `Too many requests` | Rate limit exceeded |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 5 per minute |
| `POST /auth/register` | 3 per hour |
| General API | 100 per minute |

---

## Security Headers

All responses include:

```
X-Request-ID: <uuid>
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
```
