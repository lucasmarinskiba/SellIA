#!/bin/bash
###############################################################################
# SellIA Production Deployment Script
# Deploys backend, database migrations, and frontend to production
#
# Usage: ./scripts/deploy-all.sh [backend|frontend|all] [dry-run]
# Example: ./scripts/deploy-all.sh all
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="./backend-mvp"
FRONTEND_DIR="./frontend"
DEPLOYMENT_TARGET="${1:-all}"
DRY_RUN="${2:-}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="deployment_${TIMESTAMP}.log"

###############################################################################
# Functions
###############################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}║${NC} $1" | tee -a "$LOG_FILE"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n" | tee -a "$LOG_FILE"
}

dry_run_notice() {
    if [ -n "$DRY_RUN" ]; then
        warning "DRY RUN MODE - No changes will be made"
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 is not installed. Please install it first."
        return 1
    fi
}

###############################################################################
# Pre-flight Checks
###############################################################################

preflight_checks() {
    header "PREFLIGHT CHECKS"

    log "Checking required tools..."
    check_command "git" || return 1
    check_command "node" || return 1
    check_command "python3" || return 1
    success "All required tools found"

    log "Checking git status..."
    if [ -n "$(git status --porcelain)" ]; then
        error "Git working directory is dirty. Please commit all changes first."
        git status --short
        return 1
    fi
    success "Git working directory clean"

    log "Checking environment configuration..."
    if [ ! -f ".env.production" ]; then
        error ".env.production not found"
        return 1
    fi
    success ".env.production found"

    log "Validating environment variables..."
    python3 scripts/validate-env.py || return 1

    success "All preflight checks passed"
}

###############################################################################
# Database Setup
###############################################################################

database_setup() {
    header "DATABASE SETUP"

    if [ "$DEPLOYMENT_TARGET" != "frontend" ]; then
        log "Checking database migrations..."
        cd "$BACKEND_DIR"

        if [ ! -f "alembic.ini" ]; then
            error "alembic.ini not found in $BACKEND_DIR"
            return 1
        fi

        log "Current migration status:"
        alembic current

        log "Migration history:"
        alembic history -l 5

        if [ -z "$DRY_RUN" ]; then
            log "Running database migrations..."
            alembic upgrade head
            success "Database migrations completed"
        else
            log "[DRY-RUN] Would run: alembic upgrade head"
        fi

        cd - > /dev/null
    fi
}

###############################################################################
# Backend Deployment
###############################################################################

deploy_backend() {
    header "BACKEND DEPLOYMENT (Fly.io)"

    if [ "$DEPLOYMENT_TARGET" == "frontend" ]; then
        warning "Skipping backend deployment (--frontend flag set)"
        return 0
    fi

    check_command "flyctl" || {
        error "Fly CLI not installed. Install with: curl -L https://fly.io/install.sh | sh"
        return 1
    }

    log "Getting Fly app status..."
    FLY_APP=$(grep '^app = ' fly.toml | cut -d'"' -f2)
    log "Deploying to Fly app: $FLY_APP"

    cd "$BACKEND_DIR"

    if [ -z "$DRY_RUN" ]; then
        log "Building Docker image..."
        docker build -t "sellias-backend:${TIMESTAMP}" .

        log "Deploying to Fly.io..."
        if flyctl deploy --remote-only --strategy rolling --wait-timeout 300; then
            success "Backend deployed to Fly.io"
        else
            error "Backend deployment failed"
            return 1
        fi

        log "Waiting for health check..."
        for i in {1..30}; do
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.sellia.app/healthz 2>/dev/null || echo "000")
            if [ "$HTTP_CODE" = "200" ]; then
                success "Health check passed (HTTP 200)"
                break
            fi
            log "Attempt $i/30: HTTP $HTTP_CODE"
            sleep 5
        done

        if [ "$HTTP_CODE" != "200" ]; then
            error "Health check failed after 30 attempts"
            return 1
        fi
    else
        log "[DRY-RUN] Would run:"
        log "  docker build -t sellias-backend:${TIMESTAMP} ."
        log "  flyctl deploy --remote-only --strategy rolling"
    fi

    cd - > /dev/null
}

