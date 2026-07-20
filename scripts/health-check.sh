#!/bin/bash
###############################################################################
# SellIA Production Health Check Script
# Monitors critical systems and alerts on issues
#
# Usage: ./scripts/health-check.sh [interval_seconds]
# Example: ./scripts/health-check.sh 60 (checks every 60 seconds)
###############################################################################

set -euo pipefail

# Configuration
INTERVAL="${1:-300}"  # Default: check every 5 minutes
MAX_RETRIES=3
RETRY_DELAY=5

# Thresholds
API_LATENCY_THRESHOLD_MS=200
ERROR_RATE_THRESHOLD_PERCENT=1
DB_CONN_WARNING_THRESHOLD=15

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

###############################################################################
# Functions
###############################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

###############################################################################
# Health Checks
###############################################################################

check_api_health() {
    log "Checking API health..."

    START_TIME=$(date +%s%N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://api.sellia.app/healthz 2>/dev/null || echo "000")
    END_TIME=$(date +%s%N)

    LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

    if [ "$HTTP_CODE" = "200" ]; then
        if [ $LATENCY_MS -lt $API_LATENCY_THRESHOLD_MS ]; then
            success "API health: HTTP $HTTP_CODE (${LATENCY_MS}ms)"
            return 0
        else
            warning "API slow: HTTP $HTTP_CODE (${LATENCY_MS}ms, threshold: ${API_LATENCY_THRESHOLD_MS}ms)"
            return 0
        fi
    else
        error "API unhealthy: HTTP $HTTP_CODE"
        return 1
    fi
}

check_database() {
    log "Checking database connectivity..."

    if python3 << 'EOF'
import os
import sys
import psycopg2
import time

try:
    start = time.time()
    conn = psycopg2.connect(os.getenv("DATABASE_URL", ""))
    elapsed = (time.time() - start) * 1000

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pg_stat_activity;")
    active_connections = cursor.fetchone()[0]

    cursor.execute("SELECT datsize FROM pg_database_size(current_database());")
    db_size = cursor.fetchone()[0]

    conn.close()

    print(f"Database OK (connected in {elapsed:.0f}ms, {active_connections} active connections, {db_size/1024/1024:.1f}MB)")
    sys.exit(0)
except Exception as e:
    print(f"Database FAILED: {e}")
    sys.exit(1)
EOF
    then
        success "Database: Connected"
        return 0
    else
        error "Database: Connection failed"
        return 1
    fi
}

check_redis() {
    log "Checking Redis connectivity..."

    # Extract Redis host/port from REDIS_URL
    # Format: redis://:password@host:port/db
    REDIS_URL="${REDIS_URL:-}"
    if [ -z "$REDIS_URL" ]; then
        warning "Redis: REDIS_URL not set, skipping"
        return 0
    fi

    if python3 << 'EOF'
import os
import redis

try:
    r = redis.from_url(os.getenv("REDIS_URL", ""))
    r.ping()
    info = r.info()
    print(f"Redis OK (keys: {info.get('db0', {}).get('keys', 0)})")
except Exception as e:
    print(f"Redis FAILED: {e}")
    exit(1)
EOF
    then
        success "Redis: Connected"
        return 0
    else
        error "Redis: Connection failed"
        return 1
    fi
}

check_frontend() {
    log "Checking frontend..."

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://selldia.app 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "307" ] || [ "$HTTP_CODE" = "301" ]; then
        success "Frontend: HTTP $HTTP_CODE"
        return 0
    else
        error "Frontend: HTTP $HTTP_CODE"
        return 1
    fi
}

check_payment_webhook() {
    log "Checking payment webhook..."

    # This would require authentication
    # For now, just check if endpoint responds
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS https://api.sellia.app/webhooks/stripe 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "405" ]; then
        success "Webhook endpoint: HTTP $HTTP_CODE"
        return 0
    else
        error "Webhook endpoint: HTTP $HTTP_CODE"
        return 1
    fi
}

check_email_service() {
    log "Checking email service..."

    # Check if SendGrid API key is set
    if [ -z "${SENDGRID_API_KEY:-}" ]; then
        warning "Email: SendGrid API key not set"
        return 0
    fi

    # Test email API
    if python3 << 'EOF'
import os
import requests

try:
    response = requests.get(
        "https://api.sendgrid.com/v3/user/email",
        headers={"Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}"},
        timeout=5
    )
    if response.status_code == 200:
        print("SendGrid API OK")
    else:
        print(f"SendGrid API error: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"Email service FAILED: {e}")
    exit(1)
EOF
    then
        success "Email: SendGrid API connected"
        return 0
    else
        error "Email: SendGrid API failed"
        return 1
    fi
}

check_ssl_certificate() {
    log "Checking SSL certificates..."

    BACKEND_EXPIRY=$(echo | openssl s_client -servername api.sellia.app -connect api.sellia.app:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2 || echo "UNKNOWN")
    FRONTEND_EXPIRY=$(echo | openssl s_client -servername selldia.app -connect selldia.app:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2 || echo "UNKNOWN")

    if [ "$BACKEND_EXPIRY" != "UNKNOWN" ] && [ "$FRONTEND_EXPIRY" != "UNKNOWN" ]; then
        success "SSL: Backend expires $BACKEND_EXPIRY"
        success "SSL: Frontend expires $FRONTEND_EXPIRY"
        return 0
    else
        warning "SSL: Could not verify expiry dates"
        return 0
    fi
}

check_monitoring_pipeline() {
    log "Checking monitoring pipeline..."

    # Check if Sentry is receiving events
    if [ -z "${SENTRY_DSN:-}" ]; then
        warning "Monitoring: Sentry DSN not set"
        return 0
    fi

    # Check recent error count (this would require Sentry API token)
    # For now, just acknowledge configuration
    success "Monitoring: Sentry configured"
    return 0
}

###############################################################################
# Summary Report
###############################################################################

generate_report() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                 HEALTH CHECK SUMMARY${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "\nTime: $(date +'%Y-%m-%d %H:%M:%S')"
    echo -e "Environment: production"
    echo -e "Interval: $INTERVAL seconds\n"
    echo -e "Components checked:"
    echo -e "  • API Server"
    echo -e "  • PostgreSQL Database"
    echo -e "  • Redis Cache"
    echo -e "  • Frontend Deployment"
    echo -e "  • Payment Webhook"
    echo -e "  • Email Service"
    echo -e "  • SSL Certificates"
    echo -e "  • Monitoring Pipeline"
    echo ""
}

###############################################################################
# Main Loop
###############################################################################

run_health_checks() {
    FAILED=0

    check_api_health || ((FAILED++))
    check_database || ((FAILED++))
    check_redis || ((FAILED++))
    check_frontend || ((FAILED++))
    check_payment_webhook || ((FAILED++))
    check_email_service || ((FAILED++))
    check_ssl_certificate || ((FAILED++))
    check_monitoring_pipeline || ((FAILED++))

    echo ""
    if [ $FAILED -eq 0 ]; then
        success "All systems nominal"
    else
        error "$FAILED critical checks failed"
    fi

    return $FAILED
}

main() {
    generate_report

    if [ "$INTERVAL" -eq 0 ] || [ -z "$INTERVAL" ]; then
        # Single run mode
        log "Running single health check..."
        run_health_checks
        exit $?
    else
        # Continuous monitoring mode
        log "Starting continuous monitoring (every ${INTERVAL}s)..."
        log "Press Ctrl+C to stop"
        echo ""

        while true; do
            run_health_checks
            LAST_STATUS=$?

            # Show status bar
            if [ $LAST_STATUS -eq 0 ]; then
                echo -e "${GREEN}[●] All systems nominal${NC}"
            else
                echo -e "${RED}[●] $LAST_STATUS issues detected${NC}"
            fi

            # Sleep and check next cycle
            log "Waiting ${INTERVAL}s for next check..."
            sleep "$INTERVAL"
        done
    fi
}

# Trap Ctrl+C
trap 'echo -e "\n${BLUE}Health check stopped${NC}"; exit 0' INT TERM

# Run main
main "$@"
