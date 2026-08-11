#!/bin/bash
set -e

# Production Deployment Script v1.0.0
# Timeline: ~45 minutes
# Rollback: Available via deploy-rollback.sh

DEPLOY_START=$(date '+%Y-%m-%d %H:%M:%S')
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"
ENVIRONMENT="production"
VERSION="v1.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
  echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
  exit 1
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

notify_slack() {
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d @- << EOF
{
  "channel": "#production-deploys",
  "username": "Deployment Bot",
  "text": "$1"
}
EOF
}

# ============================================================================
# STEP 1: Pre-Deployment Verification (5 min)
# ============================================================================
log "Step 1: Pre-deployment verification"

log "  Checking git status..."
git status --porcelain | grep -v "^ M .env.local" && error "Uncommitted changes detected"

log "  Checking Docker..."
docker --version || error "Docker not installed"
docker-compose --version || error "Docker Compose not installed"

log "  Verifying tag v1.0.0..."
git tag | grep -q "v1.0.0" || error "Tag v1.0.0 not found"

log "  Checking environment variables..."
[ -z "$DATABASE_URL" ] && error "DATABASE_URL not set"
[ -z "$REDIS_URL" ] && error "REDIS_URL not set"
[ -z "$JWT_SECRET" ] && error "JWT_SECRET not set"

log "  Building Docker images (test)..."
docker-compose -f docker-compose.prod.yml build --dry-run > /dev/null || error "Docker build failed"

log "✅ Pre-deployment checks passed"

# ============================================================================
# STEP 2: Create Release Tag (2 min)
# ============================================================================
log "Step 2: Release tag verification"
log "  Tag: $(git show v1.0.0 | head -1)"
log "✅ Release tag ready"

# ============================================================================
# STEP 3: Database Migration (10 min)
# ============================================================================
log "Step 3: Database migration"

log "  Creating backup..."
BACKUP_FILE="/backups/sellia_pre_${VERSION}_$(date +%s).sql"
pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE" || error "Backup failed"
log "  Backup: $BACKUP_FILE"

log "  Running migrations..."
cd backend
alembic upgrade head || {
  warn "Migration failed, restoring backup..."
  psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"
  error "Migration rolled back"
}
cd ..

log "  Verifying migrations..."
CURRENT=$(cd backend && alembic current)
log "  Current revision: $CURRENT"
log "✅ Database migrations complete"

# ============================================================================
# STEP 4: Deploy Backend (15 min)
# ============================================================================
log "Step 4: Backend deployment"

log "  Checking out v1.0.0..."
git fetch --all
git checkout v1.0.0 || error "Checkout failed"

log "  Building backend image..."
docker-compose -f docker-compose.prod.yml build backend || error "Build failed"

log "  Stopping old backend..."
docker-compose -f docker-compose.prod.yml down backend || true

log "  Starting new backend..."
docker-compose -f docker-compose.prod.yml up -d backend || error "Start failed"

log "  Waiting for readiness..."
sleep 10
curl -f http://localhost:8000/health > /dev/null || error "Health check failed"

log "✅ Backend deployment complete"

# ============================================================================
# STEP 5: Deploy Frontend (10 min)
# ============================================================================
log "Step 5: Frontend deployment"

log "  Building frontend..."
cd frontend
npm run build || error "Frontend build failed"
cd ..

log "  Uploading to S3..."
aws s3 sync frontend/.next "s3://${S3_BUCKET}/.next" --delete || error "S3 sync failed"
aws s3 sync frontend/public "s3://${S3_BUCKET}/public" --delete || error "S3 sync failed"

log "  Invalidating CloudFront..."
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_ID" \
  --paths "/*" > /dev/null || error "CloudFront invalidation failed"

log "  Verifying frontend..."
sleep 5
curl -f "https://${DOMAIN}" > /dev/null || error "Frontend verification failed"

log "✅ Frontend deployment complete"

# ============================================================================
# STEP 6: Post-Deployment Verification (10 min)
# ============================================================================
log "Step 6: Post-deployment verification"

log "  Checking health endpoints..."
curl -f "http://localhost:8000/health" > /dev/null || error "Backend health check failed"
curl -f "http://localhost:8000/ready" > /dev/null || error "Backend readiness check failed"

log "  Checking database..."
psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null || error "Database connection failed"

log "  Checking cache..."
redis-cli -u "$REDIS_URL" ping || error "Redis connection failed"

log "  Checking logs..."
docker-compose logs --tail=50 backend | grep -i error && warn "Errors in backend logs"

log "✅ Post-deployment checks passed"

# ============================================================================
# STEP 7: Smoke Tests (5 min)
# ============================================================================
log "Step 7: Running smoke tests"

TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
  if curl -f -s "$1" > /dev/null; then
    log "  ✅ $2"
    ((TESTS_PASSED++))
  else
    error "  ❌ $2"
    ((TESTS_FAILED++))
  fi
}

test_endpoint "https://${DOMAIN}/api/v1/health" "API health"
test_endpoint "https://${DOMAIN}/api/v1/users/me" "User endpoint (authenticated)"

log "✅ Smoke tests: $TESTS_PASSED passed, $TESTS_FAILED failed"

# ============================================================================
# Deployment Complete
# ============================================================================
DEPLOY_END=$(date '+%Y-%m-%d %H:%M:%S')
DEPLOY_DURATION=$(($(date +%s) - $(date -d "$DEPLOY_START" +%s)))

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ DEPLOYMENT COMPLETE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Version: $VERSION"
log "Environment: $ENVIRONMENT"
log "Duration: ${DEPLOY_DURATION} seconds"
log "Start: $DEPLOY_START"
log "End: $DEPLOY_END"
log ""
log "Next: Monitor metrics in Grafana"
log "Rollback: ./scripts/deploy-rollback.sh"
log ""
log "Beta testing begins 2026-08-12"
log "Cohorts: Sales (20) + Ops (15) + Mobile (15) + Voice (10)"

# Notify Slack
notify_slack "✅ Production Deployment Complete
Version: $VERSION
Duration: ${DEPLOY_DURATION}s
Status: All checks passed
Monitoring: Grafana, Sentry
Next: Beta testing begins"

log "✅ Slack notification sent"
