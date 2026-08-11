#!/bin/bash

# Pre-deployment verification checklist for v1.0.0
# Run this before executing production deployment

set -e

echo "======================================================================"
echo "SellIA v1.0.0 - PRE-DEPLOYMENT VERIFICATION"
echo "======================================================================"
echo ""

PASS=0
FAIL=0
WARNINGS=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_pass() {
  echo -e "${GREEN}✅ $1${NC}"
  ((PASS++))
}

check_fail() {
  echo -e "${RED}❌ $1${NC}"
  ((FAIL++))
}

check_warn() {
  echo -e "${YELLOW}⚠️  $1${NC}"
  ((WARNINGS++))
}

# ============================================================================
# 1. GIT STATUS
# ============================================================================
echo "1️⃣  GIT STATUS"

if git status | grep -q "working tree clean"; then
  check_pass "No uncommitted changes"
else
  check_fail "Uncommitted changes detected"
fi

if git tag | grep -q "v1.0.0"; then
  check_pass "Release tag v1.0.0 exists"
else
  check_fail "Release tag v1.0.0 missing"
fi

CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo "  Current commit: $CURRENT_COMMIT"

echo ""

# ============================================================================
# 2. TESTS STATUS
# ============================================================================
echo "2️⃣  TESTS"

if [ -f "tests/test_infrastructure.py" ]; then
  check_pass "Test suite exists"
else
  check_fail "Test suite not found"
fi

if [ -d ".next" ] || [ -f "frontend/package.json" ]; then
  check_pass "Frontend build files present"
else
  check_warn "Frontend not built yet (will build during deployment)"
fi

if [ -d "backend/__pycache__" ]; then
  check_pass "Backend modules compiled"
else
  check_warn "Backend not compiled yet (will compile during deployment)"
fi

echo ""

# ============================================================================
# 3. ENVIRONMENT VARIABLES
# ============================================================================
echo "3️⃣  ENVIRONMENT VARIABLES"

check_env() {
  if [ -z "${!1}" ]; then
    check_fail "$1 not set"
  else
    check_pass "$1 is configured"
  fi
}

check_env "DATABASE_URL"
check_env "REDIS_URL"
check_env "JWT_SECRET"
check_env "VAULT_ADDR"
check_env "VAULT_TOKEN"

echo ""

# ============================================================================
# 4. DOCKER
# ============================================================================
echo "4️⃣  DOCKER"

if command -v docker &> /dev/null; then
  check_pass "Docker installed"
  DOCKER_VERSION=$(docker --version | awk '{print $3}' | cut -d',' -f1)
  echo "  Version: $DOCKER_VERSION"
else
  check_fail "Docker not installed"
fi

if command -v docker-compose &> /dev/null; then
  check_pass "Docker Compose installed"
  DC_VERSION=$(docker-compose --version | awk '{print $3}')
  echo "  Version: $DC_VERSION"
else
  check_fail "Docker Compose not installed"
fi

if [ -f "docker-compose.prod.yml" ]; then
  check_pass "Production Docker Compose config exists"
else
  check_fail "Production Docker Compose config not found"
fi

echo ""

# ============================================================================
# 5. DATABASES & BACKUPS
# ============================================================================
echo "5️⃣  DATABASE & BACKUPS"

if [ -d "/backups" ]; then
  check_pass "Backup directory exists"
  BACKUP_COUNT=$(ls /backups/sellia_pre_v1.0.0_*.sql 2>/dev/null | wc -l)
  if [ $BACKUP_COUNT -gt 0 ]; then
    check_pass "Pre-deployment backups created ($BACKUP_COUNT backups)"
  else
    check_warn "No pre-v1.0.0 backups found yet (will create during deployment)"
  fi
else
  check_warn "Backup directory /backups not found"
fi

echo ""

# ============================================================================
# 6. SSL CERTIFICATES
# ============================================================================
echo "6️⃣  SSL CERTIFICATES"

if [ -f "/etc/ssl/certs/api.production.com.crt" ]; then
  check_pass "SSL certificate exists"
  EXPIRY=$(openssl x509 -in /etc/ssl/certs/api.production.com.crt -noout -enddate | cut -d'=' -f2)
  EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
  NOW_EPOCH=$(date +%s)
  DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

  if [ $DAYS_LEFT -gt 30 ]; then
    check_pass "SSL certificate valid for $DAYS_LEFT more days"
  else
    check_fail "SSL certificate expires in $DAYS_LEFT days (need > 30)"
  fi
else
  check_warn "SSL certificate not found at expected location"
fi

echo ""

# ============================================================================
# 7. MONITORING STACK
# ============================================================================
echo "7️⃣  MONITORING STACK"

check_service() {
  SERVICE=$1
  PORT=$2
  URL=$3

  if timeout 5 bash -c "echo >/dev/tcp/localhost/$PORT" 2>/dev/null; then
    check_pass "$SERVICE running on port $PORT"
  else
    check_warn "$SERVICE not accessible on port $PORT"
  fi
}

check_service "Prometheus" "9090" "http://localhost:9090/-/healthy"
check_service "Grafana" "3000" "http://localhost:3000/api/health"
check_service "Redis" "6379" ""
check_service "PostgreSQL" "5432" ""

echo ""

# ============================================================================
# 8. CONFIGURATION FILES
# ============================================================================
echo "8️⃣  CONFIGURATION FILES"

CONFIG_FILES=(
  "docker-compose.prod.yml"
  "infrastructure/pgbouncer.ini"
  "infrastructure/prometheus.yml"
  "backend/celery_app.py"
  "backend/app/middleware/logging.py"
  "backend/app/middleware/tracing.py"
)

for file in "${CONFIG_FILES[@]}"; do
  if [ -f "$file" ]; then
    check_pass "$file exists"
  else
    check_fail "$file missing"
  fi
done

echo ""

# ============================================================================
# 9. DOCUMENTATION
# ============================================================================
echo "9️⃣  DOCUMENTATION"

DOCS=(
  "PRODUCTION_DEPLOYMENT_EXECUTION.md"
  "DEPLOYMENT_RUNBOOK.md"
  "MONITORING_OBSERVABILITY.md"
  "LOCAL_TESTING_GUIDE.md"
  "TEST_RESULTS_SIMULATION.md"
)

for doc in "${DOCS[@]}"; do
  if [ -f "$doc" ]; then
    check_pass "$doc exists"
  else
    check_fail "$doc missing"
  fi
done

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "======================================================================"
echo "PRE-DEPLOYMENT VERIFICATION SUMMARY"
echo "======================================================================"
echo -e "${GREEN}✅ Passed: $PASS${NC}"
echo -e "${RED}❌ Failed: $FAIL${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}✅ PRE-DEPLOYMENT CHECK PASSED${NC}"
  echo ""
  echo "Ready to execute deployment:"
  echo "  1. Review PRODUCTION_DEPLOYMENT_EXECUTION.md"
  echo "  2. Notify stakeholders in Slack #production-deploys"
  echo "  3. Follow each deployment phase in order"
  echo "  4. Monitor metrics during rollout"
  echo "  5. Trigger rollback if any critical failure"
  echo ""
  exit 0
else
  echo -e "${RED}❌ PRE-DEPLOYMENT CHECK FAILED${NC}"
  echo ""
  echo "Fix all ❌ failures before proceeding with deployment"
  echo ""
  exit 1
fi
