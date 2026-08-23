#!/bin/bash
set -e

echo "🚀 SellIA Backend Entrypoint"
echo "================================"

# Migrations disabled due to migration state issues
# TODO: Fix migration chain and re-enable
# ORM will create tables via Base.metadata.create_all() in sellbot.py startup
echo "⚠️  Alembic migrations temporarily disabled (using ORM fallback)"
echo "    Run 'python run_migrations.py' manually once DB is clean"

echo "================================"
echo "🎯 Starting FastAPI application..."
echo ""

# Start FastAPI
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
