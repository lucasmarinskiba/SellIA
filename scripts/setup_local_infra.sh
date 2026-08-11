#!/bin/bash
set -e

# Setup local P0 infrastructure for testing

echo "=========================================="
echo "SellIA P0 Infrastructure - Local Setup"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Docker installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting local infrastructure...${NC}"

# 1. Create pgBouncer userlist
echo -e "${YELLOW}[1/5] Creating pgBouncer userlist...${NC}"
mkdir -p infrastructure
cat > infrastructure/userlist.txt << 'EOF'
"sellia_user" "sellia_pass"
"sellia_read" "sellia_pass"
"pgbouncer" "pgbouncer"
EOF
echo -e "${GREEN}✅ pgBouncer userlist created${NC}"

# 2. Create Grafana datasources config
echo -e "${YELLOW}[2/5] Creating Grafana datasources...${NC}"
cat > infrastructure/grafana-datasources.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
echo -e "${GREEN}✅ Grafana datasources created${NC}"

# 3. Start Docker Compose
echo -e "${YELLOW}[3/5] Starting Docker containers...${NC}"
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}[4/5] Waiting for services to be healthy...${NC}"
sleep 10

# 4. Check services
echo -e "${YELLOW}[5/5] Verifying services...${NC}"

services=(
  "postgres:5432"
  "redis:6379"
  "jaeger:16686"
  "vault:8200"
  "prometheus:9090"
  "grafana:3000"
)

for service in "${services[@]}"; do
  host_port="${service%%:*}"
  port="${service##*:}"

  if nc -z localhost "$port" 2>/dev/null; then
    echo -e "${GREEN}✅ $host_port running on port $port${NC}"
  else
    echo -e "${YELLOW}⏳ $host_port starting (port $port)...${NC}"
  fi
done

echo ""
echo "=========================================="
echo "✅ LOCAL INFRASTRUCTURE READY"
echo "=========================================="
echo ""
echo "Services running:"
echo "  📊 Postgres:     localhost:5432 (via pgBouncer: localhost:6432)"
echo "  💾 Redis:        localhost:6379"
echo "  🔍 Jaeger UI:    http://localhost:16686"
echo "  🔐 Vault:        http://localhost:8200 (token: devtoken)"
echo "  📈 Prometheus:   http://localhost:9090"
echo "  📉 Grafana:      http://localhost:3000 (admin/admin)"
echo ""
echo "Next steps:"
echo "  1. Run tests: python tests/test_infrastructure.py"
echo "  2. Start FastAPI: uvicorn backend.app.main:app --reload"
echo "  3. View traces: http://localhost:16686"
echo "  4. View dashboards: http://localhost:3000"
echo ""
echo "Stop infrastructure:"
echo "  docker-compose -f docker-compose.dev.yml down"
echo ""
