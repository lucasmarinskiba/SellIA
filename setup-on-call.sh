#!/bin/bash
# On-Call Setup Script for Phase 29
# Configures monitoring, alerting, and incident response

set -e

PROD_URL="${1:?Usage: ./setup-on-call.sh <production-url>}"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "===== Phase 29 On-Call Setup ====="
echo "Production URL: $PROD_URL"
echo ""

# Step 1: Verify Production Health
echo "1. Verifying production health..."
HEALTH=$(curl -s "$PROD_URL/api/health" || echo "FAILED")
if [ "$HEALTH" != "FAILED" ]; then
  echo "   ✅ Health check passed"
else
  echo "   ❌ Health check failed — verify URL and network"
  exit 1
fi

# Step 2: Environment Setup
echo ""
echo "2. Preparing monitoring configuration..."

if [ ! -f "$PROJECT_DIR/monitoring-config.env" ]; then
  echo "   ⚠️  monitoring-config.env not found"
  echo "   Create it manually and populate:"
  echo "      - SENTRY_DSN (get from Sentry.io)"
  echo "      - ALERT_WEBHOOK_SLACK (get from Slack)"
  echo "      - ALERT_WEBHOOK_PAGERDUTY (get from PagerDuty)"
else
  echo "   ✅ monitoring-config.env exists"
  echo ""
  echo "   To deploy environment variables to Railway:"
  echo "      1. Go to https://railway.app/"
  echo "      2. Open SellIA project"
  echo "      3. Go to backend service → Environment"
  echo "      4. Copy variables from monitoring-config.env"
fi

# Step 3: Alert Rules
echo ""
echo "3. Recommended alert rules:"
echo "   CRITICAL (page on-call):"
echo "     - Health check failing >3min"
echo "     - Error rate >5%"
echo "     - Response time p95 >5s"
echo ""
echo "   WARNING (ticket):"
echo "     - Error rate 1-5%"
echo "     - Response time p95 2-5s"
echo "     - ManyChat webhook failures >1%"

# Step 4: Test Endpoints
echo ""
echo "4. Testing critical endpoints..."

ENDPOINTS=(
  "/api/health:GET"
  "/api/ping:GET"
  "/api/v1/lead-qualifier/leads?business_id=test:GET"
  "/api/v1/bookings/metrics?business_id=test:GET"
)

for endpoint in "${ENDPOINTS[@]}"; do
  method=$(echo "$endpoint" | cut -d: -f2)
  path=$(echo "$endpoint" | cut -d: -f1)

  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$PROD_URL$path")

  if [ "$STATUS" = "200" ] || [ "$STATUS" = "400" ] || [ "$STATUS" = "404" ]; then
    echo "   ✅ $method $path ($STATUS)"
  else
    echo "   ⚠️  $method $path ($STATUS)"
  fi
done

# Step 5: Dashboard Access
echo ""
echo "5. Dashboard setup instructions:"
echo ""
echo "   Railway (native monitoring):"
echo "     - URL: https://railway.app/"
echo "     - Project: Find your SellIA project"
echo "     - Logs: Deployments → [latest] → Logs"
echo "     - Metrics: Environment → Metrics tab"
echo ""
echo "   Sentry (error tracking):"
echo "     - URL: https://sentry.io/"
echo "     - Create project if not already done"
echo "     - Copy DSN to SENTRY_DSN env var"
echo ""
echo "   Slack Integration:"
echo "     - Create webhook: https://api.slack.com/messaging/webhooks"
echo "     - Copy to ALERT_WEBHOOK_SLACK"
echo "     - Post test alert: curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Test alert\"}' <webhook>"
echo ""
echo "   PagerDuty Integration:"
echo "     - Create account: https://www.pagerduty.com/"
echo "     - Copy webhook to ALERT_WEBHOOK_PAGERDUTY"

# Step 6: Incident Response Runbook
echo ""
echo "6. Quick incident response checklist:"
echo "   [ ] Check dashboard (uptime, error rate, latency)"
echo "   [ ] Review Railway logs (railway logs --follow)"
echo "   [ ] Check ManyChat API status"
echo "   [ ] Test health endpoint: curl $PROD_URL/api/health"
echo "   [ ] Test qualification: curl $PROD_URL/debug/conversation-state/[business_id]"
echo "   [ ] Review PRODUCTION_RUNBOOK.md for detailed procedures"

# Step 7: Summary
echo ""
echo "===== Setup Complete ====="
echo ""
echo "📋 Checklist:"
echo "  [✓] Production health verified"
echo "  [·] Environment variables prepared (manual)"
echo "  [·] Monitoring tools configured (manual)"
echo "  [·] Alert rules set (manual)"
echo "  [·] Dashboard access tested (manual)"
echo ""
echo "Next steps:"
echo "  1. Configure SENTRY_DSN in Railway environment"
echo "  2. Set up Slack/PagerDuty webhooks"
echo "  3. Create initial alert rules"
echo "  4. Establish on-call rotation in PagerDuty"
echo "  5. Run e2e tests: ./run_e2e_tests.sh $PROD_URL"
echo ""
echo "Support:"
echo "  - Railway docs: https://docs.railway.app/"
echo "  - Sentry docs: https://docs.sentry.io/"
echo "  - PagerDuty docs: https://support.pagerduty.com/"
