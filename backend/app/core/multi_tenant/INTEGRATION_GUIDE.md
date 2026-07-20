# Multi-Tenant System Integration Guide

## Overview

Complete multi-tenant architecture (PHASE 4) with:
- Isolated tenants per organization
- Row-level security (RLS) + PostgreSQL schema isolation
- API key management with rotation & rate-limiting
- Billing & usage tracking
- Immutable audit logs for compliance

## Installation

### 1. Add Multi-Tenant Models to Database

```bash
# Add to alembic/env.py
from app.core.multi_tenant.models import (
    Tenant,
    TenantMember,
    TenantAPIKey,
    TenantBilling,
    AuditLog,
)

# Run migration
alembic revision --autogenerate -m "Add multi-tenant models"
alembic upgrade head
```

### 2. Update FastAPI App

```python
# app/main.py
from fastapi import FastAPI
from app.core.multi_tenant import TenantContextMiddleware
from app.core.database import get_db

app = FastAPI()

# Add tenant isolation middleware
app.add_middleware(TenantContextMiddleware, get_db_func=get_db)

# Now all requests are tenant-isolated
```

### 3. Update Dependencies

```python
# app/core/deps.py
from app.core.multi_tenant import (
    require_tenant_context,
    get_tenant_context,
    require_admin_access,
)

# In your handlers:
async def get_tenant_data(
    tenant_context: TenantContext = Depends(require_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    # tenant_context automatically injected with tenant_id, user_id, role
    tenant_id = tenant_context.tenant_id
    # All DB queries auto-filtered by tenant_id via middleware
```

## API Usage Examples

### Creating a Tenant

```python
from app.core.multi_tenant import TenantManager
from app.core.database import AsyncSessionLocal

async def create_org():
    async with AsyncSessionLocal() as db:
        manager = TenantManager()
        
        tenant = await manager.create_tenant(
            db=db,
            name="Acme Corporation",
            owner_id="user-uuid-here",
            tier="starter",
            description="SaaS customer"
        )
        
        print(f"Created tenant: {tenant.id}")
        return tenant
```

### Creating API Keys

```python
from app.core.multi_tenant import APIKeyManager

async def create_key():
    async with AsyncSessionLocal() as db:
        manager = APIKeyManager()
        service = manager.get_service(db)
        
        api_key, plaintext_key = await service.create_api_key(
            tenant_id="tenant-uuid",
            name="Production Key",
            created_by="user-uuid",
            scopes=["read", "write"],
            rate_limit_per_minute=1000,
        )
        
        # Return plaintext only once to user
        print(f"API Key (save this!): {plaintext_key}")
        # key_prefix visible in UI for debugging: {plaintext_key[:16]}
```

### Validating API Keys (in middleware)

```python
from app.core.multi_tenant import APIKeyManager

async def validate_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Extract key from Authorization header
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        key = auth[7:]
    else:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    manager = APIKeyManager()
    api_key = await manager.validate_key(
        db=db,
        key=key,
        ip_address=request.client.host,
    )
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Inject tenant context
    request.state.tenant_id = api_key.tenant_id
    request.state.api_key = api_key
```

### Tracking Billing Usage

```python
from app.core.multi_tenant import BillingTracker

async def api_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # ... process request ...
    
    # Record API call for billing
    tracker = BillingTracker()
    await tracker.record_api_call(
        db=db,
        tenant_id=request.state.tenant_id,
    )
    
    return {"status": "ok"}
```

### Logging Audit Events

```python
from app.core.multi_tenant import AuditLogger, AuditAction

async def sensitive_operation(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    # ... do something ...
    
    # Log the action
    logger_service = AuditLogger()
    await logger_service.log(
        db=db,
        tenant_id=tenant_context.tenant_id,
        action=AuditAction.DATA_EXPORTED,
        resource_type="user_data",
        change_type="export",
        user_id=user_id,
        ip_address="192.168.1.1",
        status="success",
        details={"format": "csv", "records": 1000},
    )
```

### Migrating Existing Users

