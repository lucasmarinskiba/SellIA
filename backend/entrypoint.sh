#!/bin/bash
set -e

echo "🚀 SellIA Backend Entrypoint"
echo "================================"

# Run migrations if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    echo "📦 Running database migrations..."
    python run_migrations.py
    MIGRATIONS_EXIT=$?
    if [ $MIGRATIONS_EXIT -ne 0 ]; then
        echo "⚠️  Migrations failed with exit code $MIGRATIONS_EXIT (continuing startup)"
    else
        echo "✅ Migrations completed"
    fi
else
    echo "⚠️  DATABASE_URL not set, skipping migrations"
fi

echo "================================"
echo "🎯 Starting FastAPI application..."
echo ""

# Start FastAPI
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
