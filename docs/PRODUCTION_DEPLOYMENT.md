# SellIA Production Deployment Guide

Complete step-by-step guide for deploying SellIA to production across multiple platforms.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Database Setup](#database-setup)
5. [Backend Deployment](#backend-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Monitoring & Logging](#monitoring--logging)
8. [Security Hardening](#security-hardening)
9. [Scaling & Performance](#scaling--performance)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Docker & Docker Compose (latest versions)
- Git for version control
- PostgreSQL 16 client tools
- Redis CLI for cache management
- kubectl (for Kubernetes deployments)
- Terraform (for infrastructure as code)

### Required Accounts & Keys
- Database provider (AWS RDS, Heroku Postgres, Railway, etc.)
- Redis provider (AWS ElastiCache, Redis Labs, Railway)
- Email service (SendGrid, AWS SES)
- Payment processors (Stripe, MercadoPago)
- Monitoring (Datadog, Sentry)
- CDN (Cloudflare, AWS CloudFront)

### Recommended Infrastructure
- Minimum: 2 CPU cores, 4GB RAM
- Recommended: 4+ CPU cores, 8GB+ RAM for production
- Storage: 50GB+ for database and backups

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/selliaai.git
cd selliaai
```

### 2. Generate Secrets
```bash
# Generate 64-character secret key
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Generate strong passwords
openssl rand -base64 32  # Database password
openssl rand -base64 32  # Redis password
```

### 3. Configure .env.production
```bash
cp .env.production.example .env.production
# Edit .env.production with your values:
# - Database credentials
# - Redis credentials
# - API keys (Stripe, SendGrid, etc.)
# - Frontend URL
# - SSL certificates path
```

### 4. Generate SSL Certificates
```bash
# Using Let's Encrypt (recommended)
certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Copy certificates to nginx/ssl directory
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown 1000:1000 nginx/ssl/*
sudo chmod 644 nginx/ssl/*
```

## Docker Deployment

### 1. Build Images
```bash
# Build backend image
docker build -f Dockerfile.backend -t selliaai/backend:latest .

# Build frontend image
docker build -f frontend/Dockerfile -t selliaai/frontend:latest ./frontend
```

### 2. Push to Registry
```bash
# Login to Docker Hub or private registry
docker login

# Tag images
docker tag selliaai/backend:latest yourusername/selliaai-backend:latest
docker tag selliaai/frontend:latest yourusername/selliaai-frontend:latest

# Push images
docker push yourusername/selliaai-backend:latest
docker push yourusername/selliaai-frontend:latest
```

### 3. Run Docker Compose
```bash
# Create volumes and networks
docker network create sellianet
docker volume create postgres_data
docker volume create redis_data

# Start services
docker-compose -f docker-compose.yml up -d

# Verify services
docker-compose ps
docker-compose logs -f
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed initial data (optional)
docker-compose exec backend python -m app.scripts.seed_database
```

## Database Setup

### 1. PostgreSQL Configuration
```bash
# Connect to PostgreSQL
psql postgresql://selliauser:password@localhost:5432/selliadb

# Enable required extensions
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

# Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sales_cycles_status ON sales_cycles(status);
CREATE INDEX idx_automations_enabled ON automations(enabled);
```

### 2. Backup Configuration
```bash
# Create backup script at scripts/backup.sh
#!/bin/bash
BACKUP_DIR=/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump postgresql://selliauser:$DB_PASSWORD@localhost:5432/selliadb > $BACKUP_DIR/backup_$TIMESTAMP.sql
gzip $BACKUP_DIR/backup_$TIMESTAMP.sql

# Add to crontab for daily backups
0 2 * * * /app/scripts/backup.sh
```

### 3. Connection Pooling
```bash
# Update backend/app/core/database.py
from sqlalchemy.pool import QueuePool

# Configure pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
)
```

## Backend Deployment

### 1. Uvicorn Configuration
```bash
# Production startup command (from Dockerfile.backend)
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --access-log
```

### 2. Health Checks
```bash
# Add health endpoint to backend/app/main.py
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis()
    }
```

### 3. Logging Configuration
```bash
# Configure structured logging in production
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## Frontend Deployment

### 1. Build Next.js Production Bundle
```bash
cd frontend
npm install
npm run build
npm start
```

### 2. Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_STRIPE_KEY
```

### 3. Alternative: Self-Hosted Frontend
```bash
# Using Docker
docker build -f frontend/Dockerfile -t selliaai/frontend .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  selliaai/frontend
```

### 4. CDN Configuration
```bash
# Cloudflare setup
1. Add site to Cloudflare
2. Enable Caching Rules:
   - Cache HTML: 1 hour
   - Cache JS/CSS: 1 year
   - Cache images: 30 days
3. Enable HTTP/2, BROTLI compression
4. Set minification to enabled
5. Enable HTTP/3 (QUIC)
```

## Monitoring & Logging

### 1. Datadog Setup
```bash
# Install agent
curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh | bash

# Configure in docker-compose.yml
environment:
  DD_AGENT_HOST: datadog
  DD_TRACE_ENABLED: "true"
  DD_PROFILING_ENABLED: "true"
```

### 2. Sentry Configuration
```bash
# Update backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production",
)
```

### 3. CloudWatch Logs (AWS)
```bash
# Install CloudWatch agent
docker run -d \
  -v /var/run/docker.sock:/var/run/docker.sock \
  amazon/cloudwatch-agent:latest
```

### 4. Log Aggregation
```bash
# Example: ELK Stack (Elasticsearch, Logstash, Kibana)
# or Loki + Grafana for log visualization
```

## Security Hardening

### 1. HTTPS Enforcement
```nginx
# Already configured in nginx.conf
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 2. API Key Rotation
```bash
# Add to crontab for monthly rotation
0 0 1 * * /app/scripts/rotate_secrets.sh
```

### 3. Database Encryption
```bash
# Enable at-rest encryption (depends on provider)
# AWS RDS: Enable encryption in parameter group
# PostgreSQL: Use pgcrypto extension
```

### 4. DDoS Protection
```bash
# Cloudflare DDoS protection already enabled
# Nginx rate limiting configured
# Consider Cloudflare's Bot Management tier
```

### 5. CORS Configuration
```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Scaling & Performance

### 1. Horizontal Scaling (Docker Swarm)
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml selliaai

# Scale services
docker service scale selliaai_backend=3 selliaai_frontend=2
```

### 2. Kubernetes Deployment
```bash
# Create namespace
kubectl create namespace selliaai

# Apply manifests (see k8s/ directory)
kubectl apply -f k8s/ -n selliaai

# Scale deployment
kubectl scale deployment backend --replicas=3 -n selliaai
```

### 3. Database Query Optimization
```sql
-- Check slow queries
SELECT * FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC;

-- Analyze query plans
EXPLAIN ANALYZE SELECT ...;
```

### 4. Redis Optimization
```bash
# Monitor Redis memory
redis-cli INFO memory

# Configure memory policies
CONFIG SET maxmemory-policy allkeys-lru
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs backend

# Validate configuration
docker-compose config

# Rebuild image
docker-compose build --no-cache backend
```

### Database Connection Issues
```bash
# Test connection
psql postgresql://user:pass@localhost:5432/selliadb -c "SELECT 1"

# Check pool connections
SELECT count(*) FROM pg_stat_activity;
```

### Performance Issues
```bash
# Check CPU/Memory
docker stats

# Monitor nginx
tail -f /var/log/nginx/access.log

# Check backend logs
docker-compose logs -f backend
```

### SSL Certificate Issues
```bash
# Check certificate validity
openssl s_client -connect yourdomain.com:443

# Renew certificate
certbot renew --force-renewal

# Copy new certificate
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
docker-compose restart nginx
```

## Maintenance

### Regular Tasks
- Daily: Monitor logs and alerts
- Weekly: Database backups verification
- Monthly: Security patches and updates
- Quarterly: Performance audits

### Update Process
```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build

# Update containers
docker-compose up -d

# Run migrations if needed
docker-compose exec backend alembic upgrade head
```

## Support & Resources

- Documentation: docs/README.md
- API Reference: docs/API.md
- Architecture: docs/ARCHITECTURE.md
- GitHub Issues: https://github.com/yourrepo/issues
