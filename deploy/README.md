# SellIA Production Deploy

End-to-end deploy stack. Target stack:

| Layer | Provider | Cost (start) |
|---|---|---|
| Frontend | **Vercel Pro** | $20/mo |
| Backend API | **Fly.io** (gru region · 2× shared-cpu-2x) | ~$15/mo |
| Workers | Fly.io (2× shared-cpu-1x) | ~$8/mo |
| Postgres | **Neon** (paid plan w/ branching) | $19/mo |
| Redis | **Upstash** | $0-10/mo |
| DNS + CDN | **Cloudflare** (free tier) | $0 |
| Storage | **Cloudflare R2** | $0.015/GB |
| Email | **Resend** + ImprovMX (forwarding) | $20/mo |
| Errors | **Sentry** hobby | $26/mo |
| Analytics | **PostHog** Cloud | $0 (1M events) |
| **Total** | | **~$110/mo MVP** |

Scale: 10k MAU → ~$300/mo · 100k → ~$1.5k/mo.

## Pre-flight

```bash
# Tools
brew install flyctl terraform
npm i -g vercel

# Accounts
# · Fly.io · fly auth signup
# · Vercel · vercel login
# · Cloudflare · grab API token (Zone:DNS:Edit on sellia.app zone)
# · Neon · create project sellia · branch main + dev
# · Upstash · create Redis · TLS enabled
```

## Step 1 · DNS + zone

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars
# fill cloudflare_api_token + zone_id
../scripts/deploy-dns.sh
```

## Step 2 · Backend (Fly.io)

```bash
cd backend-mvp
cp .env.production.example .env.production
# fill all secrets
fly launch --copy-config --no-deploy   # create app
../deploy/scripts/deploy-backend.sh
```

Verify: `curl https://api.sellia.app/healthz`

## Step 3 · Seed demo data (one-time)

```bash
fly ssh console -C "python -m app.seed"
# Login at https://app.sellia.app · demo@sellia.app / demo-pw-change-me
```

## Step 4 · Frontend (Vercel)

```bash
cd frontend
cp .env.production.example .env.production
vercel link                          # one-time
vercel env pull .env.local           # sync vars
../deploy/scripts/deploy-frontend.sh
```

## Step 5 · Stripe webhooks

```bash
# Stripe CLI listens on prod
stripe login
stripe listen --forward-to https://api.sellia.app/webhooks/stripe
# Copy whsec_xxx → fly secrets set STRIPE_WEBHOOK_SECRET=whsec_xxx
```

In Stripe Dashboard: add webhook endpoint `https://api.sellia.app/webhooks/stripe` for events:
- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

## Step 6 · WhatsApp Business

1. Meta Business Manager → create app → WhatsApp product
2. Add phone number, get `phone_number_id`
3. Webhook URL: `https://api.sellia.app/webhooks/whatsapp` · verify token = `WA_VERIFY_TOKEN`
4. Subscribe to `messages` field
5. Generate system user access token (permanent) → `WA_ACCESS_TOKEN`

## Step 7 · CI/CD

GitHub repo:
- Settings → Secrets → add `FLY_API_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, optional `SLACK_DEPLOY_WEBHOOK`
- Settings → Environments → create `production` with required reviewers (manual approval)

Push to `main` triggers `deploy-prod.yml` · approves backend → frontend → Slack notify.

## Self-hosted alternative (k3s on Hetzner)

```bash
# On Hetzner CCX23 (8 vCPU · 16GB · ~$30/mo)
curl -sfL https://get.k3s.io | sh -
kubectl create namespace sellia
kubectl create secret generic sellia-secrets \
  --from-env-file=backend-mvp/.env.production \
  -n sellia
kubectl apply -f deploy/k8s/sellia.yaml

# cert-manager for TLS
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
```

## Rollback

```bash
fly releases                          # see versions
fly deploy --image registry.fly.io/sellia-api:v42  # pin to old image
vercel rollback                       # frontend
```

## Status page

Use **StatusPage.io** (free 1 page) or **Statuspal**.
- Add components: API · Frontend · Postgres · Redis · WhatsApp
- Pull from `/healthz` + Sentry + Fly metrics
- Public URL: `https://status.sellia.app` (CNAME to status provider)

## Monitoring checklist

- [ ] Sentry alerts on error rate > 1%
- [ ] Fly autoscaling 2-10 machines
- [ ] Neon connection pool 100 max
- [ ] Upstash Redis eviction policy `allkeys-lru`
- [ ] Cloudflare WAF rules enabled
- [ ] R2 lifecycle: archive screenshots > 90 days
- [ ] DMARC reports going to inbox · check weekly