```python
from app.core.multi_tenant import TenantMigrator

async def migrate_user_batch():
    async with AsyncSessionLocal() as db:
        migrator = TenantMigrator()
        service = migrator.get_service(db)
        
        # Migrate single user
        tenant = await service.migrate_user_to_tenant(
            user_id="user-uuid",
            tenant_name="User's Workspace",
            tier="starter"
        )
        
        # Or bulk migrate
        result = await service.migrate_bulk_users(
            user_ids=["user-1", "user-2", "user-3"],
            tenant_tier="starter"
        )
        
        print(f"Migrated: {result['successful']}/{result['total']}")
```

## Endpoint Patterns

### Tenant Admin Endpoints

```python
from fastapi import APIRouter
from app.core.multi_tenant import require_admin_access, TenantContext

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

@router.post("/{tenant_id}/members")
async def invite_member(
    tenant_id: str,
    email: str,
    role: str = "member",
    tenant_context: TenantContext = Depends(require_admin_access),
):
    """
    Invite user to tenant (admin only).
    Automatic access check via middleware.
    """
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Not your tenant")
    
    # Invite member...
    return {"status": "invited"}


@router.get("/{tenant_id}/billing/usage")
async def get_usage(
    tenant_id: str,
    tenant_context: TenantContext = Depends(require_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """Get current billing period usage."""
    if tenant_context.tenant_id != tenant_id:
        raise HTTPException(status_code=403)
    
    from app.core.multi_tenant import BillingTracker
    
    tracker = BillingTracker()
    service = tracker.get_service(db)
    usage = await service.get_usage_stats(tenant_id)
    
    return usage
```

## Security Patterns

### Row-Level Security

All database queries are auto-filtered by tenant_id:

```python
async def get_user_data(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_context: TenantContext = Depends(require_tenant_context),
):
    # Middleware automatically adds WHERE tenant_id = current_tenant
    result = await db.execute(
        select(UserData).where(UserData.user_id == user_id)
    )
    # Only returns data belonging to current tenant
```

### API Key Scopes

```python
# Create key with limited scopes
api_key, plaintext = await service.create_api_key(
    tenant_id=tenant_id,
    name="Read-only Key",
    scopes=["read"],  # Only GET requests
)

# In middleware, check scope
if "write" in api_key.scopes:
    # Allow POST/PUT/DELETE
    pass
else:
    raise HTTPException(status_code=403, detail="Write access denied")
```

### IP Whitelisting

```python
# Create key with IP whitelist
api_key, plaintext = await service.create_api_key(
    tenant_id=tenant_id,
    name="Office Key",
    ip_whitelist=[
        "203.0.113.0/24",  # CIDR notation
        "198.51.100.1",    # Single IP
    ]
)

# Validation automatically checks IP
validated = await service.validate_api_key(
    key=plaintext,
    ip_address=request.client.host,
)
```

## Database Schema

### Key Tables

- **tenants**: Org container, schema isolation
- **tenant_members**: User membership + RBAC
- **tenant_api_keys**: Service integrations
- **tenant_billing**: Usage tracking & costs
- **audit_logs**: Immutable compliance trail

All have indexes for performance:

```sql
-- Tenant access patterns
INDEX ix_tenant_owner_active (owner_id, is_active)

-- API key validation (hot path)
INDEX ix_api_key_tenant_active (tenant_id, is_active, is_revoked)

-- Audit querying
INDEX ix_audit_tenant_action_time (tenant_id, action, created_at)

-- Billing lookups
INDEX ix_billing_status_period (status, billing_period_start)
```

## Scheduled Tasks (Celery)

```python
# tasks.py
from celery import shared_task
from app.core.database import AsyncSessionLocal
from app.core.multi_tenant import APIKeyManager, BillingTracker

@shared_task
def enforce_key_rotation():
    """Revoke API keys past rotation deadline."""
    async def run():
        async with AsyncSessionLocal() as db:
            manager = APIKeyManager()
            service = manager.get_service(db)
            await service.enforce_rotation_schedule()
    
    asyncio.run(run())


@shared_task
def finalize_billing_cycles():
    """End month, calculate costs, create invoices."""
    async def run():
        async with AsyncSessionLocal() as db:
            # Get all active tenants
            result = await db.execute(
                select(Tenant).where(Tenant.is_active == True)
            )
            tenants = result.scalars().all()
            
            for tenant in tenants:
                tracker = BillingTracker()
                service = tracker.get_service(db)
                await service.finalize_billing_cycle(str(tenant.id))
    
    asyncio.run(run())


# Add to beat schedule
CELERY_BEAT_SCHEDULE = {
    'enforce-key-rotation': {
        'task': 'app.tasks.enforce_key_rotation',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'finalize-billing': {
        'task': 'app.tasks.finalize_billing_cycles',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # Monthly
    },
}
```

