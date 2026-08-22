#!/bin/bash
# Deploy script: check env vars + run migrations + verify

set -e

echo "════════════════════════════════════════════════════════════════"
echo "SellIA Multi-User Deployment: Migrations & Verification"
echo "════════════════════════════════════════════════════════════════"

# Step 1: Verify env vars
echo ""
echo "[Step 1/4] Checking Environment Variables..."
python verify_railway_config.py || {
  echo ""
  echo "[ERROR] Missing critical env vars. Add them to Railway first:"
  echo "  1. Go: https://railway.com/project/.../settings"
  echo "  2. Add: ENVIRONMENT, ANTHROPIC_API_KEY, SECRET_KEY, FRONTEND_URL"
  exit 1
}

# Step 2: Run migrations
echo ""
echo "[Step 2/4] Running Database Migrations..."
python run_migrations.py || {
  echo "[ERROR] Migrations failed. Check logs above."
  exit 1
}

# Step 3: Verify migrations applied
echo ""
echo "[Step 3/4] Verifying Migrations Applied..."
python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def check():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('''
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='public' AND table_name LIKE 'user_memory%'
            '''))
            tables = [row[0] for row in result.fetchall()]
            expected = ['user_memory', 'user_memory_events', 'user_preferences']
            for table in expected:
                if table in tables:
                    print(f'  [OK] Table: {table}')
                else:
                    print(f'  [FAIL] Missing table: {table}')
                    raise Exception(f'Table {table} not found')
    finally:
        await engine.dispose()

asyncio.run(check())
" || {
  echo "[ERROR] Tables not found. Migrations may have failed."
  exit 1
}

# Step 4: Run test
echo ""
echo "[Step 4/4] Running Multi-User Isolation Test..."
python test_memory_direct.py || {
  echo "[ERROR] Tests failed."
  exit 1
}

# Success
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "[SUCCESS] Deployment Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Deploy frontend to Vercel (git push origin main)"
echo "  2. Test multi-user: login as User A, then User B"
echo "  3. Verify isolation: each user has separate memory"
echo ""
echo "API endpoints ready:"
echo "  GET  /api/v1/memory/me"
echo "  PATCH /api/v1/memory/me"
echo "  POST /api/v1/memory/events"
echo "  POST /api/v1/memory/interests/{interest}"
echo "  POST /api/v1/memory/challenges/{challenge}"
echo ""
