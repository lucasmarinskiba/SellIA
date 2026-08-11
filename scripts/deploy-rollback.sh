#!/bin/bash
set -e

# Rollback Script - Revert to previous stable version
# Usage: ./scripts/deploy-rollback.sh [reason]

REASON="${1:-Emergency rollback triggered}"
ROLLBACK_START=$(date '+%Y-%m-%d %H:%M:%S')

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
# STEP 1: Verify Rollback Safe
# ============================================================================
log "⚠️  INITIATING ROLLBACK"
log "Reason: $REASON"
log ""
log "Checking backup existence..."

BACKUP_FILE=$(ls -t /backups/sellia_pre_*.sql 2>/dev/null | head -1)
[ -z "$BACKUP_FILE" ] && error "No backup found"
log "Using backup: $BACKUP_FILE"

# Confirm rollback
read -p "Proceed with rollback? (yes/no): " CONFIRM
[[ "$CONFIRM" != "yes" ]] && error "Rollback cancelled"

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "ROLLING BACK TO PREVIOUS VERSION"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================================================
# STEP 2: Stop Current Deployment
# ============================================================================
log "Step 1: Stopping current services..."
docker-compose -f docker-compose.prod.yml down || true
log "✅ Services stopped"

# ============================================================================
# STEP 3: Revert Code
# ============================================================================
log "Step 2: Reverting code to main branch..."
git fetch --all
git checkout main || error "Checkout main failed"
git pull origin main || error "Pull failed"
log "✅ Code reverted to main"

# ============================================================================
# STEP 4: Restore Database
# ============================================================================
log "Step 3: Restoring database from backup..."
log "  File: $BACKUP_FILE"
log "  WARNING: This will overwrite production data"

read -p "Confirm database restore? (yes/no): " CONFIRM_DB
[[ "$CONFIRM_DB" != "yes" ]] && error "Rollback cancelled"

psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE" || error "Database restore failed"
log "✅ Database restored"

# ============================================================================
# STEP 5: Restart Services
# ============================================================================
log "Step 4: Restarting services..."
docker-compose -f docker-compose.prod.yml up -d backend || error "Backend start failed"
sleep 10

log "  Checking health..."
curl -f http://localhost:8000/health > /dev/null || error "Health check failed"
log "✅ Services restarted"

# ============================================================================
# STEP 6: Invalidate CDN
# ============================================================================
log "Step 5: Invalidating CDN cache..."
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_ID" \
  --paths "/*" > /dev/null || error "CDN invalidation failed"
log "✅ CDN cache cleared"

# ============================================================================
# STEP 7: Verify Rollback
# ============================================================================
log "Step 6: Verifying rollback..."

sleep 5

curl -f "http://localhost:8000/health" > /dev/null || error "Backend verification failed"
curl -f "https://${DOMAIN}" > /dev/null || error "Frontend verification failed"

log "✅ Rollback verified"

# ============================================================================
# Rollback Complete
# ============================================================================
ROLLBACK_END=$(date '+%Y-%m-%d %H:%M:%S')

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ ROLLBACK COMPLETE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Reason: $REASON"
log "Start: $ROLLBACK_START"
log "End: $ROLLBACK_END"
log ""
log "Next Steps:"
log "  1. Investigate root cause"
log "  2. Deploy fix on staging"
log "  3. Run full test suite"
log "  4. Schedule retry deployment"

notify_slack "⚠️  PRODUCTION ROLLBACK EXECUTED
Reason: $REASON
Previous backup restored
Services restarted and verified
Status: Main branch (pre-v1.0.0)

Investigation required before retry"

log ""
log "⚠️  Slack notification sent"
