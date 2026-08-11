# Phase 26 Deployment Guide

## Overview

Phase 26 uses GitHub Actions for CI/CD with automated testing, building, and deployment to staging and production environments.

## Workflows

### 1. Test Workflow (`.github/workflows/test.yml`)

**Triggers**: Push to main/develop, pull requests

**Jobs**:
- `frontend-lint`: ESLint + TypeScript type checking
- `mobile-lint`: ESLint + TypeScript for mobile app
- `backend-tests`: pytest + PostgreSQL with coverage
- `e2e-tests`: Playwright tests (26a, 26c)
- `mobile-tests`: Jest tests
- `quality-gate`: Validates all tests pass before merge

**Duration**: ~10-15 minutes

### 2. Build Workflow (`.github/workflows/build.yml`)

**Triggers**: Push to main, git tags (v*)

**Jobs**:
- `build-frontend`: Next.js build → tar.gz artifact
- `build-backend`: Python build → tar.gz artifact
- `build-mobile`: EAS CLI build (APK/IPA)
- `build-docker`: Docker images → GHCR (GitHub Container Registry)
- `create-release`: GitHub release with artifacts

**Duration**: ~20-30 minutes

### 3. Deploy Workflow (`.github/workflows/deploy.yml`)

**Triggers**: 
- Staging: Push to main
- Production: Git tag (v*)

**Jobs**:
- `deploy-staging`: SSH deploy to staging.example.com
- `deploy-production`: CDN upload + backend deploy + DB migrations
- `rollback`: Auto-rollback on failure

**Duration**: ~5-10 minutes

## GitHub Secrets Setup

Required secrets in repository settings (`Settings → Secrets and variables → Actions`):

### Staging Secrets
```
STAGING_DEPLOY_KEY      - SSH private key for staging server
SLACK_WEBHOOK_URL       - Slack webhook for notifications
```

### Production Secrets
```
PROD_DEPLOY_KEY         - SSH private key for production server
PROD_DATABASE_URL       - Production database URL
AWS_ACCESS_KEY_ID       - AWS credentials for CDN
AWS_SECRET_ACCESS_KEY   - AWS credentials for CDN
CLOUDFRONT_ID           - CloudFront distribution ID
EAS_TOKEN               - Expo Application Services token
GITHUB_TOKEN            - Auto-generated, used for releases
```

## Local Development

### Setup
```bash
# Copy environment template
cp .env.example .env.local

# Edit with your local values
nano .env.local

# Start dev stack
docker-compose up -d
```

### Run Tests
```bash
# Frontend tests
cd frontend && npm run lint && npm run type-check

# Backend tests
cd backend && pytest tests/ -v

# E2E tests
cd frontend && npx playwright test

# Mobile tests
cd mobile && npm test
```

### Build Locally
```bash
# Frontend
cd frontend && npm run build

# Backend
cd backend && pip install -r requirements.txt

# Docker
docker-compose -f docker-compose.prod.yml build
```

## Deployment Process

### To Staging

**Automatic** on merge to main:
1. Tests run (all must pass)
2. Build artifacts created
3. Docker images pushed to GHCR
4. SSH deploy to staging server
5. Smoke tests verify deployment
6. Slack notification sent

```bash
# Manual staging deploy
git push origin main
```

### To Production

**Manual** via git tag:

```bash
# Create release tag
git tag -a v1.0.0 -m "Phase 26 Release v1.0.0"
git push origin v1.0.0
```

This triggers:
1. All tests must pass
2. Build frontend/backend/mobile
3. Docker images pushed with version tag
4. Frontend deployed to CDN (S3 + CloudFront invalidation)
5. Backend deployed via SSH
6. Database migrations run
7. Smoke tests verify production
8. GitHub release created with artifacts
9. Slack notification sent

**Automatic rollback** on any failure:
- Reverts backend to main branch
- Restarts containers
- Slack alert sent

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env.local)
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sellia
REDIS_URL=redis://localhost:6379
API_ENV=development
SECRET_KEY=dev-secret-key
```

### Production
All secrets managed via GitHub Actions secrets (never committed).

## Docker Images

### Image Naming
```
ghcr.io/sellia/sellia-backend:v1.0.0
ghcr.io/sellia/sellia-frontend:v1.0.0
```

### Tags
- `latest`: Latest main branch build
- `vX.Y.Z`: Release tag build
- `sha-abc123`: Specific commit build

### Registry
Images stored in GitHub Container Registry (GHCR):
```bash
# Pull production images
docker pull ghcr.io/sellia/sellia-backend:v1.0.0
docker pull ghcr.io/sellia/sellia-frontend:v1.0.0

# Run
docker-compose -f docker-compose.prod.yml up -d
```

## Database Migrations

Alembic migrations run automatically during deployment:

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Run migrations (automatic in deploy)
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring & Alerts

### Health Checks
All services expose health endpoints:
- Frontend: `GET /`
- Backend: `GET /health` → `{"status": "ok"}`
- Database: PostgreSQL liveness probe
- Redis: Redis PING

### Slack Notifications
Events posted to Slack channel:
- Test suite pass/fail
- Build completion
- Staging deployment
- Production deployment
- Rollback events

### Logs
View logs via GitHub Actions UI or:
```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# SSH to production
ssh deploy@api.production.com
sudo docker-compose logs -f
```

## Troubleshooting

### Test Failures
1. Check GitHub Actions log
2. Review test output
3. Run locally: `npm run lint`, `pytest`, `playwright test`
4. Fix issues, commit, push

### Build Failures
1. Check Docker build log
2. Verify all dependencies in requirements.txt/package.json
3. Test locally: `docker-compose build`
4. Fix Dockerfile, commit, push

### Deployment Failures
1. Check SSH access to server
2. Verify secrets in GitHub
3. Check server disk space: `ssh deploy@production "df -h"`
4. View server logs: `ssh deploy@production "docker-compose logs"`
5. Manual rollback: `ssh deploy@production "git checkout main && docker-compose up -d"`

### Database Migration Failures
1. Check migration file syntax
2. Test locally: `alembic upgrade head`
3. Verify database connectivity
4. Manual fix: SSH to server, run `alembic upgrade head --sql` to see SQL

## Release Checklist

- [ ] All tests pass locally
- [ ] E2E tests run without failures
- [ ] Version bump in package.json/setup.py
- [ ] CHANGELOG.md updated
- [ ] Staging deployment verified
- [ ] Smoke tests pass on staging
- [ ] Team approval
- [ ] Create git tag: `git tag -a v1.0.0 -m "Release notes"`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Monitor production deployment
- [ ] Verify production health
- [ ] Post release notes
- [ ] Notify stakeholders

## Rollback Procedure

### Automatic
Deployment automatically rolls back on failure.

### Manual
```bash
# SSH to production
ssh deploy@api.production.com

# Rollback to previous commit
cd /app
git checkout main
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl https://api.production.com/health
```

## References

- GitHub Actions: https://docs.github.com/en/actions
- Docker Compose: https://docs.docker.com/compose/
- Alembic Migrations: https://alembic.sqlalchemy.org/
- Playwright Testing: https://playwright.dev/