###############################################################################
# Frontend Deployment
###############################################################################

deploy_frontend() {
    header "FRONTEND DEPLOYMENT (Vercel)"

    if [ "$DEPLOYMENT_TARGET" == "backend" ]; then
        warning "Skipping frontend deployment (--backend flag set)"
        return 0
    fi

    check_command "vercel" || {
        error "Vercel CLI not installed. Install with: npm install -g vercel"
        return 1
    }

    cd "$FRONTEND_DIR"

    log "Running type checks..."
    npx tsc --noEmit --skipLibCheck || {
        error "TypeScript type checking failed"
        return 1
    }
    success "Type checks passed"

    log "Building frontend..."
    if npm run build; then
        success "Frontend build succeeded"
    else
        error "Frontend build failed"
        return 1
    fi

    if [ -z "$DRY_RUN" ]; then
        log "Deploying to Vercel..."
        if vercel --prod --yes --token "$VERCEL_TOKEN"; then
            success "Frontend deployed to Vercel"
        else
            error "Frontend deployment failed"
            return 1
        fi
    else
        log "[DRY-RUN] Would run: vercel --prod --yes"
    fi

    cd - > /dev/null
}

###############################################################################
# Post-Deployment Verification
###############################################################################

verify_deployment() {
    header "POST-DEPLOYMENT VERIFICATION"

    log "Checking backend API health..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.sellia.app/healthz)
    if [ "$HTTP_CODE" = "200" ]; then
        success "Backend API responding (HTTP 200)"
    else
        error "Backend API not responding (HTTP $HTTP_CODE)"
        return 1
    fi

    log "Checking frontend..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://selldia.app)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "307" ]; then
        success "Frontend responding (HTTP $HTTP_CODE)"
    else
        warning "Frontend check returned HTTP $HTTP_CODE"
    fi

    log "Checking database connectivity..."
    if python3 << 'EOF'
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL: {version[0][:50]}...")
    conn.close()
    print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    exit(1)
EOF
    then
        success "Database connectivity verified"
    else
        error "Database connectivity check failed"
        return 1
    fi

    success "All verifications passed"
}

###############################################################################
# Notifications
###############################################################################

notify_deployment() {
    header "DEPLOYMENT NOTIFICATIONS"

    if [ -z "$DRY_RUN" ]; then
        COMMIT_SHA=$(git rev-parse --short HEAD)
        DEPLOYED_AT=$(date -u +'%Y-%m-%d %H:%M:%S UTC')

        log "Sending deployment notification to Slack..."
        if [ -n "${SLACK_WEBHOOK:-}" ]; then
            curl -s -X POST \
                -H 'Content-Type: application/json' \
                -d "{
                    \"text\": \"🚀 SellIA Production Deployed\",
                    \"blocks\": [
                        {
                            \"type\": \"section\",
                            \"text\": {
                                \"type\": \"mrkdwn\",
                                \"text\": \"✅ *SellIA Production Deployment Complete*\n\nCommit: \`$COMMIT_SHA\`\nDeployed: $DEPLOYED_AT\nTarget: $DEPLOYMENT_TARGET\"
                            }
                        }
                    ]
                }" \
                "$SLACK_WEBHOOK" || warning "Failed to send Slack notification"
            success "Slack notification sent"
        fi
    fi
}

###############################################################################
# Main Execution
###############################################################################

main() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}         SellIA Production Deployment Script v1.0         ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

    dry_run_notice

    # Run all checks and deployments
    if preflight_checks && \
       database_setup && \
       deploy_backend && \
       deploy_frontend && \
       verify_deployment && \
       notify_deployment; then

        header "DEPLOYMENT COMPLETE ✅"
        success "SellIA has been successfully deployed to production"
        log "Deployment log saved to: $LOG_FILE"
        return 0
    else
        header "DEPLOYMENT FAILED ❌"
        error "Deployment did not complete successfully"
        error "Check log file for details: $LOG_FILE"
        return 1
    fi
}

# Run main function
main "$@"
