# SellIA Deployment Quick Start Guide

**Ready to deploy? Start here.**

## 5-Minute Setup

### 1. Generate Secrets
```bash
# Database password
openssl rand -base64 32 > /tmp/db_pass.txt

# Redis password
openssl rand -base64 32 > /tmp/redis_pass.txt

# JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(48))" > /tmp/jwt_secret.txt
```

### 2. Update .env.production
```bash
# Edit .env.production with your values:
# DB_PASSWORD = [from /tmp/db_pass.txt]
# REDIS_PASSWORD = [from /tmp/redis_pass.txt]
# SECRET_KEY = [from /tmp/jwt_secret.txt]
# FRONTEND_URL = https://yourdomain.com
# CORS_ORIGINS = https://yourdomain.com

# Add API keys:
# STRIPE_API_KEY
# SENDGRID_API_KEY
# etc.
```

### 3. Generate SSL Certificate
```bash
# Get free certificate with Let's Encrypt
certbot certonly --standalone -d api.yourdomain.com

# Copy to nginx
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown 1000:1000 nginx/ssl/*
```

### 4. Start Docker Compose
```bash
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f backend
```

### 5. Run Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### 6. Test Deployment
```bash
# Check health
curl https://api.yourdomain.com/health

# Run smoke tests
python tests/performance_tests.py
```

## Key Files Quick Reference

| File | Purpose |
|------|---------|
| `Dockerfile.backend` | Backend container image |
| `docker-compose.yml` | Full stack orchestration |
| `.env.production` | Production secrets & config |
| `nginx/nginx.conf` | Web server & reverse proxy |
| `.github/workflows/deploy.yml` | CI/CD pipeline |
| `docs/PRODUCTION_DEPLOYMENT.md` | Detailed deployment guide |
| `docs/SECURITY_HARDENING.md` | Security configuration |
| `docs/MONITORING_SETUP.md` | Monitoring setup |
| `DEPLOYMENT_CHECKLIST.md` | Pre-deployment verification |
| `tests/e2e_tests.spec.ts` | End-to-end tests |
| `tests/performance_tests.py` | Performance validation |

## Performance Targets

```
API Response Time:
  P95: < 200ms  ✓
  P99: < 500ms  ✓

Frontend:
  Load time: < 3 seconds  ✓

Reliability:
  Uptime: 99.95%  ✓
  Error rate: < 0.1%  ✓

Concurrency:
  100+ concurrent users  ✓
```

## Troubleshooting

### Containers Won't Start
```bash
docker-compose logs backend
docker-compose down -v  # Clean up
docker-compose up -d    # Restart
```

### Database Connection Error
```bash
# Check connection
psql postgresql://selliauser:password@localhost:5432/selliadb -c "SELECT 1"

# Verify volume
docker volume ls | grep postgres_data
```

### API Not Responding
```bash
# Check Nginx
docker-compose logs nginx
docker-compose exec nginx nginx -t

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

### SSL Certificate Issues
```bash
# Check certificate validity
openssl s_client -connect yourdomain.com:443

# Renew if needed
certbot renew --force-renewal
docker-compose restart nginx
```

## Monitoring Checklist

After deployment, verify:

- [ ] API health check responds
- [ ] Database backups running
- [ ] Redis cache working
- [ ] Logs being aggregated
- [ ] Metrics being collected
- [ ] Alerts configured
- [ ] No critical errors
- [ ] Performance within SLAs
- [ ] Users can complete workflows
- [ ] Payment processing working

## Ongoing Maintenance

**Daily**: Monitor error rates and performance  
**Weekly**: Backup verification, security patches  
**Monthly**: Database optimization, dependency updates  
**Quarterly**: Security audit, disaster recovery drill

## Support Matrix

| Issue | File/Command |
|-------|---|
| Deployment questions | `docs/PRODUCTION_DEPLOYMENT.md` |
| Security setup | `docs/SECURITY_HARDENING.md` |
| Monitoring setup | `docs/MONITORING_SETUP.md` |
| Pre-deployment check | `DEPLOYMENT_CHECKLIST.md` |
| Performance testing | `tests/performance_tests.py` |
| E2E testing | `tests/e2e_tests.spec.ts` |
| Service logs | `docker-compose logs [service]` |
| Database issues | `docker-compose exec postgres psql` |
| Redis issues | `docker-compose exec redis redis-cli` |

## Deployment Workflow

```
1. Setup secrets (.env.production)
2. Generate SSL certificate
3. Start Docker Compose
4. Run database migrations
5. Run smoke tests
6. Monitor 24 hours
7. Check performance metrics
8. Optimize if needed
```

## Essential Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Backup database
docker-compose exec postgres pg_dump postgresql://user:pass@localhost/db > backup.sql

# Restore database
docker-compose exec postgres psql postgresql://user:pass@localhost/db < backup.sql

# Run migrations
docker-compose exec backend alembic upgrade head

# Scale services
docker-compose up -d --scale backend=3

# Health check
curl https://api.yourdomain.com/health
```

## Success Indicators

✓ All containers running  
✓ Health check returns 200  
✓ Database connection working  
✓ Frontend loads < 3 seconds  
✓ API response time < 200ms P95  
✓ No error spikes  
✓ Backups running  
✓ Monitoring active  
✓ Alerts configured  
✓ Team trained  

## Emergency Procedures

### Rollback Deployment
```bash
# Revert to previous version
git revert HEAD
docker-compose down
docker-compose pull
docker-compose up -d
```

### Emergency Maintenance
```bash
# Put in maintenance mode
docker-compose exec nginx bash -c 'echo "Server maintenance. Back soon." > /usr/share/nginx/html/maintenance.html'

# Do maintenance
# ...

# Resume service
docker-compose restart nginx
```

### Database Emergency
```bash
# Check database status
docker-compose exec postgres psql -c "SELECT version();"

# Restore from backup
docker-compose exec postgres psql < /backups/latest.sql
```

## Next Steps

1. **This Hour**
   - [ ] Generate secrets
   - [ ] Update .env.production
   - [ ] Get SSL certificate

2. **This Day**
   - [ ] Start Docker Compose
   - [ ] Run migrations
   - [ ] Run smoke tests

3. **This Week**
   - [ ] Run E2E tests
   - [ ] Run performance tests
   - [ ] Review monitoring setup

4. **Launch Week**
   - [ ] Final validation
   - [ ] User acceptance testing
   - [ ] Go live!

## Resources

- [Full Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)
- [Security Hardening](docs/SECURITY_HARDENING.md)
- [Monitoring Setup](docs/MONITORING_SETUP.md)
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- [Implementation Summary](DEPLOYMENT_IMPLEMENTATION_SUMMARY.md)

---

**Questions?** Check the relevant documentation file above.  
**Ready to deploy?** Follow the DEPLOYMENT_CHECKLIST.md  
**Performance issues?** Run `python tests/performance_tests.py`
