# SellIA Threat Model

Audience: ops + security review. Scope: MVP backend + frontend + Chrome extension.

## Assets

| Asset | Sensitivity | Where |
|---|---|---|
| User passwords (hashed bcrypt cost 12) | high | Postgres `users.password_hash` |
| JWT access tokens | high | client localStorage + Authorization header |
| Stripe Connect access tokens | critical | Stripe vault · we hold only account_id |
| WhatsApp permanent access tokens | high | `channels.config` JSONB (encrypted-at-rest via Postgres TDE) |
| Anthropic API key | critical | env var · never in DB |
| Tenant data (deals · contacts · conversations) | high | Postgres · RLS-isolated |
| Audit logs | medium | Postgres · 90-day retention |
| AFIP cert per tenant | high | (future) encrypted at-rest |

## Trust boundaries

```
Public internet ─→ Cloudflare WAF ─→ Vercel (frontend) ─→ Fly (api)
                                                   │
                                                   ├→ Postgres (RLS)
                                                   ├→ Redis (private network)
                                                   ├→ Anthropic API
                                                   └→ Stripe · Meta · etc.
```

## OWASP Top 10 mitigations

| Risk | Mitigation |
|---|---|
| A01 Broken Access Control | Postgres Row-Level Security · `app.tenant_id` bound per session · `require_role()` dep on endpoints |
| A02 Cryptographic Failures | bcrypt cost 12 · HTTPS-only via Cloudflare · HSTS preload · TLS 1.3 |
| A03 Injection | SQLAlchemy 2 parameterized · Pydantic validation · no string concat in queries |
| A04 Insecure Design | Multi-tenant isolation at DB · JWT short-lived (7d) · webhook signature verify |
| A05 Security Misconfiguration | CSP header strict · X-Frame-Options DENY · env-driven config · no debug in prod |
| A06 Vulnerable Components | `npm audit` in CI · dependabot weekly · pinned versions in requirements.txt |
| A07 ID/Auth Failures | bcrypt+JWT · rate limit on /auth/login · password min 8 chars |
| A08 Software/Data Integrity | Stripe webhook signature · WA HMAC-SHA256 · CI-signed Docker images |
| A09 Logging/Monitoring | Audit logs table · Sentry · /metrics · Cloudflare access logs |
| A10 SSRF | URL allowlist in API client · no user-supplied URLs to fetch |

## Specific attacks + counters

### Cross-tenant data leak
- **Threat:** authenticated user accesses another tenant's deals
- **Counter:** RLS policy `tenant_id::text = current_setting('app.tenant_id')` enforced at DB layer
- **Test:** `tests/test_cross_tenant.py` (TODO) attempts list with tenant-B token after binding tenant-A

### JWT token theft
- **Threat:** XSS steals localStorage token
- **Counter:** strict CSP w/o unsafe-inline scripts · `httpOnly` cookies (future migration) · short JWT TTL
- **Mitigation in progress:** migrate to httpOnly cookies + refresh tokens

### Webhook spoofing
- **Threat:** attacker POSTs fake Stripe webhook → upgrades tenant plan free
- **Counter:** `stripe.Webhook.construct_event()` verifies signature using `STRIPE_WEBHOOK_SECRET`
- **Same for WA:** HMAC-SHA256 of body w/ `WA_APP_SECRET`

### Computer Use sandbox escape
- **Threat:** malicious task tries to access host
- **Counter:** Firecracker microVMs (E2B) · network egress allowlist · disk quota · 30min auto-kill
- **Future:** seccomp + AppArmor profiles

### Rate-limited abuse
- **Threat:** brute-force /auth/login · spam /v1/auth/signup
- **Counter:** SlowAPI rate limiter (see `app/core/ratelimit.py`) · Cloudflare WAF rules
- **Limits:** login 5/min/IP · signup 3/hour/IP · API 60/min/user

### Stored XSS in messages
- **Threat:** user sends `<script>` in WhatsApp message · viewed in CRM
- **Counter:** React auto-escapes JSX · no `dangerouslySetInnerHTML` w/ user content · CSP blocks inline scripts

### CSRF
- **Threat:** cross-origin form posts JWT-auth'd action
- **Counter:** JWT in Authorization header (not cookies) · SameSite=Strict on `sellia.tenant` cookie · CORS allowlist

### Browser extension supply chain
- **Threat:** attacker compromises Chrome Web Store publish account
- **Counter:** 2FA on dev account · code-signed builds in CI · manifest reviewed each release

## Compliance roadmap

- [ ] SOC 2 Type 1 (Vanta · ~3 months prep)
- [ ] GDPR DPA template per integrator
- [ ] LGPD (Brasil)
- [ ] Pen test before GA (HackerOne or Doyensec)
- [ ] Bug bounty program post-GA

## Incident response

1. Detection: Sentry alert + Cloudflare WAF + /metrics anomaly
2. Triage: on-call PagerDuty rotation
3. Containment: kill switch via env var · revoke compromised tokens
4. Notification: customers within 72h (GDPR Article 33)
5. Post-mortem: blameless · published internally within 14d
