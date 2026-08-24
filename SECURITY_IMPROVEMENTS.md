# Security Improvements - SellIA

## Password Security

### Requirements
Passwords must now meet professional security standards:
- **Length**: Minimum 8 characters
- **Uppercase**: At least 1 uppercase letter (A-Z)
- **Lowercase**: At least 1 lowercase letter (a-z)
- **Digits**: At least 1 number (0-9)
- **Special Characters**: At least 1 of: `@`, `+`, `-`, `!`, `#`, `$`, `%`

**Example valid password**: `SecurePass123@`

### Password Hashing
- Upgraded from SHA256 to **bcrypt** (cost factor 12)
- Each password independently salted
- Resistant to rainbow table attacks
- Better protection against brute force

## Two-Factor Authentication (2FA)

### Overview
- Optional TOTP (Time-based One-Time Password) 2FA
- Industry-standard authentication method
- Compatible with Google Authenticator, Microsoft Authenticator, Authy, etc.

### API Endpoints

#### 1. Enable 2FA
```bash
POST /api/v1/auth/2fa/enable
Body: { "user_id": "uuid" }

Response:
{
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "qr_code": "data:image/png;base64,...",
  "message": "Scan QR code with authenticator app"
}
```

**Steps:**
1. User calls this endpoint
2. Receives QR code + base32 secret
3. Scans QR with Authenticator app
4. App displays 6-digit code
5. User verifies code with next endpoint

#### 2. Verify & Enable 2FA
```bash
POST /api/v1/auth/2fa/verify
Body: {
  "user_id": "uuid",
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "totp_code": "123456"
}

Response:
{
  "message": "2FA enabled successfully"
}
```

**After this:**
- User must provide TOTP code on every login
- 6-digit codes change every 30 seconds
- System accepts codes with 1-window tolerance (±30 seconds)

#### 3. Login with 2FA
```bash
POST /api/v1/auth/signin
Body: {
  "email": "user@example.com",
  "password": "SecurePass123@",
  "totp_code": "123456"  // Optional if 2FA enabled
}
```

**Flow if 2FA enabled but no code provided:**
```json
{
  "requires_2fa": true,
  "user_id": "uuid",
  "message": "2FA code required"
}
```

Client must then ask user for code and retry with `totp_code`.

#### 4. Disable 2FA
```bash
POST /api/v1/auth/2fa/disable
Body: {
  "user_id": "uuid",
  "password": "SecurePass123@"  // Confirm password
}

Response:
{
  "message": "2FA disabled"
}
```

**Security**: Requires password confirmation to prevent accidental disabling.

## Sign-up Flow (Updated)

```bash
POST /api/v1/auth/signup
Body: {
  "email": "user@example.com",
  "password": "SecurePass123@",  // Must meet requirements
  "full_name": "John Doe"
}

Response:
{
  "user_id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "access_token": "jwt...",
  "requires_2fa_setup": true,
  "message": "Account created. Set up 2FA for security."
}
```

## Frontend Integration

### Sign-up Form
1. Add real-time password validation feedback
2. Show requirements as user types:
   - ✓ 8+ characters
   - ✓ Uppercase letter
   - ✓ Lowercase letter
   - ✓ Digit
   - ✓ Special char (@+-!#$%)

### 2FA Setup After Signup
1. Show QR code image
2. Provide backup secret (copyable text)
3. Ask user to enter code from app
4. Confirm 2FA is enabled

### Login Flow
1. Email + password
2. If 2FA enabled: ask for 6-digit code
3. Auto-refresh after 30 seconds (code expires)

## Security Best Practices

### For Users
- Use unique passwords for SellIA
- Enable 2FA immediately after signup
- Save backup codes somewhere safe
- Never share TOTP secret with anyone

### For Developers
- Never log passwords
- Never send passwords in URLs
- Always use HTTPS
- Validate on both client and server
- Rate limit login attempts
- Log suspicious auth activity

## Database Schema

```sql
ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN totp_secret VARCHAR(32);
```

Both fields are nullable. Only populated if 2FA is enabled.

## Compliance

Security improvements align with:
- **OWASP Top 10**: A02:2021 – Cryptographic Failures
- **NIST SP 800-63B**: Digital Identity Guidelines
- **PCI DSS 3.2.1**: Password security requirements
- **ISO/IEC 27001**: Information security management

## Testing

```bash
# Test password validation
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "weak",
    "full_name": "Test User"
  }'
# Returns: 422 Unprocessable Entity (invalid password)

# Test 2FA enable
curl -X POST http://localhost:8000/api/v1/auth/2fa/enable \
  -H "Content-Type: application/json" \
  -d '{"user_id": "..."}'
# Returns: QR code + secret

# Test 2FA verify
curl -X POST http://localhost:8000/api/v1/auth/2fa/verify \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "...",
    "secret": "...",
    "totp_code": "123456"
  }'
```

## Migration Status

- ✅ Code changes deployed
- ⏳ Database schema update (Railway auto-migration)
- ⏳ Frontend UI update (QR code display + code input)
- ⏳ Documentation update (help & settings)

---
**Last Updated**: 2026-08-24
**Commit**: eee8a02
