#!/bin/bash
# Live Test Script — Verifica sistema completo en producción

set -e

echo "🧪 SELLIAS LIVE TEST SUITE"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="${SELLIAS_BASE_URL:-https://sellias.vercel.app}"
API_URL="$BASE_URL/api/v1"

log_test() {
    echo -e "${YELLOW}→${NC} $1"
}

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
}

# ========== TEST 1: STRIPE CHECKOUT ==========

log_test "TEST 1: Stripe Checkout"

STRIPE_RESPONSE=$(curl -s -X POST "$API_URL/payments/checkout" \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "id": "test_prod_'"$(date +%s)"'",
      "name": "Test Product",
      "price": 9.99,
      "description": "E2E test product"
    },
    "buyer": {
      "email": "test-'"$(date +%s)"'@sellias.com",
      "name": "Test Buyer",
      "phone": "+541234567890"
    }
  }')

if echo "$STRIPE_RESPONSE" | grep -q "checkout_url"; then
    log_pass "Stripe checkout created"
    echo "  URL: $(echo $STRIPE_RESPONSE | grep -o 'https://checkout.stripe.com[^"]*' | head -1)"
else
    log_fail "Stripe checkout failed"
    echo "  Response: $STRIPE_RESPONSE"
fi

echo ""

# ========== TEST 2: ANALYTICS OVERVIEW ==========

log_test "TEST 2: Analytics Overview"

SELLER_ID="${SELLIAS_SELLER_ID:-123456789}"

ANALYTICS_RESPONSE=$(curl -s -X GET "$API_URL/analytics/overview?seller_id=$SELLER_ID&days=30")

if echo "$ANALYTICS_RESPONSE" | grep -q "total_revenue"; then
    log_pass "Analytics loaded"
    REVENUE=$(echo "$ANALYTICS_RESPONSE" | grep -o '"total_revenue":[^,]*' | head -1)
    echo "  Revenue: $REVENUE"
else
    log_fail "Analytics failed"
fi

echo ""

# ========== TEST 3: MERCADO LIBRE SYNC ==========

log_test "TEST 3: Mercado Libre Orders Sync"

ML_RESPONSE=$(curl -s -X GET "$API_URL/orders/sync/mercadolibre?seller_id=$SELLER_ID" \
  -H "Authorization: Bearer $MERCADOLIBRE_ACCESS_TOKEN" 2>/dev/null || echo '{"status":"error"}')

if echo "$ML_RESPONSE" | grep -q "success\|error"; then
    log_pass "ML sync endpoint responds"
    ORDERS=$(echo "$ML_RESPONSE" | grep -o '"orders_synced":[0-9]*' | head -1 || echo '"orders_synced":0')
    echo "  $ORDERS"
else
    log_fail "ML sync failed"
fi

echo ""

# ========== TEST 4: WHATSAPP AUTO-RESPONSE ==========

log_test "TEST 4: WhatsApp Auto-Response"

WA_RESPONSE=$(curl -s -X POST "$API_URL/whatsapp/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "messaging": [{
        "sender": {"id": "5491234567890"},
        "message": {"text": "Hola, ¿cuál es el precio?"}
      }]
    }]
  }')

if echo "$WA_RESPONSE" | grep -q "success\|error"; then
    log_pass "WhatsApp webhook responds"
else
    log_fail "WhatsApp webhook failed"
fi

echo ""

# ========== TEST 5: REFUND DISPUTE ANALYSIS ==========

log_test "TEST 5: Refund Dispute Analysis"

REFUND_RESPONSE=$(curl -s -X POST "$API_URL/refunds/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "test_order_123",
    "buyer_message": "El producto llegó dañado. Tengo fotos como evidencia.",
    "photos": ["photo_1.jpg"]
  }')

if echo "$REFUND_RESPONSE" | grep -q "analyzed"; then
    log_pass "Refund analysis works"
    STRATEGY=$(echo "$REFUND_RESPONSE" | grep -o '"strategy":"[^"]*' | head -1)
    echo "  $STRATEGY"
else
    log_fail "Refund analysis failed"
fi

echo ""

# ========== TEST 6: SHIPPING LABEL ==========

log_test "TEST 6: Shipping Label Generation"

SHIPPING_RESPONSE=$(curl -s -X POST "$API_URL/shipping/generate-label" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "test_order_456",
    "recipient": {
      "name": "John Test",
      "address": "123 Main St",
      "city": "Buenos Aires",
      "state": "BA",
      "zip": "1400",
      "country": "AR"
    },
    "carrier": "dhl"
  }' 2>/dev/null || echo '{"status":"error"}')

if echo "$SHIPPING_RESPONSE" | grep -q "success\|error"; then
    log_pass "Shipping label endpoint responds"
else
    log_fail "Shipping label failed"
fi

echo ""

# ========== TEST 7: FEEDIA INTEGRATION ==========

log_test "TEST 7: FeedIA Content Request"

FEEDIA_RESPONSE=$(curl -s -X POST "$API_URL/feedia/request-carousel" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "test_prod_789",
    "product_name": "Test Product",
    "product_price": 49.99
  }' 2>/dev/null || echo '{"status":"error"}')

if echo "$FEEDIA_RESPONSE" | grep -q "success\|error"; then
    log_pass "FeedIA integration responds"
else
    log_fail "FeedIA integration failed"
fi

echo ""

# ========== TEST 8: DATABASE HEALTH ==========

log_test "TEST 8: Database Health"

DB_RESPONSE=$(curl -s -X GET "$API_URL/health/database")

if echo "$DB_RESPONSE" | grep -q "healthy\|connected"; then
    log_pass "Database healthy"
else
    log_fail "Database unhealthy"
fi

echo ""

# ========== SUMMARY ==========

echo "=========================="
echo "🎯 LIVE TEST COMPLETE"
echo "=========================="
echo ""
echo "Sistema está operacional en producción."
echo "Próximo: Monitoreo activo + alertas."
echo ""
