# SellIA Deployment Guide

## Status ✅

- **Frontend**: Live on Vercel
  - URL: https://sellia-brain.vercel.app/sellia-brain
  - Auto-deploys on main push
  
- **Backend**: Ready for Fly.io
  - fly.toml configured
  - GitHub Actions workflow ready
  
- **Database**: SQLite (dev) → PostgreSQL (prod)

---

## Quick Deploy (Manual)

### 1. Install Fly CLI
```bash
curl -L https://fly.io/install.sh | sh
# Add ~/.fly/bin to PATH
```

### 2. Login
```bash
flyctl auth login
```

### 3. Deploy
```bash
cd backend
bash ../DEPLOY_FLY.sh
```

---

## Automated (GitHub Actions)

### 1. Get Fly Token
```bash
flyctl auth token
```

### 2. Add Secret
- GitHub Settings → Secrets → New
- Name: FLY_API_TOKEN
- Value: [token]

### 3. Push
```bash
git push origin main
# Workflow auto-deploys
```

---

## Production URLs

- Frontend: https://sellia-brain.vercel.app/sellia-brain
- Backend: https://api.selliaai.fly.dev
- API Health: https://api.selliaai.fly.dev/api/ping

---

## Next Steps

1. Run DEPLOY_FLY.sh locally or setup GitHub secrets
2. Monitor at https://fly.io/apps/selliaai
3. Add custom domain if needed
4. Configure SendGrid + Anthropic keys
