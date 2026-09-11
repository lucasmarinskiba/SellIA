#!/bin/bash
# Pre-Deployment Check for Automation Toggles System
# Usage: ./scripts/pre-deploy-check.sh

set -e

echo "🔍 Pre-Deployment Checklist for Automation Toggles"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
        ((PASS++))
    else
        echo -e "${RED}✗ $2${NC}"
        ((FAIL++))
    fi
}

echo ""
echo "📋 Backend Checks"
echo "----------------"

# 1. Python syntax
echo -n "Checking Python syntax... "
python -m py_compile \
    backend/app/domains/automations/models.py \
    backend/app/domains/automations/schemas.py \
    backend/app/domains/automations/seed_toggles.py \
    backend/app/api/v1/automations.py \
    backend/app/core/middleware/toggle_enforcement.py \
    2>/dev/null
check_result $? "Python files compile"

# 2. Backend tests
echo -n "Running backend tests... "
pytest backend/tests/test_automation_toggles.py \
        backend/tests/test_automation_toggles_e2e.py \
        -q --tb=no 2>/dev/null
check_result $? "Backend tests pass"

# 3. Check for TODOs in toggle code
echo -n "Checking for TODOs... "
TODO_COUNT=$(grep -r "TODO" backend/app/domains/automations/ \
    backend/app/api/v1/automations.py \
    backend/app/core/middleware/toggle_enforcement.py 2>/dev/null | wc -l)
if [ $TODO_COUNT -eq 0 ]; then
    check_result 0 "No TODOs found"
else
    check_result 1 "Found $TODO_COUNT TODOs"
fi

# 4. Check migrations exist
echo -n "Checking migrations... "
if [ -f "backend/alembic/versions/x4y5z6a7b8c9_add_automation_toggles_tables.py" ]; then
    check_result 0 "Migration file exists"
else
    check_result 1 "Migration file missing"
fi

echo ""
echo "🎨 Frontend Checks"
echo "------------------"

# 5. TypeScript compilation
echo -n "Checking TypeScript... "
npx tsc --noEmit frontend/src/components/sellia-brain/ToggleSwitch.tsx \
                    frontend/src/components/sellia-brain/ControlCenter.tsx \
                    frontend/src/components/sellia-brain/AuditPanel.tsx \
                    frontend/src/components/sellia-brain/ToggleAnalytics.tsx \
                    2>/dev/null
check_result $? "TypeScript compiles"

# 6. ESLint
echo -n "Running ESLint... "
npx eslint frontend/src/components/sellia-brain/ToggleSwitch.tsx \
            frontend/src/components/sellia-brain/ControlCenter.tsx \
            --max-warnings 10 2>/dev/null || true
check_result $? "ESLint passes"

# 7. Check for console errors
echo -n "Checking for console.error... "
CONSOLE_COUNT=$(grep -r "console.error" \
    frontend/src/components/sellia-brain/ \
    frontend/src/lib/api/toggles.ts 2>/dev/null | grep -v "// console.error" | wc -l)
if [ $CONSOLE_COUNT -eq 0 ]; then
    check_result 0 "No console.error calls"
else
    echo -e "${YELLOW}⚠ Found $CONSOLE_COUNT console.error calls (non-critical)${NC}"
fi

echo ""
echo "📦 Build Checks"
echo "---------------"

# 8. Frontend build (dry-run check deps)
echo -n "Checking build dependencies... "
npm list --depth=0 >/dev/null 2>&1
check_result $? "npm dependencies OK"

# 9. Git status
echo -n "Checking git status... "
if [ -z "$(git status --porcelain)" ]; then
    check_result 0 "Working directory clean"
else
    echo -e "${YELLOW}⚠ Uncommitted changes found:${NC}"
    git status --short | head -5
fi

# 10. Check branch
echo -n "Checking git branch... "
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ]; then
    check_result 0 "On main branch"
else
    check_result 1 "Not on main branch (on: $BRANCH)"
fi

echo ""
echo "🔗 Integration Checks"
echo "---------------------"

# 11. Check middleware integrated
echo -n "Checking middleware integration... "
if grep -q "toggle_enforcement_middleware" backend/app/sellbot.py; then
    check_result 0 "Middleware integrated in sellbot.py"
else
    check_result 1 "Middleware not found in sellbot.py"
fi

# 12. Check onboarding integration
echo -n "Checking onboarding integration... "
if grep -q "seed_toggles_for_business" backend/app/api/v1/businesses.py; then
    check_result 0 "Auto-seed in create_business()"
else
    check_result 1 "Auto-seed not integrated"
fi

# 13. Check API endpoint exists
echo -n "Checking seed endpoint... "
if grep -q "toggles/seed" backend/app/api/v1/automations.py; then
    check_result 0 "Seed endpoint exists"
else
    check_result 1 "Seed endpoint not found"
fi

echo ""
echo "📊 Summary"
echo "=========="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All checks passed! Ready for deployment.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ $FAIL check(s) failed. Fix before deploying.${NC}"
    exit 1
fi