## Compliance & Audit

### Querying Audit Logs

```python
from app.core.multi_tenant import AuditLogger

async def get_audit_report(
    tenant_id: str,
    action: str,
    db: AsyncSession,
):
    service = AuditLogger().get_service(db)
    
    logs, count = await service.list_tenant_audit_logs(
        tenant_id=tenant_id,
        action_filter=action,
        days_back=90,
        limit=1000,
    )
    
    return [
        {
            "timestamp": log.created_at.isoformat(),
            "action": log.action,
            "user": log.user_email,
            "ip": log.ip_address,
            "status": log.status,
        }
        for log in logs
    ]
```

### Exporting Audit for Compliance

```python
# For SOC2/GDPR audits
csv_data = await service.export_audit_logs(
    tenant_id=tenant_id,
    export_user_id=current_user.id,
    days_back=365,
)

# Save to S3 for audit trail
s3.put_object(
    Bucket='audit-exports',
    Key=f'tenant-{tenant_id}-audit-{datetime.now().date()}.csv',
    Body=csv_data,
)
```

## Testing

```bash
# Run all multi-tenant tests
pytest app/core/multi_tenant/tests.py -v

# Run specific test
pytest app/core/multi_tenant/tests.py::test_create_tenant -v

# With coverage
pytest app/core/multi_tenant/tests.py --cov=app.core.multi_tenant
```

## Performance Tuning

### Connection Pooling

```python
# app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # Connections to keep open
    max_overflow=10,        # Overflow connections if needed
    pool_timeout=30,        # Wait 30s for connection
    pool_recycle=1800,      # Recycle after 30 min
    pool_pre_ping=True,     # Verify connection health
)
```

### Query Optimization

```python
# Use joins instead of N+1 queries
result = await db.execute(
    select(Tenant)
    .options(selectinload(Tenant.members))
    .options(selectinload(Tenant.api_keys))
    .where(Tenant.owner_id == user_id)
)
tenants = result.scalars().all()

# Eager load relationships
for tenant in tenants:
    # members and api_keys already loaded, no extra queries
    print(len(tenant.members))
```

## Troubleshooting

### Issue: "Tenant context not found"

Usually means middleware not installed or tenant_id not extracted.

```python
# Check middleware is added
app.add_middleware(TenantContextMiddleware, get_db_func=get_db)

# Check request has tenant_id
# Path: /api/tenants/{tenant_id}/...
# Header: X-Tenant-ID: tenant-uuid
# Query: ?tenant_id=tenant-uuid
```

### Issue: "You do not have access to this tenant"

User is not a member of tenant or membership is inactive.

```python
# Check membership exists
result = await db.execute(
    select(TenantMember).where(
        and_(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == user_id,
            TenantMember.is_active == True,
        )
    )
)
member = result.scalar_one_or_none()
```

### Issue: API key validation failing

Key might be revoked, rotated, or IP blocked.

```python
# Check key status
key = await service.get_api_key(key_id)
print(f"Active: {key.is_active}, Revoked: {key.is_revoked}")
print(f"IP whitelist: {key.ip_whitelist}")
print(f"Last used: {key.last_used_at}")
```

## Next Steps

1. **Run migrations**: `alembic upgrade head`
2. **Add middleware**: `app.add_middleware(TenantContextMiddleware)`
3. **Migrate existing users**: Use `TenantMigrator.migrate_bulk_users()`
4. **Enable billing**: Connect to Stripe webhook handler
5. **Schedule tasks**: Configure Celery beat for key rotation & billing
6. **Monitor**: Track audit logs & usage stats
