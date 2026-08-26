#!/bin/bash
# Requires: railway CLI installed + authenticated

cd backend
echo "Fetching production URL from Railway..."
echo ""

# Show all deployments (user selects latest)
railway deployment list --max 5 2>/dev/null || echo "Use: railway open (in browser)"

echo ""
echo "Manual method:"
echo "1. Run: railway open"
echo "2. Go to Deployments tab"
echo "3. Click latest deployment"
echo "4. Copy domain/URL"
echo "5. Run: ./run_e2e_tests.sh https://[url]"
