#!/bin/bash
# Comprehensive E2E test suite for Phase 29 (ManyChat + Auto-qualification + Booking)
# Usage: ./run_e2e_tests.sh https://backend.railway.app

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <production_url>"
  echo "Example: $0 https://backend.railway.app"
  exit 1
fi

BASE_URL="$1"
PASS=0
FAIL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_endpoint() {
  local name="$1"
  local method="$2"
  local endpoint="$3"
  local data="$4"
  local expected_code="$5"

  echo -n "Testing: $name... "

  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>&1)
  else
    response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
      -H "Content-Type: application/json" \
      -d "$data" 2>&1)
  fi

  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | head -n -1)

  if [[ "$http_code" == "$expected_code" ]] || [[ "$http_code" == "200" ]] || [[ "$http_code" == "202" ]]; then
    echo -e "${GREEN}✓${NC} ($http_code)"
    PASS=$((PASS + 1))
  else
    echo -e "${RED}✗${NC} (expected $expected_code, got $http_code)"
    echo "  Response: ${body:0:100}"
    FAIL=$((FAIL + 1))
  fi
}

echo "========================================"
echo "E2E Test Suite — SellIA Phase 29"
echo "========================================"
echo "Target: $BASE_URL"
echo ""

# Test 1: Health
echo "=== INFRASTRUCTURE ==="
test_endpoint "Health check" "GET" "/api/health" "" "200"
test_endpoint "Ping" "GET" "/api/ping" "" "200"
echo ""

# Test 2: Auth (if available)
echo "=== AUTHENTICATION ==="
test_endpoint "Signup" "POST" "/api/v1/auth/signup" \
  '{"email":"test@example.com","password":"TestPassword123","first_name":"Test","last_name":"User"}' "200"
echo ""

# Test 3: Business
echo "=== BUSINESS MANAGEMENT ==="
test_endpoint "List businesses" "GET" "/api/v1/businesses" "" "200"
test_endpoint "Create business" "POST" "/api/v1/businesses" \
  '{"name":"Test Business","industry":"software","type":"services"}' "200"
echo ""

# Test 4: Channels
echo "=== CHANNEL MANAGEMENT ==="
test_endpoint "List channels" "GET" "/api/v1/businesses/1/channels" "" "200"
test_endpoint "Create ManyChat channel" "POST" "/api/v1/businesses/1/channels" \
  '{"platform":"manychat","name":"Test","credentials":{"api_token":"test"}}' "201"
echo ""

# Test 5: ManyChat Webhook
echo "=== MANYCHAT WEBHOOK ==="
test_endpoint "Webhook (msg 1)" "POST" "/api/v1/businesses/webhook/manychat?token=test" \
  '{"business_id":"550e8400-e29b-41d4-a716-446655440000","subscriber_id":"123","first_name":"Juan","email":"juan@example.com","last_input_text":"Hello"}' "202"
test_endpoint "Webhook (msg 2)" "POST" "/api/v1/businesses/webhook/manychat?token=test" \
  '{"business_id":"550e8400-e29b-41d4-a716-446655440000","subscriber_id":"123","first_name":"Juan","email":"juan@example.com","last_input_text":"Price?"}' "202"
echo ""

# Test 6: Lead Qualification
echo "=== LEAD QUALIFICATION ==="
test_endpoint "List leads" "GET" "/api/v1/lead-qualifier/leads?business_id=550e8400-e29b-41d4-a716-446655440000" "" "200"
echo ""

# Test 7: Communication Angles
echo "=== COMMUNICATION ANGLES ==="
test_endpoint "Generate angles" "POST" "/api/v1/business-context/550e8400-e29b-41d4-a716-446655440000/generate-angles" \
  '{}' "200"
test_endpoint "Get context" "GET" "/api/v1/business-context/550e8400-e29b-41d4-a716-446655440000" "" "200"
echo ""

# Test 8: Booking Metrics
echo "=== BOOKING METRICS ==="
test_endpoint "Get webhook token" "GET" "/api/v1/bookings/webhook-token?business_id=550e8400-e29b-41d4-a716-446655440000" "" "200"
test_endpoint "Booking webhook" "POST" "/api/v1/bookings/webhook/550e8400-e29b-41d4-a716-446655440000?token=test" \
  '{"event":"invitee.created","payload":{"invitee":{"email":"juan@example.com"},"start_time":"2026-08-27T10:00:00Z"}}' "202"
test_endpoint "Get metrics" "GET" "/api/v1/bookings/metrics?business_id=550e8400-e29b-41d4-a716-446655440000" "" "200"
echo ""

# Test 9: Debug Endpoints
echo "=== DEBUG ENDPOINTS (should work) ==="
test_endpoint "Conversation state" "GET" "/api/v1/businesses/debug/conversation-state/550e8400-e29b-41d4-a716-446655440000" "" "200"
test_endpoint "LLM test" "POST" "/api/v1/businesses/debug/llm-test" '{}' "200"
echo ""

echo "========================================"
echo -e "Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "========================================"

if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some tests failed${NC}"
  exit 1
fi
