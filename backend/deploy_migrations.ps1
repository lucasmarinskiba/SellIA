# Deploy script: check env vars + run migrations + verify (PowerShell)

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SellIA Multi-User Deployment: Migrations & Verification" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Step 1: Verify env vars
Write-Host ""
Write-Host "[Step 1/4] Checking Environment Variables..." -ForegroundColor Yellow

$envCheck = python verify_railway_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Missing critical env vars. Add them to Railway first:" -ForegroundColor Red
    Write-Host "  1. Go: https://railway.com/project/.../settings" -ForegroundColor Red
    Write-Host "  2. Add: ENVIRONMENT, ANTHROPIC_API_KEY, SECRET_KEY, FRONTEND_URL" -ForegroundColor Red
    exit 1
}

# Step 2: Run migrations
Write-Host ""
Write-Host "[Step 2/4] Running Database Migrations..." -ForegroundColor Yellow

$migrations = python run_migrations.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Migrations failed. Check logs above." -ForegroundColor Red
    exit 1
}

# Step 3: Verify migrations applied
Write-Host ""
Write-Host "[Step 3/4] Verifying Migrations Applied..." -ForegroundColor Yellow

$verifyScript = @"
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
"@

$verifyScript | python
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Tables not found. Migrations may have failed." -ForegroundColor Red
    exit 1
}

# Step 4: Run test
Write-Host ""
Write-Host "[Step 4/4] Running Multi-User Isolation Test..." -ForegroundColor Yellow

python test_memory_direct.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Tests failed." -ForegroundColor Red
    exit 1
}

# Success
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "[SUCCESS] Deployment Complete!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. Deploy frontend to Vercel (git push origin main)" -ForegroundColor Green
Write-Host "  2. Test multi-user: login as User A, then User B" -ForegroundColor Green
Write-Host "  3. Verify isolation: each user has separate memory" -ForegroundColor Green
Write-Host ""
Write-Host "API endpoints ready:" -ForegroundColor Green
Write-Host "  GET  /api/v1/memory/me" -ForegroundColor Green
Write-Host "  PATCH /api/v1/memory/me" -ForegroundColor Green
Write-Host "  POST /api/v1/memory/events" -ForegroundColor Green
Write-Host "  POST /api/v1/memory/interests/{interest}" -ForegroundColor Green
Write-Host "  POST /api/v1/memory/challenges/{challenge}" -ForegroundColor Green
Write-Host ""
