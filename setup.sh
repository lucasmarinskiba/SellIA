#!/bin/bash
# Setup script — Inicia sistema completo

echo "🚀 Sellia Sales Automation — Setup Script"

# 1. Crear .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env with your API keys (Stripe, SendGrid, etc)"
fi

# 2. Crear database directory
mkdir -p ./data/postgres

# 3. Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# 4. Run migrations (if using Alembic)
echo "🗄️  Running database migrations..."
cd backend
# alembic upgrade head

# 5. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# 6. Start FastAPI backend
echo "🚀 Starting FastAPI backend..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# 7. Start frontend (if needed)
echo "⚡ Frontend ready at http://localhost:3000"
echo "🔌 Backend API at http://localhost:8000"
echo "📊 API Docs at http://localhost:8000/docs"

echo "✅ Setup complete!"
