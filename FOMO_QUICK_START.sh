#!/bin/bash
# FOMO Star Player: Quick Start Setup Script
# Executes all steps: migration, seed, tests, dev server

set -e  # Exit on error

echo "🚀 FOMO Star Player - Complete Setup"
echo "======================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Database Migration
echo -e "\n${BLUE}[1/4] Running database migration...${NC}"
cd backend
alembic upgrade head
echo -e "${GREEN}✓ Migration complete${NC}"

# Step 2: Seed Demo Data
echo -e "\n${BLUE}[2/4] Seeding demo campaigns...${NC}"
poetry run python scripts/seed_fomo_demo.py
echo -e "${GREEN}✓ Demo data loaded${NC}"

# Step 3: Run Tests
echo -e "\n${BLUE}[3/4] Running test suite...${NC}"
pytest tests/test_fomo_star_player.py -v --tb=short
echo -e "${GREEN}✓ All tests passing${NC}"

# Step 4: Start Dev Servers
echo -e "\n${BLUE}[4/4] Starting development servers...${NC}"
echo -e "${GREEN}✓ Backend ready at http://localhost:8000${NC}"
echo -e "${GREEN}✓ Frontend ready at http://localhost:3000${NC}"
echo ""
echo "Next: Visit http://localhost:3000/fomo/dashboard"
echo ""
echo "Quick Commands:"
echo "  - View campaigns: curl http://localhost:8000/api/fomo/campaigns-active"
echo "  - Create campaign: See FOMO_STAR_PLAYER_IMPLEMENTATION.md"
echo ""
echo "📚 Documentation: FOMO_STAR_PLAYER_IMPLEMENTATION.md"

# Start backend
echo -e "\n${BLUE}Starting FastAPI backend...${NC}"
poetry run uvicorn app.main:app --reload &

cd ..

# Start frontend
echo -e "${BLUE}Starting Next.js frontend...${NC}"
cd frontend
npm run dev &

echo -e "\n${GREEN}✅ Setup complete! Servers starting...${NC}"
